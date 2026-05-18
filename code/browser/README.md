# Browser RPA

这个目录放 CloudPhone 的网页控制方向代码。

当前重点不是做一个一次性微博脚本，而是逐步形成一套可复用的网页 RPA 结构。微博是当前最先跑通、最适合沉淀标准结构的站点样板。

## 当前目录

```text
browser/
  README.md
  runtime/       # 浏览器运行时、profile 等本地状态，不作为源码主线
  weibo-rpa/     # 微博网页 RPA，当前主样板
```

## 当前主线

`weibo-rpa` 里当前只有两条正式业务主线：

```text
Lead:
  scripts/run_lead_task.py
    -> scripts/run_task.py
      -> src/flows/weibo_lead_collect.py

Chat:
  scripts/run_chat_task.py
    -> src/flows/weibo_chat_send.py
```

其他脚本多数属于历史调试、探针、兼容入口或任务框架支撑，不应该被理解为同级主功能。

## 分层约定

`scripts/` 是运行入口层，只负责外部怎么启动能力：

- 解析命令行参数
- 设置默认路径
- 调用 `src` 里的 flow
- 输出 JSON 结果
- 返回进程退出码

`src/flows/` 是业务流程层，负责一件完整业务：

- `weibo_lead_collect.py`：微博 lead 收集
- `weibo_chat_send.py`：微博聊天发送

`src/adapters/` 是站点适配层，封装微博站点能力。

`src/pages/` 是页面对象层，集中管理 selector 和页面动作。

`src/policies/` 是场景策略层，例如微博聊天发送的降频节奏。

`src/core/` 是网页 RPA 基础能力，例如浏览器会话、artifact、输入动作、错误码。

## 迁移原则

旧代码可以继续运行，但新代码按以下规则收口：

- 新业务逻辑进入 `src/flows`、`src/adapters`、`src/pages`、`src/policies` 或 `src/core`。
- `scripts` 只保留薄入口，不继续堆页面逻辑、selector 或业务判断。
- 探针脚本放在 `scripts/probe` 或 `src/probes`，不作为正式业务入口。
- 运行产物放 `runs/`，浏览器状态放 `runtime/`，都不作为源码主线。

## 当前整理方向

短期目标是让 `weibo-rpa` 收敛成清晰的两条能力：

```text
weibo lead collect
weibo chat send
```

等微博网页控制稳定后，再考虑把 `src/core` 中真正跨站点复用的部分上移到 `code/browser` 的公共层。
