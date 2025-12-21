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
   - 引入拼音字典校验，防止误伤外国名字 (如 Simona 不会被拆)
=========================================================
"""

import re
import html
from models.citation_model import CitationData

# === 1. 数据准备 ===

# 常见中国姓氏拼音 (大写)，用于触发检查
# 包含百家姓 Top 200+，覆盖率极高，防止对纯老外名字触发拼音检测
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

# 全量合法拼音音节表 (无声调)
# 来源：标准汉语拼音方案
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
    """清洗 HTML 标签"""
    if not text:
        return ""
    clean_str = re.sub(r'<[^>]+>', '', text)
    clean_str = html.unescape(clean_str)
    return clean_str.strip()


def try_split_pinyin(given_name: str) -> str:
    """
    【智能拼音拆分 - 严格校验版】
    尝试将连写的拼音双名拆开。
    策略：
    1. 遍历所有可能的分割点。
    2. 只有当拆分出的【两部分】都在 VALID_PINYINS 字典中时，才视为有效拆分。
    3. 防止将 "Simona" 误拆为 "Si mona" (mona 不是拼音)。
    """
    given_name = given_name.strip()
    length = len(given_name)

    # 拼音音节最短2字母(除了a,o,e)，最长6字母(zhuang)。
    # 双名总长度至少4 (如 bo yi)，通常不超过12。
    if length < 3 or length > 12:
        return given_name

    # 尝试从第2个字符到倒数第2个字符进行切分
    # 例如 "Shaoheng" (len 8)
    # i=2: Sh, aoheng (No)
    # i=4: Shao, heng (Yes!)

    # 优先寻找最合理的切分。
    # 从前往后切
    for i in range(1, length):
        part1 = given_name[:i].lower()
        part2 = given_name[i:].lower()

        # 核心校验：两部分必须都是合法拼音
        if part1 in VALID_PINYINS and part2 in VALID_PINYINS:
            # 找到合法拆分！直接返回
            return f"{given_name[:i]} {given_name[i:]}"

    # 如果找不到合法拆分，保持原样
    return given_name


def format_western_name(name_str: str) -> str:
    """
    【姓名整形师 V5.0】
    将外文姓名转换为 GB/T 7714 格式 (严格全大写)
    输入: "Ludwig van Beethoven" -> 输出: "VAN BEETHOVEN L"
    输入: "Han Shaoheng"         -> 输出: "HAN S H"
    输入: "Lee Simona"           -> 输出: "LEE S" (Simona 不是双名，不拆)
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

    # 2. 名: 处理逻辑
    # 【新增】针对中国学者拼音双名连写的特殊优化
    # 条件：姓氏是常见中国姓，且名字没有空格/连字符
    if family_fmt in COMMON_CN_SURNAMES and ' ' not in given and '-' not in given:
        given = try_split_pinyin(given)

    # 清理分隔符，统一变空格 (处理 Jean-Pierre -> Jean Pierre)
    given_clean = given.replace('.', ' ').replace('-', ' ')
    given_tokens = given_clean.split()

    # 提取首字母
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


# ==============================================================================
# 自查测试模块 (Run this file to verify)
# ==============================================================================
if __name__ == "__main__":
    print("🚀 开始自查测试 (Formatter Self-Check)...\n")

    test_cases = [
        # --- 组1: 标准中国双名 (连写) ---
        ("Han Shaoheng", "HAN S H", "双名连写 - 基础"),
        ("Li Xiaolong", "LI X L", "双名连写 - Xiao"),
        ("Zhang Ziyi", "ZHANG Z Y", "双名连写 - Zi yi"),
        ("Wang Jingwei", "WANG J W", "双名连写 - Jing wei"),
        ("Chen Guangkun", "CHEN G K", "双名连写 - Guang kun"),

        # --- 组2: 中国单名 (不应拆) ---
        ("Wang Jing", "WANG J", "单名 - 不应拆分"),
        ("Li Wei", "LI W", "单名 - 不应拆分"),

        # --- 组3: 外国名 (不应误拆) ---
        ("Lee Simona", "LEE S", "外国名 Simona - 不应拆为 S M"),
        ("Han Solo", "HAN S", "外国名 Solo - 不应拆为 S L"),
        ("James Lebron", "JAMES L", "外国名 Lebron - bron非拼音，不拆"),
        ("Tan Christopher", "TAN C", "外国名 Christopher - 不拆"),
        ("Albert Einstein", "EINSTEIN A", "标准外国名"),
        ("Ludwig van Beethoven", "VAN BEETHOVEN L", "带前缀的复姓"),

        # --- 组4: 已有格式 (保持原样) ---
        ("Han, Shao-Heng", "HAN S H", "已有连字符"),
        ("Han, Shao Heng", "HAN S H", "已有空格"),

        # --- 组5: 复杂拼音边界 ---
        ("Lin Yingying", "LIN Y Y", "Ying ying"),
        ("Xu Xian", "XU X", "Xian 是单字 - 不应拆为 Xi an"),
        ("Fan Bingbing", "FAN B B", "Bing bing"),
        ("Ma Yo-Yo", "MA Y Y", "Yo-Yo 连字符")
    ]

    success_count = 0
    fail_count = 0

    print(f"{'输入':<25} | {'预期':<15} | {'实际':<15} | {'结果'}")
    print("-" * 75)

    for raw_name, expected, note in test_cases:
        actual = format_western_name(raw_name)
        is_pass = (actual == expected)
        status = "✅ PASS" if is_pass else "❌ FAIL"
        if is_pass:
            success_count += 1
        else:
            fail_count += 1

        print(f"{raw_name:<25} | {expected:<15} | {actual:<15} | {status}")
        if not is_pass:
            print(f"   >>> 失败原因: {note}")

    print("-" * 75)
    print(f"测试结束: 成功 {success_count} / 总计 {len(test_cases)}")