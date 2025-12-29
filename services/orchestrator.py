"""
文件路径: services/orchestrator.py
=========================================================
【接口说明】
def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
    '''
    批量处理 (纯多线程并发版，无缓存)
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
import html
import traceback
import config
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        """
        批量处理 - 并发加速版 (无缓存)
        """
        lines = raw_text_block.split('\n')
        valid_tasks = []
        results_container = [None] * len(lines)

        for i, line in enumerate(lines):
            original_line = line.strip()
            if not original_line:
                results_container[i] = {
                    "text": "", "full": "", "html": ""
                }
                continue

            match = re.match(r'^\s*(\[\d+\]|\d+\.|\d+、|\(\d+\))\s*(.*)', original_line)
            prefix = ""
            clean_query = original_line
            if match:
                prefix = match.group(1)
                clean_query = match.group(2)

            valid_tasks.append((i, clean_query, prefix))

        total_tasks = len(valid_tasks)
        finished_count = 0

        # max_workers=4 既能显著提速，又不容易触发 API 的 429 限流
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 直接提交 _format_single_with_status 任务，不走缓存逻辑
            future_to_info = {
                executor.submit(self._format_single_with_status, query): (idx, query, pfx)
                for idx, query, pfx in valid_tasks
            }

            for future in as_completed(future_to_info):
                idx, query, prefix = future_to_info[future]
                finished_count += 1

                try:
                    formatted_content, is_success, url = future.result()

                    full_text_line = f"{prefix} {formatted_content}" if prefix else formatted_content
                    safe_text = html.escape(full_text_line)

                    if is_success and url:
                        html_line = (
                            f'<div style="margin-bottom: 12px;">'
                            f'<a href="{url}" style="color: #606266; text-decoration: none; font-weight: normal;" title="点击跳转原文: {url}">'
                            f'{safe_text}'
                            f'</a>'
                            f'</div>'
                        )
                    elif is_success:
                        html_line = f'<div style="margin-bottom: 12px; color:#2c3e50;">{safe_text}</div>'
                    else:
                        html_line = f'<div style="margin-bottom: 12px; color:#95a5a6;">{safe_text}</div>'

                    results_container[idx] = {
                        "text": formatted_content,
                        "full": full_text_line,
                        "html": html_line
                    }

                    if callback_signal:
                        progress = int((finished_count / total_tasks) * 100)
                        status_tag = "PREV_OK" if is_success else "PREV_FAIL"
                        short_q = query[:15].replace("\n", "")
                        next_msg = f"已完成: {short_q}..."

                        if hasattr(callback_signal, 'emit'):
                            callback_signal.emit(progress, f"{status_tag}|{next_msg}")
                        else:
                            callback_signal(progress, f"{status_tag}|{next_msg}")

                except Exception as e:
                    print(f"❌ 行 {idx + 1} 处理异常: {e}")
                    traceback.print_exc()
                    err_text = f"{lines[idx]} (系统错误)"
                    results_container[idx] = {
                        "text": err_text, "full": err_text,
                        "html": f'<div style="color:red;">处理出错: {html.escape(lines[idx])}</div>'
                    }

        list_with_num = []
        list_no_num = []
        list_html = []

        for item in results_container:
            if item:
                if item["text"]:
                    list_no_num.append(item["text"])
                    list_with_num.append(item["full"])
                    list_html.append(item["html"])

        return {
            "with_num": "\n\n".join(list_with_num),
            "no_num": "\n\n".join(list_no_num),
            "display_html": "".join(list_html)
        }

    def _extract_and_clean_doi(self, text: str):
        """【保留原逻辑】提取 DOI 并清洗文本"""
        valid_dois = []
        cleaned_text = text

        # === 优先策略：检测并修复带有空格的断裂 DOI ===
        broken_pattern = r'doi\.org/(10\.[0-9a-zA-Z./_:;()\-]+(?:\s+[0-9a-zA-Z./_:;()\-]+)+)'
        broken_matches = re.findall(broken_pattern, cleaned_text, re.IGNORECASE)

        for raw_broken in broken_matches:
            fixed_doi = raw_broken.replace(" ", "").replace("\t", "").rstrip(".")
            if "/" in fixed_doi and len(fixed_doi) > 10:
                valid_dois.append(fixed_doi)
                remove_pattern = r'(https?://(dx\.)?doi\.org/)?\s*' + re.escape(raw_broken)
                cleaned_text = re.sub(remove_pattern, '', cleaned_text, flags=re.IGNORECASE)

        # === 常规策略：匹配标准的无空格 DOI ===
        doi_pattern = r'(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)'
        found_dois = re.findall(doi_pattern, cleaned_text)

        for raw_doi in found_dois:
            clean_doi = raw_doi.rstrip(".")
            if clean_doi not in valid_dois:
                valid_dois.append(clean_doi)
            remove_pattern = r'(https?://(dx\.)?doi\.org/)?\s*' + re.escape(clean_doi)
            cleaned_text = re.sub(remove_pattern, '', cleaned_text, flags=re.IGNORECASE)

        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return valid_dois, cleaned_text

    def _try_fix_broken_doi(self, text: str):
        """【保留原逻辑】尝试修复断裂的 DOI"""
        match = re.search(r'doi\.org/(10\..+)', text, re.IGNORECASE)
        if match:
            potential_part = match.group(1)
            fixed_doi = potential_part.replace(" ", "").replace("\t", "").rstrip(".")
            return fixed_doi

        match_no_prefix = re.search(r'(10\.\d{4,5}/[\w\s\.-]+)', text)
        if match_no_prefix:
            potential = match_no_prefix.group(1)
            if " " in potential:
                fixed = potential.replace(" ", "").rstrip(".")
                if len(fixed) > 10:
                    return fixed
        return None

    def _format_single_with_status(self, query: str) -> (str, bool, str):
        """内部辅助方法：执行真实的 API 查询"""
        if not self.engines:
            return f"{query} ❌ (未启用API)", False, ""

        extracted_dois, text_without_doi = self._extract_and_clean_doi(query)

        if not extracted_dois:
            broken_doi = self._try_fix_broken_doi(query)
            if broken_doi:
                print(f"   [智能修复] 检测到疑似断裂 DOI，尝试修复为: {broken_doi}")
                extracted_dois = [broken_doi]
                text_without_doi = query.replace("doi", "").replace("DOI", "")

        if extracted_dois:
            target_doi = extracted_dois[0]
            print(f"   [策略] 发现 DOI ({target_doi})，启动精准打击...")

            for engine in self.engines:
                if "Crossref" in engine.name or "OpenAlex" in engine.name:
                    try:
                        citation_data = engine.search(target_doi)
                        if citation_data and citation_data.title:
                            if len(text_without_doi) > 10:
                                print("   [核对] 正在比对 DOI 结果与原文描述...")
                                is_match, reason = self._validate_result(text_without_doi, citation_data)
                                if is_match:
                                    print(f"   [成功] DOI 精准命中且核对通过: {citation_data.title[:20]}...")
                                    return formatter.to_gbt7714(citation_data), True, citation_data.url
                                else:
                                    print(
                                        f"   [警告] DOI 结果与原文描述严重不符 ({reason})，放弃 DOI 结果，转为常规搜索...")
                                    break
                            else:
                                print(f"   [成功] 纯 DOI 输入，无核对直接返回: {citation_data.title[:20]}...")
                                return formatter.to_gbt7714(citation_data), True, citation_data.url

                    except Exception as e:
                        print(f"   [DOI失败] {engine.name} 未能解析: {e}")

            print("   [策略] DOI 查询失效或校验未通过，转为常规搜索（已移除 DOI 字符串）...")

        search_query = text_without_doi if text_without_doi else query
        if len(search_query) < 4:
            return f"{query} ❌ (内容过短)", False, ""

        print(f"   [搜索] 关键词: {search_query[:30]}...")

        for engine in self.engines:
            try:
                citation_data = engine.search(search_query)
                if citation_data:
                    is_match, reason = self._validate_result(search_query, citation_data)
                    if is_match:
                        return formatter.to_gbt7714(citation_data), True, citation_data.url
                    else:
                        print(f"   [校验失败] {engine.name} 结果被拦截: {reason}")
                        continue
            except Exception as e:
                print(f"   [引擎错误] {engine.name}: {e}")
                continue

        return f"{query} ❌", False, ""

    def format_single(self, query: str) -> str:
        """
        单条处理入口，直接调用处理函数
        """
        res, _, _ = self._format_single_with_status(query)
        return res

    def _validate_result(self, user_query: str, data) -> (bool, str):
        """保留您之前的所有验证逻辑，包括抗粘连算法"""
        if not data.title: return False, "无标题"

        query_lower = user_query.lower()
        title_lower = data.title.lower()

        if data.doi and len(data.doi) > 5 and data.doi.lower() in query_lower:
            return True, "DOI精确匹配"

        def super_clean(t):
            return re.sub(r'[\W_]+', '', t).lower()

        q_super = super_clean(user_query)
        t_super = super_clean(data.title)

        if len(t_super) > 15:
            if t_super in q_super:
                return True, "抗粘连:标题全匹配"
            if len(q_super) > 15 and q_super in t_super:
                return True, "抗粘连:原文是标题子集"

        def get_tokens(text):
            if not text: return []
            clean = re.sub(r'[^\w\s]', ' ', text)
            return [w for w in clean.split() if len(w) > 2]

        query_tokens = get_tokens(query_lower)
        title_tokens = get_tokens(title_lower)

        if not title_tokens: return False, "API标题无效"

        match_count = sum(1 for w in title_tokens if w in query_tokens)
        coverage = match_count / len(title_tokens)

        if coverage > 0.8:
            return True, f"标题高度吻合({coverage:.1%})"

        if coverage < 0.4:
            return False, f"标题差异过大({coverage:.1%})"

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

        looks_like_has_author = "et al" in query_lower or "," in query_lower
        year_match = data.year and (str(data.year) in query_lower)

        author_match = False
        if data.authors:
            for auth in data.authors:
                if not auth: continue
                raw_auth_clean = re.sub(r'[^\w\s]', ' ', auth.lower())
                raw_parts = raw_auth_clean.split()
                for part in raw_parts:
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