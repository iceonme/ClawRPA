---
name: weibo-rpa
description: 面向微博自动化的 skill。当前第一阶段正式收口为微博找客（lead）：围绕某个演出/关键词在微博中搜索相关帖子，提取潜在客户线索并输出结构化结果。后续将在同一 skill 下扩展 chat 等能力。
---

# weibo-rpa



## 当前正式能力
### `lead`
适用于：
- 输入某个演出查询短语，例如 `时代少年团 广州`
- 在微博搜索结果页批量发现潜在购票用户
- 输出结构化潜客结果，供后续人工筛选或下游 chat pipeline 消费

## 当前不负责
- 自动私信发送（未来 `chat` 子能力）
- 热度分析
- 多平台统一编排
- 验证码/风控绕过

## 推荐运行模式
继续采用：
- **工作浏览器长期驻留**
- **固定 CDP 端口**
- **Playwright attach**
- **脚本做真实工作，文件保存真实产物，stdout 只输出少量结构化状态/结果索引**

## 正式入口
### Lead 主任务
```bash
python scripts/run_lead_task.py --input examples/lead/weibo.event.json
```

### 当前稳定可用的微博找客入口
```bash
python scripts/weibo_collect_test_leads.py --event-query "时代少年团 广州" --max-leads 100 --max-pages-per-keyword 12
```

### Probe
```bash
python scripts/run_weibo_probe.py --input examples/lead/weibo.event.json
```

## 脚本分层约定
### 正式入口
- `scripts/run_lead_task.py`
- `scripts/run_weibo_probe.py`
- `scripts/weibo_collect_test_leads.py`

### 工作浏览器辅助
- `scripts/launch_work_chrome.ps1`
- `scripts/check_cdp.py`
- `scripts/attach_playwright.py`

### 探针
- `scripts/probe/*`

### 归档
- `scripts/archive/*`

## 当前版本说明
当前 v1 更偏：
- 微博 lead 发现
- 高召回
- 快速出池
- 结构化落盘

其中已验证：
- 100 条量级快速抓取
- UID / profile / source_post_url 等关键字段可稳定产出
- 搜索结果页内可直接展开评论层并抽取评论信号

当前推荐的真实工作流已调整为以下 SOP：

1. **搜索核心关键词**
   - 先跑主查询（如 `郑州 汪苏泷`），作为当前关键词任务的起点
2. **在搜索结果首页筛候选帖子**
   - 重点看两个数据：**时间**、**回复数/评论数**
   - 优先处理：时间更近、回复数更高的帖子
3. **不做搜索页浅层评论试探，直接点击进入帖子主页**
   - 对候选帖子直接进入详情页 / 帖子主页
   - 优先深挖高热帖的完整评论区
4. **在帖子主页抽取评论 lead**
   - 从评论层识别潜在需求（如“没抢到”“蹲票”“求票”“谁出”“有偿代抢”等）
5. **在当前搜索结果页的候选帖子中重复迭代**
   - 直到本页高价值帖子处理完成
6. **点击搜索结果页底端的下一页继续循环**
   - 继续处理下一页候选帖子
   - 直到当前关键词下已经没有足够高价值的帖子（主要看时效性和评论数）
7. **当前关键词任务完成后，再进入下一个关键词**
   - 扩展关键词（如 `求票` / `收票` / `没抢到`）用于补召回，而不是替代主查询
8. **整理输出并去重**
   - 汇总所有关键词与页面结果，按统一规则去重后输出
9. **整个过程中加入人类节奏控制**
   - 翻页、点击、进入详情页、滚动评论区之间都应有短暂停顿与小幅动作，避免机械连续操作

也就是说，当前版本的关键链路应理解为：**核心关键词搜索 -> 按时间/回复数筛帖 -> 直接进帖子主页抓完整评论 -> 翻页继续覆盖 -> 扩展关键词补召回 -> 统一去重输出**。

当前像“搜索结果页首页已有 1900+ 评论的大帖”这类场景，应优先进入帖子主页深挖评论；如果最终只抓到极少量 lead，通常说明没有真正执行到高热帖主页评论层，而不是需求本身太少。

### 去重建议
建议分两层去重：

- **lead 级去重（优先）**
  - 首选键：`platform + commenter_uid`
  - 如果没有 uid，则退化为：`platform + commenter_profile_url`
  - 再退化为：`platform + commenter_nickname + normalized_signal_text`

- **帖子内重复评论去重（辅助）**
  - 使用：`source_post_id + commenter_uid + normalized_signal_text`
  - 避免同一用户在同一帖子下因重复抓取被多次记入

推荐保留策略：
- 同一人命中多次时，优先保留：
  1. **时间更新**的记录
  2. **证据更强**的记录（例如明确“求票/收票”优于仅“没抢到”）
  3. **上下文更完整**的记录（详情页评论优于搜索页浅层评论）

这样既能避免同一个人跨关键词、跨页面反复出现，也能尽量保住信息量更高的那条记录。

## 后续演进方向
同一 skill 下继续扩：
- `lead/state`
- `lead/incremental-refresh`
- `chat/send`
- `chat/history`

而不是现在就过早抽象成跨平台 `lead-skill/chat-skill`。

## 更多说明
- 架构：`references/architecture.md`
- 任务定义：`references/task-definition.md`
- 工作流：`references/workflow.md`
- 输出：`references/output-schema.md`
- 工作浏览器：`references/work-browser.md`
