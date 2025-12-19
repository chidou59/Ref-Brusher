"""
文件路径: services/api_engines/semantic_scholar.py
=========================================================
【可用接口说明】

class SemanticScholarEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        输入: 论文标题
        输出: CitationData 对象
        优势: AI 驱动，搜索精度高，覆盖全球文献
        '''
        pass
=========================================================
"""

from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config

class SemanticScholarEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "SemanticScholar"
        # 官方图谱 API 搜索端点
        self.api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.api_key = config.SourceConfig.S2_API_KEY

    def get_headers(self) -> dict:
        headers = super().get_headers()
        # 如果用户申请了 Key (免费的)，带上可以提高限额
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.S2_ENABLED:
            return None

        # 1. 构造参数
        # fields 参数指定我们需要返回哪些字段，避免数据冗余
        params = {
            "query": query,
            "limit": 1,
            "fields": "title,authors,year,venue,url,externalIds,publicationTypes"
        }

        self.logger.info(f"[{self.name}] 正在请求 API: {query[:20]}...")

        # 2. 发送请求
        data = self.safe_request(self.api_url, params)

        # 3. 解析
        if not data or "data" not in data or not data["data"]:
            self.logger.info(f"[{self.name}] 未找到结果。")
            return None

        best_match = data["data"][0]
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item
        citation.entry_type = "article"

        # A. 标题
        citation.title = item.get("title", "")

        # B. 作者 (列表字典)
        if "authors" in item and item["authors"]:
            citation.authors = [a["name"] for a in item["authors"] if "name" in a]

        # C. 年份
        citation.year = str(item.get("year", ""))

        # D. 来源 (venue)
        citation.source = item.get("venue", "")

        # E. 链接 & DOI
        citation.url = item.get("url", "")
        if "externalIds" in item and item["externalIds"]:
            citation.doi = item["externalIds"].get("DOI", "")

        return citation