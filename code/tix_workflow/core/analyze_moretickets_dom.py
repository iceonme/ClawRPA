import asyncio
import os
from playwright.async_api import async_playwright

async def analyze_detail_dom():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            # 找到那个活跃的详情页
            pages = browser.contexts[0].pages
            target_page = None
            for page in pages:
                if "show-detail" in page.url or "seat-and-seatplan" in page.url:
                    target_page = page
                    break
            
            if not target_page:
                print("[Analyze] 未找到详情页，请确保浏览器停在五月天项目详情页。")
                return

            print(f"[Analyze] 正在分析页面: {target_page.url}")
            
            # 尝试点击“立即购票”以确保价格弹窗出现
            try:
                # 寻找包含“购票”文本的元素并点击
                buy_btns = await target_page.query_selector_all("text='立即购票', text='选座购票'")
                if buy_btns:
                    print(f"[Analyze] 发现 {len(buy_btns)} 个购票按钮，尝试点击第一个...")
                    await buy_btns[0].click()
                    await asyncio.sleep(2)
            except:
                pass

            # 遍历所有元素，寻找疑似价格的项
            elements = await target_page.query_selector_all("*")
            print(f"[Analyze] 扫描到 {len(elements)} 个元素，正在筛选价格相关项...")
            
            found_count = 0
            for el in elements:
                try:
                    class_name = await el.get_attribute("class") or ""
                    text = await el.inner_text()
                    
                    # 过滤逻辑：类名包含 price/sku/item 且 文本包含数字或￥
                    if ("price" in class_name.lower() or "sku" in class_name.lower() or "item" in class_name.lower()) \
                       and ("￥" in text or any(char.isdigit() for char in text)):
                        
                        # 只打印深度较浅或具有代表性的
                        if len(text) < 50: 
                            print(f"  - 类名: {class_name} | 文本: {text.strip()}")
                            found_count += 1
                except:
                    continue
            
            print(f"[Analyze] 扫描完成，共找到 {found_count} 个疑似项。")
            
        except Exception as e:
            print(f"[Analyze] 发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_detail_dom())
