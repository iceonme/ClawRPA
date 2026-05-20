# T002 board — 真机桥接 RPA

> **状态：** 🟡 doing
> **更新：** 2026-05-20 14:50

## 子任务

| # | 任务 | 状态 | 产出/备注 |
|---|------|------|-----------|
| 2.1 | 桥接服务开发 | ✅ done | `code/mobile/bridge.js` v1.1 带日志（:18900） |
| 2.2 | AutoX.js 代理脚本 | ✅ done | `code/mobile/autox_agent.js` v1.4 setInterval 版 |
| 2.3 | 联调 + 截图回传 | ✅ done | 端到端跑通：大麦/闲鱼 |
| 2.4 | 无线 ADB 保活 | ✅ done | ADB 可远程开无障碍 + 推脚本 |
| 2.5 | 新手机适配 (15000952727) | ✅ done | DT1901A / Android 10 / Smartisan OS |
| 2.6 | TIX1号 集成 | 🟡 doing | 对话中可控制手机（桥接口已就绪） |
| 2.7 | 多机扩展 | ⬜ todo | 2+ 台手机同步抢票 |

## 手机列表

| 标识 | 型号 | 系统 | IP | 状态 |
|------|------|------|-----|------|
| 15000952727 | DT1901A | Android 10 (Smartisan) | 192.168.1.32 | ✅ 在线 |
| phone-1 (旧) | 锤子 | Smartisan OS | 192.168.1.59 | ⏸️ 待重连 |

## 当前进展

- 桥接服务和手机端联调通过 ✅
- 新手机 DT1901A 适配完成（v1.4 方案：setInterval + try-catch 容错）
- 大麦 App 打开、截图、读 UI 皆可正常控制
- 待开发：具体抢票脚本逻辑

## 踩坑记录

- **WeChat UI 不可读** — 微信使用自绘引擎，uiautomator 和 textMatches 均无法读取，需坐标+OCR
- **锤子 OS 上 threads.start() 失效** — `while(true)` 和 `threads.start()` 均不可靠，改用 `setInterval()` 可行
- **http.postJson 大体积崩溃** — 截图 base64（~170KB）回传时 `http.postJson` 会崩溃，需 try-catch 包裹
- **ADB 重启后需 USB 重连一次** — 手机重启后 TCP/IP 重置，需先 USB 开 `adb tcpip 5555`
