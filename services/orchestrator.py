"""
文件路径: services/orchestrator.py
=========================================================
【接口说明】
def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
    '''
    批量处理
    返回字典包含:
    - "with_num": 纯文本（带序号） -> 用于复制
    - "no_num":   纯文本（无序号） -> 用于复制
    - "display_html": HTML格式（带链接） -> 用于界面显示
    '''
=========================================================
"""

import sys
import os
import time
import re
import difflib
import html
import traceback  # 【新增】用于打印详细错误堆栈
import config
from services import formatter
from services.api_engines.openalex_engine import OpenAlexEngine
from services.api_engines.crossref import CrossrefEngine
from services.api_engines.semantic_scholar import SemanticScholarEngine


# 【回退】不再引入 CnkiEngine


class Orchestrator:
    """总指挥"""

    def __init__(self):
        self.engines = []
        self._init_engines()

    def _init_engines(self):
        print("--- [调试] 正在初始化引擎 ---")
        if config.SourceConfig.OPENALEX_ENABLED: self.engines.append(OpenAlexEngine())
        if config.SourceConfig.CROSSREF_ENABLED: self.engines.append(CrossrefEngine())
        if config.SourceConfig.S2_ENABLED: self.engines.append(SemanticScholarEngine())
        # 【回退】删除了中文引擎加载逻辑
        print(f"--- [调试] 引擎初始化完毕，共加载 {len(self.engines)} 个引擎")

    def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
        """批量处理"""
        lines = raw_text_block.split('\n')
        list_with_num = []
        list_no_num = []
        list_html = []  # 用于存储 HTML 显示内容

        total = len(lines)

        for i, line in enumerate(lines):
            try:
                # === 核心处理逻辑包裹在 try 块中，防止单条报错导致程序闪退 ===
                original_line = line.strip()
                if not original_line:
                    continue

                print(f"--- [调试] 处理第 {i + 1} 条 ---")

                # 分离序号
                match = re.match(r'^\s*(\[\d+\]|\d+\.|\d+、|\(\d+\))\s*(.*)', original_line)
                prefix = ""
                clean_query = original_line
                if match:
                    prefix = match.group(1)
                    clean_query = match.group(2)

                # 处理单条 (现在返回 3 个值: 文本, 是否成功, URL)
                formatted_content, is_success, url = self._format_single_with_status(clean_query)

                # 通过 callback 发送状态: "PREV_OK" 或 "PREV_FAIL"
                if callback_signal:
                    progress = int(((i + 1) / total) * 100)
                    status_tag = "PREV_OK" if is_success else "PREV_FAIL"
                    next_msg = f"正在处理: {clean_query[:15]}..."

                    # 【核心修复】智能兼容 Qt 信号和普通函数
                    # 防止因为直接调用 Signal 对象导致 TypeError 从而引发 0xC0000409 崩溃
                    if hasattr(callback_signal, 'emit'):
                        # 如果是 Qt 信号，必须用 .emit()
                        callback_signal.emit(progress, f"{status_tag}|{next_msg}")
                    else:
                        # 如果是普通函数，直接调用
                        callback_signal(progress, f"{status_tag}|{next_msg}")

                # 1. 构建纯文本结果 (用于复制)
                list_no_num.append(formatted_content)
                full_text_line = f"{prefix} {formatted_content}" if prefix else formatted_content
                list_with_num.append(full_text_line)

                # 2. 构建 HTML 结果 (用于显示和点击)
                safe_text = html.escape(full_text_line)

                if is_success and url:
                    # 成功且有链接：直接在 style 属性里写死颜色为灰色 (#606266)，去掉下划线
                    html_line = (
                        f'<div style="margin-bottom: 12px;">'
                        f'<a href="{url}" style="color: #606266; text-decoration: none; font-weight: normal;" title="点击跳转原文: {url}">'
                        f'{safe_text}'
                        f'</a>'
                        f'</div>'
                    )
                elif is_success:
                    # 成功但无链接
                    html_line = f'<div style="margin-bottom: 12px; color:#2c3e50;">{safe_text}</div>'
                else:
                    # 失败：用浅灰色显示，不加链接
                    html_line = f'<div style="margin-bottom: 12px; color:#95a5a6;">{safe_text}</div>'

                list_html.append(html_line)

                if i < total - 1:
                    time.sleep(config.MIN_REQUEST_INTERVAL)

            except Exception as e:
                # 【防崩兜底】万一某一行处理出错，打印错误，但不要让程序死掉
                print(f"❌ 第 {i + 1} 行处理发生严重错误: {e}")
                traceback.print_exc()  # 打印详细堆栈以便调试
                # 依然添加一条错误记录，保证结果对齐
                list_no_num.append(f"{line} (处理出错)")
                list_with_num.append(f"{line} (处理出错)")
                list_html.append(f'<div style="color:red;">处理出错: {html.escape(line)}</div>')

        return {
            "with_num": "\n\n".join(list_with_num),
            "no_num": "\n\n".join(list_no_num),
            "display_html": "".join(list_html)
        }

    def _format_single_with_status(self, query: str) -> (str, bool, str):
        """
        内部辅助方法
        返回: (格式化后的文本, 是否成功, 原文URL)
        """
        if not self.engines:
            return f"{query} ❌ (未启用API)", False, ""
        if len(query) < 4:
            return f"{query} ❌", False, ""

        is_pure_doi = "10." in query and "/" in query and len(query.split()) < 2
        if is_pure_doi: query = query.strip()

        # 【回退】移除了针对中文的引擎重排序逻辑，直接遍历英文引擎
        for engine in self.engines:
            try:
                citation_data = engine.search(query)
                if citation_data:
                    # 调用验证逻辑 (V3.1版本)
                    is_match, reason = self._validate_result(query, citation_data)
                    if is_match:
                        # 成功！返回 URL
                        return formatter.to_gbt7714(citation_data), True, citation_data.url
                    else:
                        print(f"   [校验失败] {engine.name} 结果被拦截: {reason}")
                        continue
            except Exception as e:
                print(f"   [引擎错误] {engine.name}: {e}")
                continue

        # 失败
        return f"{query} ❌", False, ""

    def format_single(self, query: str) -> str:
        """兼容旧接口"""
        res, _, _ = self._format_single_with_status(query)
        return res

    def _validate_result(self, user_query: str, data) -> (bool, str):
        """
        【保留 V3.1 核心修复】
        保留了短姓氏支持、标题确信豁免等英文优化逻辑。
        移除了中文特权通道。
        """
        if not data.title: return False, "无标题"

        # 【回退】移除了中文/本地解析的特权通道

        query_lower = user_query.lower()
        title_lower = data.title.lower()

        # 0. DOI 绝对信任
        if data.doi and len(data.doi) > 5 and data.doi.lower() in query_lower:
            return True, "DOI精确匹配"

        # 预处理：分词
        def get_tokens(text):
            # 增加对 None 的保护
            if not text: return []
            clean = re.sub(r'[^\w\s]', ' ', text)
            return [w for w in clean.split() if len(w) > 2]

        query_tokens = get_tokens(query_lower)
        title_tokens = get_tokens(title_lower)

        if not title_tokens: return False, "API标题无效"

        # 1. 标题词覆盖率
        match_count = sum(1 for w in title_tokens if w in query_tokens)
        coverage = match_count / len(title_tokens)

        # 标题确信豁免 (V3.1 保留)
        if coverage > 0.8:
            return True, f"标题高度吻合({coverage:.1%})"

        if coverage < 0.4:
            return False, f"标题差异过大({coverage:.1%})"

        # 2. 连词检测 (V3.1 保留)
        has_bigram = False
        if len(title_tokens) >= 2:
            for i in range(len(title_tokens) - 1):
                bigram = f"{title_tokens[i]} {title_tokens[i + 1]}"
                if bigram in query_lower:
                    has_bigram = True
                    break
        else:
            if title_tokens[0] in query_lower: has_bigram = True

        if not has_bigram and coverage < 0.8:
            return False, "无连续词重叠"

        # 3. 作者校验 (V3.1 保留)
        looks_like_has_author = "et al" in query_lower or "," in query_lower
        year_match = data.year and (str(data.year) in query_lower)

        author_match = False
        if data.authors:
            for auth in data.authors:
                if not auth: continue  # 保护空作者
                raw_auth_clean = re.sub(r'[^\w\s]', ' ', auth.lower())
                raw_parts = raw_auth_clean.split()
                for part in raw_parts:
                    # 放宽长度限制到 >= 2 (保留对 Li, Wu, Yao 的支持)
                    if len(part) >= 2 and part in query_lower:
                        author_match = True
                        break
                if author_match: break

        if looks_like_has_author:
            if not author_match:
                return False, "作者不匹配"
            if not year_match:
                if coverage < 0.9:
                    return False, "年份不匹配"
        else:
            if not year_match and coverage < 0.8:
                return False, "年份不匹配且标题存疑"

        return True, "验证通过"