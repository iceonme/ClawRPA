# Playwright RPA 脚本体系设计（browser 目录）

## 目标

在 `C:\Projects\CloudPhone\code\browser` 下建立一套可复用、可扩展、可控风控风险的 Playwright 自动化体系，用于支持微博、小红书及后续更多平台的：

- Lead 获取
- 评论采集
- 私信首触达
- 跟进聊天
- 人工接管
- 任务编排与回放

本设计的核心目标不是“把脚本跑通”，而是建立一个**三层式自动化体系**：

1. **浏览器与人类模拟中间层**，统一封装 Playwright、等待、鼠标轨迹、输入节奏、风控节奏、日志与异常分类
2. **站点适配层**，封装微博 / 小红书等站点的页面结构、选择器、页面对象与站点行为
3. **任务流程层**，面向业务任务（找客、首触达、复核、聊天）做流程编排，不直接接触底层 DOM 细节

---

## 当前现状简述

当前 `browser` 目录中已有：

- `weibo-rpa/`
- `runtime/chrome-workbench/`

`weibo-rpa/src/` 已经形成了初步模块划分：

- `core/`：浏览器、human actions、waits 等占位
- `flows/`：lead collection、chat send、search、comments
- `probes/`：微博/小红书探测
- `schemas/`：输入输出结构

但目前存在几个明显问题：

1. **Playwright 原语泄漏到业务流中**
   - 页面打开、输入、点击、发送等行为直接散落在 flow 中
2. **人类行为模拟未真正抽象**
   - `human_actions.py`、`browser.py`、`waits.py` 仍是占位，没有形成统一执行入口
3. **站点逻辑与浏览器执行逻辑混杂**
   - 微博 DOM 适配、发送逻辑、节奏控制耦合在单文件脚本里
4. **风控策略不可统一升级**
   - 批量发送、等待节奏、失败重试、账号冷却尚未成为统一机制
5. **后续扩展到 xhs-rpa / 其他平台时复用性不足**

---

## 设计原则

### 1. 业务 flow 不直接操作 Playwright 原语

业务层尽量不直接调用：

- `page.goto()`
- `locator.click()`
- `locator.fill()`
- `page.keyboard.press()`

而是统一通过中间层 Actor 或 Action 接口调用。

### 2. 人类模拟行为默认启用

随机等待、鼠标移动、滚动、阅读停顿、输入节奏、批量冷却，不应该作为“附加选项”，而应该成为默认执行路径。

### 3. 站点差异留在适配层

微博、小红书等平台的：

- 选择器
- 页面结构
- DOM 变化
- 私信页、搜索页、评论页特性

应全部限制在 adapter / page object 中，而不污染通用中间层。

### 4. 风控策略统一管理

发送频率、批量限制、冷却周期、行为模式、失败分类，应由统一 RiskController 控制，而不是每个脚本各写一套。

### 5. 所有自动化步骤必须可观测

任何 run 都应该产出：

- screenshot
- html snapshot
- events.jsonl
- result.json
- 统一错误码

这样便于复盘、风控诊断、DOM 失效排查。

---

## 推荐总体结构

推荐将 `C:\Projects\CloudPhone\code\browser` 最终收敛成如下结构：

```text
browser/
  packages/
    browser-kernel/          # Playwright + 人类模拟 + 风控 + observability
    site-weibo/              # 微博站点适配
    site-xhs/                # 小红书站点适配
    task-flows/              # 找客/触达/聊天等任务编排
  apps/
    weibo-rpa/               # 微博业务入口脚本
    xhs-rpa/                 # 小红书业务入口脚本
  shared/
    schemas/                 # 通用 schema
    configs/                 # 通用配置模板
    prompts/                 # 话术/规则模板
  docs/
    architecture/
    anti-detection/
    site-notes/
```

如果短期不想做大搬迁，也可以先保守落地为：

```text
browser/
  common/
    kernel/
    site_base/
    task_base/
  weibo-rpa/
  xhs-rpa/
```

---

## 三层架构说明

## 第一层：Browser Kernel（浏览器与人类模拟中间层）

这一层是整个体系的核心。

职责包括：

