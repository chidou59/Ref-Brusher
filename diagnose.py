"""
文件路径: diagnose.py
=========================================================
【作用】
独立运行此脚本，诊断 API、配置和路径问题。
不依赖界面，直接在控制台输出结果。
=========================================================
"""
import sys
import os
import time

# 1. 强制设置路径，模拟 main.py 的环境
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 50)
print(f"🚀 开始诊断 (RefFormatter Diagnostic)")
print(f"📂 当前工作目录: {os.getcwd()}")
print(f"🐍 Python 解释器: {sys.executable}")
print("=" * 50)

try:
    # 2. 检查 Config
    print("\n[1/4] 检查配置 (config.py)...")
    import config

    print(f"   -> 配置文件路径: {config.__file__}")
    print(f"   -> OpenAlex 开关: {config.SourceConfig.OPENALEX_ENABLED}")
    print(f"   -> MIN_REQUEST_INTERVAL: {config.MIN_REQUEST_INTERVAL}")

    if not config.SourceConfig.OPENALEX_ENABLED:
        print("   ❌ 警告: OpenAlex 未启用！请修改 config.py。")

    # 3. 检查 Orchestrator 文件来源
    print("\n[2/4] 检查核心逻辑 (Orchestrator)...")
    from services.orchestrator import Orchestrator
    import inspect

    orc_file = inspect.getfile(Orchestrator)
    print(f"   -> 代码加载自: {orc_file}")

    # 读取文件前几行，看看有没有我们写的 [调试] 字样
    with open(orc_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if "[调试]" in content:
            print("   ✅ 代码版本验证通过 (检测到调试代码)")
        else:
            print("   ❌ 警告: 加载的是旧版本代码！没有检测到 print 调试语句。")
            print("      请检查你是否保存了文件，或是否有重名文件。")

    # 4. 检查 API 引擎
    print("\n[3/4] 初始化引擎...")
    orc = Orchestrator()
    print(f"   -> 已加载引擎数量: {len(orc.engines)}")
    if len(orc.engines) > 0:
        print(f"   -> 第一个引擎是: {orc.engines[0].name}")
    else:
        print("   ❌ 错误: 引擎列表为空！")

    # 5. 实弹射击测试
    print("\n[4/4] 发起测试请求...")
    test_query = "Deep learning Nature 2015"
    print(f"   -> 测试词: '{test_query}'")

    # 强制刷新缓冲区，确保 print 出来
    sys.stdout.flush()

    result = orc.format_single(test_query)

    print("-" * 30)
    print(f"📝 最终返回结果:\n{result}")
    print("-" * 30)

    if "[J]" in result or "Nature" in result:
        print("\n✅ 诊断结论: 核心逻辑正常！问题可能出在 UI 或 线程调用上。")
    else:
        print("\n❌ 诊断结论: 核心逻辑返回了非标准格式，请检查网络或解析代码。")

except Exception as e:
    import traceback

    print("\n❌ 发生严重错误:")
    traceback.print_exc()

print("\n诊断结束。")