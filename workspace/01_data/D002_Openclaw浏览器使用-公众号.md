你有没有遇到过这种情况：给AI助手一个网页，让它帮你填写信息，结果AI说"我看不见网页内容，无法操作"？这是AI工具的经典痛点——它们能处理文字，但看不见你屏幕上的网页。OpenClaw 最新版本彻底解决了这个问题。它可以像真人一样控制你的浏览器：打开网页、点击按钮、填写表单、截取截图。而且完全隔离，不影响你正在用的Chrome。今天这篇教程，把 OpenClaw 浏览器控制从头到尾讲清楚。它是怎么工作的？OpenClaw 会在你的电脑上启动一个独立的浏览器实例——这个浏览器归 AI 使用，和你日常刷网页的 Chrome 完全分开。它的工作原理：
    
    
    
  AI指令 → OpenClaw Gateway → 控制服务 → Chrome/Brave/Edge（独立Profile）底层依赖 Chrome DevTools Protocol（CDP）协议，配合 Playwright 实现高级操作（点击、填表、截图、PDF导出等）。关键点：你的个人浏览器数据完全隔离，AI 用的不是你平时登录的那个 Chrome。快速上手（5分钟搞定）第一步：确认浏览器功能已开启
    
    
    
  openclaw browser --browser-profile openclaw status如果看到 "running": false，启动它：
    
    
    
  openclaw browser --browser-profile openclaw start打开一个网页试试：
    
    
    
  openclaw browser --browser-profile openclaw open https://www.baidu.com截个图：
    
    
    
  openclaw browser screenshot能执行这些命令，说明基础配置已经完成。第二步：让 AI 帮你操控在 OpenClaw 对话中，AI 可以直接使用 browser 工具：• browser snapshot — 拍下当前页面结构（带可点击区域编号）• browser click 12 — 点击编号为12的区域• browser type 23 "你好" — 在编号23的输入框里打字• browser screenshot — 截当前页面图AI 会先"快照"页面，然后告诉你它看到了什么、接下来要做什么，整个过程透明可控。Profiles：同时管理多个浏览器OpenClaw 支持多 profiles，等于同时管理多个独立浏览器实例。默认有两个内置 profiles：
        
          
            
            
          Profile类型说明openclaw独立管理AI 专用，完全隔离user现有会话复用你已登录的Chrome（通过Chrome DevTools MCP）
        
      配置多个Profiles在 ~/.openclaw/openclaw.json 中配置：
    
    
    
  {
  "browser": {
    "enabled": true,
    "defaultProfile": "openclaw",
    "profiles": {
      "openclaw": {
        "cdpPort": 18800,
        "color": "#FF4500"
      },
      "work": {
        "cdpPort": 18801,
        "color": "#0066CC"
      },
      "brave": {
        "driver": "existing-session",
        "attachOnly": true,
        "userDataDir": "~/Library/Application Support/BraveSoftware/Brave-Browser",
        "color": "#FB542B"
      },
      "remote": {
        "cdpUrl": "http://10.0.0.42:9222",
        "color": "#00AA00"
      }
    }
  }
}每个 profile 有自己的：• CDP 端口（本地独立）• 颜色标识（方便识别是哪个浏览器）• 启动方式（本地启动 / 附加现有 / 远程CDP）切换浏览器 profile：
    
    
    
  openclaw browser --browser-profile work open https://gmail.com使用 Brave、Edge 或其他浏览器OpenClaw 会按以下顺序自动检测系统默认浏览器：1. Chrome2. Brave3. Edge4. Chromium5. Chrome Canary如果你的默认浏览器不是 Chromium 系列，可以通过 executablePath 强制指定：macOS 指定 Brave：
    
    
    
  {
  "browser": {
    "executablePath": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
  }
}Linux 指定 Chrome：
    
    
    
  {
  "browser": {
    "executablePath": "/usr/bin/google-chrome"
  }
}Windows 指定 Edge：
    
    
    
  {
  "browser": {
    "executablePath": "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
  }
}复用你已登录的浏览器（user profile）这是最实用的功能之一：AI 可以直接使用你已经登录了账号的 Chrome，操作你正在用的网页。设置方法第一步：打开 Chrome，在地址栏输入 chrome://inspect/#remote-debugging，勾选"启用远程调试"。第二步：在配置文件中添加 existing-session profile：
    
    
    
  {
  "browser": {
    "profiles": {
      "mychrome": {
        "driver": "existing-session",
        "attachOnly": true,
        "userDataDir": "~/Library/Application Support/Google/Chrome",
        "color": "#4285F4"
      }
    }
  }
}第三步：启动并验证
    
    
    
  openclaw browser --browser-profile mychrome status
