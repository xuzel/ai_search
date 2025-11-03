"""
完整系统测试 - 全量功能测试

测试范围：
- Phase 1: RAG 系统
- Phase 2: 重排序系统
- Phase 3: 领域工具（天气、金融、路线）
- Phase 4: 多模态（OCR、Vision、PDF）
- Phase 5: 工作流引擎
- 核心代理（Research、Code、Chat、RAG）
- 路由器
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# 测试 1: 配置和环境验证
# ============================================================================

async def test_configuration():
    """测试配置加载和 API 密钥"""
    print("\n" + "=" * 60)
    print("测试 1: 配置和环境验证")
    print("=" * 60)

    try:
        config = get_config()

        # 检查核心配置
        print("\n【核心 API 配置】")

        # LLM
        dashscope_key = config.llm.dashscope.api_key
        print(f"✓ DashScope API Key: {'已配置' if dashscope_key and dashscope_key != 'your_dashscope_api_key_here' else '❌ 未配置'}")

        # 搜索
        serpapi_key = config.search.serpapi_key
        print(f"✓ SerpAPI Key: {'已配置' if serpapi_key and 'your' not in serpapi_key else '❌ 未配置'}")

        # 多模态
        print("\n【Phase 4 - 多模态配置】")
        google_key = config.multimodal.vision.api_key if hasattr(config.multimodal, 'vision') else None
        print(f"✓ Google Gemini API: {'已配置' if google_key and 'your' not in google_key else '❌ 未配置'}")

        # 领域工具
        print("\n【Phase 3 - 领域工具配置】")
        weather_key = config.domain_tools.weather.api_key if hasattr(config.domain_tools, 'weather') else None
        print(f"✓ OpenWeatherMap: {'已配置' if weather_key and 'your' not in weather_key else '❌ 未配置'}")

        finance_key = config.domain_tools.finance.alpha_vantage_key if hasattr(config.domain_tools, 'finance') else None
        print(f"✓ Alpha Vantage: {'已配置' if finance_key and 'your' not in finance_key else '❌ 未配置'}")

        routing_key = config.domain_tools.routing.api_key if hasattr(config.domain_tools, 'routing') else None
        print(f"✓ OpenRouteService: {'已配置' if routing_key and 'your' not in routing_key else '❌ 未配置'}")

        print("\n✅ 配置加载成功")
        return True

    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 2: LLM 管理器
# ============================================================================

async def test_llm_manager():
    """测试 LLM 管理器"""
    print("\n" + "=" * 60)
    print("测试 2: LLM 管理器")
    print("=" * 60)

    try:
        from src.llm import LLMManager

        config = get_config()
        llm = LLMManager(config=config)

        print(f"\n可用提供商: {llm.available_providers}")
        print(f"首选提供商: {llm.preferred_provider}")

        # 测试简单补全
        print("\n测试 LLM 补全...")
        response = await llm.complete(
            messages=[{"role": "user", "content": "用一句话介绍 Python"}],
            max_tokens=100
        )

        print(f"✓ LLM 响应: {response[:100]}...")
        print("\n✅ LLM 管理器测试通过")
        return True

    except Exception as e:
        print(f"\n❌ LLM 管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 3: 路由器
# ============================================================================

async def test_router():
    """测试查询路由器"""
    print("\n" + "=" * 60)
    print("测试 3: 路由器")
    print("=" * 60)

    try:
        from src.router import Router, TaskType

        test_cases = [
            ("今天北京天气怎么样", TaskType.DOMAIN_WEATHER),
            ("AAPL股价多少", TaskType.DOMAIN_FINANCE),
            ("从上海到北京怎么走", TaskType.DOMAIN_ROUTING),
            ("一周有多少小时", TaskType.CODE),
            ("什么是机器学习", TaskType.RESEARCH),
            ("你好", TaskType.CHAT),
        ]

        print("\n测试查询分类:")
        all_correct = True

        for query, expected_type in test_cases:
            result = Router.classify(query)
            confidence = Router.get_confidence(query, result)

            status = "✓" if result == expected_type else "❌"
            print(f"{status} '{query}' -> {result.value} (置信度: {confidence:.2f})")

            if result != expected_type:
                all_correct = False

        if all_correct:
            print("\n✅ 路由器测试全部通过")
            return True
        else:
            print("\n⚠️  部分路由测试未通过")
            return False

    except Exception as e:
        print(f"\n❌ 路由器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 4: 搜索工具
# ============================================================================

async def test_search_tool():
    """测试搜索工具"""
    print("\n" + "=" * 60)
    print("测试 4: 搜索工具")
    print("=" * 60)

    try:
        from src.tools import SearchTool

        config = get_config()
        search = SearchTool(api_key=config.search.serpapi_key)

        print("\n执行搜索: 'Python programming'")
        results = await search.search("Python programming", num_results=3)

        print(f"\n搜索结果数: {len(results)}")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result.get('title', 'N/A')}")
            print(f"   来源: {result.get('source', 'N/A')}")
            print(f"   摘要: {result.get('snippet', 'N/A')[:100]}...")

        print("\n✅ 搜索工具测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 搜索工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 5: 代码执行器
# ============================================================================

async def test_code_executor():
    """测试代码执行器"""
    print("\n" + "=" * 60)
    print("测试 5: 代码执行器")
    print("=" * 60)

    try:
        from src.tools import CodeExecutor

        config = get_config()
        executor = CodeExecutor(config=config)

        # 测试简单计算
        code = """
