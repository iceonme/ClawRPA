# T004 — 健壮 Agent 连接系统

> **方案：** I005 Agent 模式架构
> **创建：** 2026-05-20 | **负责人：** TIX1号
> **前置：** T002（真机桥接 RPA，联调已完成）
> **状态跟踪：** `board.md` | **过程记忆：** `memory.md`

---

## 目标

将 T002 的 agent 原型升级为生产级健壮连接系统。agent 作为手机端操作系统，永不死亡、可监控、可自愈。

## 架构（基于 I005）

```
TIX1号 (OpenClaw)
  │
  ▼
bridge (:18900) ← v1.2 稳定版
  │
  ├── phone-1: agent v2.x (常驻)
  │     └── engines.execScriptFile → 任务脚本
  │
  ├── 15000952727: agent v2.x (常驻)
  │     └── engines.execScriptFile → 任务脚本
  │
  └── future phones...
```

## 健壮性设计目标

### 1. Agent 守护
- 无障碍服务保活（Android 级保活，force-stop 杀不死）
- 崩溃自重启（达到零人工干预）
- 心跳上报（可观测，bridge 侧可感知失联）

### 2. Bridge 高可用
- 手机断连检测 + 自动重连通知
- 命令超时 + 重试机制
- 日志分级（info/warn/error）

### 3. 多机管理
- 手机注册/注销
- 按 target 精准路由
- 状态面板（在线/离线/最后心跳）

### 4. 任务分发
- `execScriptFile` 支持（推代码直接跑）
- 任务结果回传
- 独立脚本崩溃不影响 agent

## 技术栈

| 层 | 技术 |
|-----|------|
| 手机 Agent | AutoX.js v6 + setInterval + 无障碍保活 |
| 通信桥 | Node.js HTTP (:18900) |
| 架构 | I005 Agent 模式 |

## 关联

- I005: Agent vs 直连架构决策（本任务的设计来源）
- I004: 真机自动化三方案对比
- T002: 真机桥接 RPA（原型 + 验证场地）
