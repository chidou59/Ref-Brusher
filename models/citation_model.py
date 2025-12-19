"""
文件路径: models/citation_model.py
=========================================================
【可用接口说明】

class CitationData:
    # --- 核心属性 (直接访问/赋值) ---
    title: str       # 标题
    authors: list    # 作者列表，如 ["张三", "Li Si"]
    source: str      # 来源 (期刊名/会议名/出版社)
    year: str        # 年份 (如 "2023")
    volume: str      # 卷
    issue: str       # 期
    pages: str       # 页码
    doi: str         # DOI号
    url: str         # 链接
    entry_type: str  # 类型 ("article", "book", "thesis", "conference")

    # --- 常用方法 ---
    def is_valid(self) -> bool:
        '''
        检查数据是否基本完整。
        返回: True (完整) / False (缺关键信息)
        '''
        pass

    def get_formatted_authors(self, max_authors=3) -> str:
        '''
        获取格式化后的作者字符串。
        参数: max_authors (超过多少人显示"等")
        返回: 如 "张三, 李四, 等"
        '''
        pass
=========================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CitationData:
    """
    统一的文献数据模型。
    作用：无论从哪个网站(OpenAlex/CNKI)抓取的数据，
    都必须先转换成这个类，然后再进行格式化。
    """
    # 核心字段
    title: str = ""
    authors: List[str] = field(default_factory=list)  # 注意：这是列表，不是字符串
    source: str = ""  # 期刊名、会议名或出版社
    year: str = ""

    # 详细字段
    volume: str = ""  # 卷
    issue: str = ""  # 期
    pages: str = ""  # 页码 (起止页)
    doi: str = ""  # Digital Object Identifier (数字对象唯一标识符)
    url: str = ""  # 链接

    # 元数据
    entry_type: str = "article"  # 默认为期刊论文，可选 book, thesis, conference
    raw_data: dict = field(default_factory=dict)  # 保留原始API返回的数据，以此备查

    def is_valid(self) -> bool:
        """
        判断数据是否基本完整。
        标准：至少要有 标题、作者、来源、年份。
        如果返回 False，UI 上可以用红色高亮显示，提示用户补全。
        """
        # 使用 all() 检查核心字段是否都有值
        required_fields = [self.title, self.authors, self.source, self.year]
        return all(required_fields)

    def get_formatted_authors(self, max_authors=3) -> str:
        """
        根据国标逻辑简单处理作者名单。
        注：更复杂的逻辑（如英文姓在前名在后）会在 formatter 服务中处理，
        这里提供的是用于 UI 预览的基础文本。
        """
        if not self.authors:
            return "[佚名]"

        # 1. 清理数据：移除可能的空字符串和多余空格
        cleaned_authors = [str(a).strip() for a in self.authors if str(a).strip()]

        if not cleaned_authors:
            return "[佚名]"

        # 2. 判断是否超过限制
        if len(cleaned_authors) <= max_authors:
            # 不超过3人，全部列出
            return ", ".join(cleaned_authors)
        else:
            # 超过3人，列出前3个 + ", 等" (英文环境可能需要变成 ", et al.")
            # 这里的本地化处理将在 formatter 中完善，此处暂用中文
            return ", ".join(cleaned_authors[:max_authors]) + ", 等"

    def __repr__(self):
        """控制台打印时的显示格式，方便调试查看"""
        author_preview = self.authors[0] if self.authors else "No Author"
        return f"<Citation: {self.title[:20]}... | {author_preview} ({self.year})>"