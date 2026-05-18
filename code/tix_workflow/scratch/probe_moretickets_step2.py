import os
import time
import sys

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def probe_motianlun_prices():
    print("[Probe] Stepping into MoreTickets Price Selection (Retry)...")
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        page.set_viewport_size({"width": 375, "height": 812})
        
        # 1. 跳转详情页
        # 注意：这里直接进入五月天北京站的真实详情页
        page.goto("https://m.motianlun.cn/content/show/detail?showId=278144", wait_until="networkidle")
        time.sleep(3)
        
        # 2. 唤起场次面板
        print("[Probe] Opening session panel...")
        page.click(".show-detail-button.one-button")
        page.wait_for_selector(".session-card", timeout=5000)
        
        # 3. 点击第一个场次并确定
        print("[Probe] Selecting first session...")
        # 显式点击第一个可见的 session-card
        page.locator(".session-card").first.click()
        time.sleep(1)
        
        print("[Probe] Clicking Confirm button (uni-button)...")
        # 直接点击 uni-button，并使用 force=True 规避拦截
        try:
            # 尝试通过类名和文字结合定位
            confirm_btn = page.locator("uni-button.mtl-button").filter(has_text="确定")
            confirm_btn.click(force=True)
        except:
            # 备选方案：直接点底部的那个大红按钮
            page.click(".button-container uni-button", force=True)
            
        time.sleep(5) # 等待价格面板加载
        
        # 4. 抓取价格面板
        ts = int(time.time())
        screenshot_path = f"c:/Projects/CloudPhone/workspace/01_data/debug/mtl_price_panel_{ts}.png"
        dom_path = f"c:/Projects/CloudPhone/workspace/01_data/debug/mtl_price_panel_{ts}.html"
        
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        page.screenshot(path=screenshot_path)
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print(f"[Probe] Price Panel Captured! Screenshot: {screenshot_path}")
        
        # 5. 分析价格档位
        items = page.locator("uni-view[class*='item'], .sku-item, .ticket-item").count()
        print(f"[Probe] Found {items} potential items on current screen")

if __name__ == "__main__":
    probe_motianlun_prices()
