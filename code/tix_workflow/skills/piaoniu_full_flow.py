import sys
import os
import time
import random
import json
import re
import io
import subprocess
import urllib.parse
from typing import List, Dict, Any

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)

from src.core.session import BrowserSession

def clean_price(price_str: str) -> int:
    if not price_str: return 0
    nums = re.findall(r'\d+', price_str.replace(',', ''))
    return int(nums[0]) if nums else 0

def launch_clean_chrome():
    print("[Piaoniu-V13.8] 1. 环境重生...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
        time.sleep(2)
    except: pass
    new_profile_dir = os.path.join(project_root, "code", "browser", "runtime", f"stable_v138_{int(time.time())}")
    os.makedirs(new_profile_dir, exist_ok=True)
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_path, f"--remote-debugging-port=9222",
        f"--user-data-dir={new_profile_dir}",
        "--no-first-run", "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled", "about:blank"
    ]
    subprocess.Popen(cmd)
    time.sleep(12)
    return new_profile_dir

def piaoniu_stable_harvest_v13_8(keyword: str):
    """
    全流程 v13.8：全链路抗延迟版
    """
    city_target = "广州"
    main_actor = "周传雄"
    print(f"[Piaoniu-V13.8] 全链路抗延迟版启动: {keyword}")
    profile_path = launch_clean_chrome()
    debug_dir = os.path.join(project_root, "workspace", "01_data", "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    final_data = {
        "event": keyword, "event_date": "...", "venue": "...",
        "harvest_time": time.strftime("%Y-%m-%d %H:%M:%S"), "dates": []
    }
    
    try:
        with BrowserSession(port=9222) as session:
            page = session.context.new_page()
            page.set_default_timeout(60000) # 提高全局超时到 60s
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
            
            # 2. 首页热身 (抗延迟加载)
            print("[Piaoniu-V13.8] 2. 正在加载首页热身...")
            try: page.goto("https://m.piaoniu.com/", timeout=60000)
            except: pass
            time.sleep(15) 
            
            # 3. 正在跳转至 PC 版搜索页 (获取 ID 更稳)
            search_keyword = urllib.parse.quote(keyword)
            pc_search_url = f"https://www.piaoniu.com/sh-all/s_{search_keyword}"
            print(f"[Piaoniu-V13.8] 3. 正在 PC 端搜索获取 ID: {pc_search_url}")
            try:
                page.goto(pc_search_url, timeout=45000)
                time.sleep(10)
            except Exception as e:
                print(f"[Piaoniu-V13.8] WARNING: PC 搜索页加载异常，尝试使用保底逻辑: {e}")
            
            # 4. PC 端精准提取 ID (直达选座页战术)
            print("[Piaoniu-V13.8] 4. 执行 PC 端 ID 锁定战术...")
            start_scan = time.time()
            activity_id = None
            while time.time() - start_scan < 40:
                pc_cards = page.locator(".results.activities li.item")
                if pc_cards.count() > 0:
                    for i in range(pc_cards.count()):
                        card = pc_cards.nth(i)
                        if main_actor in card.inner_text() and city_target in card.inner_text():
                            href = card.locator("a").first.get_attribute("href") or ""
                            match = re.search(r'activity/(\d+)', href)
                            if match:
                                activity_id = match.group(1)
                                print(f"[Piaoniu-V13.8] OK: PC 端成功锁定 Activity ID: {activity_id}")
                                break
                    if activity_id: break
                time.sleep(5)
            
            # 保底逻辑：针对热门演出直接注入验证过的 ID
            if not activity_id:
                if "五月天" in keyword and "北京" in keyword:
                    activity_id = "763004"
                    print(f"[Piaoniu-V13.8] WARNING: 搜索失败，启用五月天北京保底 ID: {activity_id}")
            
            if not activity_id:
                print("[Piaoniu-V13.8] FAIL: PC 端未能锁定 Activity ID。")
                return

            # 5. 跨端空降：直达 Mobile 选座页面
            seat_url = f"https://m.piaoniu.com/seat/seat.html?id={activity_id}&areaTicketType=1&originSource=search_page_result&buyType=DIRECT_BUY"
            print(f"[Piaoniu-V13.8] GO: 跨端空降 Mobile 选座页: {seat_url}")
            page.goto(seat_url, timeout=60000)
            time.sleep(10)

            print("[Piaoniu-V13.8] 5. 成功杀入详情页，等待渲染...")
            time.sleep(12)
            
            # 预抓取场馆（通常在详情页头部）
            venue_info = page.evaluate("""
                () => {
                    const v = document.querySelector('.venue-name, .addr, .location');
                    return v ? v.innerText.trim() : "未知场馆";
                }
            """)
            final_data["venue"] = venue_info

            # 6. 具体页面深度开启 (20s 超长等待)
            print("[Piaoniu-V13.8] 6. 执行精准点击唤起具体页面 (极慢网速容错)...")
            page.evaluate("document.querySelectorAll('.mask, .overlay, .download-banner, .sku-mask').forEach(el => el.remove())")
            
            target_path = ".bottom-btn.direct-tag, .buy-btn, .btn-buy, .bottom-button"
            opened = False
            for attempt in range(5):
                btn = page.locator(target_path).filter(visible=True).first
                if btn.count() > 0:
                    print(f"[Piaoniu-V13.8] 发现购买按钮，执行 Click...")
                    btn.click(force=True)
                
                # 等待面板弹出
                time.sleep(15)
                
                is_ready = page.evaluate("""
                    () => {
                        const selectors = ['.popup', '.sku-overlay', '.spec-container', '.sku-container', '.buy-panel', '.spec-content'];
                        const hasPanel = selectors.some(s => {
                            const el = document.querySelector(s);
                            return el && window.getComputedStyle(el).display !== 'none';
                        });
                        const hasText = document.body.innerText.includes('去选座') || document.body.innerText.includes('场次');
                        return hasPanel || hasText;
                    }
                """)
                if is_ready:
                    print(f"[Piaoniu-V13.8] OK: 具体面板已确认就绪！")
                    opened = True; break
                print(f"[Piaoniu-V13.8] 面板未见，重试第 {attempt+2} 次...")

            if not opened:
                print("[Piaoniu-V13.8] FAIL: 超时等待后依然未见具体页面。")
                page.screenshot(path=f"{debug_dir}/v13_8_timeout_final.png")
                return

            # --- 7. 深度多场次循环收割 ---
            print("[Piaoniu-V13.8] 7. 开始执行多场次循环探测...")
            
            # 1. 唤起日期选择器获取所有场次
            page.locator(".tooltip-container, .top-bar-center").first.click(force=True)
            time.sleep(5)
            
            # 获取所有场次节点的数量
            session_selectors = ".popup-body .event-wrap .event, .spec-content .item, .session-item"
            session_count = page.locator(session_selectors).count()
            print(f"[Piaoniu-V13.8] 发现 {session_count} 个场次，准备逐一收割...")
            
            # 先关闭刚才打开的选择器（如果是遮挡的）
            page.keyboard.press("Escape")
            time.sleep(2)

            for idx in range(session_count):
                print(f"\\n[Session Loop] >>> 正在处理第 {idx+1}/{session_count} 个场次")
                
                # 切换场次
                page.locator(".tooltip-container, .top-bar-center").first.click(force=True)
                time.sleep(3)
                target_session = page.locator(session_selectors).nth(idx)
                target_session.click(force=True)
                time.sleep(2)
                
                # --- 新增：点击“确认”按钮触发真正跳转 ---
                confirm_btn = page.locator("button:has-text('确认'), .btn-submit, .submit-btn, .confirm-btn").filter(visible=True).first
                if confirm_btn.count() > 0:
                    print("   [Action] 点击'确认'按钮提交场次选择...")
                    confirm_btn.click(force=True)
                else:
                    # 备选逻辑：有些版本可能直接点击场次就跳转，或者按钮叫“去选座”
                    go_seat_btn = page.locator("text='去选座'").filter(visible=True).first
                    if go_seat_btn.count() > 0:
                        go_seat_btn.click(force=True)
                
                time.sleep(10) # 等待场次切换加载
                
                # 清理遮罩
                page.evaluate("document.querySelectorAll('.mask, .overlay, .sku-mask').forEach(el => el.remove())")
                
                # 提取日期
                session_date = page.evaluate("""
                    () => {
                        const eventName = document.querySelector('.event-name, .event-right .event-name');
                        return eventName ? eventName.innerText.trim().replace(/\\n/g, ' ') : "日期获取失败";
                    }
                """)
                print(f"[Piaoniu-V13.8] 当前场次日期: {session_date}")
                
                # 提取档位并收割
                # 优化：精准匹配截图中的 .ticket-item 药丸
                time.sleep(5) 
                sku_js = """
                    () => {
                        // 根据截图，药丸类名为 .ticket-item，容器可能是 .ticket-wrap
                        return Array.from(document.querySelectorAll('.ticket-item, .sku-item, .spec-item, .item'))
                            .filter(el => {
                                const t = el.innerText.trim();
                                // 兼容：纯数字、带“元”、带“看台”、带“内场”
                                const hasPrice = /\\d{3,5}/.test(t);
                                const hasKeywords = t.includes('看台') || t.includes('内场') || t.includes('包厢') || t.includes('元');
                                const isShort = t.length > 1 && t.length < 15;
                                
                                // 必须是可见的，且不在底部的购买列表里
                                const inList = el.closest('.ticket-list, .list-container, .buy-list');
                                return (hasPrice || hasKeywords) && isShort && !inList && el.offsetParent !== null;
                            })
                            .map(el => el.innerText.trim());
                    }
                """
                tier_names = list(dict.fromkeys([n for n in page.evaluate(sku_js) if n]))
                print(f"[Piaoniu-V13.8] 发现有效档位药丸: {tier_names}")
                
                current_obj = {"date": session_date, "original_tiers": []}
                for t_name in tier_names:
                    try:
                        # 提取面值（3-5位数字），避开前面的折扣数字
                        import re
                        match = re.search(r"\d{3,5}", t_name)
                        core_price = match.group(0) if match else "".join(filter(str.isdigit, t_name))
                        if not core_price: continue
                        
                        print(f"   [Action] 准备切换至档位: {t_name} (提取面值: {core_price})")
                        
                        # 核心加固：点击动作必须发生在 .ticket-wrap-container 内部
                        pill_container = page.locator(".ticket-wrap-container, .sku-list, .spec-list").first
                        if pill_container.count() > 0:
                            target_pill = pill_container.locator(".ticket-item, .sku-item, .item, span").filter(has_text=core_price).first
                            if target_pill.count() > 0:
                                target_pill.click(force=True)
                                print(f"   [OK] 已成功点击档位药丸: {core_price}")
                                time.sleep(8)
                        
                        lst = []
                        # 抓取数据：只从下方的 ticket-list 容器里抓取，避开上方的药丸容器
                        # 截图显示下方列表容器类名为 .ticket-list
                        rows = page.locator(".ticket-list .ticket, .ticket-list .list-item, .ticket-list .sku-ticket")
                        if rows.count() == 0:
                            # 备选：如果类名不匹配，尝试 generic 但排除药丸容器
                            rows = page.locator(".ticket, .list-item, .sku-ticket").filter(has_not=page.locator(".ticket-wrap-container *"))
                        
                        for i in range(rows.count()):
                            try:
                                row = rows.nth(i)
                                n_el = row.locator(".ticket-name, .name, .title, .info").first
                                p_el = row.locator(".price-display, .num, .price, .money").first
                                if n_el.count() and p_el.count():
                                    lst.append({
                                        "detail": n_el.inner_text().strip(), 
                                        "current_price": clean_price(p_el.inner_text())
                                    })
                            except: continue
                        
                        if lst: 
                            current_obj["original_tiers"].append({"original_price": t_name, "listings": lst})
                    except Exception as e:
                        print(f"   [Error] 档位 {t_name} 采集失败: {str(e)}")
                        continue
                
                final_data["dates"].append(current_obj)
                
            output_path = f"c:/tix_work_bench/Piaoniu_Auto_Report/{keyword}_v13_8_multi.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f: json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"[Piaoniu-V13.8] OK: 多场次循环收割完成！报告: {output_path}")

    except Exception as e:
        print(f"[Piaoniu-V13.8] 运行时故障: {e}")
    finally:
        print(f"[Piaoniu-V13.8] 记录归档完成。")

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "广州 周传雄"
    piaoniu_stable_harvest_v13_8(kw)
