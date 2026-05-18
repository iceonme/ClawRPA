import sys
import os
from typing import Dict, Any

# 将 weibo-rpa 的 src 目录加入路径，以便复用 BrowserSession
# 假设当前文件在 code/tix_workflow/skills/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def fetch_damai_event_info(keyword: str) -> Dict[str, Any]:
    """
    通过大麦搜索关键词并提取首个项目的基本信息。
    """
    print(f"[DamaiInfo] 正在搜索关键词: {keyword}")
    
    with BrowserSession(port=9222) as session:
        # 优先查找是否已经打开了大麦搜索页
        page = session.get_or_create_page("https://search.damai.cn/search.htm")
        
        # 如果当前页面不是搜索页，或者关键词不对，则导航
        if keyword not in page.url:
            search_url = f"https://search.damai.cn/search.htm?keyword={keyword}"
            page.goto(search_url, wait_until="load")
        
        # 等待搜索结果加载
        page.wait_for_selector(".items", timeout=10000)
        
        # 获取第一个结果
        first_item = page.query_selector(".items")
        if not first_item:
            print("[DamaiInfo] 未找到相关结果")
            return {}
        
        # 提取信息 (PC端搜索页结构)
        info = {
            "title": "",
            "time": "",
            "venue": "",
            "price_range": "",
            "artist": "",
            "url": "",
            "poster_url": ""
        }
        
        # 提取各个文本行 (大麦搜索页通常是按顺序排布的 div)
        txt_box = first_item.query_selector(".items__txt")
        if txt_box:
            title_el = txt_box.query_selector(".items__txt__title a")
            if title_el:
                info["title"] = title_el.inner_text().strip()
                info["url"] = "https:" + title_el.get_attribute("href")
            
            # 使用列表索引获取更稳健，或者尝试具体的类
            # 经探测：1-艺人, 2-场馆, 3-时间, 4-价格
            info["artist"] = txt_box.query_selector(".items__txt__artist").inner_text().strip() if txt_box.query_selector(".items__txt__artist") else ""
            info["venue"] = txt_box.query_selector(".items__txt__venue").inner_text().strip() if txt_box.query_selector(".items__txt__venue") else ""
            info["time"] = txt_box.query_selector(".items__txt__time").inner_text().strip() if txt_box.query_selector(".items__txt__time") else ""
            info["price_range"] = txt_box.query_selector(".items__txt__price").inner_text().strip() if txt_box.query_selector(".items__txt__price") else ""

        # 海报图
        img_el = first_item.query_selector(".items__img img")
        if img_el:
            info["poster_url"] = "https:" + img_el.get_attribute("src")

        # --- 深度抓取：进入详情页 ---
        if info["url"]:
            print(f"[DamaiInfo] 正在进入详情页抓取深度信息...")
            detail_page = session.context.new_page()
            detail_page.goto(info["url"], wait_until="load")
            
            # 使用探测到的 .words 容器
            detail_page.wait_for_selector(".words", timeout=10000)
            
            # 自动滚动以触发懒加载 (滚动3次)
            for _ in range(3):
                detail_page.mouse.wheel(0, 800)
                detail_page.wait_for_timeout(500)
            
            detail_content = detail_page.query_selector(".words")
                
            if detail_content:
                info["artist_intro"] = detail_content.inner_text().strip()
                
                # 抓取物料图 (兼容多种懒加载属性)
                img_elements = detail_content.query_selector_all("img")
                img_urls = []
                for img in img_elements:
                    # 尝试多种可能的图片属性
                    src = img.get_attribute("data-src") or img.get_attribute("src") or img.get_attribute("original-src")
                    if src:
                        if src.startswith("//"):
                            src = "https:" + src
                        elif not src.startswith("http"):
                            continue
                        img_urls.append(src)
                
                info["detail_images"] = list(set(img_urls)) # 去重
                print(f"[DamaiInfo] 发现详情图片: {len(info['detail_images'])} 张")

            # 场馆简介 (大麦PC版有时在单独的 tab，这里先尝试当前页抓取)
            venue_info = detail_page.query_selector(".venue-info")
            if venue_info:
                info["venue_intro"] = venue_info.inner_text().strip()
            
            detail_page.close()

        print(f"[DamaiInfo] 成功抓取项目: {info['title']}")
        return info

if __name__ == "__main__":
    # 简单的冒烟测试
    res = fetch_damai_event_info("北京五月天")
    print(res)
