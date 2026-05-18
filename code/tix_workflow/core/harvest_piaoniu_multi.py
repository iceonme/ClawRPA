import asyncio
import os
import json
import time
from playwright.async_api import async_playwright

async def harvest_piaoniu_multi_sessions():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            pages = context.pages
            
            target_page = None
            for page in pages:
                if "piaoniu.com/seat" in page.url:
                    target_page = page
                    break
            
            if not target_page:
                print("[Piaoniu-Multi] 错误：未找到选座页。")
                return

            print(f"[Piaoniu-Multi] 正在启动全场次收割: {await target_page.title()}")
            
            total_inventory = []

            # 1. 寻找所有的场次按钮 (Session Buttons)
            # 票牛的场次通常在 .count-o-box 里的 .count 元素
            session_buttons = await target_page.query_selector_all(".count-o-box .count, .calendar-item")
            print(f"[Piaoniu-Multi] 探测到 {len(session_buttons)} 个可选场次。")

            for i in range(len(session_buttons)):
                # 重新获取按钮，防止页面刷新导致元素失效
                buttons = await target_page.query_selector_all(".count-o-box .count, .calendar-item")
                btn = buttons[i]
                
                session_name = await btn.inner_text()
                print(f"\n[Piaoniu-Multi] 正在切换至场次: {session_name.strip()}")
                
                # 点击切换场次
                await btn.click()
                # 关键：等待价格列表刷新 (异步加载)
                await asyncio.sleep(2) 
                
                # 2. 提取当前场次的价格
                list_rows = await target_page.query_selector_all(".ticket")
                session_count = 0
                for row in list_rows:
                    try:
                        name_el = await row.query_selector(".ticket-name")
                        price_el = await row.query_selector(".price-display, .num, .price")
                        
                        if name_el and price_el:
                            final_name = await name_el.inner_text()
                            final_price = await price_el.inner_text()
                            
                            total_inventory.append({
                                "session": session_name.strip(),
                                "tier": final_name.strip(),
                                "price": final_price.replace("¥", "").replace("/张", "").strip()
                            })
                            session_count += 1
                    except:
                        continue
                print(f"[Piaoniu-Multi] 场次 {session_name.strip()} 抓取完成，共 {session_count} 条。")

            # 保存最终的全量矩阵
            output_path = "c:/tix_work_bench/Event_北京五月天_20260508/inventory/piaoniu_full_inventory.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(total_inventory, f, ensure_ascii=False, indent=4)
            
            print(f"\n[Piaoniu-Multi] 🎉 全流程收割成功！数据已保存至: {output_path}")

        except Exception as e:
            print(f"[Piaoniu-Multi] 运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(harvest_piaoniu_multi_sessions())