- 连接 Playwright / CDP
- 管理 browser / context / page 生命周期
- 提供统一的人类行为接口
- 控制等待与节奏
- 处理风控策略
- 记录 artifacts 与事件
- 统一错误码与失败分类

### 推荐模块

```text
browser-kernel/
  src/
    kernel/
      session.py         # browser/context/page 生命周期
      page_pool.py       # 页签复用，减少冷启动痕迹
      artifacts.py       # 截图、html、trace、事件日志
      errors.py          # 统一错误与错误码
      config.py          # 通用运行时配置

    human/
      timing.py          # 随机等待、阶段停顿
      mouse.py           # 贝塞尔曲线、hover、抖动
      keyboard.py        # 打字节奏、错字、修正、分段输入
      scroll.py          # 滚动策略
      reading.py         # 模拟阅读与停留
      planner.py         # 人类行为编排器

    actions/
      page_actions.py    # goto/click/type/select 等高层动作
      safe_click.py
      safe_type.py
      safe_navigate.py

    detection/
      throttling.py      # 限频与速率控制
      anti_risk.py       # 批量节奏、账号冷却、模板限频
      heuristics.py      # 风控信号判断

    observability/
      events.py
      logger.py
      metrics.py
```

### 核心对象建议

#### 1. BrowserSession
负责浏览器连接与上下文生命周期。

建议职责：

- `connect_cdp()`
- `get_context()`
- `get_page()`
- `close_page()`
- `save_artifacts()`

#### 2. HumanActor
负责执行像人的动作。

建议方法：

- `goto(url, intent=None)`
- `move_to(locator)`
- `click(locator, style="human")`
- `type_text(locator, text, mode="adaptive")`
- `paste_text(locator, text)`
- `read_page(seconds=None)`
- `scroll_feed(...)`
- `hover(locator)`

#### 3. RiskController
负责风控与节奏控制。

建议方法：

- `before_send_message(account_id, target_id)`
- `after_send_message(result)`
- `should_cooldown()`
- `next_delay()`
- `record_template_usage(template_id)`

#### 4. ArtifactRecorder
统一落盘 screenshot/html/events/result。

#### 5. ErrorClassifier
将超时、找不到输入框、登录失效、账号限制等转换为统一错误码。

---

## 第二层：Site Adapter（站点适配层）

站点适配层负责将通用 Kernel 与具体平台连接起来。

### 微博站点层职责

- 如何搜索关键词
- 如何识别搜索结果卡片
- 如何进入帖子详情
- 如何展开评论区
- 如何进入私信页
- 如何定位私信输入框与发送按钮
- 如何识别登录失效、账号异常、目标不可私信等页面状态

### 推荐结构（微博）

```text
site-weibo/
  src/
    adapters/
      weibo_adapter.py
    selectors/
      search.py
      comments.py
      chat.py
    pages/
      search_page.py
      post_page.py
      chat_page.py
    policies/
      anti_risk.py
      lead_filters.py
```

### Page Object 建议

#### WeiboSearchPage
职责：
- 打开搜索页
- 输入关键词
- 判断结果页加载完成
- 抽取帖子卡片

#### WeiboPostPage
职责：
- 展开正文
- 打开评论
- 深翻评论
- 提取评论候选

#### WeiboChatPage
职责：
- 打开会话页
- 定位输入框
- 输入消息
- 点击发送
- 检测是否登录失效 / 账号限制 / 无法私信

### SiteAdapter 接口建议

```python
class SiteAdapter(Protocol):
    def open_search(...): ...
    def collect_candidates(...): ...
    def open_chat(...): ...
    def send_chat_message(...): ...
    def parse_failure(...): ...
```

微博、小红书分别实现自己的 Adapter。

---

## 第三层：Task Flow（任务编排层）

任务层面向业务，不直接触碰 DOM。

### 典型任务

#### 1. FindLeadFlow
流程：
- 根据任务生成关键词
- 调用 SiteAdapter 搜索与采集
- 调用评论提取与 lead judgement
- 落盘 lead 结果

#### 2. FirstTouchFlow
流程：
- 读取 lead
- 调用 ScriptResolver 获取 `话术.md`
- 调用 RiskController 做发送前判断
- 调用 SiteAdapter 打开聊天页并发送
- 记录发送结果

