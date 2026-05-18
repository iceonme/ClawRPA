import asyncio
import os
import json
from playwright.async_api import async_playwright

async def harvest_piaoniu_structured():
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
                print("[Piaoniu-Struct] 未找到选座页面。")
                return

            # 抓取成对的数据
            final_matrix = []
            
            # 1. 尝试抓取顶部的档位横向列表 (SKU Tab)
            sku_tabs = await target_page.query_selector_all(".sku-item, .spec-item")
            for tab in sku_tabs:
                text = await tab.inner_text()
                # 文本通常包含：355看台 \n ¥1223起
                parts = text.split('\n')
                if len(parts) >= 2:
                    final_matrix.append({
                        "tier": parts[0].strip(),
                        "price": parts[1].replace("¥", "").replace("起", "").strip(),
                        "type": "summary"
                    })
            
            # 2. 尝试抓取下方的详细票源列表 (List Items)
            list_items = await target_page.query_selector_all(".ticket-item, .list-item")
            for item in list_items:
                try:
                    title_el = await item.query_selector(".title, .name")
                    price_el = await item.query_selector(".price, .num, .price-display")
                    if title_el and price_el:
                        final_matrix.append({
                            "tier": await title_el.inner_text(),
                            "price": (await price_el.inner_text()).replace("¥", "").replace("/张", "").strip(),
                            "type": "detail"
                        })
                except:
                    continue
            
            # 保存
            output_path = "c:/tix_work_bench/Event_北京五月天_20260508/inventory/piaoniu_matrix_20260506.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_matrix, f, ensure_ascii=False, indent=4)
            
            print(f"[Piaoniu-Struct] 结构化数据已保存: {len(final_matrix)} 条")
            
        except Exception as e:
            print(f"[Piaoniu-Struct] 错误: {e}")

if __name__ == "__main__":
    asyncio.run(harvest_piaoniu_structured())
