# 输出结构

当前输出目标是：**便于后续智能体逐个触达的微博潜客表**。

## 建议主表字段
- `platform`：固定为 `weibo`
- `event_query`：原始任务输入，如 `周杰伦 南宁 演唱会`
- `normalized_event_name`：规范化后的演出名
- `event_city`：城市
- `inferred_date`：可推断的日期
- `inferred_venue`：可推断的场馆

### 用户信息
- `commenter_nickname`：昵称
- `commenter_unique_id`：微博 uid 或其他稳定唯一标识
- `commenter_profile_url`：用户主页链接
- `commenter_homepage_hint`：若主页链接暂拿不到，可先保留可定位线索

### 来源帖子信息
- `source_post_id`：来源帖子 ID
- `source_post_url`：来源帖子链接
- `source_post_title`：帖子标题或摘要
- `source_post_author`：发帖人昵称
- `source_post_published_at`：发帖时间

### 触发信号
- `signal_text`：触发判定的具体文本
- `signal_type`：`comment` / `reply` / `post`
- `signal_url`：信号所在链接
- `signal_published_at`：信号发布时间

### 判定结果
- `intent_label`：如 `明确求票`、`高意向想看`、`疑似求票`
- `confidence`：0-1
- `evidence`：证据列表，可多条
- `recommended_action`：`dm_first` / `reply_first` / `skip`
- `outreach_angle`：建议从什么角度切入触达
- `risk_flags`：如 `疑似黄牛`、`语义模糊`、`缺少唯一ID`
- `needs_agent_review`：是否需要 agent 复审
- `review_reason`：需要复审的原因
- `captured_at`：抓取时间

## 建议附加输出
除主表外，还建议输出：
- `raw_posts.jsonl`：候选帖子列表
- `raw_comments.jsonl`：原始评论记录
- `review_queue.jsonl`：需要 agent 介入判断的评论队列
- `summary.json`：本轮搜索关键词、遍历帖子数、评论数、入选 lead 数、复审数
