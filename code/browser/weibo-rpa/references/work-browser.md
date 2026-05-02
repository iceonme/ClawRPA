# 工作浏览器 / CDP 常驻说明

## 目标
为微博这类强登录、强风控场景准备一个长期驻留的工作浏览器，供 Playwright 通过 CDP 附着使用。

## 推荐目录
默认工作目录：
- `runtime/chrome-workbench/profile/`

## 推荐端口
默认 CDP 端口：
- `9222`

## 推荐流程
1. 运行 `scripts/launch_work_chrome.ps1`
2. 手工在该浏览器中登录微博
3. 保持该浏览器开启，不要关闭
4. 运行 `python scripts/check_cdp.py`
5. 运行 `python scripts/attach_playwright.py`
6. 确认 attach 正常后，再继续微博搜索与评论探测

## 注意事项
- 建议使用单独 profile，不要与日常浏览器混用
- 可在该浏览器里手工登录、过验证码、打开目标页面
- 不建议在 agent 自动操作同一 tab 时同时频繁人工点击
- 如果端口已被其他 Chrome 使用，启动脚本会直接复用现有 CDP 端口

## 脚本说明
### `scripts/launch_work_chrome.ps1`
启动一个带固定 `user-data-dir` 和固定 CDP 端口的 Chrome。

### `scripts/check_cdp.py`
检查 `json/version` 和 `json/list` 是否可读，并列出当前 tabs。

### `scripts/attach_playwright.py`
用 Playwright `connect_over_cdp()` 附着到该浏览器，并输出当前 contexts/pages 摘要。
