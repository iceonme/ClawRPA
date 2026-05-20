# T002 memory — 真机桥接 RPA

> 开始：2026-05-19

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
