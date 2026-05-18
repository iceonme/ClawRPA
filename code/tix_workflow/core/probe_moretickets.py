import asyncio
import os
from playwright.async_api import async_playwright

async def probe_structure_async():
    async with async_playwright() as p:
        # 连接到现有的浏览器
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = await context.new_page()
            
            url = "https://m.motianlun.cn/content/list?keyword=五月天"
            print(f"[Probe] 正在访问: {url}")
            
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(5) # 给点渲染时间
            
            # 获取 HTML
            content = await page.content()
            # 确保目录存在
            os.makedirs("workspace/01_data", exist_ok=True)
            with open("workspace/01_data/moretickets_probe.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 检查是否有结果容器
            items = await page.query_selector_all("*")
            print(f"[Probe] 总元素数量: {len(items)}")
            
            # 搜索包含 "五月天" 的文本块
            mayday_elements = await page.get_by_text("五月天").all()
            print(f"[Probe] 包含 '五月天' 文本的元素数量: {len(mayday_elements)}")
            
            await browser.close()
            print("[Probe] 探测完成，请分析 workspace/01_data/moretickets_probe.html")
            
        except Exception as e:
            print(f"[Probe] 发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(probe_structure_async())
