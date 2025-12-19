"""
文件路径: config.py
=========================================================
【可用接口说明】

# 常量直接导入使用
from config import USER_AGENT, SEARCH_PRIORITY, SourceConfig, MIN_REQUEST_INTERVAL

# 1. 爬虫伪装与安全
USER_AGENT: str       # 发送请求时必须带上的身份标识
MIN_REQUEST_INTERVAL: float # 两次请求之间的最小间隔(秒)，防封号关键

# 2. 搜索策略
SEARCH_PRIORITY: list # 定义了API的搜索顺序

# 3. 数据源配置类
SourceConfig.OPENALEX_ENABLED  # OpenAlex 开关 (必须为 True 才能测试成功)
SourceConfig.DBLP_ENABLED      # DBLP 开关
SourceConfig.PUBMED_ENABLED    # PubMed 开关
...
=========================================================
"""

import os

# === 1. 全局身份标识 (防封号第一步: 礼貌) ===
# 许多学术 API (OpenAlex, Crossref) 鼓励开发者提供真实邮箱进入 "Polite Pool"。
# 如果你是公开发布软件，建议让用户在第一次打开软件时填入自己的邮箱，
# 或者申请一个项目专用的公共联系邮箱。
APP_NAME = "RefFormatter/1.0"
CONTACT_EMAIL = "developer@example.com"  # TODO: 建议在发布前改为真实邮箱
USER_AGENT = f"{APP_NAME} (mailto:{CONTACT_EMAIL})"

# === 2. 网络请求与安全设置 (防封号第二步: 克制) ===
TIMEOUT = 15  # 单个请求超时时间 (秒)
MAX_RETRIES = 2  # 请求失败后的重试次数

# 【关键】请求冷却时间 (秒)
# 公开软件必须限制请求频率，避免用户 IP 被各大网站拉黑。
# 建议至少设置为 1.0 秒。
MIN_REQUEST_INTERVAL = 1.0

# 代理池配置 (可选)
# 如果你需要翻墙查外文，且电脑开了代理，可以在这里配置
# 例如: PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXIES = None


# === 3. 数据源配置 ===
class SourceConfig:
    """
    管理各个 API 数据源的开关。
    """

    # --- 英文/国际权威数据源 (API友好，封号风险低) ---

    # 【核心】OpenAlex: 极其全面，免费，强烈推荐 (请确保此项为 True)
    OPENALEX_ENABLED = True
    OPENALEX_API_URL = "https://api.openalex.org/works"

    # Crossref: 英文 DOI 官方，数据最准 (备用)
    CROSSREF_ENABLED = True
    CROSSREF_API_URL = "https://api.crossref.org/works"

    # Semantic Scholar: AI 驱动，质量高 (需注意每5分钟100次限制)
    S2_ENABLED = True
    S2_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    S2_API_KEY = None

    # DBLP: 计算机科学领域权威 (无需Key，非常安全)
    DBLP_ENABLED = True
    DBLP_API_URL = "https://dblp.org/search/publ/api"

    # PubMed: 医学/生物领域 (无需Key，非常安全)
    PUBMED_ENABLED = True
    PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # --- 中文/网页爬虫数据源 (风险较高，需谨慎) ---
    # 注意：如果你还没有编写这些引擎的代码，即使设置为 True 也不会生效，
    # 因为 Orchestrator 里还没有加载它们。

    CNKI_ENABLED = True
    WANFANG_ENABLED = True
    BAIDU_SCHOLAR_ENABLED = True


# === 4. 智能搜索策略 ===
# 建议顺序：先查 API 开放友好的，再查需要硬爬的。
SEARCH_PRIORITY = [
    "cnki",  # 中文优先
    "wanfang",  # 中文补充
    "openalex",  # 英文首选 (量大速度快)
    "dblp",  # 计算机首选
    "pubmed",  # 医学首选
    "semanticscholar",  # 英文高质量
    "crossref",  # 英文保底
    "baidu_scholar"  # 最后的补漏
]

# === 5. 格式化标准 ===
DEFAULT_STYLE = "gbt7714-2015"