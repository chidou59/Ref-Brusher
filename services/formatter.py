"""
文件路径: services/formatter.py
=========================================================
【功能】
将 CitationData 对象转换为标准的 GB/T 7714-2015 字符串。
遵循最严格的国标规定：
1. 姓氏全部大写 (EINSTEIN)
2. 名字首字母大写，无缩写点 (A)
3. 支持 van, von 等复姓识别
=========================================================
"""

import re
import html
from models.citation_model import CitationData


def clean_text(text: str) -> str:
    """清洗 HTML 标签"""
    if not text:
        return ""
    clean_str = re.sub(r'<[^>]+>', '', text)
    clean_str = html.unescape(clean_str)
    return clean_str.strip()


def format_western_name(name_str: str) -> str:
    """
    【姓名整形师 V4.0】
    将外文姓名转换为 GB/T 7714 格式 (严格全大写)
    输入: "Ludwig van Beethoven"
    输出: "VAN BEETHOVEN L"
    """
    name_str = clean_text(name_str)
    if not name_str:
        return ""

    # 中文名直接返回 (简单判定)
    if re.search(r'[\u4e00-\u9fff]', name_str):
        return name_str

    # 定义常见的姓氏前缀 (小写)
    surname_prefixes = ['van', 'von', 'de', 'du', 'da', 'del', 'la', 'le']

    family = ""
    given = ""

    # 情况 A: 已经有逗号 "Beethoven, Ludwig van"
    if ',' in name_str:
        parts = name_str.split(',', 1)
        family = parts[0].strip()
        given = parts[1].strip()

    # 情况 B: 自然序 "Ludwig van Beethoven"
    else:
        tokens = name_str.split()
        if not tokens: return ""
        if len(tokens) == 1: return tokens[0].upper()

        # 智能检测复姓 (查看倒数第二个词是否是前缀)
        # 例如: ["Ludwig", "van", "Beethoven"]
        if len(tokens) > 2 and tokens[-2].lower() in surname_prefixes:
            # 姓是最后两个词: "van Beethoven"
            family = " ".join(tokens[-2:])
            given = " ".join(tokens[:-2])
        else:
            # 默认最后一个词是姓
            family = tokens[-1]
            given = " ".join(tokens[:-1])

    # === 核心国标规则 ===
    # 1. 姓: 全大写
    family_fmt = family.upper()

    # 2. 名: 首字母大写，无缩写点
    given_clean = given.replace('.', ' ').replace('-', ' ')
    given_tokens = given_clean.split()
    given_initials = [t[0].upper() for t in given_tokens if t]
    given_fmt = " ".join(given_initials)

    if given_fmt:
        return f"{family_fmt} {given_fmt}"
    else:
        return family_fmt


def format_authors(authors: list) -> str:
    """格式化作者列表"""
    if not authors:
        return "[佚名]"

    formatted_authors = []
    for auth in authors:
        fmt_name = format_western_name(auth)
        formatted_authors.append(fmt_name)

    # 前3位列出，超过3位加 et al.
    if len(formatted_authors) > 3:
        return ", ".join(formatted_authors[:3]) + ", et al"
    else:
        return ", ".join(formatted_authors)


def to_gbt7714(data: CitationData) -> str:
    """转换为国标字符串"""
    title = clean_text(data.title)
    source = clean_text(data.source)
    authors_str = format_authors(data.authors)

    doc_type = "[J]"
    if source:
        lower_source = source.lower()
        if "conference" in lower_source or "proceedings" in lower_source:
            doc_type = "[C]"
        elif "thesis" in lower_source or "dissertation" in lower_source:
            doc_type = "[D]"

    # 拼装
    result = f"{authors_str}. {title}{doc_type}"

    if source: result += f". {source}"
    if data.year: result += f", {data.year}"

    if data.volume:
        result += f", {data.volume}"
        if data.issue: result += f"({data.issue})"
    elif data.issue:
        result += f"({data.issue})"

    if data.pages:
        clean_pages = data.pages.replace("--", "-")
        result += f": {clean_pages}"

    result += "."
    return result