# Prompt Tool Web Demo 技术文档

## 1. 项目定位

`web_demo` 是一个本地运行的素材处理与 Prompt 生成 Demo，当前覆盖两类工作流：

- Prompt 生成工作台
- 视频剪辑工作台

它更偏向“本地个人生产辅助工具”，而不是完整的线上服务系统。

## 2. 技术框架

当前代码结构不是 React/Vue + API 服务的分离式工程，而是一个轻量单体本地项目：

- 前端：原生 `HTML + CSS + JavaScript`
- 后端：Python 标准库 `http.server`
- 通信：浏览器调用本地 JSON API
- 模型接口：OpenAI-compatible `chat/completions`
- 任务执行：内存态任务 + 后台线程
- 本地视频处理：`opencv-python` + `imageio-ffmpeg`

## 3. 当前目录结构

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
```

## 4. 模块职责

### 4.1 前端

前端位于 `frontend/`，主要负责：

- 首页与工作台入口
- Prompt 工作台子模块切换
- 剪辑工作台模式切换
- 文件选择和拖拽导入
- API 配置读取与保存
- Prompt 配置读取与保存
- 视频匹配预览
- 发起生成任务与剪辑任务
- 轮询任务状态
- 展示日志、进度、输出文件

关键文件：

- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`

### 4.2 后端

后端位于 `backend/app/`，主要负责：

- 托管静态前端页面
- 提供 JSON API
- 初始化并维护配置文件
- 启动后台任务
- 调用 LLM
- 执行本地视频批处理
- 写出结果文件

关键入口：

- `backend/app/main.py`

### 4.3 配置层

`backend/app/core/config.py` 负责：

- 定义默认 API 配置
- 定义默认 Prompt 配置
- 加载与保存 `api_config.json`
- 加载与保存 3 份 Prompt 配置文件
- 处理输出目录的相对路径/绝对路径转换
- 兼容旧的 `apinebula.ai/v1` 地址，并在运行时规范为 `https://api.yhlxj.ai/v1`

### 4.4 LLM 调用层

`backend/app/core/llm_client.py` 当前只实现了一层轻量适配：

- 请求地址：`{base_url}/chat/completions`
- 消息结构：`system` + `user`
- 多媒体输入方式：`image_url` / 媒体 URL
- 响应提取方式：从 `choices[0].message.content` 提取文本

它本质上是 OpenAI-compatible 调用层，不是多供应商统一抽象层。

### 4.5 服务层

#### 图片 Prompt 生成

`backend/app/services/prompt_generator.py` 负责：

- 接收前端传来的图片输入
- 调用图片 Prompt 配置
- 在 `mock` 或真实模型之间切换
- 尝试从模型文本中提取 JSON
- 写出 `json`、`txt`、`csv`

#### 图生图 Prompt 生成

`backend/app/services/image_edit_prompt_generator.py` 负责：

- 接收图片输入
- 调用图生图 Prompt 配置
- 在 `mock` 或真实模型之间切换
- 解析结果并写出 `json`、`txt`、`csv`

#### 视频匹配

`backend/app/services/video_matcher.py` 负责：

- 过滤支持的视频/图片扩展名
- 以视频主名为键做固定同名匹配
- 输出匹配列表和统计摘要

状态包括：

- `matched`
- `partial_match`
- `missing_reference`
- `naming_conflict`

#### 视频 Prompt 生成

`backend/app/services/video_prompt_generator.py` 负责：

- 接收视频项和参考图项
- 组织视频模块的用户提示词
- 将视频与参考图作为多媒体输入发送给模型
- 解析结果并写出 `json`、`txt`、`csv`

#### 视频剪辑服务

`backend/app/services/video_clip_service.py` 负责：

- 定义剪辑预设注册表 `CLIP_PRESETS`
- 对外提供剪辑预设列表
- 根据预设执行本地视频批处理
- 兼容单文件夹裁切与双文件夹顺序合并
- 写出 `manifest.json` 与 `summary.csv`

