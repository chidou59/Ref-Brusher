"""
文件路径: services/api_engines/crossref.py
=========================================================
【可用接口说明】

class CrossrefEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        输入: 论文标题 (支持中文) 或 DOI
        输出: 及其标准的 CitationData 对象
        优势: 官方API，极其稳定，无验证码，不封IP
        '''
        pass
=========================================================
"""

import urllib.parse
from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class CrossrefEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "Crossref"
        self.api_url = config.SourceConfig.CROSSREF_API_URL
        self.email = config.CONTACT_EMAIL

    def get_headers(self) -> dict:
        headers = super().get_headers()
        if self.email and "example.com" not in self.email:
            headers["User-Agent"] += f" (mailto:{self.email})"
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.CROSSREF_ENABLED:
            return None

        # 1. 智能判断：如果是 DOI 格式，直接精准查询
        # 判断逻辑：包含 "10." 且包含 "/"，且不包含空格（或长度很短）
        # Orchestrator 传进来的 DOI 应该是清洗过的，不含空格
        is_pure_doi = "10." in query and "/" in query and " " not in query

        params = {}
        if is_pure_doi:
            # 如果看起来像 DOI，清理一下直接查
            clean_doi = query.strip()
            # 移除可能的前缀 (虽然 Orchestrator 已经移除了，这里双重保险)
            if "doi.org/" in clean_doi:
                clean_doi = clean_doi.split("doi.org/")[-1]

            # Crossref 搜索模式，如果只有 query.bibliographic 放 DOI，通常能直接命中
            params = {
                "query.bibliographic": clean_doi,
                "rows": 1
            }
        else:
            # 普通标题搜索
            params = {
                "query.bibliographic": query,
                "rows": 1,
                # 启用相关性排序
                "sort": "relevance"
            }

        self.logger.info(f"[{self.name}] 正在请求 API ({'DOI模式' if is_pure_doi else '搜索模式'}): {query[:20]}...")

        # 2. 发送请求
        data = self.safe_request(self.api_url, params)

        # 3. 解析数据
        if not data or "message" not in data or "items" not in data["message"]:
            return None

        items = data["message"]["items"]
        if not items:
            self.logger.info(f"[{self.name}] 未找到结果。")
            return None

        # 取第一条最佳匹配
        best_match = items[0]

        # 4. 转换为模型
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item
        citation.entry_type = "article"  # 默认为文章

        # A. 标题 (Crossref 返回的是列表)
        if "title" in item and item["title"]:
            citation.title = item["title"][0]

        # B. 作者
        if "author" in item:
            authors = []
            for a in item["author"]:
                # 拼接 姓 + 名
                given = a.get("given", "")
                family = a.get("family", "")
                full_name = f"{given} {family}".strip()
                if full_name:
                    authors.append(full_name)
            citation.authors = authors

        # C. 来源 (期刊名)
        if "container-title" in item and item["container-title"]:
            citation.source = item["container-title"][0]

        # D. 年份 (结构较深: published-print -> date-parts -> [[2023, 1, 1]])
        date_parts = None
        if "published-print" in item:
            date_parts = item["published-print"]["date-parts"]
        elif "published-online" in item:
            date_parts = item["published-online"]["date-parts"]
        elif "created" in item:  # 保底
            date_parts = item["created"]["date-parts"]

        if date_parts and date_parts[0]:
            citation.year = str(date_parts[0][0])

        # E. 卷期页
        citation.volume = item.get("volume", "")
        citation.issue = item.get("issue", "")
        citation.pages = item.get("page", "")
        citation.doi = item.get("DOI", "")
        citation.url = item.get("URL", "")

        return citation