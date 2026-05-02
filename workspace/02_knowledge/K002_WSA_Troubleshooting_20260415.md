# K002_WSA_Troubleshooting_20260415

## 1. 故障现象
安装 WSA (Windows Subsystem for Android) 后，点击安卓应用（如 Magisk、设置等）无反应，或弹出“无法启动 Windows 安卓子系统”的错误提示。

## 2. 环境核心要求
在进行高级调试前，必须确保以下两项：
- **Windows 功能**：已启用“虚拟机平台” (`VirtualMachinePlatform`)。
- **BIOS 硬件虚拟化**：主板 BIOS 中的 `Intel Virtualization Technology` 或 `AMD-V` 必须处于 `Enabled` 状态。可以通过任务管理器“性能”页签下的“虚拟化：已启用”来确认。

## 3. 基础工具链部署
WSA 的自动化管理依赖于 ADB (Android Debug Bridge)。
- **安装命令**：`winget install Google.PlatformTools`
- **默认连接地址**：`127.0.0.1:58526`

## 4. 常见排查流程
1. **开发者模式**：在 WSA 设置中勾选“开发者模式”，否则无法通过端口连接。
2. **激活子系统**：若 `adb connect` 提示拒绝连接，通常是因为安卓子系统尚未真正运行。
3. **Issue #593 闪退与 CFG 错误**：
    - **系统要求**：若出现“Make sure Control Flow Guard is turned on”报错，必须确保系统全局 CFG 已开启（在 Exploit Protection 设置中）。
    - **显卡优化（推荐修复）**：在“Windows 设置 > 系统 > 屏幕 > 显示卡”中，添加 `Windows Subsystem for Android` 并将其设置为 **“高性能”**。这通常能解决 GApps 闪退而无需修改安全策略。
4. **安全排除**：将镜像所在根目录加入 Windows Defender 排除项。
5. **GPU 驱动**：某些旧版本驱动可能导致子系统无法渲染，建议更新显卡驱动。