当前预设族包括：

- 前半段裁切：`first_half_ffmpeg`、`first_half_opencv`
- 前段比例裁切：`first_30pct`、`first_70pct`
- 前段秒数裁切：`first_3s`、`first_5s`、`first_7s`
- 后段秒数裁切：`last_3s`、`last_5s`、`last_7s`
- 后段比例裁切：`tail_30pct`、`tail_50pct`、`tail_70pct`
- 双文件夹合并：`merge_pairwise`

## 5. 当前业务流程

### 5.1 图片 -> I2V Prompt

流程：

1. 前端读取图片文件或图片 URL
2. 后端接收 `images`
3. 如果 `use_mock=true` 或 `api_key` 为空，直接使用 `mock_result`
4. 否则调用图片模型接口
5. 解析返回 JSON
6. 写出：
   - `*.prompt.json`
   - `*.prompt.txt`
   - `prompts.csv`

### 5.2 图片 -> 图生图 Prompt

流程：

1. 前端读取图片文件或图片 URL
2. 后端接收 `images`
3. 按图生图 Prompt 配置组装请求
4. 在 `mock` 或真实模型之间切换
5. 解析返回 JSON
6. 写出：
   - `*.prompt.json`
   - `*.prompt.txt`
   - `prompts.csv`

### 5.3 视频 -> 视频编辑 Prompt

流程：

1. 前端先做视频与参考图的匹配扫描
2. 仅将可生成项送入生成流程
3. 后端将视频与参考图组织成多媒体输入
4. 调用模型生成视频编辑 Prompt
5. 解析返回 JSON
6. 写出：
   - `*.prompt.json`
   - `*.prompt.txt`
   - `prompts.csv`

这里需要明确：

当前视频 Prompt 模块不是“整视频原生理解”，而是“视频 + 参考图 -> Prompt”的批量生成流程。

### 5.4 视频剪辑工作台

流程：

1. 前端读取 `/api/clip/presets`
2. 用户在前端选择：
   - 单文件夹裁切 或 双文件夹合并
   - 对应预设
   - 本地输入路径
   - 输出根目录
3. 前端发起 `POST /api/clip/run`
4. 后端创建 `video_clip` 类型任务
5. 服务层按预设执行批处理
6. 任务完成后写出：
   - 裁切视频或合并视频
   - 预览帧
   - `manifest.json`
   - `summary.csv`

## 6. 配置文件体系

所有运行时配置都位于 `backend/` 下。

### 6.1 API 配置

文件：

- `backend/api_config.json`

结构：

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

行为：

- 文件不存在时会自动生成
- 字段缺失时会按默认配置补齐
- `output_dir` 会被标准化为相对路径优先
- 如果 `base_url` 结尾是 `apinebula.ai/v1`，运行时会被自动改写为 `https://api.yhlxj.ai/v1`
- 视频剪辑工作台不依赖这份 API 配置

### 6.2 Prompt 配置

文件：

- `backend/image_prompt_config.json`
- `backend/image_edit_prompt_config.json`
- `backend/video_prompt_config.json`

公共字段：

- `system_prompt`
- `user_text`
- `mock_result`

行为：

- 文件不存在时会自动写入默认模板
- 保存时会与默认结构合并

## 7. 路径策略

当前项目实现的是“相对路径优先”。

例如：

- `output`
- `output/video_clip`

在运行时会被解析为相对于项目根目录的真实目录。

好处是：

- 整个 `web_demo` 目录移动后，默认输出路径仍然可用
- 配置文件里不必固定写死本机绝对路径

## 8. 本地依赖策略

视频剪辑工作台当前依赖：

- `opencv-python`
- `imageio-ffmpeg`

推荐安装方式：

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

技术要点：

