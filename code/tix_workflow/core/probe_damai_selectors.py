import sys
import os

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def probe_selectors():
    with BrowserSession(port=9222) as session:
        # 获取当前的详情页
        page = session.get_or_create_page("https://detail.damai.cn/item.htm")
        
        print(f"当前页面标题: {page.title()}")
        
        # 探测可能的正文容器
        candidates = [".project-detail", ".words", ".content", ".item-detail", "#projectDetail"]
        for c in candidates:
            el = page.query_selector(c)
            if el:
                print(f"找到匹配容器: {c}")
                # 打印前 100 个字符
                print(f"内容预览: {el.inner_text()[:100]}...")
        
        # 探测图片
        imgs = page.query_selector_all("img")
        print(f"页面共有图片: {len(imgs)} 张")
        for img in imgs[:10]:
            src = img.get_attribute("src")
            if src and "poster" in src.lower():
                print(f"疑似海报图: {src}")

if __name__ == "__main__":
    probe_selectors()
