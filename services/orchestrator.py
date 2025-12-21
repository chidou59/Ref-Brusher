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
import config
from services import formatter
from services.api_engines.openalex_engine import OpenAlexEngine
from services.api_engines.crossref import CrossrefEngine
from services.api_engines.semantic_scholar import SemanticScholarEngine


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
        print(f"--- [调试] 引擎初始化完毕，共加载 {len(self.engines)} 个引擎")

    def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
        """批量处理"""
        lines = raw_text_block.split('\n')
        list_with_num = []
        list_no_num = []
        list_html = []  # 用于存储 HTML 显示内容

        total = len(lines)

        for i, line in enumerate(lines):
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

        for engine in self.engines:
            try:
                citation_data = engine.search(query)
                if citation_data:
                    # 调用新的验证逻辑 V3.1
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
        【核心修复】兼容性优化 V3.1
        1. 放宽作者长度限制 (>=2)，适配 Li, Wu, Yao 等中国姓氏。
        2. 引入标题确信豁免 (High Confidence Bypass)。
        """
        if not data.title: return False, "无标题"

        query_lower = user_query.lower()
        title_lower = data.title.lower()

        # --- 0. DOI 绝对信任通道 ---
        if data.doi and len(data.doi) > 5 and data.doi.lower() in query_lower:
            return True, "DOI精确匹配"

        # --- 预处理：分词 ---
        def get_tokens(text):
            # 替换常见标点为空格
            clean = re.sub(r'[^\w\s]', ' ', text)
            # 拆分，且只保留长度>2的实词
            return [w for w in clean.split() if len(w) > 2]

        query_tokens = get_tokens(query_lower)
        title_tokens = get_tokens(title_lower)

        if not title_tokens: return False, "API标题无效"

        # --- 1. 标题词覆盖率 (Recall) ---
        match_count = sum(1 for w in title_tokens if w in query_tokens)
        coverage = match_count / len(title_tokens)

        # 【优化点1】标题确信豁免
        # 如果标题覆盖率极高(>80%)，说明就是这篇，直接跳过作者检查
        # 防止因作者格式(Yao vs Yao D.) 或短姓氏导致的误杀
        if coverage > 0.8:
            return True, f"标题高度吻合({coverage:.1%})"

        # 覆盖率过低直接毙掉
        if coverage < 0.4:
            return False, f"标题差异过大({coverage:.1%})"

        # --- 2. 连词检测 (Bigram Check) ---
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
            return False, "无连续词重叠(语义不同)"

        # --- 3. 作者校验 (兼容短姓氏) ---
        looks_like_has_author = "et al" in query_lower or "," in query_lower
        year_match = data.year and (str(data.year) in query_lower)

        author_match = False
        if data.authors:
            query_token_set = set(query_tokens)
            for auth in data.authors:
                auth_parts = get_tokens(auth.lower())  # 这里还是保留了>2，即至少3个字母

                # 但是为了支持 'Wu', 'Li' 等，我们需要单独处理 author parts
                # get_tokens 过滤掉了 len<=2 的词，这里手动拆解更稳妥
                raw_auth_clean = re.sub(r'[^\w\s]', ' ', auth.lower())
                raw_parts = raw_auth_clean.split()

                for part in raw_parts:
                    # 【优化点2】放宽长度限制到 >= 2
                    # 只要是2个字母及以上，且在用户输入里出现过，就算匹配
                    if len(part) >= 2 and part in query_lower:
                        # 注意：这里用 query_lower 而不是 token set，
                        # 因为 'Wu' 可能被 token set 过滤掉了(如果 token set 也只留了>2的)
                        author_match = True
                        break
                if author_match: break

        if looks_like_has_author:
            if not author_match:
                return False, "作者不匹配"
            if not year_match:
                if coverage < 0.9:  # 极高相似度可豁免年份
                    return False, "年份不匹配"
        else:
            if not year_match and coverage < 0.8:
                return False, "年份不匹配且标题存疑"

        return True, "验证通过"