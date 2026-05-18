import asyncio
import os
from playwright.async_api import async_playwright

async def stealth_harvest():
    async with async_playwright() as p:
        try:
            # 连接现有浏览器
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            pages = browser.contexts[0].pages
            
            print(f"[Stealth-Harvest] 发现 {len(pages)} 个开启的页面。")
            
            for page in pages:
                url = page.url
                title = await page.title()
                print(f"[Stealth-Harvest] 正在扫描页面: {title} | {url}")
                
                # 识别票牛、有票或摩天轮
                platform = None
                if "piaoniu.com" in url: platform = "Piaoniu"
                elif "ypiao.com" in url: platform = "Ypiao"
                elif "motianlun.cn" in url: platform = "Moretickets"
                
                if platform:
                    print(f"[Stealth-Harvest] 锁定 {platform} 目标页，正在提取价格...")
                    # 通用嗅探逻辑：寻找价格类元素
                    content = await page.content()
                    
                    # 保存快照供人类确认
                    os.makedirs("workspace/01_data", exist_ok=True)
                    snapshot_path = f"workspace/01_data/{platform.lower()}_active_snapshot.html"
                    with open(snapshot_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    # 尝试寻找数字 + ￥
                    elements = await page.query_selector_all(".price, .num, .item-price, .price-display, .sku-item")
                    print(f"[Stealth-Harvest] 在 {platform} 发现 {len(elements)} 个疑似价格元素。")
                    
                    for el in elements:
                        text = await el.inner_text()
                        if any(char.isdigit() for char in text):
                            print(f"  - [Found] {text.strip()}")
            
        except Exception as e:
            print(f"[Stealth-Harvest] 错误: {e}")

if __name__ == "__main__":
    asyncio.run(stealth_harvest())