openclaw browser --browser-profile mychrome tabstabs 命令能列出你 Chrome 里已打开的所有页面，说明连接成功。注意事项• attachOnly: true 意味着 AI 不会启动新浏览器，只附加到已有浏览器• 首次附加时，Chrome 会弹出确认对话框，需要你在电脑前点击同意• 这个模式比独立 profile 权限更大（可以操作你的登录状态），建议仅在需要时开启远程CDP：控制其他机器上的浏览器如果你想让 AI 控制另一台电脑上的浏览器，或者在服务器上运行浏览器，远程 CDP 是解决方案。基本配置
    
    
    
  {
  "browser": {
    "profiles": {
      "remote": {
        "cdpUrl": "http://10.0.0.42:9222",
        "color": "#00AA00"
      }
    }
  }
}带认证的远程CDP支持 Query Token 和 HTTP Basic Auth 两种方式：
    
    
    
  {
  "browser": {
    "profiles": {
      "browserless": {
        "cdpUrl": "wss://production-sfo.browserless.io?token=你的TOKEN",
        "color": "#00AA00"
      }
    }
  }
}云端浏览器：Browserless 和 Browserbase不想在本地跑浏览器？可以使用云端托管方案。BrowserlessBrowserless 提供云端 Chromium，通过 WebSocket 直连：
    
    
    
  {
  "browser": {
    "enabled": true,
    "defaultProfile": "browserless",
    "remoteCdpTimeoutMs": 2000,
    "remoteCdpHandshakeTimeoutMs": 4000,
    "profiles": {
      "browserless": {
        "cdpUrl": "wss://production-sfo.browserless.io?token=你的TOKEN",
        "color": "#00AA00"
      }
    }
  }
}BrowserbaseBrowserbase 是另一个云端浏览器平台，集成 CAPTCHA 解决、反检测、住宅代理：
    
    
    
  {
  "browser": {
    "enabled": true,
    "defaultProfile": "browserbase",
    "remoteCdpTimeoutMs": 3000,
    "remoteCdpHandshakeTimeoutMs": 5000,
    "profiles": {
      "browserbase": {
        "cdpUrl": "wss://connect.browserbase.com?apiKey=你的API_KEY",
        "color": "#F97316"
      }
    }
  }
}常用命令速查基础操作：
    
    
    
  openclaw browser status          # 查看状态
openclaw browser start          # 启动
openclaw browser stop           # 停止
openclaw browser open https://...  # 打开网页页面操作：
    
    
    
  openclaw browser snapshot --interactive  # 获取页面结构
openclaw browser screenshot                # 截图
openclaw browser screenshot --full-page    # 全页截图AI 操作（使用 snapshot 返回的编号）：
    
    
    
  openclaw browser click 12 --double   # 双击编号12
openclaw browser type 23 "你好"       # 在输入框打字
openclaw browser press Enter         # 按回车
openclaw browser hover 44            # 悬停
openclaw browser select 9 OptionA    # 下拉选择等待和调试：
    
    
    
  openclaw browser wait --url "**/dash"    # 等待URL变化
openclaw browser wait --load networkidle # 等待网络空闲
openclaw browser errors --clear          # 清除错误记录
openclaw browser trace start              # 开始录制Trace
openclaw browser trace stop               # 停止Trace安全建议1. 独立 profile 优先：日常 AI 操作用 openclaw profile，不影响你的个人浏览器2. user profile 谨慎使用：复用登录状态权限更大，建议按需开启、用完即停3. 远程 CDP 注意保密：CDP URL 和 Token 都是敏感信息，优先使用环境变量4. 关闭 evaluate：如果不需要执行 JS，设置 browser.evaluateEnabled: false5. SSRF 防护：生产环境建议开启严格模式，限制可访问的域名范围常见问题Q:  提示 unknown command
A: 检查 plugins.allow 配置，确认 "browser" 在列表中：
    
    
    
  {
  "plugins": {
    "allow": ["telegram", "browser"]
  }
}Q: AI 说 browser tool unavailable
A: 确认 browser.enabled: true 且 plugins.entries.browser.enabled 未被禁用。Q: 截图是黑的/空白
A: 可能是 Playwright 未安装。检查：openclaw doctor 并安装 Playwright：
    
    
    
  npm install playwright && npx playwright install chromiumQ: 远程 CDP 连接超时
A: 增加超时配置：
    
    
    
  {
  "browser": {
    "remoteCdpTimeoutMs": 5000,
    "remoteCdpHandshakeTimeoutMs": 10000
  }
}一句话总结OpenClaw 的浏览器控制让你的 AI 助手真正"看得见"网页——默认的 openclaw profile 开箱即用，与个人浏览器完全隔离；user profile 则可以操作你已登录的网页；远程 CDP 和云端方案让分布式浏览器控制成为可能。建议从独立 profile 开始，先让 AI 完成一个完整的网页操作流程（打开→截图→点击→填表），感受一下"AI替你上网"的体验，再根据需要解锁更高级的配置。