- 启动器优先使用 `.venv\Scripts\python.exe`
- `video_clip_service.py` 会优先使用 `imageio-ffmpeg` 提供的本地 ffmpeg 二进制
- 这意味着系统 PATH 不必额外配置全局 `ffmpeg`

## 9. 后端 API

后端主入口：

- `backend/app/main.py`

### 9.1 静态页面

- `GET /`
- `GET /app.js`
- `GET /style.css`

### 9.2 初始化和配置接口

- `GET /api/config`
- `GET /api/prompt-config`
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

说明：

- `GET /api/prompt-config` 当前仍兼容图片模块 Prompt 配置
- `runtime-config` 实际对应 `api_config.json` 中的模块配置

### 9.3 Prompt 业务接口

- `POST /api/video/scan-match`
- `POST /api/generate`
- `POST /api/generate/image-prompt`
- `POST /api/generate/image-edit-prompt`
- `POST /api/generate/video-prompt`

说明：

- `POST /api/generate` 当前兼容图片模块生成
- 图生图和视频生成走各自独立接口

### 9.4 剪辑接口

- `GET /api/clip/presets`
- `POST /api/clip/run`

### 9.5 任务接口

- `GET /api/jobs/{jobId}`
- `GET /api/jobs/{jobId}/files`
- `GET /api/jobs/{jobId}/files/{filename}`
- `POST /api/jobs/{jobId}/open-output`

## 10. 任务执行机制

任务系统是一个轻量内存实现。

核心结构：

- `JobState`
- `JobStore`

执行方式：

1. 创建任务对象
2. 后台线程执行服务层函数
3. 实时更新日志、进度、输出路径
4. 前端轮询任务状态

当前任务类型包括：

- `image`
- `image_edit`
- `video`
- `video_clip`

当前限制：

- 服务一重启，任务历史会丢失
- 没有持久化数据库
- 没有取消、暂停、恢复、失败重试机制

## 11. 输出文件设计

### 11.1 Prompt 生成任务

每次 Prompt 任务会在输出根目录下创建一个时间戳子目录，通常包含：

- `*.prompt.json`
- `*.prompt.txt`
- `prompts.csv`

### 11.2 视频剪辑任务

每次剪辑任务也会创建独立时间戳子目录。

单文件夹裁切通常会在子目录下再生成：

- `trimmed/`
- `last_frames/` 或 `first_frames/`
- `manifest.json`
- `summary.csv`

双文件夹合并通常会直接输出合并结果视频，并附带：

- `manifest.json`
- `summary.csv`

## 12. 一键启动器

项目根目录包含：

- `PromptToolLauncher.cs`
- `build_launcher.ps1`
- `PromptToolLauncher.exe`

当前机制：

- 启动器以自身目录为基准定位 `backend/app/main.py`
- 优先尝试 `.venv\Scripts\python.exe`
- 回退到系统 `python` 或 `py -3`
- 轮询 `http://127.0.0.1:8000/`
- 服务就绪后自动打开浏览器

这让项目在更换工作目录时仍然更稳，不依赖“从哪个终端目录启动”。

## 13. 已知限制

当前版本仍然是 Demo，存在这些边界：

- 没有登录和权限系统
- 没有数据库和历史任务查询
- 没有手动修正视频匹配关系
- 没有 Prompt 结果二次编辑页
- 没有失败重跑、暂停、取消
- LLM 调用层没有重试、退避、限流控制
- 目前没有专门的多供应商适配层
- 视频剪辑当前以固定预设为主，不支持任意时间轴编辑器

## 14. 后续演进建议

如果后续继续扩展，建议优先级如下：

1. 补手动修正视频匹配
2. 补任务历史和失败重跑
3. 补 Prompt 结果页二次编辑
4. 给视频剪辑补更细粒度参数化选项
5. 增强 LLM 返回校验和重试
6. 增强配置模板管理
7. 如果复杂度继续增长，再考虑前后端进一步拆分
