# weibo-rpa 任务记录 / run 模型 / 增量监控建议

日期：2026-04-20

## 放置位置
本条 insight 放在项目 workspace 下：
- `C:\Projects\CloudPhone\workspace\03_insight\weibo-rpa-task-logging-and-run-model.md`

---

## 背景
当前 `weibo-rpa` 已经不再只是一次性脚本试跑，而是在向可重复执行、可复盘、可监控增量的任务系统演进。

用户明确提出：
- 需要考虑任务记录日志怎么做最理想
- 需要支持未来多任务
- 需要支持重复监控（按时间看更新）
- 需要从任务管理工程角度优化

因此，项目不应只保留 `summary.json + leads.jsonl` 这一层，而应建立完整的 task / run / event / state 模型。

---

## 核心概念

### 1. task_id
表示一个“长期任务身份”，不随单次执行改变。

示例：
- `weibo_lead:郑州汪苏泷`
- `weibo_lead:蔡依林苏州`

适合表达：
- 某个核心关键词的持续监控任务
- 某个演出 lead 发现任务

### 2. run_id
表示某一次具体执行。

示例：
- `20260420_163012`
- `20260420_220501`

适合表达：
- 某个 task 的一次试跑
- 某次正式采集
- 某次增量刷新

### 3. run status
建议至少支持：
- `running`
- `success`
- `partial_success`
- `failed`
- `cancelled`

其中 `partial_success` 很重要：
- 某些关键词 / 页 / 帖子已经成功处理
- 但中途某个关键词超时或报错
- 不应整体当作完全失败

---

## 推荐的四层记录体系

### 第一层：任务主记录（task/run metadata）
每次 run 都应有一个任务元信息文件，例如 `task.json`。

建议字段：
```json
{
  "task_id": "weibo_lead:郑州汪苏泷",
  "run_id": "20260420_163012",
  "platform": "weibo",
  "task_type": "lead_collect",
  "event_query": "郑州 汪苏泷",
  "keywords": ["郑州 汪苏泷", "郑州 汪苏泷 求票", "郑州 汪苏泷 没抢到"],
  "status": "running",
  "started_at": "2026-04-20T16:30:12+08:00",
  "finished_at": null,
  "max_leads": 30,
  "operator": "scripts/weibo_collect_test_leads.py",
  "entrypoint_version": "git_sha_or_script_version"
}
```

作用：
- 让每次 run 都有正式身份
- 便于以后做列表、检索、回放、统计

---

### 第二层：结构化事件日志（events.jsonl）
这是最关键的日志层。

不要只依赖 stdout 人读文本；应该把执行过程落成结构化事件流。

建议每行一个事件：
```json
{"ts":"...","run_id":"...","level":"info","event":"task_started","event_query":"郑州 汪苏泷"}
{"ts":"...","run_id":"...","level":"info","event":"keyword_started","keyword":"郑州 汪苏泷"}
{"ts":"...","run_id":"...","level":"info","event":"search_page_loaded","keyword":"郑州 汪苏泷","page":1}
{"ts":"...","run_id":"...","level":"info","event":"candidate_post_selected","post_url":"...","reply_count":128,"post_time":"04月20日 12:01"}
{"ts":"...","run_id":"...","level":"info","event":"detail_page_entered","post_url":"..."}
{"ts":"...","run_id":"...","level":"info","event":"lead_extracted","lead_key":"weibo:uid:123","signal_type":"comment"}
{"ts":"...","run_id":"...","level":"warn","event":"goto_timeout","keyword":"郑州 汪苏泷 求票","page":1,"url":"..."}
{"ts":"...","run_id":"...","level":"info","event":"task_finished","status":"partial_success","lead_count":3}
```

建议至少记录的事件类型：
- `task_started`
- `keyword_started`
- `search_page_loaded`
- `candidate_post_selected`
- `candidate_post_skipped`
- `detail_page_entered`
- `detail_page_failed`
- `comment_page_scrolled`
- `lead_extracted`
- `lead_deduped`
- `page_finished`
- `keyword_finished`
- `task_finished`
- `error`

作用：
- 调试
- 回放
- 失败分析
- 监控面板
- 任务审计

---

### 第三层：状态存储（state store）
用于支持断点恢复、重复监控、增量刷新。

建议每个长期 task 都有自己的 state 文件，例如：
- `state/weibo_lead_郑州汪苏泷.json`

示例：
```json
{
  "task_id": "weibo_lead:郑州汪苏泷",
  "last_run_id": "20260420_163012",
  "last_success_at": "2026-04-20T16:35:42+08:00",
  "keywords_state": {
    "郑州 汪苏泷": {
      "last_page_finished": 3,
      "stopped_reason": "completed"
    },
    "郑州 汪苏泷 求票": {
      "last_page_finished": 0,
      "stopped_reason": "goto_timeout"
    }
  },
  "seen_posts": ["post_id_1", "post_id_2"],
  "seen_lead_keys": ["weibo:uid:123", "weibo:uid:456"],
  "last_high_value_post_time": "2026-04-20T12:01:00+08:00"
}
```

