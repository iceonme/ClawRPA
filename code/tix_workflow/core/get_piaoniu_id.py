import asyncio
import os
import re
import sys
from playwright.async_api import async_playwright

async def get_piaoniu_id_human_like(keyword: str):
    """
    拟人化探测：首页 -> 搜索 -> 输入 -> ID提取
    """
    page = None
    try:
        async with async_playwright() as p:
            print(f"[Piaoniu-Human] 正在以真人模式搜索: {keyword}...")
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            except:
                print("[Piaoniu-Human] 连接失败，请确保 prep_browser.py 已启动。")
                return None
                
            context = browser.contexts[0]
            page = await context.new_page()
            
            # 1. 访问首页
            print("[Piaoniu-Human] 1. 访问首页...")
            await page.goto("https://m.piaoniu.com/", wait_until="load")
            await asyncio.sleep(2)
            
            # 2. 点击搜索入口
            print("[Piaoniu-Human] 2. 激活搜索框...")
            search_trigger = await page.query_selector(".search-input, .search-box, .search-text")
            if search_trigger:
                await search_trigger.click()
            else:
                # 如果没找到，尝试访问搜索页（退而求其次）
                await page.goto("https://m.piaoniu.com/search")
            
            await asyncio.sleep(1)
            
            # 3. 输入关键词 (模拟键盘输入)
            print(f"[Piaoniu-Human] 3. 输入关键词: {keyword}")
            input_box = await page.query_selector("input[type='search'], .search-input input")
            if input_box:
                await input_box.type(keyword, delay=100)
                await asyncio.sleep(1)
                # 敲击回车
                await page.keyboard.press("Enter")
            else:
                print("[Piaoniu-Human] 未找到输入框！")
                return None
            
            # 4. 等待结果并提取
            print("[Piaoniu-Human] 4. 等待结果加载...")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            links = await page.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href") or ""
                text = await link.inner_text()
                match = re.search(r"/activity/(\d+)", href)
                if match:
                    p_id = match.group(1)
                    print(f"[Piaoniu-Human] 成功！项目: {text.strip()[:20]} | ID: {p_id}")
                    return p_id
            
            print("[Piaoniu-Human] 未发现结果。")
            return None
            
    except Exception as e:
        print(f"[Piaoniu-Human] 运行出错: {e}")
    finally:
        if page:
            await page.close()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "周杰伦"
    asyncio.run(get_piaoniu_id_human_like(kw))
