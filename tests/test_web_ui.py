"""
Web UI功能测试
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp


async def test_endpoints():
    """测试Web UI的各个端点"""

    base_url = "http://localhost:8000"

    print("\n" + "=" * 70)
    print("Web UI 功能测试")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:

        # 测试1: 健康检查
        print("\n【测试 1/5】健康检查")
        print("-" * 70)
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查通过: {data}")
                else:
                    print(f"❌ 健康检查失败: {response.status}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试2: 主页加载
        print("\n【测试 2/5】主页加载")
        print("-" * 70)
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    html = await response.text()
                    if "AI Search Engine" in html and "base_new.html" in html or "sidebar" in html:
                        print(f"✅ 主页加载成功")
                        print(f"   HTML长度: {len(html)} 字符")
                    else:
                        print(f"⚠️  主页加载但内容可能不正确")
                else:
                    print(f"❌ 主页加载失败: {response.status}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试3: CSS加载
        print("\n【测试 3/5】CSS样式表加载")
        print("-" * 70)
        try:
            async with session.get(f"{base_url}/static/css/new-style.css") as response:
                if response.status == 200:
                    css = await response.text()
                    print(f"✅ CSS加载成功")
                    print(f"   CSS长度: {len(css)} 字符")
                else:
                    print(f"❌ CSS加载失败: {response.status}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试4: JavaScript加载
        print("\n【测试 4/5】JavaScript加载")
        print("-" * 70)
        try:
            async with session.get(f"{base_url}/static/js/main.js") as response:
                if response.status == 200:
                    js = await response.text()
                    print(f"✅ JavaScript加载成功")
                    print(f"   JS长度: {len(js)} 字符")
                else:
                    print(f"❌ JavaScript加载失败: {response.status}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        # 测试5: 查询分类（不执行完整查询，只测试分类）
        print("\n【测试 5/5】查询分类测试")
        print("-" * 70)
        test_queries = [
            ("What is machine learning?", "RESEARCH"),
            ("Calculate 25% of 480", "CODE"),
            ("Tell me a joke", "CHAT"),
        ]

        for query, expected_type in test_queries:
            try:
                async with session.post(
                        f"{base_url}/classify",
                        data={"query": query}
                ) as response:
                    if response.status == 200:
                        result = await response.text()
                        if expected_type.lower() in result.lower():
                            print(f"✅ '{query}' → {expected_type}")
                        else:
                            print(f"⚠️  '{query}' → 分类可能不正确")
                            print(f"   响应: {result[:100]}...")
                    else:
                        print(f"❌ 分类请求失败: {response.status}")
            except Exception as e:
                print(f"❌ 错误: {e}")

    # 汇总
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    print("\n✅ 如果所有测试都通过，说明Web UI基本功能正常工作！")
    print("\n🌐 访问 http://localhost:8000 查看完整界面")
    print("\n📝 建议手动测试:")
    print("   1. 打开浏览器访问 http://localhost:8000")
    print("   2. 测试搜索框输入不同类型的查询")
    print("   3. 测试主题切换（亮色/暗色）")
    print("   4. 测试响应式设计（调整浏览器窗口大小）")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
