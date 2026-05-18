import asyncio
import os
import json
import re
from playwright.async_api import async_playwright

async def harvest_piaoniu_precision():
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
                print("[Piaoniu-Precision] 错误：未找到选座页。")
                return

            # 1. 提取场次日期 (Session)
            # 查找包含日期的元素，通常在顶部的日期下拉框或展示文本中
            session_text = ""
            date_el = await target_page.query_selector(".date-text, .time-text, .calendar-wrap, .top-bar-info")
            if date_el:
                raw_session = await date_el.inner_text()
                # 提取日期格式 YYYY.MM.DD
                match = re.search(r"(\d{4}[./-]\d{1,2}[./-]\d{1,2})", raw_session)
                session_text = match.group(1) if match else raw_session.strip().split('\n')[0]
            
            print(f"[Piaoniu-Precision] 当前场次: {session_text}")

            # 2. 提取价格矩阵
            final_data = []
            list_rows = await target_page.query_selector_all(".ticket")
            
            for row in list_rows:
                try:
                    name_el = await row.query_selector(".ticket-name")
                    price_el = await row.query_selector(".price-display, .num, .price")
                    
                    if name_el and price_el:
                        name_text = await name_el.inner_text()
                        price_text = await price_el.inner_text()
                        
                        # 结构化
                        # 尝试从 name 中抠出票面档位数字
                        tier_match = re.search(r"(\d{3,4})", name_text)
                        original_price = tier_match.group(1) if tier_match else "未知"
                        
                        final_data.append({
                            "session": session_text,
                            "tier_name": name_text.strip(),
                            "original_price": original_price,
                            "sale_price": price_text.replace("¥", "").replace("/张", "").strip(),
                            "platform": "piaoniu"
                        })
                except:
                    continue

            # 保存
            output_path = "c:/tix_work_bench/Event_北京五月天_20260508/inventory/piaoniu_precision_20260506.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            
            print(f"[Piaoniu-Precision] 成功抓取 {len(final_data)} 条高精度数据。")
            
        except Exception as e:
            print(f"[Piaoniu-Precision] 运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(harvest_piaoniu_precision())
