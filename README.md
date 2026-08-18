# Prompt Tool Web Demo

`web_demo` 是一个本地运行的素材处理与 Prompt 生成工具，当前包含两组能力：

- `Prompt 生成工作台`
  - 图片 -> I2V Prompt
  - 图片 -> 图生图 Prompt
  - 视频 + 参考图 -> 视频编辑 Prompt
- `视频剪辑工作台`
  - 单文件夹批量裁切
  - 双文件夹顺序合并

它是一个单机、本地 Web Demo，不依赖数据库，也没有前后端分离构建流程。前端使用原生 `HTML + CSS + JavaScript`，后端使用 Python 标准库 HTTP 服务。

## 当前功能

- Prompt 工作台：
  - 统一入口切换 3 个 Prompt 子模块
  - 每个子模块保留独立的输入区、配置区、运行区和输出区
  - 支持 `mock` 模式
  - 支持输出 `json`、`txt`、`csv`
- 图片 -> I2V Prompt：
  - 批量导入图片
  - 生成中英双语 I2V Prompt
  - 读写 `backend/image_prompt_config.json`
  - 读写 `backend/api_config.json` 中的 `image` 配置
- 图片 -> 图生图 Prompt：
  - 批量导入图片
  - 生成高保真、最小改动的图生图编辑 Prompt
  - 读写 `backend/image_edit_prompt_config.json`
  - 读写 `backend/api_config.json` 中的 `image_edit` 配置
- 视频 -> 视频编辑 Prompt：
  - 批量导入视频和参考图
  - 先做同名匹配预览，再生成视频编辑 Prompt
  - 读写 `backend/video_prompt_config.json`
  - 读写 `backend/api_config.json` 中的 `video` 配置
- 视频剪辑工作台：
  - 集成 `batch_editing` 目录中的批量裁切与双文件夹合并能力
  - 支持前/后几秒、前/后百分比、前半段裁切、双文件夹顺序合并
  - 使用本地路径直接处理视频，不走浏览器大文件上传
  - 每次任务输出独立时间戳目录、`manifest.json`、`summary.csv`
- 通用能力：
  - 输出目录支持相对路径优先
  - 支持一键启动器 `PromptToolLauncher.exe`
  - 项目内 `.venv` 已可承载视频处理依赖

## 当前技术实现

- 前端：`frontend/index.html`、`frontend/style.css`、`frontend/app.js`
- 后端入口：`backend/app/main.py`
- 配置层：`backend/app/core/config.py`
- LLM 调用层：`backend/app/core/llm_client.py`
- 图片 Prompt 生成：`backend/app/services/prompt_generator.py`
- 图生图 Prompt 生成：`backend/app/services/image_edit_prompt_generator.py`
- 视频匹配：`backend/app/services/video_matcher.py`
- 视频 Prompt 生成：`backend/app/services/video_prompt_generator.py`
- 视频剪辑服务：`backend/app/services/video_clip_service.py`
- 输出写入工具：`backend/app/utils/file_writer.py`

## 两个关键说明

### 1. 视频 Prompt 模块不是“原生整视频理解”

视频 Prompt 模块当前不是把整段视频直接上传给模型，而是：

1. 前端准备视频数据与参考图。
2. 后端组织“1 段视频输入 + 1 到 3 张参考图”的生成任务。
3. 调用 OpenAI-compatible `POST /chat/completions` 完成 Prompt 生成。

所以它本质上仍然是面向 Prompt 生成的多媒体理解流程，而不是独立的视频编辑引擎。

### 2. 视频剪辑模块是本地批处理，不依赖远程模型

视频剪辑工作台直接读取你机器上的本地目录，调用项目内 Python 依赖执行：

- `opencv-python`
- `imageio-ffmpeg`

其中 ffmpeg 能力优先来自项目 `.venv` 内的 `imageio-ffmpeg` 自带二进制，不要求系统 PATH 里预装 `ffmpeg`。

## 目录结构

