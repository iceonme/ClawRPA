# 项目交接文档 (2026-04-19 20:32 更新)

## 当前重点项目：weibo-rpa（已收口到微博平台优先）

### 目录位置
`C:\Projects\CloudPhone\code\browser\weibo-rpa`

> 注意：原目录 `C:\Projects\CloudPhone\code\browser\lead-discovery` 已在今晚正式改名为 `weibo-rpa`。

### 当前架构结论
当前不再按“跨平台 lead-skill / chat-skill”抽象，而是采用：
- 顶层：`weibo-rpa`
- 当前正式能力：`lead`
- 下一阶段能力：`chat`

也就是：
- 先把微博做深、做稳、做工程化
- 再在同一个平台工程里扩 chat
- 更晚阶段才考虑多平台统一编排

---

## 今晚新增/完成的关键事项

### 一、完成一轮 weibo-rpa 收口重构
已更新：
- `README.md`
- `SKILL.md`
- `pyproject.toml`
- `references/architecture.md`
- `references/task-definition.md`
- `references/workflow.md`

已新增：
- `scripts/run_lead_task.py`
- `scripts/run_weibo_probe.py`
- `examples/lead/weibo.event.json`

已整理 `scripts/`：
#### 正式入口
- `scripts/run_lead_task.py`
- `scripts/run_weibo_probe.py`
- `scripts/weibo_collect_test_leads.py`

#### 工作浏览器辅助
- `scripts/launch_work_chrome.ps1`
- `scripts/check_cdp.py`
- `scripts/attach_playwright.py`

#### probe
- `scripts/probe/weibo_comments_probe.py`
- `scripts/probe/weibo_detail_entry_probe.py`
- `scripts/probe/weibo_logged_in_probe.py`

#### archive
- `scripts/archive/weibo_ui_probe.py`
- `scripts/archive/extract_weibo_detail_urls.py`

### 二、物理目录已改名
已将：
- `C:\Projects\CloudPhone\code\browser\lead-discovery`

改为：
- `C:\Projects\CloudPhone\code\browser\weibo-rpa`

并确认：
- 新路径下 `git status` 正常
- `scripts/run_lead_task.py` 可正常运行

### 三、100 条 lead 测试已确认有效
今晚前段已用：
- `scripts/weibo_collect_test_leads.py`

跑通：
- `时代少年团 广州`
- 成功抓取 100 条 lead

产物目录：
- `C:\Projects\CloudPhone\code\browser\weibo-rpa\runs\weibo-test-leads\20260419_194015`

结果说明：
- 当前版本主要基于**微博搜索结果页正文信号**
- 还不是评论层深挖版
- 但已经具备很强的第一版出池能力
- 关键词里“没抢到”是明显高产词

### 四、额外测试：`蔡依林 苏州` 跑通 20 条
今晚又测试：
- `蔡依林 苏州`
- `max_leads=20`

成功落盘：
- `C:\Projects\CloudPhone\code\browser\weibo-rpa\runs\weibo-test-leads\20260419_202725`

这轮结果说明：
- 当前 skill 已具备可迁移性，不只限于单一案例
- 但产出仍明显依赖关键词表达差异
- 对这个案例，“没抢到”依然是主力词

---

## 当前产品/工程判断
### `weibo-rpa/lead` 已接近第一版完成
当前已经具备：
- 工作浏览器 / CDP attach
- 微博搜索结果页信号抓取
- 结构化产物落盘
- 100 条量级测试通过
- 统一入口与工程文档
- 脚本分层整理

### 当前刻意不做/不阻塞当前版本的内容
- 评论层完整结构化抽取
- 自动私信发送
- 跨平台统一架构
- 复杂 confidence 优化

这些不影响当前第一版“微博找客”能力成立。

---

## 下一步建议（明天优先）

### 0. 增加评论区抓取的（重点）
### 1. 增加最小 state store（SQLite）
目标：
- lead 去重
- 记录首次发现 / 最近发现
- 支持定时增量刷新
- 为 chat 子域做数据流转打底

建议最先落两张表：
- `lead_candidates`
- `task_runs`

### 2. 把 `weibo_collect_test_leads.py` 往正式 pipeline 靠
当前它其实是最能打的入口，但名字还偏测试。
下一步要么：
- 并入 `run_lead_task.py`
- 要么抽进 `src/` 的正式 workflow，再由 `run_lead_task.py` 调用

### 3. 再考虑 `chat`
`chat` 建议仍放在同一个 `weibo-rpa` 工程下，而不是拆成新的独立 skill。

---

## 关键提交（今晚）
- `07fd803` — `refactor: reshape project as weibo-rpa lead-first`

之前重要提交仍包括：
- `93e8a76` — `feat: bootstrap probe runtime foundation`
- `efb2cc5` — `feat: refine weibo lead discovery task model`
- `2234fcd` — `feat: add manual weibo ui probe script`
- `928caf3` — `feat: add work browser cdp bootstrap scripts`
- `fabeb1e` — `feat: add logged-in weibo probe`
- `1f4361f` — `feat: validate weibo detail entry extraction`
- `d060d4b` — `feat: align task schema and runnable weibo skeleton`
- `7447db9` — `feat: add weibo lead collection test runners`
