# I004 — 真机桥接 RPA 方案

> 日期：2026-05-19 | 作者：TIX1号
> 前情：Redroid 云手机方案（I003）因大麦阿里安全 SDK 反模拟器检测受阻，转向真机方案。
> 决策：桥接服务 + AutoX.js，手机只装一个 App。

---

## 为什么选这个方案

| 理由 | 说明 |
|------|------|
| 手机最轻 | 只装 AutoX.js，不装 Termux、不装 Node.js、不装 OpenClaw |
| 代码最少 | 桥 30 行 + AutoX.js 30 行 = 总 60 行 |
| 绕过密码学 | 不实现 OpenClaw Node 协议的 ED25519 密钥配对 |
| 隐蔽性 | AutoX.js 无障碍服务，大麦检测概率低 |
| 今晚可跑 | 没有任何阻塞项 |

**弃用的路径：**
- Termux + `openclaw node run`：手机装三个东西，偏重，且 Termux 无 ADB 权限，自动化命令仍靠 AutoX.js
- 自开发 APK：Android 开发 + OpenClaw 协议实现，工作量大，不急

---

## 架构

```
┌────────── TIXClaw ──────────┐
│                              │
│  Gateway（我，AI 大脑）       │
│     │ exec: curl             │
│     ▼                        │
│  桥接服务（端口 18900）       │
│     ▲ WebSocket              │
└─────┼────────────────────────┘
      │
┌─────┼── 手机 ────────────────┐
│     ▼                        │
│  AutoX.js（WS 客户端）        │
│     │ 无障碍服务              │
│     ▼                        │
│  大麦 App                    │
└──────────────────────────────┘
```

**为什么不用 Gateway 直连：** Gateway WebSocket 要求 ED25519 密钥签名，AutoX.js 的 Rhino 引擎不支持 `crypto.subtle`。桥挡掉这套密码学，协议只剩纯 JSON。

---

## 协议（极简）

```
TIXClaw → 桥（HTTP POST）
   POST /rpa/launch     {"pkg":"cn.damai"}
   POST /rpa/click      {"text":"立即购买"}
   POST /rpa/screenshot  {}
   POST /rpa/eval       {"js":"text('搜索').findOne().click()"}

桥 → AutoX.js（WebSocket JSON）
   → {"id":"1","action":"click","text":"立即购买"}
   ← {"id":"1","ok":true}

AutoX.js 命令集：
   launch    — 启动 App
   click     — 按文本点击
   screenshot — 截图回传 base64
   eval      — 执行任意 AutoX.js 无障碍代码（万能接口）
```

---

## 关联

- I003: Redroid 方案（被替代）
- T001_Redroid_CloudPhone: 云手机归档
- T002_Phone_Bridge_RPA: 实施任务
- T003_Redroid_Anti_Detection: Redroid 探索方向延伸