# 计算一周有多少小时
hours_per_day = 24
days_per_week = 7
result = hours_per_day * days_per_week
print(f"一周有 {result} 小时")
"""

        print("\n执行代码:")
        print("-" * 40)
        print(code)
        print("-" * 40)

        result = await executor.execute(code)

        print(f"\n执行结果:")
        print(f"成功: {result['success']}")
        print(f"输出: {result['output']}")

        if result['success']:
            print("\n✅ 代码执行器测试通过")
            return True
        else:
            print(f"\n❌ 代码执行失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ 代码执行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 6: 天气工具
# ============================================================================

async def test_weather_tool():
    """测试天气工具"""
    print("\n" + "=" * 60)
    print("测试 6: 天气工具 (Phase 3)")
    print("=" * 60)

    try:
        from src.tools import WeatherTool

        config = get_config()
        weather = WeatherTool(
            api_key=config.domain_tools.weather.api_key,
            units="metric",
            language="zh_cn"
        )

        print("\n查询北京天气...")
        result = await weather.get_current_weather("Beijing")

        print(f"\n城市: {result['location']}")
        print(f"温度: {result['temperature']}°C")
        print(f"湿度: {result['humidity']}%")
        print(f"天气: {result['status']}")
        print(f"描述: {result['description']}")

        # 格式化输出
        summary = weather.format_weather_summary(result)
        print(f"\n格式化摘要:\n{summary}")

        print("\n✅ 天气工具测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 天气工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 7: 金融工具
# ============================================================================

async def test_finance_tool():
    """测试金融工具"""
    print("\n" + "=" * 60)
    print("测试 7: 金融工具 (Phase 3)")
    print("=" * 60)

    try:
        from src.tools import FinanceTool

        config = get_config()
        finance = FinanceTool(
            alpha_vantage_key=config.domain_tools.finance.alpha_vantage_key
        )

        print("\n查询 AAPL 股票价格...")
        result = await finance.get_stock_price("AAPL")

        print(f"\n股票: {result['symbol']}")
        print(f"价格: ${result['price']}")
        print(f"变化: ${result.get('change', 'N/A')}")
        print(f"涨跌幅: {result.get('change_percent', 'N/A')}")

        # 格式化输出
        summary = finance.format_stock_summary(result)
        print(f"\n格式化摘要:\n{summary}")

        print("\n✅ 金融工具测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 金融工具测试失败: {e}")
        print("注意: 如果是 API 限额问题，会自动回退到 yfinance")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 8: 路线工具
# ============================================================================

async def test_routing_tool():
    """测试路线工具"""
    print("\n" + "=" * 60)
    print("测试 8: 路线工具 (Phase 3)")
    print("=" * 60)

    try:
        from src.tools import RoutingTool

        config = get_config()
        routing = RoutingTool(api_key=config.domain_tools.routing.api_key)

        print("\n地理编码: '上海'")
        locations = await routing.geocode("上海", limit=1)

        if locations:
            shanghai = locations[0]
            print(f"位置: {shanghai['name']}")
            print(f"坐标: {shanghai['coordinates']}")

            print("\n地理编码: '北京'")
            locations = await routing.geocode("北京", limit=1)

            if locations:
                beijing = locations[0]
                print(f"位置: {beijing['name']}")
                print(f"坐标: {beijing['coordinates']}")

                print("\n计算上海到北京的驾车路线...")
                route = await routing.get_route(
                    start=shanghai['coordinates'],
                    end=beijing['coordinates'],
                    profile="driving-car"
                )

                print(f"\n距离: {route['distance_km']:.1f} 公里")
                print(f"时间: {route['duration_minutes']:.0f} 分钟 ({route['duration_hours']:.1f} 小时)")

                # 格式化输出
                summary = routing.format_route_summary(route, "上海", "北京")
                print(f"\n格式化摘要:\n{summary}")

                print("\n✅ 路线工具测试通过")
                return True

        print("\n❌ 地理编码失败")
        return False

    except Exception as e:
        print(f"\n❌ 路线工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 9: OCR 工具
# ============================================================================

async def test_ocr_tool():
    """测试 OCR 工具"""
    print("\n" + "=" * 60)
    print("测试 9: OCR 工具 (Phase 4)")
    print("=" * 60)

    try:
        from src.tools import OCRTool

        ocr = OCRTool(languages=["ch", "en"], use_gpu=False)

        print("\n✓ OCR 工具初始化成功")
        print(f"支持的语言: {ocr.get_supported_languages()[:5]}...")

        # 检查是否有测试图片
        test_image = Path("test_image.png")
        if test_image.exists():
            print(f"\n测试图像: {test_image}")
            result = await ocr.extract_text(str(test_image))

            print(f"检测到 {result['line_count']} 行文本")
            print(f"提取的文本:\n{result['text'][:200]}...")

            print("\n✅ OCR 工具测试通过")
            return True
        else:
            print("\n⚠️  未找到测试图像 'test_image.png'")
            print("OCR 工具初始化成功，但跳过实际测试")
            print("\n✅ OCR 工具基础测试通过")
            return True

    except Exception as e:
        print(f"\n❌ OCR 工具测试失败: {e}")
        print("注意: 首次运行需要下载 PaddleOCR 模型（约 10MB）")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 10: Vision 工具
# ============================================================================

async def test_vision_tool():
    """测试 Vision 工具"""
    print("\n" + "=" * 60)
    print("测试 10: Vision 工具 (Phase 4)")
    print("=" * 60)

    try:
        from src.tools import VisionTool

        config = get_config()
        vision = VisionTool(
            api_key=config.multimodal.vision.api_key,
            model="gemini-2.0-flash-exp"
        )

        print("\n✓ Vision 工具初始化成功")

        # 检查是否有测试图片
        test_image = Path("test_photo.jpg")
        if test_image.exists():
            print(f"\n分析图像: {test_image}")
            result = await vision.analyze_image(
                str(test_image),
                prompt="用一句话描述这张图片"
            )

            print(f"\n分析结果:\n{result['analysis']}")

            print("\n✅ Vision 工具测试通过")
            return True
        else:
            print("\n⚠️  未找到测试图像 'test_photo.jpg'")
            print("Vision 工具初始化成功，但跳过实际测试")
            print("\n✅ Vision 工具基础测试通过")
            return True

    except Exception as e:
        print(f"\n❌ Vision 工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 11: 工作流引擎
# ============================================================================

async def test_workflow_engine():
    """测试工作流引擎"""
    print("\n" + "=" * 60)
    print("测试 11: 工作流引擎 (Phase 5)")
    print("=" * 60)

    try:
        from src.workflow import WorkflowEngine, ExecutionMode

        engine = WorkflowEngine(max_parallel_tasks=3)
        workflow = engine.create_workflow("test_workflow", mode=ExecutionMode.DAG)

        # 定义测试任务
        async def task_a():
            print("  执行任务 A")
            await asyncio.sleep(0.5)
            return {"task": "A", "value": 10}

        async def task_b(a_result):
            print("  执行任务 B")
            await asyncio.sleep(0.5)
            return {"task": "B", "value": a_result['value'] * 2}

        async def task_c(a_result, b_result):
            print("  执行任务 C")
            await asyncio.sleep(0.5)
            return {"task": "C", "value": a_result['value'] + b_result['value']}

        # 添加任务
        workflow.add_task("A", func=task_a)
        workflow.add_task("B", func=task_b, dependencies={"A"})
        workflow.add_task("C", func=task_c, dependencies={"A", "B"})

        # 验证工作流
        workflow.validate()
        print("\n✓ 工作流验证通过（无循环依赖）")

        # 执行
        print("\n执行工作流...")
        result = await engine.execute(workflow)

        print(f"\n执行结果:")
        print(f"成功: {result.success}")
        print(f"完成任务: {result.completed_count}/{result.task_count}")
        print(f"执行时间: {result.execution_time:.2f}s")
        print(f"最终结果: {result.results.get('C')}")

        if result.success:
            print("\n✅ 工作流引擎测试通过")
            return True
        else:
            print(f"\n❌ 工作流执行失败: {result.errors}")
            return False

    except Exception as e:
        print(f"\n❌ 工作流引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 12: 任务分解器
# ============================================================================

async def test_task_decomposer():
    """测试任务分解器"""
    print("\n" + "=" * 60)
    print("测试 12: 任务分解器 (Phase 5)")
    print("=" * 60)

    try:
        from src.workflow import TaskDecomposer
        from src.llm import LLMManager

        config = get_config()
        llm = LLMManager(config=config)
        decomposer = TaskDecomposer(llm, max_subtasks=5)

        # 测试查询
        query = "对比北京和上海的温度差异"

        print(f"\n分解查询: '{query}'")
        plan = await decomposer.decompose(query)

        print(f"\n目标: {plan.goal}")
        print(f"复杂度: {plan.complexity}")
        print(f"步骤数: {plan.estimated_steps}")

        print(f"\n子任务:")
        for i, subtask in enumerate(plan.subtasks, 1):
            deps = f" (依赖: {', '.join(subtask.dependencies)})" if subtask.dependencies else ""
            print(f"{i}. [{subtask.tool}] {subtask.description}{deps}")
            print(f"   查询: {subtask.query}")

        print("\n✅ 任务分解器测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 任务分解器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 13: Research Agent
# ============================================================================

async def test_research_agent():
    """测试研究代理"""
    print("\n" + "=" * 60)
    print("测试 13: Research Agent")
    print("=" * 60)

    try:
        from src.agents import ResearchAgent
        from src.llm import LLMManager
        from src.tools import SearchTool, ScraperTool

        config = get_config()
        llm = LLMManager(config=config)
        search_tool = SearchTool(api_key=config.search.serpapi_key)
        scraper = ScraperTool()

        agent = ResearchAgent(
            llm_manager=llm,
            search_tool=search_tool,
            scraper=scraper
        )

        print("\n执行研究: 'What is Python?'")
        result = await agent.research("What is Python?", max_sources=2)

        print(f"\n研究完成:")
        print(f"来源数: {len(result.get('sources', []))}")
        print(f"\n摘要:\n{result.get('summary', 'N/A')[:300]}...")

        print("\n✅ Research Agent 测试通过")
        return True

    except Exception as e:
        print(f"\n❌ Research Agent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 测试 14: Code Agent
# ============================================================================

async def test_code_agent():
    """测试代码代理"""
    print("\n" + "=" * 60)
    print("测试 14: Code Agent")
    print("=" * 60)

    try:
        from src.agents import CodeAgent
        from src.llm import LLMManager
        from src.tools import CodeExecutor

        config = get_config()
        llm = LLMManager(config=config)
        executor = CodeExecutor(config=config)

        agent = CodeAgent(llm_manager=llm, code_executor=executor)

        print("\n执行任务: '计算一周有多少小时'")
        result = await agent.solve("计算一周有多少小时")

        print(f"\n生成的代码:\n{result.get('code', 'N/A')}")
        print(f"\n执行结果:\n{result.get('output', 'N/A')}")
        print(f"\n解释:\n{result.get('explanation', 'N/A')[:200]}...")

        print("\n✅ Code Agent 测试通过")
        return True

    except Exception as e:
        print(f"\n❌ Code Agent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 主测试函数
# ============================================================================

async def run_all_tests():
    """运行所有测试"""

    print("\n" + "=" * 60)
    print("AI 搜索引擎 - 完整系统测试")
    print("=" * 60)
    print("\n测试范围: Phase 1-5 全部功能")
    print("预计时间: 5-10 分钟\n")

    tests = [
        ("配置和环境", test_configuration),
        ("LLM 管理器", test_llm_manager),
        ("路由器", test_router),
        ("搜索工具", test_search_tool),
        ("代码执行器", test_code_executor),
        ("天气工具 (Phase 3)", test_weather_tool),
        ("金融工具 (Phase 3)", test_finance_tool),
        ("路线工具 (Phase 3)", test_routing_tool),
        ("OCR 工具 (Phase 4)", test_ocr_tool),
        ("Vision 工具 (Phase 4)", test_vision_tool),
        ("工作流引擎 (Phase 5)", test_workflow_engine),
        ("任务分解器 (Phase 5)", test_task_decomposer),
        ("Research Agent", test_research_agent),
        ("Code Agent", test_code_agent),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results[test_name] = False

        # 暂停一下，避免 API 限流
        await asyncio.sleep(1)

    # 汇总结果
    print("\n\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")

    print("\n详细结果:")
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print("\n" + "=" * 60)

    if passed == total:
        print("🎉 恭喜！所有测试通过！")
    elif passed >= total * 0.8:
        print("✅ 大部分测试通过，系统基本可用")
    else:
        print("⚠️  多个测试失败，请检查配置和依赖")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
