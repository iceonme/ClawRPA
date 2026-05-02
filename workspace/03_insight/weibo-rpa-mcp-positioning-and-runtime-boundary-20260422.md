# weibo-rpa 中 Playwright MCP 的定位：探索/录制优先，运行时仍以脚本为主

日期：2026-04-22

## 放置位置
本条 insight 放在项目 workspace 下：
- `C:\Projects\CloudPhone\workspace\03_insight\weibo-rpa-mcp-positioning-and-runtime-boundary-20260422.md`

---

## 背景
围绕 `weibo-rpa` 的浏览器自动化路线，已经实际讨论和比较过三类能力：

- 现有 Playwright 脚本
- OpenClaw browser / browser tool
- Playwright CLI

在此基础上，进一步讨论了 **Playwright MCP（Model Context Protocol）** 是否是一个被遗漏的重要方向。

结论不是“完全不需要 MCP”，也不是“应该立刻重构成 MCP 路线”，而是需要明确它在当前项目中的**正确定位**。

---

## 核心结论

### 1. MCP 不是当前 weibo-rpa 主运行时的关键缺口
当前 `weibo-rpa` 的主要瓶颈并不是：
- 浏览器能不能被 agent 控制
- 有没有统一工具协议
- agent 能不能自己 click / type / snapshot

当前更关键的是：
- 评论层抽取稳定性
- UID / profile / chat_url 补抓
- 候选评论筛选质量
- AI 如何在抓取过程中实时介入判断
- 脚本与 OpenClaw agent 的协同方式

因此，**MCP 不是当前主链路缺失的关键拼图**。

---

### 2. 当前主线仍应是：固化后的 Playwright 脚本 + OpenClaw/process 协同
对 `weibo-rpa` 这类固定平台、固定目标、固定流程的任务，更适合的主链路仍然是：

- 用 Playwright 脚本承载稳定抓取、DOM 适配、容错、落盘
- 用 OpenClaw agent 承载批次判断、策略决策、流程调度
- 用 `process` 作为脚本与 agent 之间的主交互通道

简化表达：

> 脚本 = 眼睛和手  
> OpenClaw agent = 脑子

也就是说，**正式批量执行仍应以脚本为主，而不是让 MCP 直接承担生产主链路。**

---

### 3. MCP 更适合“新任务探索 / 页面摸底 / 录制 / 脚本草稿生成”
MCP 的最佳价值，不在当前项目里替代正式运行脚本，而在于：

- 新任务刚开始时的页面探索
- 页面结构摸底
- 操作路径试探
- selector / DOM 抽取思路验证
- 录制关键交互路径
- 生成 Playwright 脚本草稿

也就是：

> **MCP 更适合做探路和原型，不适合直接做当前阶段的大规模稳定跑批主引擎。**

这个定位比“把 MCP 当正式生产执行器”更合理，也更符合当前项目状态。

---

## 为什么是这个定位

### A. MCP 更擅长探索，不擅长承接成熟流水线
在新页面、新任务、新站点上，最难的往往是：
- 页面怎么走
- 入口在哪里
- 哪些元素稳定
- 需要哪些交互
- 有没有弹窗/登录/风控

MCP/browser 工具在这个阶段很有价值，因为 agent 可以边看边试。

但一旦路径确认，进入稳定执行阶段后，真正需要的是：
- 可重复运行
- 可调试
- 好做异常处理
- 易插入业务逻辑
- 易做批量执行

这时候，**沉淀为正式 Playwright 脚本通常更优。**

---

### B. 当前业务问题在业务层，不在通用浏览器协议层
即使引入 MCP，也不会自动解决这些问题：
- 哪类评论是真 lead
- 哪些帖子值得继续深翻
- 哪些候选值得补身份信息
- 何时中断当前 query 或切下一条

这些仍然需要业务判断层，而当前最有效的业务判断承接方式，是：
- 脚本产出候选 batch
- OpenClaw agent 通过 `process` 审批次
- 再由脚本继续执行

所以真正关键的是**业务协同协议**，不是先上 MCP。

---

## 推荐的分工模型

### 1. MCP / browser 工具负责
用于：
- 新任务探索
- 页面摸底
- 录制关键交互
- 验证 selector / DOM 抽取
- 辅助生成脚本草稿
- 页面变化后的快速重新探路

### 2. 正式 Playwright 脚本负责
用于：
- 稳定批量执行
- DOM 抽取与容错
- 结构化数据落盘
- 状态管理
- 与 OpenClaw 的 `process` 协议对接

### 3. OpenClaw agent 负责
用于：
- 审核 candidate batch
- 决定接受/拒绝/继续深翻/跳过
- 决定是否做身份补抓
- 协调整体任务流程

---

## 对当前 weibo-rpa 的推荐开发流程

### 阶段 1：探索 / 录制 / 摸底
优先使用：
- MCP
- OpenClaw browser
- Playwright CLI

产出应包括：
- 页面入口说明
- 关键 selector 列表
- 可抽取字段草稿
- 关键交互路径
- 弹窗/登录/风控观察
- 可转成 Playwright 的代码草稿

### 阶段 2：沉淀成正式脚本
将探索结果整理为：
- Playwright Python 脚本
- 稳定抽取逻辑
- 异常处理
- run / task / event 结构
- 可长期复用的采集流程

### 阶段 3：运行时协同
正式运行时采用：
- 脚本负责抓
- OpenClaw agent 负责判断
- `process` 负责双向交互

---

## 对当前项目的直接建议
当前不建议：
- 为了 MCP 而重构整个 `weibo-rpa` 运行主链路
- 把批量执行强行迁到 MCP 主导

当前建议：
- 保持 **Playwright 脚本 + OpenClaw/process** 为主线
- 把 MCP 纳入“新任务探索与录制”的标准工具集
- 当未来出现多平台统一抽象、agent 自由探索增多、脚本维护成本显著上升时，再重新评估 MCP 的升级价值

---

## 一句话总结

> 对 `weibo-rpa` 来说，Playwright MCP 目前最合适的定位，不是替代正式运行脚本，而是作为**新任务探索、录制、页面摸底、脚本草稿生成**的前置工具层；正式稳定跑批仍以固化后的 Playwright 脚本为主，并通过 OpenClaw `process` 接入 AI 决策。
