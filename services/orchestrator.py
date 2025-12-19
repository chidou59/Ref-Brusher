"""
文件路径: services/orchestrator.py
=========================================================
【接口说明】
def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
    '''批量处理，并在 callback_signal 中附带 [OK] 或 [FAIL] 标记'''
=========================================================
"""

import sys
import os
import time
import re
import difflib
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

            # 处理单条
            formatted_content, is_success = self._format_single_with_status(clean_query)

            # 通过 callback 发送状态: "PREV_OK" 或 "PREV_FAIL"
            if callback_signal:
                progress = int(((i + 1) / total) * 100)
                status_tag = "PREV_OK" if is_success else "PREV_FAIL"
                next_msg = f"正在处理: {clean_query[:15]}..."
                callback_signal(progress, f"{status_tag}|{next_msg}")

            # 存入列表
            list_no_num.append(formatted_content)
            if prefix:
                list_with_num.append(f"{prefix} {formatted_content}")
            else:
                list_with_num.append(formatted_content)

            if i < total - 1:
                time.sleep(config.MIN_REQUEST_INTERVAL)

        return {
            "with_num": "\n\n".join(list_with_num),
            "no_num": "\n\n".join(list_no_num)
        }

    def _format_single_with_status(self, query: str) -> (str, bool):
        """
        内部辅助方法：处理单条并返回 (结果字符串, 是否成功)
        """
        if not self.engines:
            return f"{query} ❌ (未启用API)", False
        if len(query) < 4:
            return f"{query} ❌", False

        is_pure_doi = "10." in query and "/" in query and len(query.split()) < 2
        if is_pure_doi: query = query.strip()

        for engine in self.engines:
            try:
                citation_data = engine.search(query)
                if citation_data:
                    is_match, reason = self._validate_result(query, citation_data)
                    if is_match:
                        # 成功！
                        return formatter.to_gbt7714(citation_data), True
                    else:
                        continue
            except Exception:
                continue

        # 失败
        return f"{query} ❌", False

    def format_single(self, query: str) -> str:
        """兼容旧接口"""
        res, _ = self._format_single_with_status(query)
        return res

    def _validate_result(self, user_query: str, data) -> (bool, str):
        if not data.title: return False, "无标题"
        query_lower = user_query.lower()
        title_lower = data.title.lower()
        if data.doi and data.doi.lower() in query_lower: return True, "DOI匹配"
        similarity = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
        if similarity > 0.7: return True, "相似度达标"
        query_words = [w for w in re.split(r'\W+', query_lower) if len(w) > 3]
        if not query_words: return True, "输入过短"
        hit_count = sum(1 for w in query_words if w in title_lower)
        if hit_count / len(query_words) > 0.7: return True, "关键词覆盖"
        has_author = False
        if data.authors:
            for auth in data.authors:
                for p in auth.lower().split():
                    if len(p) > 2 and p in query_lower:
                        has_author = True
                        break
        has_year = data.year and (str(data.year) in query_lower)
        if has_author and has_year: return True, "作者年份匹配"
        if query_lower in title_lower or title_lower in query_lower: return True, "包含关系"
        return False, f"相似度低({similarity:.2f})"