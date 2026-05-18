import sys
import os
import time
from typing import List, Dict, Any

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def fetch_moretickets_price(keyword: str) -> List[Dict[str, Any]]:
    """
    抓取摩天轮 H5 官网的实时价格矩阵
    """
    print(f"[Moretickets] 正在查询比价信息: {keyword}")
    
    results = []
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        # 使用更通用的搜索词
        search_keyword = "五月天"
        search_url = f"https://m.motianlun.cn/content/list?keyword={search_keyword}"
        page.goto(search_url, wait_until="load")
        
        # 1. 查找搜索结果 (根据探测到的 .recommend-show-item)
        try:
            page.wait_for_selector(".recommend-show-item", timeout=10000)
            items = page.query_selector_all(".recommend-show-item")
            
            target_item = None
            for item in items:
                text = item.inner_text()
                if "北京" in text and "五月天" in text:
                    target_item = item
                    break
            
            if not target_item:
                print("[Moretickets] 未找到匹配北京场次的项目")
                return []
            
            target_item.click()
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"[Moretickets] 搜索结果点击失败: {e}")
            return []
        
        # 2. 抓取价格列表 (进入详情页后)
        try:
            # 等待选座或价格区域
            # 在 H5 详情页，价格通常在弹窗或底部区域展示，可能需要点一下“立即购票”
            buy_btn = page.query_selector(".buy-btn, .footer-buy, .u-button")
            if buy_btn:
                buy_btn.click()
                time.sleep(1) # 等待弹窗
            
            # 查找价格档位
            page.wait_for_selector(".sku-item, .price-list-item, .price-item", timeout=10000)
            skus = page.query_selector_all(".sku-item, .price-list-item, .price-item")
            
            print(f"[Moretickets] 发现 {len(skus)} 个价格档位")
            
            for sku in skus:
                try:
                    name_el = sku.query_selector(".sku-name, .item-title, .name")
                    price_el = sku.query_selector(".sell-price, .item-price, .price")
                    
                    if price_el:
                        item = {
                            "name": name_el.inner_text().strip() if name_el else "未知档位",
                            "sell_price": price_el.inner_text().replace("￥", "").replace("元", "").strip(),
                            "status": "available"
                        }
                        results.append(item)
                except:
                    continue
        except Exception as e:
            print(f"[Moretickets] 详情页解析失败: {e}")

        page.close()
    
    return results

if __name__ == "__main__":
    prices = fetch_moretickets_price("北京五月天")
    print("\n--- 摩天轮比价结果 ---")
    if prices:
        for p in prices:
            print(f"档位: {p['name']} | 现价: {p['sell_price']}")
    else:
        print("未抓取到有效价格数据。")
