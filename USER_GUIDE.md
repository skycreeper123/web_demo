# Prompt Tool Web Demo 使用说明

## 1. 使用前准备

建议先确认：

- 你在 Windows 或 Linux 环境下运行
- 已安装 Python
- 可以打开本地浏览器

如果使用项目内虚拟环境，推荐：

```text
Windows: .venv\Scripts\python.exe
Linux:   .venv/bin/python
```

如果你要使用视频剪辑工作台，先安装依赖：

Windows:

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

Linux:

```bash
.venv/bin/python -m pip install opencv-python imageio-ffmpeg
```

## 2. 启动方式

### 命令行启动

Windows:

```powershell
python .\backend\app\main.py
```

Linux:

```bash
python3 ./backend/app/main.py
```

启动后打开：

```text
http://127.0.0.1:8000
```

### 平台启动器

Windows：

- 双击 `PromptToolLauncher.exe`

Linux：

```bash
bash ./run_linux.sh
```

## 3. 页面结构

首页有两个入口：

- `Prompt 生成工作台`
- `视频剪辑工作台`

顶部导航包含：

- `首页`
- `返回`
- `退出`

## 4. Prompt 生成工作台

Prompt 工作台包含 3 个子模块：

- 图片 -> I2V Prompt
- 图片 -> 图生图 Prompt
- 视频 -> 视频编辑 Prompt

它们共用一套页面结构：

1. 选择输入
2. 配置 API
3. 编辑 Prompt 配置
4. 运行并查看结果

### 4.1 图片 -> I2V Prompt

适合批量生成图生视频前置 Prompt。

输入方式：

- 选择图片
- 拖拽图片
- 选择图片文件夹
- 填写图片 URL

常用配置：

- `API Key`
- `Base URL`
- `Model`
- `输出目录`
- `use_mock`
- `overwrite`

输出文件通常包括：

- `*.prompt.json`
- `*.prompt.txt`
- `prompts.csv`

### 4.2 图片 -> 图生图 Prompt

适合批量生成高保真、小改动的编辑 Prompt。

输入方式与图片模块一致：

- 图片文件
- 图片文件夹
- 图片 URL

输出文件通常包括：

- `*.prompt.json`
- `*.prompt.txt`
- `prompts.csv`

### 4.3 视频 -> 视频编辑 Prompt

适合根据视频和参考图生成视频编辑 Prompt。

推荐顺序：

1. 导入视频
2. 导入参考图
3. 点击 `扫描`
4. 确认匹配结果
5. 点击 `开始`

当前匹配规则是固定同名规则。

例如：

```text
a001.mp4
```

会尝试匹配：

- `a001.*`
- `a001_1.*`
- `a001_2.*`

说明：

- 这个模块不是视频剪辑器
- 它更适合“视频 + 参考图 -> Prompt”的批量生成流程

## 5. 视频剪辑工作台

视频剪辑工作台直接读取本地目录，不走浏览器上传。

### 5.1 处理模式

有两种模式：

- `单文件夹裁切`
- `双文件夹合并`

单文件夹裁切：

- 按固定预设批量处理一个目录中的视频

双文件夹合并：

- 将两个目录中的视频按排序后一一配对并顺序拼接

### 5.2 剪辑预设

当前已集成的常用预设包括：

- 保留前 50%（ffmpeg）
- 保留前 50%（OpenCV）
- 保留前 30%
- 保留前 70%
- 保留前 3 秒 / 5 秒 / 7 秒
- 保留后 3 秒 / 5 秒 / 7 秒
- 保留后 30% / 50% / 70%
- 双文件夹顺序合并

简单理解：

- `ffmpeg`
  - 更适合快速视频处理
- `OpenCV`
  - 更适合逐帧处理

### 5.3 输入路径

单文件夹模式填写：

- `视频输入文件夹`

双文件夹模式填写：

- `文件夹 A`
- `文件夹 B`

支持的常见格式：

- `mp4`
- `mov`
- `avi`
- `mkv`
- `webm`

### 5.4 输出目录

建议使用相对路径，例如：

```text
output/video_clip
```

每次运行都会自动创建新的时间戳目录。

### 5.5 结果内容

剪辑任务通常会生成：

- 输出视频
- 预览帧
- `manifest.json`
- `summary.csv`

## 6. 配置文件

### API 配置

文件：

- `backend/api_config.json`

包含 3 个模块：

- `image`
- `image_edit`
- `video`

字段包括：

- `api_key`
- `base_url`
- `model`
- `output_dir`
- `use_mock`
- `overwrite`

### Prompt 配置

文件：

- `backend/image_prompt_config.json`
- `backend/image_edit_prompt_config.json`
- `backend/video_prompt_config.json`

字段包括：

- `system_prompt`
- `user_text`
- `mock_result`

## 7. 常见问题

### 为什么没填 API Key 也能运行

因为支持 `mock` 模式。

只要满足以下任一条件，就会走模拟结果：

- `use_mock = true`
- `API Key` 为空

### 为什么视频模块不等于视频理解或视频剪辑

因为它的目标是生成 Prompt，不是直接做视频编辑。

### 为什么视频剪辑模块跑不动

最常见原因是依赖未安装。

先执行：

Windows:

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

Linux:

```bash
.venv/bin/python -m pip install opencv-python imageio-ffmpeg
```

### 为什么 Linux 下目录选择体验不一致

因为前端使用了 `webkitdirectory`。

建议：

- 使用 Chrome 或 Edge

### 为什么“打开目录”没有反应

Linux 下通常是因为：

- 缺少 `xdg-open`
- 没有关联文件管理器

## 8. 文档入口

- 项目总览：[README.md](./README.md)
- 技术实现：[TECHNICAL.md](./TECHNICAL.md)
