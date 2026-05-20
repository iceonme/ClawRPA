# I003 - 移动端 RPA 蓝图：Redroid + ADB + AI 编排

> 创建: 2026-05-18 | TIX1号
> 定位：ClawRPA 第三阶段——从浏览器自动化延伸到手机 App 控制
> 前序工作：浏览器 RPA 已跑通（票牛收割、微博 RPA），微信控制已解决

---

## 一、总体架构

```
┌─────────────────────────────────────────────────────┐
│                    TIX1号 (AI Orchestrator)            │
│   接收自然语言任务 → 拆解 → 派发 → 监控 → 汇总报告      │
└──────────┬──────────────────────┬────────────────────┘
           │                      │
    ┌──────▼──────┐       ┌──────▼──────────────┐
    │ Browser RPA │       │  Mobile RPA (NEW)   │
    │ Playwright  │       │  ADB + Redroid      │
    │ CDP :9222   │       │  TCP :5555 x N      │
    └─────────────┘       └─────────────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
           ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
           │  Redroid #1 │ │ Redroid #2  │ │ Redroid #N  │
           │  大麦 App   │ │  票牛 App   │ │  猫眼 App   │
           │  Port 5555  │ │  Port 5556  │ │  Port 5557  │
           └─────────────┘ └─────────────┘ └─────────────┘
```

**核心思路：** ClawRPA 已有的浏览器自动化体系 + 新增的手机 ADB 控制层 = 全平台票务 RPA 能力。

---

## 二、组件分层

### Layer 1 — 基础设施

| 组件 | 说明 | 状态 |
|------|------|------|
| Redroid | Docker 化的 Android 11/13 容器 | 🔜 待部署 |
| ADB | Android Debug Bridge，TCP 连接 | 🔜 待安装 |
| scrcpy | 可选，实时画面投屏调试 | ⏸️ 按需 |
| uiautomator2 | Python 绑定的 UI 测试框架 | ⏸️ 备选方案 |

**最小可行部署（MVP）：**
- 一台 Redroid 容器（Android 11，arm64 兼容）
- ADB over TCP 直连
- 核心票务 App 一套（大麦 + 票牛 + 猫眼）

### Layer 2 — 控制中间层

```
code/mobile/
├── adb_client.py         # ADB 连接管理、设备发现
├── device.py             # 单设备抽象（tap/swipe/type/screenshot）
├── device_pool.py        # 多设备池（负载分配、健康检查）
├── android_input.py      # 人类化输入模拟（延迟、轨迹、压力）
├── screenshot.py         # 截图 + OCR 识别
├── ui_tree.py            # uiautomator dump 解析
└── anticheat.py          # 反检测策略（操作间隔、随机扰动）
```

**与 Browser RPA 对齐的设计原则：**
- 不裸写 ADB 命令到业务流，全部封装为 human-like actions
- 统一的 `DeviceSession` 上下文管理器（对标 `BrowserSession`）
- 截图 + UI 树双通道感知（对标 Playwright 的 screenshot + DOM）

### Layer 3 — App 适配层

```
code/mobile/adapters/
├── damai.py              # 大麦 App 适配（搜索→选场次→选座→下单）
├── piaoniu.py            # 票牛 App 适配
├── maoyan.py              # 猫眼 App 适配
├── showstart.py           # 秀动 App 适配
└── base_adapter.py        # 基础适配器（通用操作模板）
```

每个 Adapter 封装：
- 页面识别（通过 UI 树关键节点匹配）
- 操作流程（搜索、筛选、选座、下单）
- 异常处理（弹窗、验证码、网络错误）

### Layer 4 — 任务流程层

```
code/mobile/flows/
├── monitor.py             # 监控任务：定时截图 → 比对票价/库存变化
├── harvest.py             # 收割任务：遍历场次收集全部票价信息
├── purchase.py            # 购买任务：有票立即下单（半自动，需人工确认支付）
├── captcha.py             # 验证码处理：截图 → OCR/人工识别
└── scheduler.py           # 任务调度：多设备并发、任务队列
```

---

## 三、TIX1号 的编排角色

我是这个体系的大脑，负责：

```
老大说："盯着周杰伦上海站，有票立刻通知我"
          │
          ▼
    TIX1号 拆解任务
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
  搜索   监控   告警
  大麦   Redroid   → TG 通知老大
  App    定时截图
```

**我的操作闭环：**

1. **接收** — 老大在 TG/WebChat 下自然语言指令
2. **拆解** — 识别意图 → 选平台 → 分配设备
3. **执行** — 调用 ADB 指令操作 Redroid
4. **感知** — 截图 + UI 树分析当前状态
5. **决策** — 弹窗？验证码？票没了？自主处理或升级问老大
6. **汇报** — 结果推 TG，异常即时告警

---

## 四、与现有 ClawRPA 体系的整合

