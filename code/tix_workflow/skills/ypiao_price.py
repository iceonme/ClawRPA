import sys
import os
import time
import re
from typing import List, Dict, Any

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def fetch_ypiao_price_e2e(keyword: str) -> List[Dict[str, Any]]:
    """
    有票全流程端到端抓取
    """
    print(f"[Ypiao-E2E] 正在启动全流程抓取: {keyword}")
    results = []
    
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        
        try:
            # 1. 真人搜索流程
            print("[Ypiao-E2E] 正在进入首页...")
            page.goto("https://m.ypiao.com/", wait_until="load")
            time.sleep(2)
            
            # 点击搜索
            search_btn = page.query_selector(".search-box, .search, .top-search")
            if search_btn:
                search_btn.click()
                time.sleep(1)
            
            input_box = page.query_selector("input[type='search'], input[placeholder*='搜索']")
            if input_box:
                input_box.type(keyword, delay=100)
                page.keyboard.press("Enter")
            else:
                # 备选：直接跳转搜索链接
                page.goto(f"https://m.ypiao.com/search?keyword={keyword}")
            
            # 2. 匹配项目
            print("[Ypiao-E2E] 正在匹配搜索结果...")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            items = page.query_selector_all("a")
            target_link = None
            for item in items:
                href = item.get_attribute("href") or ""
                text = item.inner_text()
                # 有票详情页通常包含 /product/
                if "/product/" in href and any(k in text for k in keyword.split()):
                    target_link = item
                    break
            
            if not target_link:
                # 如果没找到，尝试第一个链接
                target_link = page.query_selector(".product-item a, .list-item a")
            
            if not target_link:
                print("[Ypiao-E2E] 未找到匹配项目。")
                return []
            
            print(f"[Ypiao-E2E] 进入详情页...")
            target_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # 3. 价格提取
            # 点击“立即购票”
            buy_btn = page.query_selector(".buy-btn, .footer-btn, text='立即购票'")
            if buy_btn:
                buy_btn.click()
                time.sleep(2)
            
            # 抓取价格档位
            skus = page.query_selector_all(".sku-item, .price-item, .spec-item")
            for sku in skus:
                try:
                    name_el = sku.query_selector(".name, .title, .sku-title")
                    price_el = sku.query_selector(".price, .num, .sku-price")
                    
                    if price_el:
                        results.append({
                            "name": name_el.inner_text().strip() if name_el else "未知档位",
                            "sell_price": price_el.inner_text().replace("￥", "").strip()
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"[Ypiao-E2E] 抓取出错: {e}")
        finally:
            page.close()
            
    return results

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "温州 周杰伦"
    prices = fetch_ypiao_price_e2e(kw)
    
    print(f"\n--- 有票 [{kw}] 比价矩阵 ---")
    if prices:
        for p in prices:
            print(f"档位: {p['name']} | 现价: {p['sell_price']}")
    else:
        print("未抓取到有效数据。")
