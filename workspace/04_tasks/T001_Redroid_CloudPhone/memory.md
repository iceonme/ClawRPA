# T001 memory — Redroid 云手机方案

> 开始：2026-05-18 | 归档：2026-05-19

## 2026-05-18

### 环境搭建
- ADB v1.0.41 (34.0.5-debian)
- Docker v29.1.3
- scrcpy v3.3.4

### Redroid 容器部署
最终可用配置：
```bash
echo "Tonghua9527_" | sudo -S docker run -d --privileged \
  --name redroid-ticketing-01 \
  -p 5555:5555 \
  -v /home/zen952727/dev/ClawRPA/workspace/01_data/redroid:/data \
  redroid-fixed:ndk \
  androidboot.redroid_width=1080 \
  androidboot.redroid_height=1920 \
  androidboot.redroid_dpi=480 \
  androidboot.redroid_gpu_mode=guest
```

本地镜像：
| 镜像 | 说明 |
|------|------|
| redroid-fixed:ndk | ✅ 可用：libndk_translation + binder 修复 + 大麦已装 |
| redroid-fixed:hidden | release-keys + user build type |
| redroid-fixed:magisk_arm2 | Magisk 尝试版（未完成） |
| redroid/redroid:11.0.0-latest | 原始官方镜像 |

## 2026-05-19

### Binder 模块踩坑
- **Kernel 7.0 + binderfs**: `mknod` 创建的 /dev/binder 在 binderfs 下无效 → 需符号链接指向 /dev/binderfs/binder
- **宿主机重启后 binder 模块不自动加载** → 需配置 `/etc/modules-load.d/redroid.conf`
- 修复脚本：
```bash
rm -f /dev/binder /dev/hwbinder /dev/vndbinder
ln -sf /dev/binderfs/binder /dev/binder
ln -sf /dev/binderfs/hwbinder /dev/hwbinder
ln -sf /dev/binderfs/vndbinder /dev/vndbinder
stop; sleep 2; start
```

### Android 13 不兼容
redroid:13.0.0-latest exit 129，回退到 11.0.0

### houdini vs libndk_translation
- houdini（libnb.so）：有 linker namespace bug → /system/lib64/arm64/nb/libtcb.so 加载失败 → 系统无法启动
- libndk_translation.so：可用 ✅

### 大麦 App 闪退分析（关键发现 🔑）
**根因：阿里安全 SDK 反模拟器检测**
- 崩溃：SIGSEGV SEGV_ACCERR（内存权限错误），不是 SIGILL（非法指令）
- 调用栈：`com.ali.mobisecenhance.ld.BridgeAppMini`
- 触发时机：点击隐私协议「同意」按钮后
- 暴露标志：ro.kernel.qemu=1、ro.debuggable=1、ro.build.tags=test-keys

**尝试过的修复（全部失败）：**
| 方法 | 结果 |
|------|------|
| 修改 build.prop → release-keys + user | ❌ ro.qemu/debuggable 无法运行时改 |
| Magisk 安装（magiskinit 替换 init） | ❌ Text file busy，需容器停止后找 overlay upperdir 替换 |
| 切换 native bridge（houdini → ndk） | ❌ 仍然闪退 |
| 切换 GPU 模式 | ❌ 无关 |

### Magisk 安装尝试
| 方法 | 结果 |
|------|------|
| x86_64 magiskboot/magiskinit | ❌ Illegal instruction |
| ARM64 magiskboot（通过 native bridge） | ✅ 可执行 |
| ARM64 magiskinit 替换 init | ❌ Text file busy（运行中） |
| Docker 层替换 init | ❌ 层路径不稳定 |
| init.rc 服务启动 daemon | ❌ magiskinit 只作为 PID 1 工作 |
| 唯一可行路径：容器停止 → overlay upperdir → 替换 init → 启动 | ⬜ 未验证 |

### 验证结论
- 简单 Android App 可在 ReDroid 上正常运行 → 容器本身正常
- 只有大麦等含阿里安全 SDK 的 App 闪退
- **结论：反模拟器检测不可绕过 → 转向真机方案**
