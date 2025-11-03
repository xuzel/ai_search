"""
全面功能测试 - 覆盖所有Phase 1-5功能

测试项目：
1. 天气工具
2. RAG系统
3. 多模态功能 (OCR, Vision)
4. 路线工具
5. 重排序系统
6. Research Agent
7. 完整的端到端场景
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_all_features():
    """运行全面功能测试"""

    print("\n" + "=" * 70)
    print("AI 搜索引擎 - 全面功能测试")
    print("=" * 70)
    print("\n测试范围: Phase 1-5 所有功能")
    print("预计时间: 10-15 分钟\n")

    results = {}

    # ===================================================================
    # 测试 1: 天气工具（更新后的API）
    # ===================================================================
    print("\n【测试 1】天气工具 (Phase 3)")
    print("-" * 70)
    try:
        from src.tools import WeatherTool
        from src.utils import get_config

        config = get_config()
        weather = WeatherTool(
            api_key=config.domain_tools.weather.api_key,
            units="metric",
            language="zh_cn"
        )

        # 测试北京天气
        result = await weather.get_current_weather("Beijing")

        if 'error' not in result:
            print(f"✅ 天气查询成功")
            print(f"   城市: {result['location']}")
            print(f"   温度: {result['temperature']}°C")
            print(f"   湿度: {result['humidity']}%")
            print(f"   天气: {result['status']}")
            print(f"   描述: {result['description']}")

            # 测试天气预报
            print(f"\n   获取未来5天预报...")
            forecast = await weather.get_forecast("Beijing", days=5)
            if 'error' not in forecast:
                print(f"   预报天数: {len(forecast['forecast'])}")

            results['天气工具'] = True
        else:
            print(f"❌ 天气查询失败: {result['error']}")
            print(f"   API Key: {config.domain_tools.weather.api_key[:10]}...")
            print(f"   建议: 检查API key是否有效，新创建的key需要等待几分钟激活")
            results['天气工具'] = False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['天气工具'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 2: RAG系统 - 文档处理和向量存储
    # ===================================================================
    print("\n【测试 2】RAG系统 - 文档处理 (Phase 1)")
    print("-" * 70)
    try:
        from src.tools import DocumentProcessor, VectorStore, SmartChunker

        # 文档处理
        processor = DocumentProcessor()
        test_doc = "test_data/sample_document.txt"

        if Path(test_doc).exists():
            docs = processor.process_file(test_doc)
            print(f"✅ 文档处理成功")
            print(f"   文件: {test_doc}")
            print(f"   页数: {len(docs)}")
            print(f"   内容长度: {len(docs[0]['content'])} 字符")

            # 智能分块
            chunker = SmartChunker(chunk_size=256, strategy="semantic")
            chunks = chunker.chunk_documents(docs)
            print(f"\n   智能分块:")
            print(f"   策略: semantic")
            print(f"   块数: {len(chunks)}")
            print(f"   第一块预览: {chunks[0]['content'][:100]}...")

            results['文档处理'] = True
        else:
            print(f"❌ 测试文档不存在: {test_doc}")
            results['文档处理'] = False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['文档处理'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 3: RAG系统 - 向量检索
    # ===================================================================
    print("\n【测试 3】RAG系统 - 向量检索 (Phase 1)")
    print("-" * 70)
    try:
        from src.tools import VectorStore
        import tempfile
        import shutil

        # 使用临时目录
        temp_dir = tempfile.mkdtemp()

        try:
            vector_store = VectorStore(
                persist_directory=temp_dir,
                collection_name="test_collection"
            )

            # 添加文档
            texts = [
                "Python is a high-level programming language",
                "Machine learning is a subset of AI",
                "Deep learning uses neural networks"
            ]
            ids = vector_store.add_documents(
                texts=texts,
                metadatas=[{"source": f"doc{i}"} for i in range(len(texts))],
                ids=[f"id{i}" for i in range(len(texts))]
            )

            print(f"✅ 向量存储成功")
            print(f"   添加文档数: {len(ids)}")

            # 相似度搜索
            results_data = vector_store.similarity_search("What is Python?", k=2)
            print(f"\n   相似度搜索:")
            print(f"   查询: 'What is Python?'")
            print(f"   结果数: {len(results_data)}")
            for i, r in enumerate(results_data, 1):
                print(f"   {i}. {r['document'][:60]}... (分数: {r['score']:.3f})")

            results['向量检索'] = True

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['向量检索'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 4: RAG Agent - 完整问答
    # ===================================================================
    print("\n【测试 4】RAG Agent - 文档问答 (Phase 1)")
    print("-" * 70)
    try:
        from src.agents import RAGAgent
        from src.llm import LLMManager
        from src.utils import get_config
        import tempfile
        import shutil

        config = get_config()
        llm = LLMManager(config=config)
        temp_dir = tempfile.mkdtemp()

        try:
            rag_agent = RAGAgent(llm, config=config, persist_directory=temp_dir)

            # 摄取文档
            test_doc = "test_data/sample_document.txt"
            if Path(test_doc).exists():
                print(f"   摄取文档: {test_doc}")
                await rag_agent.ingest_document(test_doc)

                # 查询
                print(f"\n   查询: 'What are the key features?'")
                result = await rag_agent.query("What are the key features?")

                print(f"\n✅ RAG问答成功")
                print(f"   来源数: {len(result.get('sources', []))}")
                print(f"   答案: {result.get('answer', 'N/A')[:200]}...")

                results['RAG问答'] = True
            else:
                print(f"❌ 测试文档不存在")
                results['RAG问答'] = False

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['RAG问答'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 5: OCR工具
    # ===================================================================
    print("\n【测试 5】OCR工具 - 图像文字提取 (Phase 4)")
    print("-" * 70)
    try:
        from src.tools import OCRTool

        ocr = OCRTool(languages=["ch", "en"], use_gpu=False)

        test_image = "test_data/test_image.png"
        if Path(test_image).exists():
            print(f"   处理图像: {test_image}")
            result = await ocr.extract_text(test_image)

            print(f"\n✅ OCR提取成功")
            print(f"   检测行数: {result['line_count']}")
            print(f"   提取文本:")
            print(f"   {result['text']}")

            # 测试中文OCR
            test_image_cn = "test_data/test_image_chinese.png"
            if Path(test_image_cn).exists():
                print(f"\n   处理中文图像: {test_image_cn}")
                result_cn = await ocr.extract_text(test_image_cn)
                print(f"   中文文本: {result_cn['text']}")

            results['OCR工具'] = True
        else:
            print(f"❌ 测试图像不存在: {test_image}")
            results['OCR工具'] = False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['OCR工具'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 6: Vision工具
    # ===================================================================
    print("\n【测试 6】Vision工具 - 图像理解 (Phase 4)")
    print("-" * 70)
    try:
        from src.tools import VisionTool
        from src.utils import get_config

        config = get_config()
        vision = VisionTool(
            api_key=config.multimodal.vision.api_key,
            model="gemini-2.0-flash-exp"
        )

        test_image = "test_data/test_image.png"
        if Path(test_image).exists():
            print(f"   分析图像: {test_image}")
            result = await vision.analyze_image(
                test_image,
                prompt="描述这张图片的内容"
            )

            print(f"\n✅ Vision分析成功")
            print(f"   分析结果:")
            print(f"   {result['analysis']}")

            results['Vision工具'] = True
        else:
            print(f"❌ 测试图像不存在")
            results['Vision工具'] = False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['Vision工具'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 7: 路线工具
    # ===================================================================
    print("\n【测试 7】路线工具 (Phase 3)")
    print("-" * 70)
    try:
        from src.tools import RoutingTool
        from src.utils import get_config

        config = get_config()
        routing = RoutingTool(api_key=config.domain_tools.routing.api_key)

        # 地理编码
        print(f"   地理编码: 'Shanghai'")
        locations = await routing.geocode("Shanghai", limit=1)

        if locations:
            shanghai = locations[0]
            print(f"   位置: {shanghai['name']}")
            print(f"   坐标: {shanghai['coordinates']}")

            # 获取北京坐标
            locations_bj = await routing.geocode("Beijing", limit=1)
            if locations_bj:
                beijing = locations_bj[0]
                print(f"\n   地理编码: 'Beijing'")
                print(f"   位置: {beijing['name']}")
                print(f"   坐标: {beijing['coordinates']}")

                # 计算路线
                print(f"\n   计算路线: Shanghai -> Beijing")
                route = await routing.get_route(
                    start=shanghai['coordinates'],
                    end=beijing['coordinates'],
                    profile="driving-car"
                )

                print(f"\n✅ 路线计算成功")
                print(f"   距离: {route['distance_km']:.1f} 公里")
                print(f"   时间: {route['duration_hours']:.1f} 小时")

                results['路线工具'] = True
            else:
                print(f"❌ 北京地理编码失败")
                results['路线工具'] = False
        else:
            print(f"❌ 上海地理编码失败")
            results['路线工具'] = False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['路线工具'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 8: 重排序系统
    # ===================================================================
    print("\n【测试 8】重排序系统 (Phase 2)")
    print("-" * 70)
    try:
        from src.tools import Reranker

        reranker = Reranker(model_name="BAAI/bge-reranker-large")

        query = "What is Python programming?"
        documents = [
            "Python is a high-level programming language",
            "Java is an object-oriented language",
            "Python was created by Guido van Rossum",
            "JavaScript runs in web browsers"
        ]

        print(f"   查询: '{query}'")
        print(f"   文档数: {len(documents)}")

        reranked = reranker.rerank(query, documents, top_k=3)

        print(f"\n✅ 重排序成功")
        print(f"   重排序结果 (Top 3):")
        for i, item in enumerate(reranked, 1):
            print(f"   {i}. {item['text'][:60]}... (分数: {item['score']:.3f})")

        results['重排序'] = True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['重排序'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 9: 可信度评分器
    # ===================================================================
    print("\n【测试 9】可信度评分器 (Phase 2)")
    print("-" * 70)
    try:
        from src.tools import CredibilityScorer
        from datetime import datetime

        scorer = CredibilityScorer()

        test_sources = [
            {
                "url": "https://arxiv.org/paper123",
                "content": "This peer-reviewed research paper discusses...",
                "title": "Machine Learning Research",
                "date": datetime(2024, 1, 1)
            },
            {
                "url": "https://example.com/blog",
                "content": "Sponsored content about product...",
                "title": "Product Review",
                "date": datetime(2020, 1, 1)
            }
        ]

        print(f"   评分来源数: {len(test_sources)}")

        for i, source in enumerate(test_sources, 1):
            score = scorer.score_source(
                url=source['url'],
                content=source['content'],
                title=source['title'],
                metadata={'date': source['date']}
            )
            print(f"   {i}. {source['url'][:40]}... → 分数: {score:.2f}")

        print(f"\n✅ 可信度评分成功")
        results['可信度评分'] = True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['可信度评分'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 10: Research Agent（修复后）
    # ===================================================================
    print("\n【测试 10】Research Agent")
    print("-" * 70)
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

        print(f"   查询: 'What is artificial intelligence?'")
        result = await agent.research("What is artificial intelligence?")

        print(f"\n✅ Research Agent成功")
        print(f"   来源数: {len(result.get('sources', []))}")
        print(f"   摘要长度: {len(result.get('summary', ''))} 字符")
        print(f"   摘要预览: {result.get('summary', 'N/A')[:150]}...")

        results['Research Agent'] = True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['Research Agent'] = False

    await asyncio.sleep(1)

    # ===================================================================
    # 测试 11: 结果聚合器
    # ===================================================================
    print("\n【测试 11】结果聚合器 (Phase 5)")
    print("-" * 70)
    try:
        from src.workflow import ResultAggregator
        from src.llm import LLMManager
        from src.utils import get_config

        config = get_config()
        llm = LLMManager(config=config)
        aggregator = ResultAggregator(llm_manager=llm)

        # 测试去重
        test_results = [
            {"source": "A", "content": "Python is a programming language"},
            {"source": "B", "content": "Python is a programming language"},  # 重复
            {"source": "C", "content": "Python was created in 1991"},
        ]

        print(f"   原始结果数: {len(test_results)}")
        deduplicated = aggregator.deduplicate(test_results)
        print(f"   去重后: {len(deduplicated)}")

        # 测试聚合
        aggregated = await aggregator.aggregate(
            deduplicated,
            query="What is Python?",
            strategy="synthesis"
        )

        print(f"\n✅ 结果聚合成功")
        print(f"   聚合策略: synthesis")
        print(f"   摘要长度: {len(aggregated.summary)} 字符")
        print(f"   关键点数: {len(aggregated.key_points)}")
        print(f"   置信度: {aggregated.confidence:.2f}")

        results['结果聚合'] = True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['结果聚合'] = False

    # ===================================================================
    # 汇总结果
    # ===================================================================
    print("\n\n" + "=" * 70)
    print("全面测试结果汇总")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")

    print(f"\n详细结果:")
    print("-" * 70)

    # 按阶段分组
    phase_groups = {
        "Phase 1 - RAG系统": ["文档处理", "向量检索", "RAG问答"],
        "Phase 2 - 重排序": ["重排序", "可信度评分"],
        "Phase 3 - 领域工具": ["天气工具", "路线工具"],
        "Phase 4 - 多模态": ["OCR工具", "Vision工具"],
        "Phase 5 - 工作流": ["结果聚合"],
        "核心代理": ["Research Agent"],
    }

    for phase, items in phase_groups.items():
        print(f"\n{phase}:")
        for item in items:
            if item in results:
                status = "✅" if results[item] else "❌"
                print(f"  {status} {item}")

    print("\n" + "=" * 70)

    if passed == total:
        print("🎉 恭喜！所有测试通过！")
    elif passed >= total * 0.8:
        print("✅ 大部分功能正常工作！")
    elif passed >= total * 0.6:
        print("✅ 核心功能可用")
    else:
        print("⚠️  部分功能需要检查")

    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    asyncio.run(test_all_features())
