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

def fetch_piaoniu_price_e2e(keyword: str) -> List[Dict[str, Any]]:
    """
    票牛全流程端到端抓取：搜索 -> 点击 -> 提取
    """
    print(f"[Piaoniu-E2E] 正在启动全流程抓取: {keyword}")
    results = []
    
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        
        try:
            # 1. 真人搜索流程
            print("[Piaoniu-E2E] 正在模拟真人进入首页搜索...")
            page.goto("https://m.piaoniu.com/", wait_until="load")
            time.sleep(1.5)
            
            search_trigger = page.query_selector(".search-input, .search-box, .search-text")
            if search_trigger:
                search_trigger.click()
            else:
                page.goto("https://m.piaoniu.com/search")
            
            time.sleep(1)
            input_box = page.query_selector("input[type='search'], .search-input input")
            if input_box:
                input_box.type(keyword, delay=50)
                page.keyboard.press("Enter")
            
            # 2. 等待并点击最佳匹配
            print("[Piaoniu-E2E] 正在筛选搜索结果...")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 查找所有项目链接
            items = page.query_selector_all("a")
            target_link = None
            for item in items:
                href = item.get_attribute("href") or ""
                text = item.inner_text()
                if "/activity/" in href and any(k in text for k in keyword.split()):
                    target_link = item
                    break
            
            if not target_link:
                print("[Piaoniu-E2E] 未能找到匹配项目。")
                return []
            
            print(f"[Piaoniu-E2E] 锁定项目，正在进入详情页...")
            target_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # 3. 价格提取 (适配票牛详情页)
            # 点击“选座购买”或“立即购票”唤起价格列表
            buy_btn = page.query_selector(".buy-btn, .footer-buy, .btn-buy, text='立即购票', text='选座购买'")
            if buy_btn:
                buy_btn.click()
                time.sleep(1.5)
            
            # 抓取价格档位
            # 票牛的价格类名通常包含 'price' 或在 SKU 列表中
            page.wait_for_selector(".sku-item, .price-item, .item-price, .price", timeout=10000)
            skus = page.query_selector_all(".sku-item, .price-item, .item-price")
            
            for sku in skus:
                try:
                    name_el = sku.query_selector(".sku-name, .name, .title")
                    price_el = sku.query_selector(".price, .num, .item-price")
                    
                    if price_el:
                        results.append({
                            "name": name_el.inner_text().strip() if name_el else "未知档位",
                            "sell_price": price_el.inner_text().replace("￥", "").replace("元", "").strip()
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"[Piaoniu-E2E] 抓取失败: {e}")
        finally:
            page.close()
            
    return results

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "周杰伦"
    prices = fetch_piaoniu_price_e2e(kw)
    
    print(f"\n--- 票牛 [{kw}] 比价矩阵 ---")
    if prices:
        for p in prices:
            print(f"档位: {p['name']} | 现价: {p['sell_price']}")
    else:
        print("未抓取到有效数据。")
