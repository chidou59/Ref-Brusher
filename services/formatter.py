"""
文件路径: services/formatter.py
=========================================================
【功能】
将 CitationData 对象转换为标准的 GB/T 7714-2015 字符串。
遵循最严格的国标规定：
1. 姓氏全部大写 (EINSTEIN)
2. 名字首字母大写，无缩写点 (A)
3. 支持 van, von 等复姓识别
4. 【精准版】支持中国学者拼音双名自动拆分 (Han Shaoheng -> HAN S H)
5. 【V4.0】智能纠正 API 返回的 "姓在前名在后" 格式
6. 【V5.0】新增中英文环境检测，自动切换 'et al' / '等'
7. 【V5.1 修复】修复页码显示为 "None-None" 的问题，无效页码自动隐藏
=========================================================
"""

import re
import html
from models.citation_model import CitationData

# === 1. 数据准备 ===
COMMON_CN_SURNAMES = {
    "LI", "WANG", "ZHANG", "LIU", "CHEN", "YANG", "ZHAO", "HUANG", "ZHOU", "WU",
    "XU", "SUN", "HU", "ZHU", "GAO", "LIN", "HE", "GUO", "MA", "LUO",
    "LIANG", "SONG", "ZHENG", "XIE", "HAN", "TANG", "FENG", "YU", "DONG", "XIAO",
    "CHENG", "CAO", "YUAN", "DENG", "FU", "SHEN", "ZENG", "PENG", "LV",
    "SU", "LU", "JIANG", "CAI", "JIA", "DING", "WEI", "XUE", "YE", "YAN",
    "PAN", "DU", "DAI", "XIA", "ZHONG", "TIAN", "REN", "FAN", "FANG", "SHI",
    "YAO", "TAN", "SHENG", "ZOU", "XIONG", "JIN", "HAO", "KONG", "BAI", "CUI",
    "KANG", "MAO", "QIU", "QIN", "GU", "HOU", "SHAO", "MENG", "LONG", "WAN",
    "DUAN", "QIAN", "YIN", "YI", "CHANG", "XI", "WEN", "NIE", "ZHUANG", "YAN",
    "QU", "GE", "PU", "BA", "BIE", "BING", "BO", "BU", "CEN", "CHAI", "CHE",
    "CHI", "CHU", "CHUAN", "CHUN", "CONG", "CUO", "DA", "DAN", "DAO", "DI",
    "DIAN", "DIAO", "DIE", "DOU", "DU", "DUN", "E", "EN", "ER", "FA", "FEI",
    "FO", "FOU", "GAI", "GAN", "GANG", "GEN", "GENG", "GONG", "GOU", "GUAN",
    "GUI", "GUN", "HAI", "HANG", "HEI", "HEN", "HENG", "HONG", "HUA", "HUAI",
    "HUAN", "HUI", "HUN", "HUO", "JI", "JIAN", "JIANG", "JIAO", "JIE", "JING",
    "JIONG", "JIU", "JU", "JUAN", "JUE", "JUN", "KA", "KAI", "KAN", "KAO", "KE",
    "KEN", "KENG", "KOU", "KU", "KUA", "KUAI", "KUAN", "KUANG", "KUI", "KUN",
    "KUO", "LA", "LAI", "LAN", "LANG", "LAO", "LE", "LEI", "LENG", "LIA", "LIAN",
    "LIAO", "LIE", "LIN", "LING", "LIU", "LONG", "LOU", "LUAN", "LUE", "LUN",
    "LUO", "MEI", "MEN", "MENG", "MI", "MIAN", "MIAO", "MIE", "MIN", "MING", "MIU",
    "MO", "MOU", "MU", "NA", "NAI", "NAN", "NANG", "NAO", "NE", "NEI", "NEN",
    "NENG", "NI", "NIAN", "NIANG", "NIAO", "NIE", "NIN", "NING", "NIU", "NONG",
    "NOU", "NU", "NUAN", "NUE", "NUO", "OU", "PA", "PAI", "PAN", "PANG", "PAO",
    "PEI", "PEN", "PENG", "PI", "PIAN", "PIAO", "PIE", "PIN", "PING", "PO", "POU",
    "QI", "QIA", "QIAN", "QIANG", "QIAO", "QIE", "QIN", "QING", "QIONG", "QIU",
    "QU", "QUAN", "QUE", "QUN", "RAN", "RANG", "RAO", "RE", "REN", "RENG", "RI",
    "RONG", "ROU", "RU", "RUAN", "RUI", "RUN", "RUO", "SA", "SAI", "SAN", "SANG",
    "SAO", "SE", "SEN", "SENG", "SHA", "SHAI", "SHAN", "SHANG", "SHE", "SHEI",
    "SHEN", "SHU", "SHUA", "SHUAI", "SHUAN", "SHUANG", "SHUI", "SHUN", "SHUO",
    "SI", "SONG", "SOU", "SUAN", "SUI", "SUN", "SUO", "TA", "TAI", "TAN", "TANG",
    "TAO", "TE", "TENG", "TI", "TIAN", "TIAO", "TIE", "TING", "TONG", "TOU", "TU",
    "TUAN", "TUI", "TUN", "TUO", "WA", "WAI", "WAN", "WANG", "WEI", "WEN", "WENG",
    "WO", "WU", "XI", "XIA", "XIAN", "XIANG", "XIAO", "XIE", "XIN", "XING", "XIONG",
    "XIU", "XU", "XUAN", "XUE", "XUN", "YA", "YAN", "YANG", "YAO", "YE", "YI",
    "YIN", "YING", "YONG", "YOU", "YU", "YUAN", "YUE", "YUN", "ZA", "ZAI", "ZAN",
    "ZANG", "ZAO", "ZE", "ZEI", "ZEN", "ZENG", "ZHA", "ZHAI", "ZHAN", "ZHANG",
    "ZHAO", "ZHE", "ZHEI", "ZHEN", "ZHENG", "ZHI", "ZHONG", "ZHOU", "ZHU", "ZHUA",
    "ZHUAI", "ZHUAN", "ZHUANG", "ZHUI", "ZHUN", "ZHUO", "ZI", "ZONG", "ZOU", "ZU",
    "ZUAN", "ZUI", "ZUN", "ZUO"
}

