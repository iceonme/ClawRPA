# I005 — 手机 RPA 架构：Agent vs 直连

> 日期：2026-05-20 | 作者：TIX1号
> 前情：[I004 真机自动化三方案对比](../03_insight/I004_Phone_Automation_Approaches_20260519.md)
> 决策：**采用 Agent 模式** — 常驻后台守护进程分发子任务，而非每个任务独立连接。

## 问题描述

手机 RPA 需要同时处理多种任务：抢票、监控、截图、数据采集。最简单的做法是每个任务一个独立脚本，各自轮询 bridge。但实际开发中发现这种模式在稳定性、可观测性、并发控制上存在严重问题。

## 候选方案

### 方案 A：Agent 模式（✅ 选择）

```
bridge (:18900)
  │
  └── agent (常驻后台, setInterval 轮询)
        │  
        ├── engines.execScriptFile("grab_ticket.js")   // 抢票
        ├── engines.execScriptFile("monitor.js")        // 监控
        └── engines.execScript("eval 任意代码")          // 临时任务
```

- 每台手机只维护 1 条 HTTP 轮询连接
- agent 通过 AutoX.js 无障碍服务保活（force-stop 杀不死）
- 任务脚本通过 `engines.execScriptFile()` 按需启动
- 子脚本崩溃不影响 agent 存活

### 方案 B：直连模式

```
bridge (:18900)
  │
  ├── grab_v1.js (独立轮询, name="grabber-1")
  └── monitor.js (独立轮询, name="monitor-1")
```

- 每个任务独立命名、独立轮询
- 任务脚本本身负责保活

## 选择理由

| 维度 | A: Agent ✅ | B: 直连 |
|------|------------|---------|
| **保活** | 无障碍服务保一个 agent，稳 | 每个脚本各自争保活 |
| **容错** | 子脚本崩了 agent 不受影响，可报告错误 | 脚本崩=手机失联 |
| **连接数** | 1 条 / 手机 | N 条 / 手机 |
| **可观测** | 1 条心跳 + 子任务状态上报 | N 条心跳，难以区分 |
| **多机协同** | bridge 按 target 精准分发 | 需复杂命名约定 |
| **开发效率** | 改抢票逻辑 → push → execScriptFile | 需变更轮询名 + 重启 |
| **资源** | 1 个 setInterval / 手机 | N 个 setInterval / 手机 |

Agent 本质是**手机端操作系统**——它活着、稳定、单点可控。抢票脚本只管业务逻辑。

## 实现要素

1. **AutoX.js 无障碍服务** → 提供系统级保活，App force-stop 杀不掉
2. **setInterval() 轮询** → 替代 `threads.start()`（锤子 OS 兼容）
3. **try-catch 全量包裹** → 防止大体积 base64 回传崩 agent（v1.4 发现）
4. **单次 requestScreenCapture** → 只在启动时初始化（v1.5 修复）
5. **engines.execScriptFile** → agent 按需拉起任务脚本

## 弃用路径

- 直连模式：多脚本各自轮询，复杂度随任务数线性增长，容错差
- WebSocket：AutoX.js Rhino 引擎不支持
- Termux + Node：手机装 3 个东西太重，密码学复杂（见 I004）

## 关联

- I004: 真机自动化三方案对比（本决策的来源）
- T002: 真机桥接 RPA（当前实施任务）
