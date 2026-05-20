# T002 — 真机桥接 RPA

> **方案：** I004 桥接服务 + AutoX.js / I005 Agent 模式架构
> **创建：** 2026-05-19 | **负责人：** TIX1号
> **前置：** T001（Redroid 云手机方案，已归档）
> **状态跟踪：** `board.md` | **过程记忆：** `memory.md`

---

## 目标

TIX1号 能通过一条命令控制真机上的大麦 App，实现抢票自动化。

## 架构

```
TIXClaw Gateway（我）
     │ exec: curl
     ▼
桥接服务（TIXClaw 本机 :18900）
     ▲ HTTP poll（纯 JSON，无密码学）
     │
  ┌──┴── 手机 ──────────────┐
  │                          │
  │ AutoX.js（HTTP polling）  │
  │    │ 无障碍服务           │
  │    ▼                     │
  │ 大麦 App                 │
  └──────────────────────────┘
```

## 为什么是 AutoX.js 而不是 OpenClaw Node

| 考量 | AutoX.js | Termux + Node |
|------|----------|---------------|
| 手机装的东西 | 1 个 App | 3 个（Termux+Node.js+OpenClaw） |
| 密码学 | 不需要 | 需要 ED25519 密钥配对 |
| 无障碍读屏 | ✅ 内置 | ❌ 另需无障碍服务 |
| 代码量 | ~60 行 | 200+ 行 |
| 今晚可跑 | ✅ | ⚠️ 多个潜在阻塞项 |

## 协议

```
TIXClaw → 桥（HTTP POST）
   POST /rpa/launch     {"pkg":"cn.damai"}
   POST /rpa/click      {"text":"同意"}
   POST /rpa/click      {"text":"立即购买"}
   POST /rpa/screenshot  {}
   POST /rpa/eval       {"js":"text('搜索').findOne().click()"}

桥 → AutoX.js（WebSocket JSON）
   → {"id":"1","action":"click","text":"同意"}
   ← {"id":"1","ok":true}

AutoX.js 命令集：
   launch     — 启动 App（am start）
   click      — 按文本点击（无障碍）
   screenshot — 截图回传 base64
   eval       — 执行任意 AutoX.js 无障碍代码
   click_xy   — 按坐标点击
   input      — 输入文本
   back       — 返回键
```

## 手机端步骤

```
1. 下载 AutoX.js v4 或 v6
2. 安装 → 打开 → 授予无障碍权限
3. 导入 autox_agent.js 脚本（HTTP 轮询版）
4. 运行 → Agent 开始轮询桥接服务
5. 保持屏幕常亮 + 关闭省电限制
```

## 宿主端步骤

```
1. 启动桥：cd code/mobile && node bridge.js
2. 测试：curl -X POST localhost:18900/rpa/click -d '{"text":"同意"}'
3. 截图：curl -X POST localhost:18900/rpa/screenshot -d '{}'
4. Eval：curl -X POST localhost:18900/rpa/eval -d '{"js":"currentPackage()"}'
5. TIX1号 对话中触发
```

## 技术栈

- **桥接服务**：Node.js + HTTP（无 ws 依赖），轮询代替 WebSocket
- **手机端**：AutoX.js（HTTP polling 代理）
- **通信**：TIXClaw(:18900) ← HTTP GET/POST → 手机 AutoX.js
- **保活**：ADB 无线 + `settings put secure` 自动开无障碍

## 关联

- I004: 真机自动化三方案对比
- I005: Agent vs 直连架构决策
- T001: Redroid 云手机（已归档）
