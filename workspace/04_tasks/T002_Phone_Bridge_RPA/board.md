# T002 board — 真机桥接 RPA

> **状态：** 🟡 doing
> **更新：** 2026-05-20

## 子任务

| # | 任务 | 状态 | 产出/备注 |
|---|------|------|-----------|
| 2.1 | 桥接服务开发 | ✅ done | `code/mobile/bridge.js` HTTP 轮询版（:18900） |
| 2.2 | AutoX.js 代理脚本 | ✅ done | `code/mobile/autox_agent.js` HTTP 轮询版 |
| 2.3 | 联调 + 截图回传 | ✅ done | 端到端跑通：大麦/闲鱼/微信 |
| 2.4 | 无线 ADB 保活 | ✅ done | ADB 可远程开无障碍 + 推脚本 |
| 2.5 | TIX1号 集成 | 🟡 doing | 对话中可控制手机（桥接口已就绪） |
| 2.6 | 多机扩展 | ⬜ todo | 2+ 台手机同步抢票 |

## 当前进展

- 桥接服务和手机端联调通过 ✅
- 大麦 App 打开、截图、读 UI 皆可正常控制
- 待开发：具体抢票脚本逻辑

## 踩坑记录

- **WeChat UI 不可读** — 微信使用自绘引擎，uiautomator 和 textMatches 均无法读取，需坐标+OCR
- **AutoX.js v6 无障碍崩溃** — 锤子 Smartisan OS 上无障碍循环崩溃，需 ADB 保活
- **ADB 重启后需 USB 重连一次** — 手机重启后 TCP/IP 重置，需先 USB 开 `adb tcpip 5555`
