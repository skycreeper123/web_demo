# Prompt Tool Web Demo

`web_demo` 是一个本地运行的 Prompt 生成 Demo，用来批量生成两类结果：

- 图片 -> I2V Prompt
- 视频 + 参考图 -> 视频编辑 Prompt

它目前是一个单机、本地 Web 工具，不依赖数据库，也没有前后端分离构建流程。前端使用原生 `HTML + CSS + JavaScript`，后端使用 Python 标准库 HTTP 服务。

## 当前功能

- 图片模块：
  - 批量导入图片
  - 生成中英双语 I2V Prompt
  - 独立保存图片模块的 Prompt 配置
  - 独立保存图片模块的 API 配置
- 视频模块：
  - 批量导入视频和参考图
  - 先做同名匹配预览，再生成视频编辑 Prompt
  - 独立保存视频模块的 Prompt 配置
  - 独立保存视频模块的 API 配置
- 通用能力：
  - 支持 `mock` 模式
  - 每次任务输出 `json`、`txt`、`csv`
  - 输出目录支持“相对路径优先”
  - 支持一键启动器 `PromptToolLauncher.exe`

## 当前技术实现

- 前端：`frontend/index.html`、`frontend/style.css`、`frontend/app.js`
- 后端入口：`backend/app/main.py`
- 配置层：`backend/app/core/config.py`
- LLM 调用层：`backend/app/core/llm_client.py`
- 图片生成逻辑：`backend/app/services/prompt_generator.py`
- 视频匹配逻辑：`backend/app/services/video_matcher.py`
- 视频生成逻辑：`backend/app/services/video_prompt_generator.py`
- 输出写入工具：`backend/app/utils/file_writer.py`

## 一个关键说明

视频模块当前不是“原生视频理解接口”方案。

它的实际实现是：

1. 前端先准备视频首帧或抽取帧数据。
2. 后端把“1 张视频帧 + 1 到 2 张参考图”一起发给模型。
3. 调用方式仍然是 OpenAI-compatible `POST /chat/completions` 多图输入。

所以它本质上是“多图理解生成视频编辑 Prompt”，而不是把整段视频文件直接上传给模型做原生视频语义理解。

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
    video_prompt_config.json
    outputs/
      image/
      video/
    app/
      main.py
      core/
        config.py
        llm_client.py
      services/
        prompt_generator.py
        video_matcher.py
        video_prompt_generator.py
      utils/
        file_writer.py
        image_loader.py
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

## 配置文件

### API 配置

路径：

- `backend/api_config.json`

结构：

```json
{
  "image": {
    "api_key": "",
    "base_url": "https://apinebula.ai/v1",
    "model": "Prompt",
    "output_dir": "outputs/image",
    "use_mock": true,
    "overwrite": false
  },
  "video": {
    "api_key": "",
    "base_url": "https://apinebula.ai/v1",
    "model": "Prompt",
    "output_dir": "outputs/video",
    "use_mock": true,
    "overwrite": false
  }
}
```

补充说明：

- `api_config.json` 的默认示例值会写成 `https://apinebula.ai/v1`
- 运行时如果 `base_url` 命中这个旧地址，后端会自动规范为 `https://api.yhlxj.ai/v1` 后再发起请求

### Prompt 配置

- 图片模块：`backend/image_prompt_config.json`
- 视频模块：`backend/video_prompt_config.json`

每个文件都包含：

- `system_prompt`
- `user_text`
- `mock_result`

## 路径策略

当前项目已经实现“相对路径优先”。

例如 `api_config.json` 里的：

- `outputs/image`
- `outputs/video`

会在运行时被解析为相对于 `backend/` 的输出目录。这样整体移动 `web_demo` 目录时，默认输出路径仍然有效。

## 文档入口

- 使用说明：[USER_GUIDE.md](./USER_GUIDE.md)
- 技术文档：[TECHNICAL.md](./TECHNICAL.md)

## 当前限制

- 没有数据库，任务状态只保存在内存中
- 没有登录、权限、多人协作能力
- 没有失败重跑、暂停/继续、历史任务管理
- 视频匹配目前只支持固定同名规则
- 没有结果页二次编辑能力
- LLM 调用层没有重试、限流和多供应商适配层
