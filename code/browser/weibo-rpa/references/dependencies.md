# 依赖说明

这个 skill 依赖 Python + Playwright 运行。

## 当前约定
- 如果机器上已经安装并可正常使用 Playwright，则可直接继续配置与实现
- 如果机器上尚未安装，则需要先完成依赖安装，再运行本 skill

## 基础依赖
- Python 3.10+
- Playwright

## 推荐安装步骤

### 1. 安装 Python 依赖
如果后续项目提供 `requirements.txt`：

```bash
pip install -r requirements.txt
```

如果使用 `pyproject.toml`：

```bash
pip install -e .
```

### 2. 安装 Playwright Python 包
```bash
pip install playwright
```

### 3. 安装浏览器二进制
```bash
playwright install
```

如果只需要 Chromium，也可以：

```bash
playwright install chromium
```

## 对 skill 使用者的建议
- 先执行一次 Playwright 安装检查
- 确认 `python` 与 `playwright` 命令可用
- 如涉及真实登录态、profile 或持久会话，再按具体任务说明补充配置

## 后续建议
当实现进入可运行阶段后，建议补齐：
- `requirements.txt` 或在 `pyproject.toml` 中写明正式依赖
- 一份最小可运行的安装与验证说明
- 一个 `run_probe.py` 的依赖检查逻辑
