import asyncio
import os
import json
from playwright.async_api import async_playwright

async def harvest_piaoniu_final_structured():
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
                print("[Piaoniu-Final] 错误：未找到票牛选座页。")
                return

            print(f"[Piaoniu-Final] 正在解析: {await target_page.title()}")
            
            matrix = []
            
            # 1. 解析上方的档位统计 (Summary)
            sku_items = await target_page.query_selector_all(".ticket-item")
            for item in sku_items:
                text = await item.inner_text()
                # 典型文本: "355看台\n¥1223起"
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if len(lines) >= 2:
                    matrix.append({
                        "tier": lines[0],
                        "price": lines[1].replace("¥", "").replace("起", "").strip(),
                        "type": "tier_summary"
                    })

            # 2. 解析下方的详细票源 (Details)
            list_rows = await target_page.query_selector_all(".ticket")
            for row in list_rows:
                try:
                    name_el = await row.query_selector(".ticket-name")
                    # 票牛的价格可能在不同的子类里，我们用更通用的启发式
                    price_els = await row.query_selector_all(".price-display, .num, .price, .ticket-price")
                    
                    if name_el and price_els:
                        name = await name_el.inner_text()
                        price = await price_els[0].inner_text()
                        matrix.append({
                            "tier": name.strip(),
                            "price": price.replace("¥", "").replace("/张", "").strip(),
                            "type": "ticket_detail"
                        })
                except:
                    continue

            # 保存结果
            output_dir = "c:/tix_work_bench/Event_北京五月天_20260508/inventory"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "piaoniu_matrix_final_20260506.json")
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(matrix, f, ensure_ascii=False, indent=4)
            
            print(f"[Piaoniu-Final] 抓取完成！共获得 {len(matrix)} 条结构化数据。")
            print(f"[Piaoniu-Final] 文件已存至: {output_path}")

        except Exception as e:
            print(f"[Piaoniu-Final] 发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(harvest_piaoniu_final_structured())
