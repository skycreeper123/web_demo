# Prompt Tool Web Demo 技术文档

## 1. 项目定位

`web_demo` 是一个本地运行的轻量单体项目，覆盖两类工作流：

- `Prompt 生成工作台`
- `视频剪辑工作台`

它更偏向个人生产辅助工具，不是完整的线上服务。

## 2. 技术栈

- 前端：原生 `HTML + CSS + JavaScript`
- 后端：Python 标准库 `http.server`
- 通信：本地 JSON API
- 任务执行：内存态任务 + 后台线程
- 模型接口：OpenAI-compatible `chat/completions`
- 本地视频处理：`opencv-python` + `imageio-ffmpeg`

## 3. 目录结构

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
  output/
  .venv/
  PromptToolLauncher.cs
  PromptToolLauncher.exe
  run_linux.sh
```

## 4. 模块划分

### 4.1 前端

前端位于 `frontend/`，主要负责：

- 首页与工作台入口
- Prompt 子模块切换
- 视频剪辑模式切换
- 文件选择 / 拖拽导入
- 配置读取与保存
- 发起生成任务与剪辑任务
- 轮询任务状态
- 展示日志、进度、输出文件

关键文件：

- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`

### 4.2 后端

后端位于 `backend/app/`，主要负责：

- 托管静态页面
- 提供 JSON API
- 维护配置文件
- 创建和更新任务状态
- 调用模型接口
- 执行本地视频批处理
- 输出结果文件

入口文件：

- `backend/app/main.py`

### 4.3 配置层

`backend/app/core/config.py` 负责：

- 默认 API 配置
- 默认 Prompt 配置
- `api_config.json` 的读写
- 3 份 Prompt 配置文件的读写
- 输出目录解析
- 相对路径优先策略
- 旧地址 `apinebula.ai/v1` 到 `https://api.yhlxj.ai/v1` 的兼容规范化

### 4.4 LLM 调用层

`backend/app/core/llm_client.py` 是轻量适配层，当前特点：

- 请求地址：`{base_url}/chat/completions`
- 消息结构：`system` + `user`
- 多媒体输入：URL 或数据内容
- 响应提取：`choices[0].message.content`

它是 OpenAI-compatible 调用，不是完整的多供应商抽象层。

### 4.5 服务层

#### 图片 Prompt

`backend/app/services/prompt_generator.py`

- 处理图片输入
- 读取图片 Prompt 配置
- 在 `mock` / 真实模型之间切换
- 写出 `json`、`txt`、`csv`

#### 图生图 Prompt

`backend/app/services/image_edit_prompt_generator.py`

- 处理图生图输入
- 读取图生图 Prompt 配置
- 在 `mock` / 真实模型之间切换
- 写出 `json`、`txt`、`csv`

#### 视频匹配

`backend/app/services/video_matcher.py`

- 过滤支持的扩展名
- 以主文件名做固定同名匹配
- 输出匹配列表和统计摘要

状态包括：

- `matched`
- `partial_match`
- `missing_reference`
- `naming_conflict`

#### 视频 Prompt

`backend/app/services/video_prompt_generator.py`

- 组织视频和参考图输入
- 生成视频编辑 Prompt
- 写出 `json`、`txt`、`csv`

#### 视频剪辑

`backend/app/services/video_clip_service.py`

- 定义 `CLIP_PRESETS`
- 暴露预设列表
- 执行本地批处理
- 支持单文件夹裁切与双文件夹顺序合并
- 写出 `manifest.json` 和 `summary.csv`

当前预设包括：

- `first_half_ffmpeg`
- `first_half_opencv`
- `first_30pct`
- `first_70pct`
- `first_3s`
- `first_5s`
- `first_7s`
- `last_3s`
- `last_5s`
- `last_7s`
- `tail_30pct`
- `tail_50pct`
- `tail_70pct`
- `merge_pairwise`

## 5. 业务流程

### 5.1 图片 -> I2V Prompt

1. 前端读取图片或图片 URL
2. 后端接收 `images`
3. `use_mock=true` 或 `api_key` 为空时直接使用 `mock_result`
4. 否则调用模型接口
5. 写出 `*.prompt.json`、`*.prompt.txt`、`prompts.csv`

### 5.2 图片 -> 图生图 Prompt

1. 前端读取图片或图片 URL
2. 后端接收 `images`
3. 按图生图 Prompt 配置组装请求
4. 在 `mock` / 真实模型之间切换
5. 写出 `*.prompt.json`、`*.prompt.txt`、`prompts.csv`

### 5.3 视频 -> 视频编辑 Prompt

1. 前端先扫描视频与参考图匹配
2. 仅将可生成项送入生成流程
3. 后端组织视频与参考图的多媒体输入
4. 调用模型接口生成 Prompt
5. 写出 `*.prompt.json`、`*.prompt.txt`、`prompts.csv`

