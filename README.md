# Prompt Tool Web Demo

`web_demo` 是一个本地运行的 Web Demo，当前包含两类能力：

- `Prompt 生成工作台`
  - 图片 -> I2V Prompt
  - 图片 -> 图生图 Prompt
  - 视频 + 参考图 -> 视频编辑 Prompt
- `视频剪辑工作台`
  - 单文件夹批量裁切
  - 双文件夹顺序合并

项目不依赖数据库，也没有前后端构建链。前端使用原生 `HTML + CSS + JavaScript`，后端使用 Python 标准库 HTTP 服务。

## 当前能力

- 3 个 Prompt 子模块统一收口到一个工作台
- 本地视频剪辑模块已集成 `batch_editing` 常用能力
- Prompt 任务支持 `mock` / 真实 API 两种模式
- 输出目录支持相对路径优先
- 视频剪辑优先使用项目内 `.venv` 的 `imageio-ffmpeg`
- 支持 Windows 启动器 `PromptToolLauncher.exe`
- 支持 Linux 启动脚本 `run_linux.sh`

## 快速启动

### 1. 安装视频处理依赖

只在使用视频剪辑工作台时需要：

Windows:

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

Linux:

```bash
.venv/bin/python -m pip install opencv-python imageio-ffmpeg
```

### 2. 启动服务

Windows:

```powershell
python .\backend\app\main.py
```

Linux:

```bash
python3 ./backend/app/main.py
```

浏览器打开：

```text
http://127.0.0.1:8000
```

### 3. 平台启动器

Windows:

- 双击 `PromptToolLauncher.exe`

Linux:

```bash
bash ./run_linux.sh
```

## 目录结构

```text
web_demo/
  frontend/
  backend/
  batch_editing/
  output/
  .venv/
  PromptToolLauncher.cs
  PromptToolLauncher.exe
  run_linux.sh
  README.md
  USER_GUIDE.md
  TECHNICAL.md
```

## 两个关键说明

### 视频 Prompt 模块

它不是“整视频原生理解引擎”，而是：

1. 前端准备视频和参考图
2. 后端组织多媒体输入
3. 调用 OpenAI-compatible 接口生成 Prompt

所以它更适合“批量生成视频编辑 Prompt”，不是视频剪辑器本身。

### 视频剪辑模块

它是本地批处理能力，不依赖远程模型，主要依赖：

- `ffmpeg`
  - 更适合快速视频处理
- `OpenCV`
  - 更适合逐帧处理

当前实现里，ffmpeg 能力优先来自 `.venv` 中的 `imageio-ffmpeg`。

## 平台兼容

- 核心 Web 应用支持 Windows 和 Linux 本地运行
- `打开输出目录` 在 Windows 下使用 `os.startfile`
- `打开输出目录` 在 Linux 下使用 `xdg-open`
- Windows 启动器是 `PromptToolLauncher.exe`
- Linux 推荐使用 `bash ./run_linux.sh`
- 前端目录选择依赖 `webkitdirectory`，Linux 下建议使用 Chrome 或 Edge

## 文档入口

- 使用说明：[USER_GUIDE.md](./USER_GUIDE.md)
- 技术文档：[TECHNICAL.md](./TECHNICAL.md)

## 当前限制

- 没有数据库，任务状态保存在内存中
- 没有历史任务、失败重跑、暂停/继续
- 视频匹配当前只支持固定同名规则
- Prompt 结果页没有二次编辑
- 视频剪辑当前以固定预设为主
- LLM 调用层没有完整的重试、限流、多供应商抽象
