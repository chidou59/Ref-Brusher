# logic/cn_search_engine.py
# ==============================================================================
# 模块名称: 中文文献搜索引擎 (Based on Baidu Scholar)
# 功能描述: 模拟浏览器访问百度学术，抓取搜索结果的第一条匹配项。
#
# 可用接口 (Public Interfaces):
# 1. engine = BaiduScholarEngine()
#    - 初始化引擎。
#
# 2. result = engine.search(keyword)
#    - 输入: keyword (str) - 论文标题或关键词
#    - 输出: dict (字典) 或 None
#      成功时返回字典格式:
#      {
#          'title': '论文标题',
#          'author': '作者1, 作者2',
#          'year': '2023',
#          'journal': '期刊名称',
#          'url': '百度学术链接',
#          'type': 'CN'  # 标识为中文来源
#      }
#      失败或未找到时返回: None
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import time
import random


class BaiduScholarEngine:
    """
    百度学术搜索引擎封装类
    """

    def __init__(self):
        # 基础搜索链接
        self.base_url = "https://xueshu.baidu.com/s"
        # 请求头 (User-Agent): 伪装成正常的浏览器，防止被百度拦截
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

    def search(self, keyword):
        """
        核心搜索方法
        :param keyword: 搜索关键词 (通常是论文标题)
        :return: 包含文献信息的字典，如果失败则返回 None
        """
        if not keyword or not keyword.strip():
            return None

        # 构造查询参数
        params = {
            'wd': keyword,  # 搜索词
            'tn': 'SE_baiduxueshu_c1gjeupa',  # 百度学术特定的来源标识
            'ie': 'utf-8',  # 编码
            'sc_hit': '1'  # 命中策略
        }

        try:
            # 1. 发起网络请求
            # timeout=10 表示如果10秒没反应就报错，避免程序卡死
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'  # 强制使用utf-8编码，防止中文乱码

            if response.status_code != 200:
                print(f"[CN_Search] 请求失败，状态码: {response.status_code}")
                return None

            # 2. 解析网页 (使用 BeautifulSoup)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 3. 提取第一条结果
            # 百度学术的搜索结果列表通常在 div class="sc_content" 中
            # 我们只取第一个结果 (find 方法只找第一个)
            first_result = soup.find('div', class_='sc_content')

            if not first_result:
                print(f"[CN_Search] 未找到关于 '{keyword}' 的中文结果。")
                return None

            # --- 开始提取具体字段 ---

            # (A) 标题
            # 通常在 h3 标签下的 a 标签里
            title_tag = first_result.find('h3', class_='t')
            if title_tag and title_tag.find('a'):
                raw_title = title_tag.find('a').get_text(strip=True)
                # 百度有时候会在标题里加 <em> 标签标红关键词，get_text 会自动去掉标签只留文字
                title = raw_title
                link = title_tag.find('a')['href']
            else:
                title = "未知标题"
                link = ""

            # (B) 作者、年份、期刊
            # 这些信息通常混杂在 class="sc_info" 的 div 里
            info_div = first_result.find('div', class_='sc_info')

            author_str = ""
            year_str = ""
            journal_str = ""

            if info_div:
                # 1. 提取作者 (作者通常包含在 data-click 属性或者直接是 a 标签)
                # 简单策略：提取 sc_info 下所有的 a 标签，只要不是链接到期刊的，通常就是作者
                # 百度学术结构：作者1, 作者2 - 期刊名 - 年份

                # 获取该行所有文本内容，然后手动分割可能更稳妥
                # 例子: "张三, 李四 - 计算机学报 - 2023 - 被引量: 5"
                info_text = info_div.get_text(" ", strip=True)  # 用空格连接

                # 尝试分离年份 (通常是4位数字)
                # 这是一个简单的查找策略，找文本中出现的年份
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', info_text)
                if year_match:
                    year_str = year_match.group(0)

                # 尝试分离作者 (通常在第一个破折号 - 之前)
                # 这里为了准确，我们还是解析 HTML 标签
                author_links = info_div.find_all('a')
                if author_links:
                    # 假设前2个链接是作者 (根据经验)
                    # 过滤掉不需要的链接（比如 DOI 跳转链接）
                    valid_authors = []
                    for al in author_links:
                        # 简单的过滤逻辑：作者名字通常比较短
                        name = al.get_text(strip=True)
                        if len(name) < 10 and not name.isdigit():
                            valid_authors.append(name)

                    author_str = ", ".join(valid_authors[:3])  # 只取前3个

                # 尝试分离期刊 (通常在 sc_journal 样式里，或者在作者和年份中间)
                journal_tag = info_div.find('span', class_='sc_journal')
                if journal_tag:
                    journal_str = journal_tag.get_text(strip=True)
                else:
                    # 如果没有专门标签，尝试用 sc_info 的文本分析
                    # 这是一个保底策略，未必100%准确，但够用
                    parts = info_text.split('-')
                    if len(parts) >= 2:
                        # 假设中间一段是期刊
                        potential_journal = parts[1].strip()
                        # 如果这段不是年份，就当它是期刊
                        if not potential_journal.isdigit():
                            journal_str = potential_journal

            # 4. 组装结果
            result_data = {
                'title': title,
                'author': author_str if author_str else "未知作者",
                'year': year_str if year_str else "",
                'journal': journal_str if journal_str else "网络文献/未知来源",
                'url': link,
                'type': 'CN'  # 标记为中文
            }

            # 5. 随机等待 (礼貌爬虫)
            # 避免请求太快被百度封IP，随机等待 0.5 到 1.5 秒
            time.sleep(random.uniform(0.5, 1.5))

            return result_data

        except requests.Timeout:
            print("[CN_Search] 网络请求超时。请检查网络连接。")
            return None
        except Exception as e:
            print(f"[CN_Search] 发生未知错误: {e}")
            return None


# ==============================================================================
# 自我测试模块
# 当你直接运行这个文件时 (python logic/cn_search_engine.py)，下面的代码会执行。
# 当此文件被其他文件 import 时，下面的代码不会执行。
# ==============================================================================
if __name__ == "__main__":
    print("正在测试中文搜索引擎...")

    # 1. 实例化
    engine = BaiduScholarEngine()

    # 2. 定义测试关键词
    test_keyword = "深度学习在图像识别中的应用"
    print(f"正在搜索: {test_keyword} ...")

    # 3. 执行搜索
    result = engine.search(test_keyword)

    # 4. 打印结果
    if result:
        print("\n✅ 搜索成功!")
        print("-" * 30)
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']}")
        print(f"年份: {result['year']}")
        print(f"期刊: {result['journal']}")
        print(f"链接: {result['url']}")
        print("-" * 30)
    else:
        print("\n❌ 搜索失败或未找到结果。")