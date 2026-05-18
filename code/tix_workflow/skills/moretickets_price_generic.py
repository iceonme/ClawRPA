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

def fetch_moretickets_price_generic(keyword: str) -> List[Dict[str, Any]]:
    """
    全通用抓取摩天轮价格
    """
    print(f"[Moretickets] 正在启动全自动比价: {keyword}")
    
    results = []
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        # 1. 搜索
        search_url = f"https://m.motianlun.cn/content/list?keyword={keyword}"
        page.goto(search_url, wait_until="load")
        
        # 2. 智能匹配结果
        try:
            page.wait_for_selector(".recommend-show-item", timeout=10000)
            items = page.query_selector_all(".recommend-show-item")
            
            target_item = None
            # 简单的关键词匹配逻辑：如果项目名称包含搜索词中的主要部分
            for item in items:
                text = item.inner_text()
                # 检查关键词中的核心元素（如城市、艺人）是否都在标题里
                if all(k in text for k in keyword.split() if len(k) > 1):
                    target_item = item
                    break
            
            # 如果没找到完全匹配，就选第一个（通常是最相关的）
            if not target_item and items:
                target_item = items[0]
            
            if not target_item:
                print(f"[Moretickets] 未能找到匹配 '{keyword}' 的项目")
                return []
            
            print(f"[Moretickets] 已锁定项目: {target_item.inner_text().split('\n')[0]}")
            target_item.click()
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"[Moretickets] 搜索或匹配阶段出错: {e}")
            return []
        
        # 3. 价格提取
        try:
            # 尝试点击“立即购票”唤起浮层
            buy_btn = page.query_selector(".buy-btn, .footer-buy, .u-button")
            if buy_btn:
                buy_btn.click()
                time.sleep(2)
            
            # 抓取价格档位
            # 兼容详情页直接展示和浮层展示两种模式
            page.wait_for_selector(".sku-item, .price-list-item, .price-item, .price-display", timeout=10000)
            skus = page.query_selector_all(".sku-item, .price-list-item, .price-item, .price-display")
            
            for sku in skus:
                try:
                    name_el = sku.query_selector(".sku-name, .item-title, .name, .title")
                    price_el = sku.query_selector(".sell-price, .item-price, .price, .price-display")
                    
                    if price_el:
                        val = price_el.inner_text().replace("￥", "").replace("元", "").replace("起", "").strip()
                        if val.isdigit():
                            results.append({
                                "name": name_el.inner_text().strip() if name_el else "未知档位",
                                "sell_price": val
                            })
                except:
                    continue
        except Exception as e:
            print(f"[Moretickets] 价格抓取阶段出错: {e}")

        page.close()
    
    return results

if __name__ == "__main__":
    # 测试通用性：深圳凤凰传奇
    test_keyword = sys.argv[1] if len(sys.argv) > 1 else "深圳 凤凰传奇"
    prices = fetch_moretickets_price_generic(test_keyword)
    
    print(f"\n--- {test_keyword} 比价结果 ---")
    if prices:
        for p in prices:
            print(f"档位: {p['name']} | 现价: {p['sell_price']}")
    else:
        print("未抓取到数据。")
