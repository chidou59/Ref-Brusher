"""
文件路径: services/api_engines/openalex_engine.py
=========================================================
【可用接口说明】

class OpenAlexEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        # 输入标题或 DOI，返回数据
        pass
=========================================================
"""

import sys
import os

# === 路径修复代码 ===
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ==========================================

from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class OpenAlexEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "OpenAlex"
        self.api_url = config.SourceConfig.OPENALEX_API_URL

    def search(self, query: str) -> Optional[CitationData]:
        """
        实现 OpenAlex 的具体搜索逻辑
        """
        if not config.SourceConfig.OPENALEX_ENABLED:
            return None

        # === 1. 智能参数构建 (V2.0 Update) ===
        # 判断传入的是否为纯 DOI (包含 "10." 且含 "/")
        is_pure_doi = "10." in query and "/" in query and " " not in query

        params = {}

        if is_pure_doi:
            # 【精确模式】使用 filter=doi:xxx
            # OpenAlex 要求 DOI 必须是完整的 URL 格式 (https://doi.org/10.xxx)
            # 或者直接是 doi:10.xxx
            clean_doi = query.strip()
            # 补全 https://doi.org/ 前缀，确保 OpenAlex 能识别
            if not clean_doi.startswith("https://doi.org/") and not clean_doi.startswith("http://doi.org/"):
                doi_url = f"https://doi.org/{clean_doi}"
            else:
                doi_url = clean_doi

            params = {
                "filter": f"doi:{doi_url}",
                "per_page": 1
            }
            self.logger.info(f"[{self.name}] 启动 DOI 精确查找: {clean_doi}")
        else:
            # 【模糊模式】使用 search=xxx
            params = {
                "search": query,
                "per_page": 1
            }
            self.logger.info(f"[{self.name}] 启动关键词搜索: {query[:20]}...")

        # 2. 发送请求
        data = self.safe_request(self.api_url, params)

        # 3. 解析数据
        if not data or "results" not in data or not data["results"]:
            # 如果是精确查找失败了，日志记录一下
            if is_pure_doi:
                self.logger.info(f"[{self.name}] DOI 未找到对应记录。")
            return None

        # 拿到第一条最佳匹配结果
        best_match = data["results"][0]

        # 4. 数据映射
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, json_data: dict) -> CitationData:
        """
        私有方法：处理复杂的 JSON 结构
        """
        citation = CitationData()

        # A. 提取标题
        citation.title = json_data.get("display_name", "")

        # B. 提取作者 (OpenAlex 的作者在 authorships 列表里)
        authors_raw = json_data.get("authorships", [])
        citation.authors = [
            item.get("author", {}).get("display_name", "")
            for item in authors_raw
        ]

        # C. 提取来源 (期刊/会议)
        primary_loc = json_data.get("primary_location") or {}
        source_info = primary_loc.get("source") or {}
        citation.source = source_info.get("display_name", "")

        # D. 提取年份
        citation.year = str(json_data.get("publication_year", ""))

        # E. 提取卷期页
        biblio = json_data.get("biblio", {})
        citation.volume = biblio.get("volume", "")
        citation.issue = biblio.get("issue", "")
        citation.pages = f"{biblio.get('first_page', '')}-{biblio.get('last_page', '')}"

        if citation.pages == "-":
            citation.pages = ""
        elif citation.pages.endswith("-"):
            citation.pages = citation.pages.strip("-")

        # F. 提取 DOI
        doi_url = json_data.get("doi", "")
        if doi_url:
            citation.doi = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")
            citation.url = doi_url  # 同时也赋值给 url

        # G. 保存原始数据
        citation.raw_data = json_data

        return citation