说明：

- 当前不是“整视频原生理解”
- 本质是“视频 + 参考图 -> Prompt”

### 5.4 视频剪辑工作台

1. 前端读取 `/api/clip/presets`
2. 用户选择模式、预设、输入路径、输出目录
3. 前端发起 `POST /api/clip/run`
4. 后端创建 `video_clip` 任务
5. 服务层执行本地批处理
6. 输出视频、预览帧、`manifest.json`、`summary.csv`

## 6. 配置体系

### 6.1 API 配置

文件：

- `backend/api_config.json`

模块：

- `image`
- `image_edit`
- `video`

字段：

- `api_key`
- `base_url`
- `model`
- `output_dir`
- `use_mock`
- `overwrite`

行为：

- 文件不存在时自动生成
- 字段缺失时按默认值补齐
- `output_dir` 按相对路径优先解析
- 视频剪辑模块不依赖这份配置

### 6.2 Prompt 配置

文件：

- `backend/image_prompt_config.json`
- `backend/image_edit_prompt_config.json`
- `backend/video_prompt_config.json`

公共字段：

- `system_prompt`
- `user_text`
- `mock_result`

## 7. 后端 API

### 7.1 静态资源

- `GET /`
- `GET /app.js`
- `GET /style.css`

### 7.2 配置接口

- `GET /api/config`
- `GET /api/prompt-config/image`
- `POST /api/prompt-config/image`
- `GET /api/prompt-config/image_edit`
- `POST /api/prompt-config/image_edit`
- `GET /api/prompt-config/video`
- `POST /api/prompt-config/video`
- `GET /api/runtime-config/image`
- `POST /api/runtime-config/image`
- `GET /api/runtime-config/image_edit`
- `POST /api/runtime-config/image_edit`
- `GET /api/runtime-config/video`
- `POST /api/runtime-config/video`

### 7.3 Prompt 接口

- `POST /api/generate`
- `POST /api/generate/image-prompt`
- `POST /api/generate/image-edit-prompt`
- `POST /api/generate/video-prompt`
- `POST /api/video/scan-match`

### 7.4 剪辑接口

- `GET /api/clip/presets`
- `POST /api/clip/run`

### 7.5 任务接口

- `GET /api/jobs/{jobId}`
- `GET /api/jobs/{jobId}/files`
- `GET /api/jobs/{jobId}/files/{filename}`
- `POST /api/jobs/{jobId}/open-output`

## 8. 任务系统

任务系统是轻量内存实现，核心结构：

- `JobState`
- `JobStore`

执行方式：

1. 创建任务对象
2. 后台线程执行服务函数
3. 实时更新日志、进度、输出路径
4. 前端轮询状态

当前任务类型：

- `image`
- `image_edit`
- `video`
- `video_clip`

限制：

- 服务重启后任务历史会丢失
- 没有取消、暂停、恢复、失败重试

## 9. 输出设计

### 9.1 Prompt 任务

每次任务会创建时间戳目录，通常包含：

- `*.prompt.json`
- `*.prompt.txt`
- `prompts.csv`

### 9.2 视频剪辑任务

每次任务会创建独立时间戳目录。

常见输出：

- 裁切或合并后的视频
- 预览帧
- `manifest.json`
- `summary.csv`

## 10. 本地依赖与平台兼容

视频剪辑模块依赖：

- `opencv-python`
- `imageio-ffmpeg`

技术要点：

- Windows 启动器优先使用 `.venv\Scripts\python.exe`
- Linux 启动脚本优先使用 `.venv/bin/python`
- `video_clip_service.py` 优先使用 `imageio-ffmpeg` 提供的 ffmpeg 二进制
- 不要求系统 PATH 预装全局 `ffmpeg`

平台兼容：

- Windows 使用 `PromptToolLauncher.exe`
- Linux 使用 `run_linux.sh`
- `open-output` 在 Windows 下走 `os.startfile`
- `open-output` 在 Linux 下走 `xdg-open`
- Linux 端目录选择仍依赖浏览器对 `webkitdirectory` 的支持

## 11. 已知限制

- 没有数据库和任务持久化
- 没有登录、权限和多人协作
- 没有手动修正视频匹配关系
- 没有 Prompt 结果二次编辑页
- 没有任意时间轴编辑器
- LLM 调用层缺少完整的重试、限流、多供应商适配

## 12. 后续扩展建议

建议优先级：

1. 补手动修正视频匹配
2. 补任务历史和失败重跑
3. 补 Prompt 结果二次编辑
4. 给视频剪辑补更细粒度参数
5. 增强 LLM 返回校验和重试
