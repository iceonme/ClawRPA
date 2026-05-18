import asyncio
import os
from playwright.async_api import async_playwright

async def probe_piaoniu_native_stealth():
    async with async_playwright() as p:
        try:
            # 开启 CDP 连接
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = await context.new_page()
            
            # 原生隐身：修改 webdriver 属性
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            url = "https://m.piaoniu.com/search/list?keyword=五月天"
            print(f"[Probe-Native] 正在以原生伪装模式访问: {url}")
            
            # 设置较长的超时和等待
            await page.goto(url, wait_until="load")
            await asyncio.sleep(8) 
            
            # 检查内容
            content = await page.content()
            elements = await page.query_selector_all("*")
            print(f"[Probe-Native] 扫描到 {len(elements)} 个元素")
            
            if len(elements) < 20:
                print("[Probe-Native] 警告：页面元素极少，可能触发了拦截。")
            
            # 尝试搜索结果
            results = await page.query_selector_all("a")
            for res in results:
                text = await res.inner_text()
                if "五月天" in text:
                    href = await res.get_attribute("href")
                    print(f"  - 找到: {text.strip()} | {href}")

            await page.close()
            
        except Exception as e:
            print(f"[Probe-Native] 运行错误: {e}")

if __name__ == "__main__":
    asyncio.run(probe_piaoniu_native_stealth())
