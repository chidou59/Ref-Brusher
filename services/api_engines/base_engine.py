"""
文件路径: services/api_engines/base_engine.py
=========================================================
【可用接口说明】

class BaseEngine:
    # --- 必须被子类重写的方法 ---
    def search(self, query: str) -> CitationData:
        '''
        输入: 用户给的原始文本 (query)
        输出: 标准化的 CitationData 对象
        '''
        pass

    # --- 通用工具方法 ---
    def get_headers(self) -> dict:
        '''自动生成带身份标识的 HTTP 请求头'''
        pass
=========================================================
"""

from abc import ABC, abstractmethod
import requests
from typing import Optional
import logging

# 引入我们的标准数据模型和配置
from models.citation_model import CitationData
import config

class BaseEngine(ABC):
    """
    所有 API 引擎的父类。
    作用：强制规定所有子类（OpenAlex, Crossref等）必须长什么样，
    避免未来代码乱七八糟。
    """

    def __init__(self):
        self.name = "BaseEngine"
        # 配置日志，方便调试
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

    def get_headers(self) -> dict:
        """
        生成标准请求头。
        根据 config.py 中的配置，带上 User-Agent，
        这是防封号的关键一步。
        """
        return {
            "User-Agent": config.USER_AGENT,
            "Accept": "application/json" # 告诉服务器我们要 JSON 数据
        }

    @abstractmethod
    def search(self, query: str) -> Optional[CitationData]:
        """
        核心抽象方法。
        子类必须实现这个方法，否则报错。
        """
        pass

    def safe_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        通用的网络请求发送器。
        封装了超时处理、错误捕获，防止因为断网导致程序闪退。
        """
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status() # 如果状态码不是200，抛出异常
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"[{self.name}] 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[{self.name}] 未知错误: {e}")
            return None