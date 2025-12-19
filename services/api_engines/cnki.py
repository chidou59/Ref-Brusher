"""
文件路径: services/api_engines/cnki.py
=========================================================
【可用接口说明】

class CnkiEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        策略: 百度(首选) -> Bing(备选) -> 搜狗(保底)
        解决: 百度403 & Bing验证码问题
        '''
        pass
=========================================================
"""

# ==============================================================================
# 👇 1. 必填：请填入您的百度 Cookie (这是最稳的方案，如果下面代码跑不通，请务必填这个)
MANUAL_COOKIE = ""
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import re
import uuid
import os

from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class CnkiEngine(BaseEngine):
    """
    知网 (CNKI) 搜索引擎 - 三通道生存狂版 (Baidu + Bing + Sogou)
    """

    def __init__(self):
        super().__init__()
        self.name = "CNKI_Proxy"
        self.session = requests.Session()

    def get_headers(self, source="baidu") -> dict:
        """根据不同的源生成伪装请求头"""
        # 随机选用一个浏览器头，增加通过率
        ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        ua = random.choice(ua_list)

        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }

        if source == "baidu":
            headers['Referer'] = 'https://xueshu.baidu.com/'
            if MANUAL_COOKIE: headers['Cookie'] = MANUAL_COOKIE
        elif source == "bing":
            headers['Referer'] = 'https://www.bing.com/'
        elif source == "sogou":
            headers['Referer'] = 'https://scholar.sogou.com/'
            # 搜狗有时候需要一个假的 Cookie 才能跑
            headers['Cookie'] = f'SUV={int(time.time() * 1000)};'

        return headers

    def search(self, query: str) -> CitationData:
        """总入口：三级火箭策略"""

        # 1. 尝试百度 (最全)
        res = self.search_via_baidu(query)
        if res: return res

        # 2. 尝试 Bing (最快)
        self.logger.warning(f"[{self.name}] 百度通道失效，切换至 Bing...")
        res = self.search_via_bing(query)
        if res: return res

        # 3. 尝试 搜狗 (最后的希望)
        self.logger.warning(f"[{self.name}] Bing 通道失效 (验证码)，切换至 搜狗(Sogou)...")
        return self.search_via_sogou(query)

    def search_via_baidu(self, query: str):
        url = "https://xueshu.baidu.com/s"
        params = {'wd': f"{query} site:cnki.net", 'tn': 'SE_baiduxueshu_c1gjeupa', 'ie': 'utf-8'}
        self.logger.info(f"[{self.name}] 通道 [1/3]: 百度学术...")
        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("baidu"), timeout=5)
            if resp.status_code == 200 and "验证码" not in resp.text:
                soup = BeautifulSoup(resp.text, 'html.parser')
                item = soup.find('div', class_='sc_content')
                if item: return self._parse_baidu_html(item)
            else:
                self.logger.warning(f"[{self.name}] 百度 403/验证码。")
        except Exception:
            pass
        return None

    def search_via_bing(self, query: str):
        url = "https://www.bing.com/search"
        params = {'q': f"{query} site:cnki.net"}
        self.logger.info(f"[{self.name}] 通道 [2/3]: Bing...")
        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("bing"), timeout=5)
            # Bing 的验证码页面也是 200 OK，所以要查内容
            if "captcha" in resp.text or "challenge" in resp.url:
                self.logger.warning(f"[{self.name}] Bing 触发验证码。")
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 寻找结果列表
            items = soup.find_all('li', class_='b_algo')
            for item in items:
                data = self._parse_bing_html(item)
                if data and data.title: return data
        except Exception:
            pass
        return None

    def search_via_sogou(self, query: str):
        url = "https://scholar.sogou.com/xueshu"
        params = {'ie': 'utf-8', 'query': query}
        self.logger.info(f"[{self.name}] 通道 [3/3]: 搜狗学术...")

        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("sogou"), timeout=8)
            resp.encoding = 'utf-8'

            if "验证码" in resp.text or "antispider" in resp.url:
                self.logger.warning(f"[{self.name}] 搜狗也触发了验证码...")
                # 最后的挣扎：保存搜狗页面看看
                with open("debug_sogou_error.html", "w", encoding="utf-8") as f: f.write(resp.text)
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 搜狗结果通常在 div.results > div.vrwrap
            results = soup.find_all('div', class_='vrwrap')

            if not results:
                self.logger.info(f"[{self.name}] 搜狗未找到结果。")
                return None

            # 找第一个结果
            for item in results:
                # 搜狗解析逻辑
                data = CitationData(entry_type="article", raw_data={"source": "Sogou"})

                # 1. 标题 (h3.tit > a)
                h3 = item.find('h3', class_='tit')
                if h3 and h3.find('a'):
                    data.title = h3.find('a').get_text(strip=True)
                    data.url = "https://scholar.sogou.com" + h3.find('a').get('href', '')

                # 2. 信息 (div.info)
                # 格式: 作者 - 期刊 - 年份
                info_div = item.find('div', class_='info')
                if info_div:
                    # 提取年份
                    text = info_div.get_text(" ", strip=True)
                    year_match = re.search(r'\b(19|20)\d{2}\b', text)
                    if year_match: data.year = year_match.group(0)

                    # 尝试提取作者 (span.p1 或者是第一个 - 之前的内容)
                    # 搜狗比较乱，我们简单分割
                    parts = text.split('-')
                    if len(parts) >= 1:
                        # 假设第一部分是作者
                        data.authors = parts[0].strip().split(',')
                    if len(parts) >= 2:
                        # 假设第二部分是期刊
                        possible_journal = parts[1].strip()
                        if not possible_journal.isdigit():
                            data.source = possible_journal

                if data.title:
                    return data

        except Exception as e:
            self.logger.error(f"[{self.name}] 搜狗通道出错: {e}")

        return None

    def _parse_baidu_html(self, item_soup) -> CitationData:
        """复用之前的百度解析"""
        citation = CitationData(entry_type="article", raw_data={"source": "Baidu"})
        try:
            t = item_soup.find('h3', class_='t')
            if t and t.find('a'): citation.title = t.find('a').get_text(strip=True)

            info = item_soup.find('div', class_='sc_info')
            if info:
                txt = info.get_text(" ", strip=True)
                ym = re.search(r'\b(19|20)\d{2}\b', txt)
                if ym: citation.year = ym.group(0)

                js = info.find('span', class_='sc_journal')
                if js: citation.source = js.get_text(strip=True)
        except:
            pass
        return citation

    def _parse_bing_html(self, item_soup) -> CitationData:
        """复用之前的 Bing 解析"""
        citation = CitationData(entry_type="article", raw_data={"source": "Bing"})
        try:
            h2 = item_soup.find('h2')
            if h2 and h2.find('a'):
                citation.title = h2.find('a').get_text(strip=True)
                citation.url = h2.find('a').get('href', '')

            cap = item_soup.find('div', class_='b_caption')
            if cap:
                txt = cap.get_text(" ", strip=True)
                ym = re.search(r'\b(19|20)\d{2}\b', txt)
                if ym: citation.year = ym.group(0)
        except:
            pass
        return citation