作用：
- 下次知道从哪接着跑
- 哪些帖子已经处理过
- 哪些 lead 已经见过
- 哪个关键词经常失败
- 哪些页之后价值明显下降

---

### 第四层：标准化产物层
保留当前已有的结果文件，但升级组织结构。

推荐目录：
```text
runs/
  weibo-lead/
    task-zhengzhou-wangsulong/
      20260420_163012/
        task.json
        events.jsonl
        summary.json
        leads.raw.jsonl
        leads.deduped.jsonl
        pages/
        posts/
        errors/
```

建议产物：
- `task.json`
- `events.jsonl`
- `summary.json`
- `leads.raw.jsonl`
- `leads.deduped.jsonl`
- `pages/*.json`
- `posts/*.json`
- `errors/*.json`

作用：
- 保留运行轨迹
- 支持复盘
- 支持后续做任务管理 UI

---

## 为什么不能只靠 summary.json
因为 `summary.json` 只回答“最后结果是什么”，但未来还需要回答：
- 哪一步失败了
- 哪个关键词失败了
- 当前 run 处理到第几页
- 哪些帖子被选中 / 跳过
- 哪些 lead 是新增，哪些是重复
- 下次应该从哪继续

所以 `summary.json` 只能是汇总层，不够承担任务系统职责。

---

## 多任务场景下的建议

### 1. 区分 task 与 run
一个 task 可以有多次 run。

这使得系统可以支持：
- 手动试跑
- 定时增量刷新
- 失败重跑
- 不同参数版本对比

### 2. 任务调度层需要最少字段
任务队列里建议有：
- `task_id`
- `task_type`
- `platform`
- `event_query`
- `priority`
- `schedule_type`（manual / cron / polling）
- `next_run_at`
- `last_run_status`
- `last_run_id`
- `enabled`

### 3. 同一 task 的重复监控
重复监控时，不应该每次完全全量重扫。

建议优先依赖：
- `last_seen_post_time`
- `seen_posts`
- `seen_lead_keys`

来判断：
- 哪些是新增帖子
- 哪些是新 lead
- 哪些是老帖子里的新增评论/新增命中

---

## 增量监控怎么做更合适

### 1. 新增 lead 与历史 lead 区分
lead 记录中建议有：
- `first_seen_at`
- `last_seen_at`
- `seen_run_ids`
- `hit_count`

这样就能区分：
- 新 lead
- 历史 lead 再次出现
- 历史 lead 信号变强

### 2. 监控输出不只给全量表
未来重复监控时，建议额外输出：
- `new_leads.jsonl`
- `updated_leads.jsonl`
- `unchanged_leads_count`

### 3. 停手逻辑
当前关键词不应无限翻页。

建议停止条件包括：
- 连续 N 页没有高价值帖子
- 帖子整体时效性明显下降
- 评论数普遍低于阈值
- 新增 lead 明显趋近于 0

---

## 去重与跨 run 追踪建议

### 实时去重
当前 run 内：
- 避免同一人 / 同一评论重复入池

### 全局去重
跨 run：
- 识别这个 lead 是否以前出现过

建议字段：
- `first_seen_at`
- `last_seen_at`
- `hit_count`
- `seen_run_ids`

推荐主键顺序：
1. `platform + commenter_uid`
2. `platform + commenter_profile_url`
3. `platform + commenter_nickname + normalized_signal_text`

帖子内保护键：
- `source_post_id + commenter_uid + normalized_signal_text`

同一人多次命中时，优先保留：
1. 时间更新的
2. 意图更明确的
3. 上下文更完整的
4. 详情页来源的

---

## 稳定性建议
这次 `郑州 汪苏泷` 测试暴露出：
- 主查询已能出 comment lead
- 但切到扩展关键词时 `goto` 超时

因此任务系统层应支持：
- `goto` 超时重试
- keyword 级异常捕获
- 单关键词失败不拖垮整个 run
- 最终状态支持 `partial_success`

建议：
- 不要因为一个关键词 timeout 就让整次 run 直接变成 `failed`
- 应记录为：某关键词失败，但已有部分结果成功产出

---

## MVP 级第一步落地建议
如果先做最小工程化升级，建议优先加这 6 项：

1. `task.json`
2. `events.jsonl`
3. `summary.json`（保留）
4. `leads.raw.jsonl`
5. `leads.deduped.jsonl`
6. `state/task_state.json`

并补：
- `partial_success`
- keyword 级异常容错
- run 结束后的统一汇总

---

## 当前结论
未来不应继续把 `weibo-rpa` 只当作“一次性脚本跑完”的模型；更合理的方向是：

**把它建设成一个可重复执行、可恢复、可监控增量、可复盘的任务系统。**

其中优先级最高的是：
1. 结构化事件日志
2. 任务状态持久化
3. task_id / run_id 分层
4. partial_success / retry / resume
5. 跨 run 的新增识别与全局去重
