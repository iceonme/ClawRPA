import asyncio
import os
import json
from playwright.async_api import async_playwright

async def harvest_piaoniu_final():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            pages = browser.contexts[0].pages
            
            target_page = None
            for page in pages:
                if "piaoniu.com/seat" in page.url:
                    target_page = page
                    break
            
            if not target_page:
                print("[Piaoniu-Final] 未找到选座页面，请确保票牛选座页已打开。")
                return

            print(f"[Piaoniu-Final] 正在提取数据: {await target_page.title()}")
            
            # 提取所有的价格和描述
            # 票牛选座页通常有 .sku-item 或者带有价格数字的 div
            data = []
            elements = await target_page.query_selector_all(".sku-item, .item-price, .num, .price")
            
            for el in elements:
                text = await el.inner_text()
                if any(char.isdigit() for char in text):
                    data.append(text.strip())
            
            # 保存到项目目录
            output_dir = "c:/tix_work_bench/Event_北京五月天_20260508/inventory"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "piaoniu_harvest_20260506.json")
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({"raw_data": data, "url": target_page.url}, f, ensure_ascii=False, indent=4)
            
            print(f"[Piaoniu-Final] 数据已保存至: {output_path}")
            
        except Exception as e:
            print(f"[Piaoniu-Final] 错误: {e}")

if __name__ == "__main__":
    asyncio.run(harvest_piaoniu_final())