```
ClawRPA/
├── code/
│   ├── browser/           ← 已有：Playwright RPA
│   │   └── weibo-rpa/
│   ├── mobile/            ← 新增：ADB RPA (本次)
│   │   ├── adb_client.py
│   │   ├── device.py
│   │   ├── device_pool.py
│   │   ├── adapters/
│   │   └── flows/
│   └── tix_workflow/     ← 已有：票务工作流核心
├── skills/                ← 已有：技能脚本（如 piaoniu_full_flow）
├── workspace/
│   ├── 01_data/           ← 运行时数据、截图、debug
│   ├── 02_knowledge/      ← 反爬策略、平台分析
│   └── 03_insight/        ← 架构文档（本文件）
└── agents/                ← Agent 定义（未来多 Agent 协作）
```

**关键整合点：**
- `DeviceSession` 对标 `BrowserSession`，同一种「打开→操作→关闭」范式
- 手机截图可通过相同 OCR 管线分析（复用 browser 侧的 OCR 能力）
- tix_workflow 的任务编排可以同时调度 browser 和 mobile 资源

---

## 五、典型任务时序

### 任务A：票价监控

```
Cron触发 (每10分钟)
  → DevicePool.allocate() 分配空闲设备
  → damai_adapter.search("周杰伦 上海")
  → 截图 → OCR提取票价/库存
  → 与上次数据对比 → 有变化推TG
  → DevicePool.release() 释放设备
```

### 任务B：多平台并发收割

```
老大: "收割周杰伦上海站全部票价"
  → DevicePool 分配3台设备
  → Device#1: 大麦Adapter.harvest()
  → Device#2: 票牛Adapter.harvest()
  → Device#3: 猫眼Adapter.harvest()
  → 并行执行，结果汇总 → 输出统一报表
```

### 任务C：抢票（半自动）

```
监控发现目标场次"有票"
  → 立刻通知老大 TG
  → 老大回复"抢"
  → purchase_flow 执行下单流程
  → 到支付页面 → 截图发TG → 等老大支付
```

---

## 六、实施路线图

### Phase 1：基础设施（第1-2天）
- [ ] 安装 ADB 工具链
- [ ] 部署首个 Redroid 容器
- [ ] 验证 ADB over TCP 连接
- [ ] 安装大麦/票牛/猫眼 APK
- [ ] 跑通第一个 `adb shell input tap` 测试

### Phase 2：控制中间层（第3-5天）
- [ ] 实现 `adb_client.py` 和 `device.py`
- [ ] 截图 + UI 树解析
- [ ] 人类化操作模拟（延迟、随机化）
- [ ] 单个 App 的搜索→选场次→看票完整流程

### Phase 3：编排集成（第6-8天）
- [ ] 实现 `device_pool.py` 多设备管理
- [ ] TIX1号 对接：自然语言 → ADB 指令
- [ ] Cron 定时监控任务
- [ ] TG 告警通知集成

### Phase 4：生产加固（第9天+）
- [ ] 反检测策略完善
- [ ] 异常自愈（App 崩溃重启、弹窗处理）
- [ ] 多设备并发压测
- [ ] 验证码识别接入

---

## 七、关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 容器方案 | Redroid | Docker 原生，资源隔离好，一台机器跑多实例 |
| 控制协议 | ADB (纯 shell) | 零依赖，不需要手机装 Agent App |
| UI 感知 | uiautomator dump + OCR | 双重保障，dump 做结构化，OCR 做兜底 |
| 并发模型 | Python asyncio + 设备池 | 对标 weibo-rpa 的 async 风格 |
| 人类模拟 | 操作间隔随机化 + 贝塞尔轨迹 | 复用 Playwright RPA 已有的人类行为策略 |

---

## 八、风险与对策

| 风险 | 对策 |
|------|------|
| App 反爬/检测模拟器 | Magisk + LSPosed 隐藏 Redroid 特征；操作节奏人类化 |
| 验证码拦截 | 截图 → OCR 自动识别 → 失败转人工（TG 推图，老大回复验证码） |
| Redroid 稳定性 | 健康检查 + 自动重启 + 设备池冗余 |
| 票务平台改版 | Adapter 模式隔离变化，改版只影响单文件 |
| ADB 连接断开 | 自动重连 + 心跳检测 |

---

## 关联 Task

- T001: 基于此蓝图的实施任务（已归档）

---

## 九、下一步行动

**立即可做（无需 Redroid 就绪）：**
1. 安装 ADB 工具链到 TIXClaw
2. 写出 `adb_client.py` 和 `device.py` 骨架
3. 在现有 Playwright RPA 基础上抽象通用操作接口，为 Mobile 层做准备

**等待 Redroid 就绪后：**
4. 部署容器 + 安装 App
5. 打通端到端流程
6. 对接 TIX1号 自然语言编排

---

> **一句话总结：** 把浏览器自动化的那套成熟打法平移过来——ADB 就是 Playwright 的手机版，Redroid 就是手机版的 Chromium。ClawRPA 已有的三层式架构（中间层→适配层→流程层）天生适配移动端，复制粘贴改后缀就行。
