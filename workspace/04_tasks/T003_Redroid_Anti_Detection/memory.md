# T003 memory — Redroid 风控绕过与深度伪装

> 开始：2026-05-20

## 2026-05-20

### 任务创建
- 从 T001 拆分出来的深度伪装预研任务
- 当前仅方案确定，未开始实施
- T001 阶段的踩坑记录全部可用

### 来自 T001 的关键教训
- 阿里安全 SDK 通过 SIGSEGV SEGV_ACCERR（内存权限错误）崩溃，不是 SIGILL
- 调用栈经过 `com.ali.mobisecenhance.ld.BridgeAppMini`（阿里安全桥）
- 触发时机：点击隐私协议「同意」按钮后
- 暴露标志：ro.kernel.qemu=1、ro.debuggable=1、ro.build.tags=test-keys
- build.prop 可改 release-keys + user，但 ro.qemu/debuggable 无法运行时改
- Magisk 安装需容器停止后找 overlay upperdir 替换 init