VALID_PINYINS = {
    "a", "ai", "an", "ang", "ao", "ba", "bai", "ban", "bang", "bao", "bei", "ben",
    "beng", "bi", "bian", "biao", "bie", "bin", "bing", "bo", "bu", "ca", "cai",
    "can", "cang", "cao", "ce", "cen", "ceng", "cha", "chai", "chan", "chang",
    "chao", "che", "chen", "cheng", "chi", "chong", "chou", "chu", "chua", "chuai",
    "chuan", "chuang", "chui", "chun", "chuo", "ci", "cong", "cou", "cu", "cuan",
    "cui", "cun", "cuo", "da", "dai", "dan", "dang", "dao", "de", "dei", "deng",
    "di", "dian", "diao", "die", "ding", "diu", "dong", "dou", "du", "duan", "dui",
    "dun", "duo", "e", "ei", "en", "eng", "er", "fa", "fan", "fang", "fei", "fen",
    "feng", "fo", "fou", "fu", "ga", "gai", "gan", "gang", "gao", "ge", "gei",
    "gen", "geng", "gong", "gou", "gu", "gua", "guai", "guan", "guang", "gui",
    "gun", "guo", "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng",
    "hong", "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo", "ji",
    "jia", "jian", "jiang", "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju",
    "juan", "jue", "jun", "ka", "kai", "kan", "kang", "kao", "ke", "ken", "keng",
    "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang", "kui", "kun", "kuo", "la",
    "lai", "lan", "lang", "lao", "le", "lei", "leng", "li", "lia", "lian", "liang",
    "liao", "lie", "lin", "ling", "liu", "long", "lou", "lu", "luan", "lue", "lun",
    "luo", "lv", "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng",
    "mi", "mian", "miao", "mie", "min", "ming", "miu", "mo", "mou", "mu", "na",
    "nai", "nan", "nang", "nao", "ne", "nei", "nen", "neng", "ni", "nian", "niang",
    "niao", "nie", "nin", "ning", "niu", "nong", "nou", "nu", "nuan", "nue", "nuo",
    "nv", "o", "ou", "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng", "pi",
    "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu", "qi", "qia", "qian",
    "qiang", "qiao", "qie", "qin", "qing", "qiong", "qiu", "qu", "quan", "que",
    "qun", "ran", "rang", "rao", "re", "ren", "reng", "ri", "rong", "rou", "ru",
    "ruan", "rui", "run", "ruo", "sa", "sai", "san", "sang", "sao", "se", "sen",
    "seng", "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng",
    "shi", "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun",
    "shuo", "si", "song", "sou", "su", "suan", "sui", "sun", "suo", "ta", "tai",
    "tan", "tang", "tao", "te", "teng", "ti", "tian", "tiao", "tie", "ting",
    "tong", "tou", "tu", "tuan", "tui", "tun", "tuo", "wa", "wai", "wan", "wang",
    "wei", "wen", "weng", "wo", "wu", "xi", "xia", "xian", "xiang", "xiao", "xie",
    "xin", "xing", "xiong", "xiu", "xu", "xuan", "xue", "xun", "ya", "yan", "yang",
    "yao", "ye", "yi", "yin", "ying", "yong", "you", "yu", "yuan", "yue", "yun",
    "za", "zai", "zan", "zang", "zao", "ze", "zei", "zen", "zeng", "zha", "zhai",
    "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng", "zhi", "zhong",
    "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo",
    "zi", "zong", "zou", "zu", "zuan", "zui", "zun", "zuo"
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    clean_str = re.sub(r'<[^>]+>', '', text)
    clean_str = html.unescape(clean_str)
    return clean_str.strip()


def try_split_pinyin(given_name: str) -> str:
    given_name = given_name.strip()
    length = len(given_name)

    if length < 3 or length > 12:
        return given_name

    if given_name.lower() in VALID_PINYINS:
        return given_name

    for i in range(1, length):
        part1 = given_name[:i].lower()
        part2 = given_name[i:].lower()

        if part1 in VALID_PINYINS and part2 in VALID_PINYINS:
            return f"{given_name[:i]} {given_name[i:]}"

    return given_name


def format_western_name(name_str: str) -> str:
    name_str = clean_text(name_str)
    if not name_str:
        return ""

    # 中文名直接返回
    if re.search(r'[\u4e00-\u9fff]', name_str):
        return name_str

    surname_prefixes = ['van', 'von', 'de', 'du', 'da', 'del', 'la', 'le']

    family = ""
    given = ""

    if ',' in name_str:
        parts = name_str.split(',', 1)
        family = parts[0].strip()
        given = parts[1].strip()
    else:
        tokens = name_str.split()
        if not tokens: return ""
        if len(tokens) == 1: return tokens[0].upper()

        if len(tokens) > 2 and tokens[-2].lower() in surname_prefixes:
            family = " ".join(tokens[-2:])
            given = " ".join(tokens[:-2])
        else:
            family = tokens[-1]
            given = " ".join(tokens[:-1])

            # === V4.0 反序纠错 ===
            first_token_upper = tokens[0].upper()
            is_family_hyphenated = '-' in family
            is_first_token_cn_surname = first_token_upper in COMMON_CN_SURNAMES
            family_upper = family.upper()
            is_family_cn_surname = family_upper in COMMON_CN_SURNAMES

            should_swap = False

            if is_family_hyphenated and is_first_token_cn_surname:
                should_swap = True
            elif len(tokens) == 2 and (not is_family_cn_surname) and is_first_token_cn_surname:
                should_swap = True

            if should_swap:
                family = tokens[0]
                given = " ".join(tokens[1:])

    family_fmt = family.upper()

    if family_fmt in COMMON_CN_SURNAMES and ' ' not in given and '-' not in given:
        given = try_split_pinyin(given)

    given_clean = given.replace('.', ' ').replace('-', ' ')
    given_tokens = given_clean.split()
    given_initials = [t[0].upper() for t in given_tokens if t]
    given_fmt = " ".join(given_initials)

    if given_fmt:
        return f"{family_fmt} {given_fmt}"
    else:
        return family_fmt


def has_chinese_char(text: str) -> bool:
    """【V5.0】辅助函数：检测是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def format_authors(authors: list) -> str:
    """格式化作者列表，支持语言自适应"""
    if not authors:
        return "[佚名]"

    formatted_authors = []
    # 统计中文名字数量，决定最后的后缀是 "et al" 还是 "等"
    cn_name_count = 0

    for auth in authors:
        if has_chinese_char(auth):
            cn_name_count += 1
            # 中文名直接保留
            formatted_authors.append(auth.strip())
        else:
            fmt_name = format_western_name(auth)
            formatted_authors.append(fmt_name)

    # 决策：如果超过半数是中文名，或者前3个里有中文名，则认为是中文环境
    # 简单判定：只要第一个作者是中文，就用 "等"
    is_chinese_context = False
    if authors and has_chinese_char(authors[0]):
        is_chinese_context = True

    if len(formatted_authors) > 3:
        suffix = ", 等" if is_chinese_context else ", et al"
        return ", ".join(formatted_authors[:3]) + suffix
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

    # === 【V5.1 修复】页码清洗逻辑 ===
    if data.pages:
        # 1. 移除 'None' 或 'null' 字符串 (忽略大小写)
        # 某些引擎可能会在页码缺失时生成 "None-None"
        clean_pages = re.sub(r'(?i)(none|null)', '', str(data.pages))

        # 2. 清洗多余的空格和连字符
        # 将 "123 -- 456" 变成 "123-456"，将 " - " 变成 ""
        clean_pages = clean_pages.replace(" ", "").replace("--", "-")
        clean_pages = clean_pages.strip("-")

        # 3. 只有当确实有内容时才追加
        if clean_pages:
            result += f": {clean_pages}"

    result += "."
    return result


if __name__ == "__main__":
    print("🚀 Formatter Test V5.1 (None-None Fix)")


    # 模拟 CitationData 对象
    class MockData:
        def __init__(self, title, pages):
            self.title = title
            self.pages = pages
            self.source = "Journal"
            self.authors = ["Smith A"]
            self.year = "2023"
            self.volume = "1"
            self.issue = "1"


    # 测试用例
    cases = [
        ("Case 1: Normal", "123-125"),
        ("Case 2: None-None", "None-None"),
        ("Case 3: Mixed", "None-125"),
        ("Case 4: Null string", "null-null"),
        ("Case 5: Hyphen only", "-"),
    ]

    for label, p_val in cases:
        d = MockData("Test Title", p_val)
        res = to_gbt7714(d)
        print(f"{label:<20} | Raw Pages: {p_val:<10} | Result: {res}")