# T003 — Redroid 云手机风控绕过与深度伪装

> **方案：** 针对 T001 大麦安全 SDK 闪退问题的深度攻防预研
> **创建：** 2026-05-20 | **负责人：** TIX1号
> **前置：** T001_Redroid_CloudPhone（已归档）
> **状态跟踪：** `board.md` | **过程记忆：** `memory.md`

---

## 目标

通过深度修改 Android 系统属性、挂载 Magisk 框架及反检测模块（Shamiko、HideMyApplist 等），抹除 Redroid 的容器及模拟器特征，实现大麦网等高防 App 的平稳运行。

## 方案架构

四层防御突破：

```
Layer 1: 基础指纹伪装       ← build.prop 改真机型号、抹除 QEMU/Test-keys
Layer 2: 底层权限接管       ← Magisk + Zygisk
Layer 3: 反检测屏蔽模块     ← Shamiko（隐藏 Root）+ HideMyApplist（隔离包名读取）
Layer 4: 物理传感器欺骗     ← Xposed 模块伪造电池、陀螺仪、Wi-Fi（备选）
```

## 已知问题

- 阿里安全 SDK 检测能力极强，ro.kernel.qemu、ro.debuggable 等属性暴露即闪退
- Magisk 安装卡 `Text file busy` — 容器内 init 运行时无法替换

## 关联

- T001: 前置任务（提供了完整踩坑记录和崩溃分析）
- I004: 真机自动化方案决策（本任务是其 Redroid 探索方向的延伸）
