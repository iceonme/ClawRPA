import os
import time
import json
import sys
import re

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def harvest_moretickets_full():
    print("[Harvest] Deep Scanning ALL open tabs for content...")
    
    with BrowserSession(port=9222) as session:
        real_target_page = None
        
        for page in session.context.pages:
            url = page.url
            title = page.title()
            print(f" - Checking: {title} ({url})")
            
            # 探测：该页面是否包含核心档位控件？
            try:
                if "motianlun.cn" in url:
                    # 检查药丸是否存在
                    count = page.locator(".seatplan-item").count()
                    if count > 0:
                        print(f" >>> SUCCESS! Found {count} tiers on this page.")
                        real_target_page = page
                        break
            except:
                continue
        
        if not real_target_page:
            print("[Error] No ACTIVE MoreTickets page with ticket data found!")
            print("Please ensure the price list page (Figure 2) is visible in your browser.")
            return

        print(f"\n[Harvest] Working on: {real_target_page.title()}")
        real_target_page.bring_to_front()
        
        all_data = []
        pills = real_target_page.locator(".seatplan-item").all()
        
        for i, pill in enumerate(pills):
            cls = pill.get_attribute("class") or ""
            if "disabled" in cls: continue
            
            try:
                tier_name = pill.inner_text().split("\n")[0]
                print(f"[Tier {i+1}] Scraping: {tier_name}")
                
                pill.click(force=True)
                time.sleep(2) # 摩天轮加载票品稍慢
                
                # 使用用户确认的 .ticket-item 选择器
                ticket_items = real_target_page.locator(".ticket-item").all()
                print(f" >> Found {len(ticket_items)} tickets.")
                
                tier_tickets = []
                for item in ticket_items:
                    raw_text = item.inner_text().strip().replace("\n", " | ")
                    price_match = re.search(r"¥(\d+)", raw_text)
                    price = price_match.group(1) if price_match else "N/A"
                    
                    tier_tickets.append({
                        "info": raw_text,
                        "price": price
                    })
                
                all_data.append({
                    "tier": tier_name,
                    "count": len(tier_tickets),
                    "tickets": tier_tickets
                })
            except Exception as e:
                print(f" >> Error: {e}")
                continue
            
        # 保存结果
        output_path = "c:/Projects/CloudPhone/workspace/01_data/mtl_mayday_full.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n[Harvest] FULL SUCCESS! Captured {len(all_data)} tiers.")
        print(f"[Harvest] Data: {output_path}")

if __name__ == "__main__":
    harvest_moretickets_full()