#### 3. FollowupChatFlow
流程：
- 基于历史对话状态
- 根据库存 / 上下文生成跟进消息
- 控制发送节奏与冷却

#### 4. HumanTakeoverFlow
流程：
- 自动化卡住时产出 snapshot
- 通知人工接管
- 人工操作完成后恢复任务

### 推荐结构

```text
task-flows/
  src/
    lead/
      find_lead_flow.py
      review_flow.py
    outreach/
      first_touch_flow.py
      followup_flow.py
    ops/
      human_takeover_flow.py
      recovery_flow.py
```

---

## 人类模拟体系设计

这是本次设计的关键。

### 1. TimingProfile
不同任务使用不同节奏配置。

建议对象：

```python
@dataclass
class TimingProfile:
    pre_action_ms_min: int
    pre_action_ms_max: int
    post_action_ms_min: int
    post_action_ms_max: int
    reading_pause_ms_min: int
    reading_pause_ms_max: int
```

建议预设：

- `fast_probe`
- `human_safe`
- `chat_outreach`
- `comment_mining`

### 2. MouseProfile

```python
@dataclass
class MouseProfile:
    bezier_enabled: bool
    move_duration_ms_range: tuple[int, int]
    overshoot_probability: float
    hover_probability: float
```

建议实现：

- 贝塞尔曲线路径
- 轻微 overshoot 再回拉
- hover 后再点击
- 小幅随机抖动

### 3. InputProfile

```python
@dataclass
class InputProfile:
    typing_delay_ms_range: tuple[int, int]
    typo_probability: float
    correction_probability: float
    paste_threshold: int
```

建议策略：

- 短文本使用 `type()` + 随机 delay
- 长文本避免总是 `fill()` 整段灌入
- 支持分段输入
- 支持少量删改模拟

### 4. Reading / Scroll Behavior

进入新页面后：
- 先停顿
- 偶尔滚动
- 根据任务决定是否 hover / 阅读历史记录

### 5. HumanActionPlanner

统一决定某个动作采用什么行为模式：

- 只停顿
- 移动鼠标再点击
- 滚动后再点击
- 分段输入后发送

这个 Planner 是“抽象模拟层”的关键，不应分散在业务脚本中。

---

## 风控控制体系设计

### 目标

让“能发消息”升级为“能长期稳定发消息”。

### RiskController 应负责

1. **单账号发送节奏**
   - 单轮最多几人
   - 条与条之间随机延迟
   - 批次之间冷却时间

2. **模板使用频率**
   - 同一模板单位时间内最多发送次数
   - 同一文案变体使用限制

3. **站点风险信号记录**
   - 页面警告
   - 输入框消失
   - 页面跳登录
   - 发送失败提示

4. **目标级别限制**
   - 同一用户不重复首触达
   - 同一 chat_url 冷却期内不重试

### 风控配置建议

```python
@dataclass
class RiskProfile:
    batch_size_limit: int
    inter_message_delay_range_sec: tuple[int, int]
    cooldown_between_batches_sec: tuple[int, int]
    max_same_template_per_hour: int
    max_daily_first_touch: int
```

### 初始建议值（保守）

- 每批 3 到 5 人
- 每条间隔 25 到 90 秒随机
- 每批休息 10 到 30 分钟
- 每日首触达 20 条以内
- 新号更保守

---

## 错误分类设计

当前很多 FAIL 无法指导运营动作，必须统一。

建议错误码：

```text
LOGIN_REQUIRED
ACCOUNT_RISK_WARNING
CHAT_INPUT_NOT_FOUND
TARGET_NOT_REACHABLE
TARGET_PRIVACY_RESTRICTED
SEND_BLOCKED_RATE_LIMIT
PAGE_LOAD_TIMEOUT
SELECTOR_CHANGED
UNKNOWN_SITE_ERROR
```

### 价值

有了统一错误分类后，系统可以：

- 判断是否是微博风控
- 判断是否是账号问题
- 判断是否是 DOM 变更
- 决定是否允许自动重试
- 决定是否需要人工接管

---

## 微博落地建议

## 当前 `weibo_chat_send.py` 的问题

