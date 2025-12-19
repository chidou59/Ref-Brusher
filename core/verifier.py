# --------------------------------------------------------------------------------
# 文件功能：参考文献格式复核器 (Verifier)
# --------------------------------------------------------------------------------
#
# 【可用的接口 (Public Methods)】
# 供 main.py 调用：
#
# class ReferenceVerifier:
#    - verify(text: str) -> dict:
#         检查单条文献格式。
#         返回一个字典，包含:
#         {
#             "is_valid": bool,   # 是否通过复核
#             "reason": str       # 如果失败，具体的错误原因 (例如 "缺少年份")
#         }
#
# --------------------------------------------------------------------------------

import re

class ReferenceVerifier:
    """
    专门用于检查参考文献格式是否符合 GB/T 7714 标准的工具类
    """

    def verify(self, text: str) -> dict:
        """
        核心复核方法
        :param text: 待检查的文献文本
        :return: 包含检查结果和原因的字典
        """
        text = text.strip()
        result = {
            "is_valid": True,
            "reason": "格式规范"
        }

        # 规则 1: 检查结尾标点
        # 国标规定结尾必须是点号 "."
        if not text.endswith("."):
            result["is_valid"] = False
            result["reason"] = "缺少结尾点号(.)"
            return result

        # 规则 2: 检查年份
        # 必须包含 19xx 或 20xx 的年份格式
        if not re.search(r'(19|20)\d{2}', text):
            result["is_valid"] = False
            result["reason"] = "未检测到有效年份"
            return result

        # 规则 3: 检查长度 (防止空结果或过短的错误结果)
        if len(text) < 10:
            result["is_valid"] = False
            result["reason"] = "内容过短，可能不是有效文献"
            return result

        # 如果通过所有规则
        return result