```text
web_demo/
  frontend/
    index.html
    style.css
    app.js
  backend/
    api_config.json
    image_prompt_config.json
    image_edit_prompt_config.json
    video_prompt_config.json
    app/
      main.py
      core/
        config.py
        llm_client.py
      services/
        prompt_generator.py
        image_edit_prompt_generator.py
        video_matcher.py
        video_prompt_generator.py
        video_clip_service.py
      utils/
        file_writer.py
        image_loader.py
  batch_editing/
    merge_two_folders_pairwise.py
    video_batch_half_keep.py
    video_batch_half_keep_opencv.py
    video_batch_keep_30pct.py
    video_batch_keep_70pct.py
    video_batch_keep_first_3s.py
    video_batch_keep_first_5s.py
    video_batch_keep_first_7s.py
    video_batch_keep_last_3s.py
    video_batch_keep_last_5s.py
    video_batch_keep_last_7s.py
    video_batch_keep_tail_30pct.py
    video_batch_keep_tail_50pct.py
    video_batch_keep_tail_70pct.py
  output/
  .venv/
  PromptToolLauncher.cs
  PromptToolLauncher.exe
  build_launcher.ps1
  README.md
  USER_GUIDE.md
  TECHNICAL.md
```

## 启动方式

### 方式一：直接启动 Python 服务

在 `web_demo` 根目录运行：

```powershell
python .\backend\app\main.py
```

然后在浏览器打开：

```text
http://127.0.0.1:8000
```

### 方式二：双击一键启动器

项目根目录已包含：

- `PromptToolLauncher.exe`

它会：

1. 以自身所在目录作为基准定位项目路径。
2. 优先尝试 `.venv\Scripts\python.exe`。
3. 如果虚拟环境不可用，再尝试系统 `python` 或 `py -3`。
4. 等待 `http://127.0.0.1:8000/` 就绪后自动打开浏览器。

## 本地依赖安装

如果你希望在当前目录内补齐视频处理依赖，推荐安装到项目自带 `.venv`：

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

说明：

- `opencv-python` 用于大多数批量裁切与视频合并
- `imageio-ffmpeg` 提供项目内可用的 ffmpeg 二进制
- 一键启动器会优先使用这个 `.venv`，因此装在这里就能被 app 直接使用

## 配置文件

### API 配置

路径：

- `backend/api_config.json`

结构包含 3 个 Prompt 模块：

```json
{
  "image": {
    "api_key": "",
    "base_url": "https://apinebula.ai/v1",
    "model": "Prompt",
    "output_dir": "output",
    "use_mock": true,
    "overwrite": false
  },
  "image_edit": {
    "api_key": "",
    "base_url": "https://apinebula.ai/v1",
    "model": "Prompt",
    "output_dir": "output",
    "use_mock": true,
    "overwrite": false
  },
  "video": {
    "api_key": "",
    "base_url": "https://apinebula.ai/v1",
    "model": "Prompt",
    "output_dir": "output",
    "use_mock": true,
    "overwrite": false
  }
}
```

补充说明：

- `api_config.json` 的默认示例值仍可能写成 `https://apinebula.ai/v1`
- 运行时如果命中这个旧地址，后端会自动规范为 `https://api.yhlxj.ai/v1` 再发起请求
- 视频剪辑工作台不依赖这个 API 配置文件

### Prompt 配置

- 图片模块：`backend/image_prompt_config.json`
- 图生图模块：`backend/image_edit_prompt_config.json`
- 视频模块：`backend/video_prompt_config.json`

每个文件都包含：

- `system_prompt`
- `user_text`
- `mock_result`

## 路径策略

当前项目已实现“相对路径优先”。

例如：

- `output`
- `output/video_clip`

会在运行时被解析为相对于项目根目录的真实目录。这样整体移动 `web_demo` 目录时，默认输出路径仍然有效。

## 文档入口

- 使用说明：[USER_GUIDE.md](./USER_GUIDE.md)
- 技术文档：[TECHNICAL.md](./TECHNICAL.md)

## 当前限制

- 没有数据库，任务状态只保存在内存中
- 没有登录、权限、多人协作能力
- 没有失败重跑、暂停/继续、历史任务管理
- 视频匹配目前只支持固定同名规则
- Prompt 结果页没有二次编辑能力
- 视频剪辑模块当前以固定预设为主，暂不支持任意参数化时间轴编辑
- LLM 调用层没有重试、限流和多供应商适配层