现有实现优点：
- 简单直接
- 可复用已登录 CDP
- 支持 screenshot/html 落盘

但问题明显：
- page 生命周期管理粗糙
- 输入 / 点击 / 等待逻辑散在函数中
- 风控节奏没有纳入统一控制
- 页面状态识别不完整
- 不适合作为后续批量触达内核

## 建议拆分

### 1. `pages/chat_page.py`
负责微博私信页交互：
- 打开聊天页
- 找输入框
- 填充/输入消息
- 点击发送
- 判断错误页状态

### 2. `adapters/weibo_adapter.py`
负责微博语义操作：
- 发送私信
- 打开搜索
- 读取卡片
- 抽评论

### 3. `flows/send_first_touch.py`
负责任务编排：
- 根据 lead 与 `话术.md` 生成首触达文案
- 走 RiskController
- 走 HumanActor
- 写发送记录

---

## 小红书 / 其他平台扩展方式

新增一个 `xhs-rpa` 或其他平台时，不应重写以下能力：

- Playwright CDP 连接
- browser/context/page 生命周期
- 人类模拟行为
- 风控节奏器
- 错误分类
- artifacts 记录

只需要新增：

- page object
- adapter
- selectors
- site policy

这就是抽象层真正的长期价值。

---

## 建议的迁移路线

不建议一次性重构全部代码，建议三期推进。

## 第一期：把中间层做实（低风险）

目标：在不推翻现有业务逻辑的前提下，把公共能力抽出来。

优先做：

- `src/core/browser.py`
- `src/core/human_actions.py`
- `src/core/waits.py`
- 新增 `src/core/risk_control.py`
- 新增 `src/core/errors.py`
- 新增 `src/core/session.py`

并让 `weibo_chat_send.py` 首先改为调用这些 core 模块。

## 第二期：微博 page object 化

拆出：

- `pages/chat_page.py`
- `pages/search_page.py`
- `pages/post_page.py`
- `adapters/weibo_adapter.py`

让搜索、评论、聊天分别独立。

## 第三期：抽到 browser 公共包

等微博链路稳定后，把共性模块真正迁到 `browser-kernel`，让 xhs-rpa 直接复用。

---

## 第一批优先落地项（推荐顺序）

### 1. HumanActor
统一人类模拟动作入口。

### 2. RiskController
统一节奏与风控控制。

### 3. WeiboChatPage
将 `weibo_chat_send.py` 从一次性脚本重构为页面对象。

### 4. BatchSender
将当前 for-loop 批量发送升级为批次发送器，支持：
- 批次上限
- 冷却
- 随机间隔
- 失败分类
- 中断恢复

---

## 最终验收标准

以后任何一个 `xxx-rpa` 新功能，都应满足：

1. 业务 flow 不直接写 Playwright 原语
2. 所有点击/输入/跳转默认走 HumanActor
3. 所有发送默认走 RiskController
4. 所有失败都有统一 error code
5. 所有 run 都有 screenshot/html/events/result
6. 站点差异只存在于 page object / adapter
7. 任务逻辑只存在于 flow / usecase

满足这些后，这套体系才算真正稳定、可扩展、可运营。

---

## 针对当前项目的直接建议

从当前收益最大角度，建议先做这四件事：

1. 把 `weibo_chat_send.py` 改造成 `WeiboChatPage + WeiboAdapter + FirstTouchFlow`
2. 实现统一 `HumanActor`
3. 实现 `RiskController`
4. 实现 `BatchSender`

这样你们就能先把“微博首触达”这一条链路做成标准样板，再复制到找客、评论采集、小红书等场景。

---

## 建议下一步

建议下一个交付不是继续补讨论，而是直接进入“第一期骨架实现”，在现有 `weibo-rpa/src/core/` 里把中间层做出来，并补一版微博聊天链路改造示例。

建议交付物：

- `core/session.py`
- `core/human_actions.py`
- `core/waits.py`
- `core/risk_control.py`
- `core/errors.py`
- `flows/send_first_touch.py`
- `pages/chat_page.py`
- `adapters/weibo_adapter.py`

这样后续可以边迁移边跑，不需要等大重构结束再验证。
