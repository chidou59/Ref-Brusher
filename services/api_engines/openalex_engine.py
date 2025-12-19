"""
文件路径: services/api_engines/openalex_engine.py
=========================================================
【可用接口说明】

class OpenAlexEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        # 输入标题，返回数据
        pass
=========================================================
"""

import sys
import os

# === 路径修复代码 (必须放在最前面) ===
# 1. 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 2. 获取当前文件所在目录 (services/api_engines)
current_dir = os.path.dirname(current_file_path)
# 3. 获取项目根目录 (向上跳两级: services -> project_root)
project_root = os.path.dirname(os.path.dirname(current_dir))
# 4. 将根目录加入 Python 搜索路径，解决 "ModuleNotFoundError"
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

        # 1. 准备参数
        # OpenAlex 的搜索参数通常是filter或者search
        # 这里使用 search 模式匹配标题
        params = {
            "search": query,
            "per_page": 1  # 我们只需要匹配度最高的那一条
        }

        # 2. 发送请求 (使用父类的安全方法)
        data = self.safe_request(self.api_url, params)

        # 3. 解析数据
        if not data or "results" not in data or not data["results"]:
            self.logger.info(f"[{self.name}] 未找到结果: {query[:20]}...")
            return None

        # 拿到第一条最佳匹配结果
        best_match = data["results"][0]

        # 4. 【核心】数据映射 (Data Mapping)
        # 将 OpenAlex 的 JSON 格式 转换为 我们的 CitationData 格式
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, json_data: dict) -> CitationData:
        """
        私有方法：处理复杂的 JSON 结构
        """
        # 创建空模型
        citation = CitationData()

        # A. 提取标题
        citation.title = json_data.get("display_name", "")

        # B. 提取作者 (OpenAlex 的作者在 authorships 列表里)
        # 结构: authorships -> [ {author: {display_name: "Name"}} ]
        authors_raw = json_data.get("authorships", [])
        citation.authors = [
            item.get("author", {}).get("display_name", "")
            for item in authors_raw
        ]

        # C. 提取来源 (期刊/会议)
        # 结构: primary_location -> source -> display_name
        primary_loc = json_data.get("primary_location") or {}
        source_info = primary_loc.get("source") or {}
        citation.source = source_info.get("display_name", "")

        # D. 提取年份
        citation.year = str(json_data.get("publication_year", ""))

        # E. 提取卷期页 (OpenAlex 放在 biblio 字典里)
        biblio = json_data.get("biblio", {})
        citation.volume = biblio.get("volume", "")
        citation.issue = biblio.get("issue", "")
        citation.pages = f"{biblio.get('first_page', '')}-{biblio.get('last_page', '')}"

        # 清理页码格式 (如果只有first_page没last_page，去掉横杠)
        if citation.pages == "-":
            citation.pages = ""
        elif citation.pages.endswith("-"):
            citation.pages = citation.pages.strip("-")

        # F. 提取 DOI
        # OpenAlex 返回的 DOI 通常是完整 URL (https://doi.org/10.xxx/xxx)
        # 我们只需要后面的 10.xxx 部分
        doi_url = json_data.get("doi", "")
        if doi_url:
            citation.doi = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")

        # G. 保存原始数据备查
        citation.raw_data = json_data

        return citation


# --- 单元测试代码 (仅在直接运行此文件时执行) ---
if __name__ == "__main__":
    # 这一块代码是教你如何单独测试这个文件的
    print("正在测试 OpenAlex 引擎...")
    engine = OpenAlexEngine()
    test_query = "Deep learning Nature 2015"
    result = engine.search(test_query)

    if result:
        print("✅ 测试成功!")
        print(f"标题: {result.title}")
        print(f"作者: {result.authors}")
        print(f"年份: {result.year}")
        print(f"期刊: {result.source}")
        print(f"页码: {result.pages}")
    else:
        print("❌ 测试失败或无结果")