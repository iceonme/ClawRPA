import sys
import os
import time
import json
from typing import List, Dict, Any

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def piaoniu_full_harvest_v6_2(keyword: str):
    """
    全流程 v6.2：遵从用户指示，直接使用 JS onclick 触发
    """
    print(f"[Piaoniu-V6.2] JS 强制点击收割启动: {keyword}")
    all_prices = []
    
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        debug_dir = "workspace/01_data/debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        try:
            # 1. 首页加载
            print("[Piaoniu-V6.2] 1. 进入首页...")
            page.goto("https://m.piaoniu.com/", wait_until="load")
            time.sleep(3)
            
            # 2. JS 强制唤起搜索框
            print("[Piaoniu-V6.2] 2. 正在通过 JS 触发搜索入口...")
            # 我们直接把常用的搜索框选择器都扫一遍，执行点击
            selectors = [".search-input", ".search-box", ".search-bar", ".search-text", "[placeholder*='搜索']"]
            success = False
            for selector in selectors:
                try:
                    # 使用 evaluate 直接执行原生 JS 点击
                    res = page.evaluate(f"() => {{ let el = document.querySelector('{selector}'); if(el) {{ el.click(); return true; }} return false; }}")
                    if res:
                        print(f"[Piaoniu-V6.2] 已通过 JS 触发控件: {selector}")
                        success = True
                        break
                except: continue
            
            if not success:
                print("[Piaoniu-V6.2] 警告：所有 JS 选择器均未命中。")
            
            time.sleep(1.5)
            
            # 3. 录入关键词
            input_box = page.query_selector("input[type='search'], input")
            if input_box:
                print(f"[Piaoniu-V6.2] 3. 正在录入: {keyword}")
                input_box.type(keyword, delay=100)
                page.keyboard.press("Enter")
            else:
                print("[Piaoniu-V6.2] 找不到输入框，尝试手动补救...")
                page.goto(f"https://m.piaoniu.com/search") # 如果还没唤起，最后挣扎一下
            
            # 4. 筛选项目
            time.sleep(4)
            items = page.query_selector_all("a")
            target_link = None
            for item in items:
                href = item.get_attribute("href") or ""
                text = item.inner_text()
                if "/activity/" in href and ("广州" in text or "周传雄" in text):
                    target_link = item
                    print(f"[Piaoniu-V6.2] 命中项目: {text.strip().split('\n')[0]}")
                    break
            
            if not target_link:
                page.screenshot(path=f"{debug_dir}/v6_2_no_match.png")
                return
            
            # 5. 进入并全量收割
            target_link.click()
            time.sleep(3)
            # 点击购票按钮
            buy_btn = page.query_selector(".buy-btn, .footer-buy, :has-text('立即购票')")
            if buy_btn: buy_btn.click()
            time.sleep(3)
            
            # 循环场次
            btns = page.query_selector_all(".count-o-box .count, .calendar-item, .sku-item")
            print(f"[Piaoniu-V6.2] 开始轮询 {len(btns)} 个场次...")
            for i in range(len(btns)):
                current_btns = page.query_selector_all(".count-o-box .count, .calendar-item, .sku-item")
                if i >= len(current_btns): break
                btn = current_btns[i]
                s_name = btn.inner_text().strip().split('\n')[0]
                print(f"   [Harvesting] {s_name}")
                btn.click()
                time.sleep(2.5)
                
                # 提取票价
                tickets = page.query_selector_all(".ticket, .list-item")
                for t in tickets:
                    try:
                        n = t.query_selector(".ticket-name, .name").inner_text().strip()
                        p = t.query_selector(".price-display, .num, .price").inner_text().replace("¥", "").strip()
                        all_prices.append({"session": s_name, "tier": n, "price": p})
                    except: continue

            # 6. 保存报告
            output_path = f"c:/tix_work_bench/Piaoniu_Auto_Report/{keyword}_v6_2_onclick.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_prices, f, ensure_ascii=False, indent=4)
            print(f"\n[Piaoniu-V6.2] ✅ 收割任务大获全胜！结果存至: {output_path}")

        except Exception as e:
            print(f"[Piaoniu-V6.2] 运行出错: {e}")
            page.screenshot(path=f"{debug_dir}/v6_2_fatal.png")
        finally:
            page.close()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "广州 周传雄"
    piaoniu_full_harvest_v6_2(kw)
