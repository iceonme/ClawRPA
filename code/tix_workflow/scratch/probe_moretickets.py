import os
import time
import sys
import re

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession
from playwright.sync_api import sync_playwright

def probe_motianlun():
    print("[Probe] Starting MoreTickets (motianlun.cn) Deep Probe...")
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        page.set_viewport_size({"width": 375, "height": 812}) # 模拟 iPhone X
        
        # 1. 直接跳转五月天详情页 (从之前的搜索结果中提取)
        # 也可以继续走搜索流程
        search_url = "https://m.motianlun.cn/content/list?keyword=%E5%8C%97%E4%BA%AC%E4%BA%94%E6%9C%88%E5%A4%A9"
        print(f"[Probe] Navigating to: {search_url}")
        page.goto(search_url, wait_until="load")
        time.sleep(5)
        
        # 2. 点击进入第一个结果
        print("[Probe] Clicking first result...")
        try:
            page.click(".recommend-show-item")
            time.sleep(5)
        except:
            print("[Probe] Failed to click .recommend-show-item, trying alternate...")
            page.click("uni-view[class*='recommend-show-item']")
            time.sleep(5)
            
        # 3. 点击“立即购买” (Uni-App 特有类名)
        print("[Probe] Clicking '立即购买' button...")
        try:
            # 根据 DOM 源码定位
            buy_btn = page.locator(".show-detail-button.one-button").first
            if buy_btn.count() > 0:
                print("[Probe] Found button via .show-detail-button")
                buy_btn.click()
            else:
                print("[Probe] Attempting text-based click...")
                page.click("text='立即购买'")
            time.sleep(5)
        except Exception as e:
            print(f"[Probe] Failed to click buy button: {e}")
            
        # 4. 截图并保存面板弹出后的 DOM
        ts = int(time.time())
        screenshot_path = f"c:/Projects/CloudPhone/workspace/01_data/debug/mtl_sku_panel_{ts}.png"
        dom_path = f"c:/Projects/CloudPhone/workspace/01_data/debug/mtl_sku_panel_{ts}.html"
        
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        page.screenshot(path=screenshot_path)
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print(f"[Probe] Captured! Screenshot: {screenshot_path}")
        print(f"[Probe] Captured! DOM: {dom_path}")
        
        # 5. 分析面板内容
        potential_sessions = page.locator("uni-view[class*='session-item'], uni-view[class*='sku-item']").count()
        print(f"[Probe] Found {potential_sessions} potential session/tier items")

if __name__ == "__main__":
    probe_motianlun()
