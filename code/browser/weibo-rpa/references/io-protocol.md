# I/O 协议约定

本 skill 按 OpenClaw 官方 `exec + process` 后台任务模型设计，而不是按“长期裸 stdin/stdout 对话协议”设计。

## 设计原则
- 脚本可以作为长任务运行，但默认不是持续聊天式进程
- 大内容不直接输出到 stdout，而是落盘到 `runs/` 下
- stdout 只输出少量、结构化、对 agent 真正有价值的信息
- stderr 用于调试日志、运行细节、报错堆栈
- 任务完成后，由 agent 按需读取结果文件，而不是依赖 stdout 承载全部内容

## 为什么这样设计
根据 OpenClaw 官方文档：
- `exec` 负责启动命令
- 长任务会转为后台 session
- `process` 负责 `poll / log / write / kill` 等管理动作
- session 仅保存在内存中，不落盘
- 进程输出只有在被 `process poll/log` 读取时，才会进入工具结果与会话记录
- `process` 作用域是当前 agent，只能看到本 agent 自己启动的后台 session

因此，skill 侧最稳妥的模式是：
- 用脚本完成真实工作
- 用文件保存真实产物
- 用 stdout 输出里程碑与结果索引

## stdout 允许输出的消息类型
推荐一行一个 JSON。

### 1. 状态消息
```json
{"type":"status","stage":"search_weibo","message":"微博搜索完成","post_count":20}
```

### 2. 产物消息
```json
{"type":"artifact","name":"weibo_comments_raw","path":"runs/task_001/weibo/comments_raw.json"}
```

### 3. 结果消息
```json
{"type":"result","lead_count":18,"output_path":"runs/task_001/merged/leads.json"}
```

## stderr 用途
stderr 仅用于：
- 调试日志
- 页面操作细节
- 重试信息
- 详细错误堆栈

这些内容默认不给 agent 当核心输入使用。

## 不推荐的做法
- 不要把整页 DOM、整批评论全文直接 print 到 stdout
- 不要频繁输出低价值进度，如每 1 秒输出一次 alive
- 不要假设 OpenClaw 会自动把 stdout JSON 当作系统协议完整解析
- 不要把 session 内存日志当作最终产物存储

## 推荐的任务执行模式
1. agent 通过脚本入口启动任务
2. 脚本把大内容写入 `runs/<task-id>/<platform>/...`
3. 脚本在关键里程碑输出少量 JSON 到 stdout
4. 任务结束后输出最终结果路径
5. agent 再按需读取结果文件或合并结果

## 关于 stdin
第一版 lead-discovery 默认按“少交互任务”设计：
- 以一次启动、执行、落盘、结束为主
- 默认不依赖脚本在运行中持续等待 agent 指令
- 只有在后续确实出现“中途需要 agent 决策”的场景时，才扩展 stdin 监听能力
