"""
快速测试 - 测试核心功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_all():
    """运行所有快速测试"""

    print("\n" + "=" * 70)
    print("AI 搜索引擎 - 快速功能测试")
    print("=" * 70)

    results = {}

    # 测试 1: 配置
    print("\n【测试 1】配置加载")
    try:
        from src.utils import get_config
        config = get_config()
        print(f"✅ 配置加载成功")
        print(f"   - Search API: {'已配置' if config.search.serpapi_key and 'your' not in config.search.serpapi_key else '未配置'}")
        results['配置'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['配置'] = False

    # 测试 2: LLM Manager
    print("\n【测试 2】LLM 管理器")
    try:
        from src.llm import LLMManager
        from src.utils import get_config

        config = get_config()
        llm = LLMManager(config=config)

        print(f"✅ LLM 初始化成功")
        print(f"   - 可用提供商: {list(llm.providers.keys())}")
        print(f"   - 主提供商: {llm._primary_provider}")

        # 测试补全
        response = await llm.complete(
            messages=[{"role": "user", "content": "Say 'test ok'"}],
            max_tokens=10
        )
        print(f"   - LLM 响应: {response[:50]}")
        results['LLM'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['LLM'] = False

    # 测试 3: 搜索
    print("\n【测试 3】搜索工具")
    try:
        from src.tools import SearchTool
        from src.utils import get_config

        config = get_config()
        search = SearchTool(api_key=config.search.serpapi_key)

        results_data = await search.search("Python", num_results=2)
        print(f"✅ 搜索成功")
        print(f"   - 结果数: {len(results_data)}")
        if results_data:
            print(f"   - 第一个: {results_data[0].get('title', 'N/A')[:50]}")
        results['搜索'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['搜索'] = False

    # 测试 4: 代码执行
    print("\n【测试 4】代码执行器")
    try:
        from src.tools import CodeExecutor

        executor = CodeExecutor()
        result = await executor.execute("print(7 * 24)")

        print(f"✅ 代码执行成功")
        print(f"   - 输出: {result.get('output', '').strip()}")
        results['代码执行'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['代码执行'] = False

    # 测试 5: 路由器
    print("\n【测试 5】查询路由器")
    try:
        from src.router import Router, TaskType

        test_cases = [
            ("今天北京天气怎么样", TaskType.DOMAIN_WEATHER),
            ("AAPL股价", TaskType.DOMAIN_FINANCE),
            ("一周有多少小时", TaskType.CODE),
        ]

        all_pass = True
        for query, expected in test_cases:
            result = Router.classify(query)
            if result == expected:
                print(f"   ✓ '{query}' -> {result.value}")
            else:
                print(f"   ✗ '{query}' -> {result.value} (期望: {expected.value})")
                all_pass = False

        if all_pass:
            print(f"✅ 路由器测试通过")
            results['路由器'] = True
        else:
            print(f"⚠️  部分测试未通过")
            results['路由器'] = False
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['路由器'] = False

    # 测试 6: 金融工具
    print("\n【测试 6】金融工具")
    try:
        from src.tools import FinanceTool
        from src.utils import get_config

        config = get_config()
        finance = FinanceTool(
            alpha_vantage_key=config.domain_tools.finance.alpha_vantage_key
        )

        result = await finance.get_stock_price("AAPL")
        print(f"✅ 金融工具测试通过")
        print(f"   - AAPL: ${result.get('price', 'N/A')}")
        results['金融'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['金融'] = False

    # 测试 7: 天气工具
    print("\n【测试 7】天气工具")
    try:
        from src.tools import WeatherTool
        from src.utils import get_config

        config = get_config()
        weather = WeatherTool(api_key=config.domain_tools.weather.api_key)

        result = await weather.get_current_weather("Beijing")
        if 'error' not in result:
            print(f"✅ 天气工具测试通过")
            print(f"   - 北京: {result.get('temperature', 'N/A')}°C")
            results['天气'] = True
        else:
            print(f"❌ 失败: {result.get('error')}")
            results['天气'] = False
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['天气'] = False

    # 测试 8: 工作流引擎
    print("\n【测试 8】工作流引擎")
    try:
        from src.workflow import WorkflowEngine, ExecutionMode

        engine = WorkflowEngine()
        workflow = engine.create_workflow("test", mode=ExecutionMode.SEQUENTIAL)

        async def simple_task():
            return {"value": 42}

        workflow.add_task("task1", func=simple_task)
        result = await engine.execute(workflow)

        print(f"✅ 工作流引擎测试通过")
        print(f"   - 成功: {result.success}")
        print(f"   - 结果: {result.results.get('task1')}")
        results['工作流'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['工作流'] = False

    # 测试 9: 任务分解
    print("\n【测试 9】任务分解器")
    try:
        from src.workflow import TaskDecomposer
        from src.llm import LLMManager
        from src.utils import get_config

        config = get_config()
        llm = LLMManager(config=config)
        decomposer = TaskDecomposer(llm)

        plan = await decomposer.decompose("对比北京和上海温度")
        print(f"✅ 任务分解器测试通过")
        print(f"   - 目标: {plan.goal}")
        print(f"   - 步骤数: {plan.estimated_steps}")
        results['任务分解'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['任务分解'] = False

    # 测试 10: Research Agent
    print("\n【测试 10】Research Agent")
    try:
        from src.agents import ResearchAgent
        from src.llm import LLMManager
        from src.tools import SearchTool, ScraperTool
        from src.utils import get_config

        config = get_config()
        llm = LLMManager(config=config)
        search = SearchTool(api_key=config.search.serpapi_key)
        scraper = ScraperTool()

        agent = ResearchAgent(llm, search, scraper)
        result = await agent.research("What is AI?", max_sources=1)

        print(f"✅ Research Agent 测试通过")
        print(f"   - 摘要长度: {len(result.get('summary', ''))}")
        results['Research'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['Research'] = False

    # 测试 11: Code Agent
    print("\n【测试 11】Code Agent")
    try:
        from src.agents import CodeAgent
        from src.llm import LLMManager
        from src.tools import CodeExecutor
        from src.utils import get_config

        config = get_config()
        llm = LLMManager(config=config)
        executor = CodeExecutor()

        agent = CodeAgent(llm, executor)
        result = await agent.solve("计算 10 + 20")

        print(f"✅ Code Agent 测试通过")
        print(f"   - 输出: {result.get('output', 'N/A')[:50]}")
        results['Code Agent'] = True
    except Exception as e:
        print(f"❌ 失败: {e}")
        results['Code Agent'] = False

    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)\n")

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    print("\n" + "=" * 70)

    if passed >= total * 0.8:
        print("🎉 大部分功能正常工作！")
    elif passed >= total * 0.5:
        print("✅ 核心功能可用")
    else:
        print("⚠️  需要检查配置")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all())
