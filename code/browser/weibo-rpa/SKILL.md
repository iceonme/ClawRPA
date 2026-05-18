---
name: weibo-rpa
description: 微博网页 RPA skill。当前正式能力包括微博 lead 收集和微博 chat 私信发送；使用长期驻留的工作浏览器，通过 CDP/Playwright attach 执行任务，并把结果落盘到 runs/ 或 tasks/。
---

# weibo-rpa

这是 CloudPhone 网页控制方向下的微博站点能力目录。当前重点是把微博作为网页 RPA 的样板站点，沉淀可复用的浏览器控制、站点适配和任务流程。

## 使用前提

在 `code/browser/weibo-rpa` 目录下运行命令。

需要先启动并保持工作浏览器在线：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/launch_work_chrome.ps1 -Port 9222 -NewWindow
```

检查 CDP：

```powershell
python scripts/check_cdp.py
```

浏览器需要保持微博已登录。

## 当前正式能力

### Lead 收集

用途：围绕一个演出/关键词，在微博搜索和帖子评论中发现潜在购票用户，输出结构化 lead。

自定义关键词测试：

```powershell
python scripts/run_lead_collect.py --event-query "杭州 颜人中"
```

按 `tasks/task_list.json` 的任务编号运行：

```powershell
python scripts/run_lead_task.py --task-no 1
```

批量运行任务列表：

```powershell
python scripts/run_task_batch.py
```

Lead 结果位置：

```text
runs/weibo-leads/<run_id>/
  summary.json
  leads.jsonl
  leads.csv
  raw_cards.json
  events.jsonl
```

默认采集参数：

```text
max_leads = 50
max_pages_per_keyword = 10
max_posts_per_page = 8
max_comments_per_post = 200
```

需要快速冒烟测试时再显式调小这些参数。

如果通过 `run_lead_task.py` 运行，结果还会合并到对应 `tasks/<task_id>/current_leads.*`。

### Chat 发送

用途：向微博聊天页发送私信。当前已按微博 chat 场景加入简单降频策略，避免快速连续发送触发 HTTP 418 风控。

示例：

```powershell
python scripts/run_chat_task.py --chat-url "https://api.weibo.com/chat/#/chat?to_uid=1830582752" --message "测试消息"
```

Chat 结果位置：

```text
runs/weibo-chat/<run_id>/
  summary.json / events.jsonl / screenshot / html
```

当前微博 chat 发送节奏说明见：

```text
src/flows/weibo_chat_send.md
```

## 分层约定

`scripts/` 只作为运行入口层：

- 解析命令行参数
- 调用 `src` 中的 flow
- 输出 JSON 结果
- 返回进程退出码

`src/flows/` 放完整业务流程：

- `weibo_lead_collect.py`
- `weibo_chat_send.py`

`src/adapters/` 放微博站点能力封装。

`src/pages/` 放页面对象、selector 和页面动作。

`src/policies/` 放场景策略，例如微博 chat 降频。

`src/core/` 放浏览器会话、artifact、输入动作、错误码等基础能力。

## 旧入口说明

`scripts/weibo_collect_test_leads.py` 仍保留为兼容入口，但正式测试和新调用应使用：

```text
scripts/run_lead_collect.py
scripts/run_lead_task.py
scripts/run_chat_task.py
```

## 当前不负责

- 验证码处理
- 登录绕过
- 复杂风控绕过
- 跨平台统一抽象
- 热度分析

微博 chat 当前只做场景级降频，不做通用风控框架。

## 已验证

- `杭州 颜人中` lead 小样本测试可通过 `run_lead_collect.py` 对应 flow 跑通，成功产出带 `chat_url` 的 lead。
- `https://api.weibo.com/chat/#/chat?to_uid=1830582752` chat 测试可发送成功。
- 快速机械重复发送会触发微博 HTTP 418；降频后 10 条测试消息发送成功。

## 更多说明

- 浏览器目录说明：`../README.md`
- 架构：`references/architecture.md`
- 任务定义：`references/task-definition.md`
- 工作流：`references/workflow.md`
- 输出：`references/output-schema.md`
- 工作浏览器：`references/work-browser.md`
