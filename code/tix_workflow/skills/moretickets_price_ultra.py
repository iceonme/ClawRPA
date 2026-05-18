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

def fetch_moretickets_price_ultra(keyword: str) -> List[Dict[str, Any]]:
    """
    极强鲁棒性的通用抓取逻辑
    """
    print(f"[Moretickets] 正在启动超强比价模式: {keyword}")
    
    results = []
    with BrowserSession(port=9222) as session:
        page = session.context.new_page()
        # 1. 搜索
        search_url = f"https://m.motianlun.cn/content/list?keyword={keyword}"
        page.goto(search_url, wait_until="load")
        
        # 2. 智能锁定项目
        try:
            page.wait_for_selector(".recommend-show-item, .show-item", timeout=10000)
            items = page.query_selector_all(".recommend-show-item, .show-item")
            
            target_item = None
            for item in items:
                text = item.inner_text()
                # 关键词核心匹配
                if any(k in text for k in keyword.split() if len(k) > 1):
                    target_item = item
                    break
            
            if not target_item and items:
                target_item = items[0]
            
            if not target_item:
                print(f"[Moretickets] 未发现匹配项")
                return []
            
            print(f"[Moretickets] 锁定项目: {target_item.inner_text().split('\n')[0][:20]}...")
            target_item.click()
            page.wait_for_load_state("networkidle")
        except:
            return []
        
        # 3. 唤起价格列表 (多态按钮识别)
        try:
            # 识别所有可能的购票/查看按钮
            selectors = [
                ".buy-btn", ".footer-buy", ".u-button", 
                "text='立即购票'", "text='选座购票'", "text='查看价格'", "text='预约'", "text='预选场次'"
            ]
            for sel in selectors:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    print(f"[Moretickets] 触发操作按钮: {sel}")
                    btn.click()
                    time.sleep(2)
                    break
        except:
            pass
        
        # 4. 启发式数据抓取 (哪怕类名变了也能抓)
        try:
            # 等待任何看起来像价格列表的容器
            page.wait_for_selector(".sku-item, .price-item, .ticket-item, .price-display", timeout=5000)
            
            # 扫描所有元素
            elements = page.query_selector_all("*")
            for el in elements:
                try:
                    text = el.inner_text()
                    # 匹配规则：长度短，包含数字，或者就在价格类名下
                    if 1 < len(text) < 15 and (text.isdigit() or "￥" in text):
                        # 尝试获取它的兄弟或父节点作为档位名
                        parent = el.query_selector("xpath=..")
                        p_text = parent.inner_text()
                        
                        price_val = text.replace("￥", "").replace("元", "").replace("起", "").strip()
                        if price_val.isdigit() and int(price_val) > 100:
                            results.append({
                                "name": p_text.replace(text, "").strip().split('\n')[0],
                                "sell_price": price_val
                            })
                except:
                    continue
            
            # 如果启发式抓取失败，回退到标准选择器
            if not results:
                skus = page.query_selector_all(".sku-item, .price-item, .price-display")
                for sku in skus:
                    # ... 基础抓取逻辑 ...
                    pass
        except:
            pass

        # 结果去重与整理
        unique_results = []
        seen = set()
        for r in results:
            if r['sell_price'] not in seen:
                unique_results.append(r)
                seen.add(r['sell_price'])

        page.close()
    
    return unique_results

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "深圳 凤凰传奇"
    prices = fetch_moretickets_price_ultra(keyword)
    print(f"\n--- {keyword} 比价快照 ---")
    for p in prices[:10]: # 只展示前10条
        print(f"档位/描述: {p['name'][:15]} | 现价: {p['sell_price']}")
