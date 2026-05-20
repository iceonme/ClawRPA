# T002 memory — 真机桥接 RPA

> 开始：2026-05-19

## 2026-05-20 — 新手机 DT1901A (15000952727) 适配

### 手机信息
| 项 | 值 |
|------|------|
| 型号 | DT1901A (Delta) |
| 系统 | Android 10 + Smartisan OS |
| IP | 192.168.1.32 |
| 无线 ADB | ✅ :5555 |

### 适配踩坑（锤子 OS 三大坑 + 解决方案）

| # | 坑 | 现象 | 解决方案 |
|---|------|------|------|
| 1 | `threads.start()` 失效 | 脚本运行后不发送 HTTP 请求 | 改用 `setInterval()` |
| 2 | `http.postJson` 大体积崩溃 | 截图 base64 回传时脚本死亡 | try-catch 包裹 |
| 3 | `requestScreenCapture` 重复调崩 | 第二次截图后代理挂 | 移到初始化只调一次 |

### 版本演进
| 版本 | 关键变更 |
|------|------|
| v1.1 | 初始版（threads） |
| v1.2 | 单线程 while(true) — 失效 |
| v1.3 | setInterval — 首次工作，截图后崩 |
| v1.4 | try-catch 容错 + 心跳 toast — 截图后 eval 正常但二次截图崩 |
| **v1.5** | requestScreenCapture 移到初始化 — **稳定** ✅ |

### 最终稳定验证
- ✅ 连续截图不崩
- ✅ 截图后 eval 正常
- ✅ 闲鱼打开 + 截图（1711KB）
- ✅ 小红书打开 + 截图（1271KB）
- ✅ 心跳 toast 持续显示

### 新工具能力
- bridge.js v1.1: 带时间戳日志，多队列 fallback
- 截图保存路径: `workspace/04_tasks/T002_Phone_Bridge_RPA/files/screenshots/`

## 2026-05-19

### 方案决策
- 确定 AutoX.js + HTTP 轮询桥方案，弃用 OpenClaw Node（密码学太复杂）
- 决策文档见 I004

### 联调验证
- ✅ 大麦 App：打开 → 读 UI → 显示上海演出列表
- ✅ 闲鱼 App：打开 → 读 UI → 翻商品列表
- ❌ 微信 UI：自绘引擎，textMatches 无法读取（需坐标/OCR）

### 已知踩坑
- **AutoX.js v6 在 Smartisan OS 上无障碍循环崩溃** — 需 ADB 保活（`settings put secure enabled_accessibility_services ...`）。后续考虑换 v4 或直接用 ADB 驱动。
- **无线 ADB 重启丢失** — 手机重启后 TCP/IP 模式重置，需先 USB 连一下开 `adb tcpip 5555`。手机 IP：192.168.1.59

### 代码
- bridge.js: TIXClaw 本机 :18900
- autox_agent.js: 手机端 AutoX.js 脚本，每 500ms HTTP polling
- 代码路径：`code/mobile/`
