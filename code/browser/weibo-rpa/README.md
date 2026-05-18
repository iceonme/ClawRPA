# weibo-rpa

这是一个面向 **微博自动化（RPA）** 的工程目录。当前第一阶段已经收口到：

- **微博找客（lead）**：已可用，能稳定产出结构化潜客列表
- **微博私聊（chat）**：暂未实现，作为下一阶段能力

当前版本的核心目标，不是做一个“大而全的社媒框架”，而是先把 **微博 lead discovery** 做稳、做工程化、做成可被 agent 清晰调用的正式能力。

## 当前版本边界
### 已完成/可用
- 工作浏览器 + 固定 user-data-dir + CDP 常驻模式
- 通过 Playwright attach 到已登录微博工作浏览器
- 基于微博搜索结果页正文信号批量抓取潜在客户
- 一次性抓取 100 条量级 lead，并输出结构化产物
- 标准化输出：`leads.jsonl` / `leads.csv` / `summary.json`

### 暂不纳入当前收口范围
- 自动私信发送
- 多平台统一抽象（如微博 + 小红书统一 lead/chat skill）
- 评论层完整结构化抽取
- 热度分析

## 当前推荐的正式入口
### 1. 单 task 正式入口（第一版 task/run 框架）
```bash
python scripts/run_task.py --task-no 1
```

如需让任务完成后主动回消息到当前 OpenClaw 会话，可额外传入：
```bash
python scripts/run_task.py --task-no 1 --callback-session-id <当前session_id>
```

### 2. 批量 task 顺序执行入口
```bash
python scripts/run_task_batch.py
```

批量入口也支持把当前 session id 透传给每个 task：
```bash
python scripts/run_task_batch.py --callback-session-id <当前session_id>
```

### 3. 当前最稳定的微博 collector（被 task 框架调用）
```bash
python scripts/run_lead_task.py --task-no 1
```

### 4. 微博 probe 入口
```bash
python scripts/run_weibo_probe.py --input examples/lead/weibo.event.json
```

## 运行前提
详见 `references/work-browser.md`。

简述：
- 启动一个长期驻留的工作浏览器
- 保持微博登录态
- 开启固定 CDP 端口（默认 9222）
- 让 Playwright 通过 `connect_over_cdp()` 附着

## 当前目录结构
```text
scripts/
  run_lead_task.py            # 正式 lead 入口（统一命名）
  run_weibo_probe.py          # 正式 probe 入口（统一命名）
  run_task.py                 # 现有主任务骨架
  run_probe.py                # 现有 probe 骨架
  weibo_collect_test_leads.py # 兼容旧命令；正式实现已迁到 src/flows/weibo_lead_collect.py
  launch_work_chrome.ps1
  check_cdp.py
  attach_playwright.py
  probe/                      # 保留的有效探针
  archive/                    # 阶段性实验脚本归档

src/
  core/
  flows/
  schemas/
  probes/

examples/
  lead/

references/
  architecture.md
  task-definition.md
  workflow.md
  output-schema.md
  work-browser.md

runs/
  # 历史一次性 run 产物（兼容旧用法）

tasks/
  task_list.json               # scheduler loop 的任务列表
  task01_蔡依林苏州20260408/
    task.json                  # task 元信息
    status.json                # 增量边界 / 最近一次状态 / total_leads
    task_summary.json          # 任务级汇总
    task_log.jsonl             # task 级运行日志
    current_leads.jsonl        # task 级累计可用 leads 池
    current_leads.csv
    runs/
      <run_id>/
        run.json               # 本次 run 参数与状态
        summary.json
        events.jsonl
        leads.jsonl            # run_raw_leads
        leads.csv
        new_leads.jsonl        # run_new_leads
        new_leads.csv
        updated_leads.jsonl    # 本次对历史 lead 的增强记录
        updated_leads.csv
        raw_cards.json
```

## 对 agent 的调用口径
当前建议把这个工程理解为：

- 顶层：`weibo-rpa`
- 当前正式能力：`lead`
- 下一阶段能力：`chat`

也就是说：
- 现在先把 `weibo-rpa/lead` 工程化
- 等状态层、去重、任务流转收好后，再补 `weibo-rpa/chat`

## task/run 数据流说明
- `run_raw_leads`：本次 run 原始抓到的 leads，落在 `runs/<run_id>/leads.*`
- `run_new_leads`：相对 task 历史池，本次真正新增的 leads，适合交给下游联系 agent
- `current_leads`：task 级累计可用 leads 池，会在每次 run 后增量更新
- `total_leads`：只是 `current_leads` 的数量，不是另一张单独表

第一版默认策略：
- 每次 run 自动读取 `status.json` 中上一次成功运行时间
- 将其作为 `search_since / comment_since` 的输入边界
- 如果 task 还是首跑，则回退到 `comment_recent_days=5` 这类 recent window

## 下一阶段建议
当前收口之后，下一阶段优先顺序建议是：

1. 补强搜索结果页“连续无效页停止”规则
2. 补强真正基于 `search_since` 的结果页截断逻辑
3. 把 lead 结果沉淀成可供 chat 消费的候选池
4. 视规模再评估是否引入 SQLite

## 依赖安装
请先查看：`references/dependencies.md`

当前最小安装方式：
```bash
pip install -r requirements.txt
playwright install
```
