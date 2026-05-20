# T003 board — Redroid 风控绕过与深度伪装

> **状态：** 🔵 verifying（预研中）
> **更新：** 2026-05-20

## 子任务

| # | 任务 | 状态 | 产出/备注 |
|---|------|------|-----------|
| 3.1 | 提取真实手机指纹 | ⬜ todo | `device_fingerprint.json` |
| 3.2 | 修改镜像构建脚本注入属性 | ⬜ todo | 修改后的 Dockerfile 或启动注入脚本 |
| 3.3 | Magisk 环境搭建 | ⬜ todo | 解决 `Text file busy` 限制，成功挂载 Magisk |
| 3.4 | Shamiko & LSPosed 模块安装 | ⬜ todo | Zygisk 成功激活，模块就绪 |
| 3.5 | 验证大麦网绕过 | ⬜ todo | 成功进入大麦首页，无闪退 |

## 当前进展

- 方案已确定（四层伪装架构）
- 尚未开始实质实施
- 前提条件：安装 NVIDIA 官方驱动以改善 redroid 兼容性（目前 nouveau 开源驱动有限）

## 踩坑记录

- **T001 阶段已有教训：** 阿里安全 SDK 检测能力极强，ro.kernel.qemu、ro.debuggable 等属性暴露即死
- **Magisk 安装卡 Text file busy** — 容器内 init 无法在运行时替换，需停止容器后找 overlay upperdir 替换
