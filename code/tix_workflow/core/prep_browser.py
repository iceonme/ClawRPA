import os
import subprocess
import time
import sys

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
launch_script = os.path.join(project_root, "code", "browser", "weibo-rpa", "scripts", "launch_work_chrome.ps1")
dashboard_html = os.path.join(current_dir, "prep_dashboard.html")

# 引入 BrowserSession
weibo_rpa_path = os.path.join(project_root, "code", "browser", "weibo-rpa")
if weibo_rpa_path not in sys.path:
    sys.path.append(weibo_rpa_path)
from src.core.session import BrowserSession

def prepare_browser_environment():
    """
    启动工作浏览器并引导用户进行手动准备。
    """
    print("[Prep] 正在启动工作浏览器...")
    try:
        subprocess.run(["powershell", "-File", launch_script], check=True)
    except Exception as e:
        print(f"[Prep] 启动失败: {e}")
        return False

    time.sleep(2) # 等待 CDP 响应

    print("[Prep] 正在初始化引导页面...")
    with BrowserSession(port=9222) as session:
        # 1. 打开 Dashboard
        dashboard_page = session.context.new_page()
        dashboard_page.goto(f"file:///{dashboard_html.replace('\\', '/')}")
        
        # 2. 打开业务页面供用户登录
        try:
            damai_page = session.context.new_page()
            damai_page.goto("https://www.damai.cn", timeout=20000)
        except:
            print("[Prep] 大麦页加载较慢，请手动刷新。")
        
        try:
            weibo_page = session.context.new_page()
            weibo_page.goto("https://weibo.com", timeout=15000)
        except:
            print("[Prep] 微博页加载较慢，可手动处理。")
        
        dashboard_page.bring_to_front()
        
        print("\n" + "="*50)
        print(" 请在浏览器中完成以下操作：")
        print(" 1. 登录大麦网并处理可能的验证码")
        print(" 2. 登录微博（如需找客）")
        print(" 3. 确认无误后，请回到命令行按 [回车] 键继续...")
        print("="*50 + "\n")
        
        input("按 [回车] 键继续任务...")
        
    print("[Prep] 准备就绪，交还控制权。")
    return True

if __name__ == "__main__":
    if prepare_browser_environment():
        print("\n[Prep] 准备就绪！浏览器端口 9222 已开启并保持挂载。")
        print("输入 'exit' 并按 [回车] 键退出并关闭浏览器...")
        while True:
            cmd = input("> ")
            if cmd.lower() == 'exit':
                break
    else:
        print("[Prep] 环境启动失败。")
