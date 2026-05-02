# 任务定义

## 当前目标（微博版 / lead v1）
输入通常是一句类似：
- `周杰伦 南宁 演唱会`
- `林俊杰 福州 演唱会`
- `时代少年团 广州`

系统当前将其视为一个**微博 lead 查询任务**：

1. 先使用 `event_query` 本身作为核心查询，进入微博搜索结果页
2. 在搜索结果页按**时间**与**回复数/评论数**筛选高价值候选帖子
3. 对候选帖子直接点击进入帖子主页 / 详情页
4. 在详情页中获取更完整的评论区，并抽取潜在购票 lead
5. 处理完当前页的高价值帖子后，继续点击搜索结果底部下一页
6. 当当前关键词下已没有足够高价值的帖子时，再进入扩展关键词补召回
7. 汇总、去重并输出结构化潜客结果，供后续人工筛选或未来 `chat` 子能力消费

> 当前版本重点是：**核心关键词宽召回、详情页评论深挖、分页覆盖、统一去重输出**。

---

## 推荐输入字段
- `event_query`：用户输入的演出查询短语
- `platforms`：当前固定为 `weibo`
- `search_keywords`：额外搜索关键词，可为空；当前推荐先跑 `event_query` 主查询，召回不足时再补扩展关键词
- `inferred_date`：已知演出日期，可选
- `inferred_venue`：已知场馆，可选
- `max_posts_per_platform`：最多遍历多少帖子
- `min_comment_count`：进入详情页深挖前，搜索结果页候选帖子建议满足的最小回复数/评论数阈值
- `max_comments_per_post`：每个帖子主页最多抽取多少条评论，当前版本建议作为主产出路径的重要参数
- `max_nested_comments_per_post`：楼中楼预留字段
- `max_leads`：最多输出多少条潜客
- `allow_agent_review`：是否允许对模糊样本交给 agent 复审
- `output_dir`：输出目录

---

## 当前输出目标
至少输出一份潜客列表，每行建议包含：
- 昵称
- 唯一 ID（微博 uid）
- 用户主页链接
- 来源帖子 ID / URL
- 触发判定的具体正文文本
- 判定标签
- 证据摘要
- 建议触达方式
- 是否需要 agent 复审

---

## 当前不做
- 自动私信
- 自动关注
- 自动点赞
- 热度分析
- 多平台统一编排

这些将在后续阶段分别进入：
- `weibo-rpa/chat`
- 独立的 heat-analysis / orchestrator 设计

---

## 去重原则（建议）
### Lead 主键
优先使用以下顺序：
1. `platform + commenter_uid`
2. `platform + commenter_profile_url`
3. `platform + commenter_nickname + normalized_signal_text`

### 帖子内重复保护
同一帖子内建议使用：
- `source_post_id + commenter_uid + normalized_signal_text`

### 保留哪条
当同一人有多条候选记录时，优先保留：
1. 时间更新的
2. 意图更明确的
3. 评论上下文更完整的
4. 详情页来源的
