import os
import time
import json
import sys
import re

# 强制设置输出编码为 UTF-8，防止 Windows 终端报错
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def full_date_harvest():
    print("[Harvest] Starting Multi-Date Polling for MoreTickets...")
    
    with BrowserSession(port=9222) as session:
        page = None
        for p in session.context.pages:
            if "seat-and-seatplan" in p.url:
                page = p
                break
        
        if not page:
            print("[Error] No price page found!")
            return

        all_dates_data = []

        # 1. 获取所有日期场次
        print("[Flow] Opening Session Selector...")
        # 确保面板是关闭状态再点
        if not page.locator(".session-selecter").is_visible():
            page.click(".header-session-count")
            page.wait_for_selector(".session-card")
        
        session_count = page.locator(".session-card").count()
        print(f"[Flow] Found {session_count} total sessions.")
        
        for s_idx in range(session_count):
            if s_idx > 0:
                page.click(".header-session-count")
                page.wait_for_selector(".session-card")
            
            target_session = page.locator(".session-card").nth(s_idx)
            # 处理可能的渲染延迟
            time.sleep(0.5)
            session_text = target_session.inner_text().strip().replace("\n", " ")
            print(f"\n>>> [Session {s_idx+1}/{session_count}] Switching to: {session_text}")
            
            target_session.click()
            time.sleep(0.5)
            page.locator("uni-button.mtl-button").filter(has_text="确定").click(force=True)
            
            # 等待新场次加载（通过判断药丸容器的 visibility 或等待一段时间）
            time.sleep(2.5) 
            
            # 2. 档位循环
            pills = page.locator(".seatplan-item").all()
            print(f"    - Found {len(pills)} price tiers.")
            
            session_data = {"session": session_text, "tiers": []}
            
            for p_idx, pill in enumerate(pills):
                cls = pill.get_attribute("class") or ""
                if "disabled" in cls: continue
                
                try:
                    tier_name = pill.locator(".seatplan-display").inner_text()
                    print(f"      - Scraping Tier: {tier_name}")
                    
                    pill.click(force=True)
                    time.sleep(1.5)
                    
                    ticket_items = page.locator(".ticket-item").all()
                    tier_tickets = []
                    for item in ticket_items:
                        raw_text = item.inner_text().strip().replace("\n", " | ")
                        price_match = re.search(r"¥(\d+)", raw_text)
                        price = price_match.group(1) if price_match else "N/A"
                        tier_tickets.append({"info": raw_text, "price": price})
                    
                    session_data["tiers"].append({
                        "tier": tier_name,
                        "tickets": tier_tickets
                    })
                except:
                    continue
            
            all_dates_data.append(session_data)
            
        # 3. 最终保存
        output_path = "c:/Projects/CloudPhone/workspace/01_data/mtl_mayday_ALL_DATES.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_dates_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n[Harvest] MISSION COMPLETE! Full data for {len(all_dates_data)} sessions saved.")

if __name__ == "__main__":
    full_date_harvest()
