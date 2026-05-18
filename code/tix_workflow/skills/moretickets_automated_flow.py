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

def full_automated_harvest():
    print("[Flow] Initializing Full Automated Harvest for MoreTickets...")
    
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        page.set_viewport_size({"width": 375, "height": 812})
        
        # 1. 搜索并进入详情页
        print("[Flow] Searching for Mayday Beijing...")
        search_url = "https://m.motianlun.cn/content/list?keyword=%E4%BA%94%E6%9C%88%E5%A4%A9%E5%8C%97%E4%BA%AC"
        page.goto(search_url, wait_until="networkidle")
        
        try:
            page.wait_for_selector(".recommend-show-item", timeout=10000)
            page.click(".recommend-show-item")
            print("[Flow] Entered Detail Page.")
        except:
            print("[Error] Search result not found!")
            return

        # 2. 唤起场次选择面板
        time.sleep(2)
        print("[Flow] Opening Session Panel...")
        try:
            # 点击底部的立即购买
            page.click(".show-detail-button.one-button")
            page.wait_for_selector(".session-card", timeout=5000)
        except:
            print("[Error] Could not open session panel!")
            return

        # 3. 选择第一场并确认，进入价格页
        print("[Flow] Confirming first session...")
        page.locator(".session-card").first.click()
        time.sleep(0.5)
        # 强制点击确定按钮
        page.locator("uni-button.mtl-button").filter(has_text="确定").click(force=True)
        
        # 4. 等待价格页（药丸）加载
        print("[Flow] Waiting for Price Page (Pills)...")
        try:
            page.wait_for_selector(".seatplan-item", timeout=10000)
        except:
            print("[Error] Price page didn't load in time.")
            return

        # 5. 开始遍历收割
        print("[Flow] Target Reached! Starting extraction...")
        all_data = []
        pills = page.locator(".seatplan-item").all()
        
        for i, pill in enumerate(pills):
            cls = pill.get_attribute("class") or ""
            if "disabled" in cls: continue
            
            try:
                tier_name = pill.locator(".seatplan-display").inner_text()
                print(f" >> Extracing Tier: {tier_name}")
                
                pill.click(force=True)
                time.sleep(2)
                
                ticket_items = page.locator(".ticket-item").all()
                tier_tickets = []
                for item in ticket_items:
                    raw_text = item.inner_text().strip().replace("\n", " | ")
                    price_match = re.search(r"¥(\d+)", raw_text)
                    price = price_match.group(1) if price_match else "N/A"
                    tier_tickets.append({"info": raw_text, "price": price})
                
                all_data.append({"tier": tier_name, "tickets": tier_tickets})
            except:
                continue

        # 6. 存档
        output_path = "c:/Projects/CloudPhone/workspace/01_data/mtl_mayday_full.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n[Flow] MISSION ACCOMPLISHED! Data saved to: {output_path}")

if __name__ == "__main__":
    full_automated_harvest()
