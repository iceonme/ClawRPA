import asyncio
import os
import sys
import requests
from playwright.async_api import async_playwright

async def scrape_mobile_images(item_id, target_dir):
    async with async_playwright() as p:
        device = p.devices['iPhone 12']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**device)
        page = await context.new_page()
        
        url = f"https://m.damai.cn/damai/detail/item.html?itemId={item_id}"
        print(f"[ImageScrape] 正在访问: {url}")
        await page.goto(url, wait_until="load")
        
        # 模拟滚动以触发所有图片加载
        print("[ImageScrape] 正在模拟滚动触发懒加载...")
        for i in range(10):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(1)
            
        # 获取所有图片链接 (在大麦 H5 详情中)
        content_el = await page.query_selector(".project-detail-content") or await page.query_selector(".detail-content")
        img_urls = []
        if content_el:
            imgs = await content_el.query_selector_all("img")
            for img in imgs:
                src = await img.get_attribute("data-src") or await img.get_attribute("src")
                if src:
                    if src.startswith("//"): src = "https:" + src
                    if src.startswith("http") and ".jpg" in src.lower():
                        img_urls.append(src)
        
        # 去重并下载
        img_urls = list(set(img_urls))
        print(f"[ImageScrape] 发现有效图片: {len(img_urls)} 张")
        
        downloaded = 0
        for i, url in enumerate(img_urls):
            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    ext = ".jpg" if ".jpg" in url.lower() else ".png"
                    filename = f"detail_{downloaded}{ext}"
                    with open(os.path.join(target_dir, filename), "wb") as f:
                        f.write(res.content)
                    downloaded += 1
            except:
                continue
        
        print(f"[ImageScrape] 成功下载新物料: {downloaded} 张")
        await browser.close()

if __name__ == "__main__":
    target = "c:\\tix_work_bench\\Event_北京五月天_20260508\\info"
    asyncio.run(scrape_mobile_images("1034211764114", target))
