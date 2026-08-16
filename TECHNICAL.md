# Prompt Tool Web Demo 技术文档

## 1. 项目定位

`web_demo` 是一个本地运行的 Prompt 生成 Demo，目标是低门槛验证下面两条流程：

- 图片 -> I2V Prompt
- 视频 + 参考图 -> 视频编辑 Prompt

它当前更偏向“本地个人生产辅助工具”，而不是完整的线上服务系统。

## 2. 技术框架

当前代码结构不是 React/Vue + API 服务的分离式工程，而是一个轻量单体本地项目：

- 前端：原生 `HTML + CSS + JavaScript`
- 后端：Python 标准库 `http.server`
- 通信：浏览器调用本地 JSON API
- 模型接口：OpenAI-compatible `chat/completions`
- 任务执行：内存态任务 + 后台线程

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
```

## 4. 模块职责

### 4.1 前端

前端位于 `frontend/`，主要负责：

- 主页和模块切换
- 文件选择和拖拽导入
- API 配置读取与保存
- Prompt 配置读取与保存
- 视频匹配预览
- 发起生成任务
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
- 写出结果文件

关键入口：

- `backend/app/main.py`

### 4.3 配置层

`backend/app/core/config.py` 负责：

- 定义默认 API 配置
- 定义默认 Prompt 配置
- 加载与保存 `api_config.json`
- 加载与保存两份 Prompt 配置文件
- 处理输出目录的相对路径/绝对路径转换
- 兼容旧的 `apinebula.ai/v1` 地址，并在运行时规范为 `https://api.yhlxj.ai/v1`

### 4.4 LLM 调用层

`backend/app/core/llm_client.py` 当前只实现了一层轻量适配：

- 请求地址：`{base_url}/chat/completions`
- 消息结构：`system` + `user`
- 图像输入方式：`image_url`
- 响应提取方式：从 `choices[0].message.content` 提取文本

它本质上是 OpenAI-compatible 调用层，不是多供应商统一抽象层。

### 4.5 服务层

#### 图片生成

`backend/app/services/prompt_generator.py` 负责：

- 接收前端传来的图片 `dataUrl`
- 调用图片 Prompt 配置
- 在 `mock` 或真实模型之间切换
- 尝试从模型文本中提取 JSON
- 写出 `json`、`txt`、`csv`

#### 视频匹配

`backend/app/services/video_matcher.py` 负责：

- 过滤支持的音视频/图片扩展名
- 以视频主名为键做固定同名匹配
- 输出匹配列表和统计摘要

状态包括：

- `matched`
- `partial_match`
- `missing_reference`
- `naming_conflict`

#### 视频生成

`backend/app/services/video_prompt_generator.py` 负责：

- 接收视频项、参考图、视频帧数据
- 组织视频模块的用户提示词
- 将“1 张视频帧 + 1 到 2 张参考图”一起发给模型
- 解析结果并写出 `json`、`txt`、`csv`

## 5. 当前生成逻辑

### 5.1 图片模块

流程：

1. 前端读取图片并转成 `dataUrl`
2. 后端接收 `images`
3. 如果 `use_mock=true` 或 `api_key` 为空，直接使用 `mock_result`
4. 否则调用 `chat_with_image(...)`
5. 解析返回 JSON
6. 写出：
   - `*.prompt.json`
   - `*.prompt.txt`
   - `prompts.csv`

### 5.2 视频模块

流程：

1. 前端先做视频与参考图的匹配扫描
2. 仅将可生成项送入生成流程
3. 为每个视频准备一张 `frameDataUrl`
4. 将 `frameDataUrl + references[].dataUrl` 一起发送给模型
5. 解析返回 JSON
6. 写出：
   - `*.prompt.json`
   - `*.prompt.txt`
   - `prompts.csv`

这里需要明确：

当前视频模块不是“整视频原生理解”，而是“视频帧 + 参考图”的多图输入实现。

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

行为：

- 文件不存在时会自动生成
- 字段缺失时会按默认配置补齐
- `output_dir` 会被标准化为相对路径优先
- 如果 `base_url` 结尾是 `apinebula.ai/v1`，运行时会被自动改写为 `https://api.yhlxj.ai/v1`

### 6.2 Prompt 配置

文件：

- `backend/image_prompt_config.json`
- `backend/video_prompt_config.json`

公共字段：

- `system_prompt`
- `user_text`
- `mock_result`

行为：

- 文件不存在时会自动写入默认模板
- 保存时会与默认结构合并

## 7. 路径策略

当前项目已经实现“相对路径优先”的输出目录策略。

例如：

- `outputs/image`
- `outputs/video`

在运行时会被解析为相对于 `backend/` 的真实目录。

对应逻辑在：

- `default_output_root(...)`
- `resolve_output_path(...)`
- `_normalize_output_path_text(...)`

好处是：

- 整个 `web_demo` 目录移动后，默认输出路径仍然可用
- 配置文件里不必固定写死本机绝对路径

## 8. 后端 API

后端主入口：

- `backend/app/main.py`

### 8.1 静态页面

- `GET /`
- `GET /app.js`
- `GET /style.css`

### 8.2 初始化和配置接口

- `GET /api/config`
- `GET /api/prompt-config`
- `GET /api/prompt-config/image`
- `POST /api/prompt-config/image`
- `GET /api/prompt-config/video`
- `POST /api/prompt-config/video`
- `GET /api/runtime-config/image`
- `POST /api/runtime-config/image`
- `GET /api/runtime-config/video`
- `POST /api/runtime-config/video`

说明：

- `GET /api/prompt-config` 当前等价于读取图片模块 Prompt 配置
- `runtime-config` 实际对应 `api_config.json` 中的模块配置

### 8.3 业务接口

- `POST /api/video/scan-match`
- `POST /api/generate`
- `POST /api/generate/image-prompt`
- `POST /api/generate/video-prompt`

说明：

- `POST /api/generate` 当前兼容图片模块生成
- 视频生成独立走 `POST /api/generate/video-prompt`

### 8.4 任务接口

- `GET /api/jobs/{jobId}`
- `GET /api/jobs/{jobId}/files`
- `GET /api/jobs/{jobId}/files/{filename}`
- `POST /api/jobs/{jobId}/open-output`

## 9. 任务执行机制

任务系统是一个轻量内存实现。

核心结构：

- `JobState`
- `JobStore`

执行方式：

1. 创建任务对象
2. 后台线程执行生成函数
3. 实时更新日志、进度、输出路径
4. 前端轮询任务状态

当前限制：

- 服务一重启，任务历史就会丢失
- 没有持久化数据库
- 没有取消、暂停、恢复、失败重试机制

## 10. 输出文件设计

每次任务会在：

- `output_dir/{jobId}/`

下生成结果。

通常包含三类文件：

### 10.1 `*.prompt.json`

保存结构化结果和原始模型返回内容，便于复用和排查问题。

### 10.2 `*.prompt.txt`

保存适合直接阅读和复制的文本结果。

### 10.3 `prompts.csv`

保存汇总表，便于批量整理和筛选。

## 11. 一键启动器

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

## 12. 已知限制

当前版本仍然是 Demo，存在这些边界：

- 没有登录和权限系统
- 没有数据库和历史任务查询
- 没有手动修正视频匹配关系
- 没有结果二次编辑页
- 没有失败重跑、暂停、取消
- LLM 调用层没有重试、退避、限流控制
- 目前没有专门的多供应商适配层
- 视频模块不支持原生整视频理解 API

## 13. 后续演进建议

如果后续继续扩展，建议优先级如下：

1. 补手动修正视频匹配
2. 补任务历史和失败重跑
3. 补结果页二次编辑
4. 增强 LLM 返回校验和重试
5. 增强配置模板管理
6. 如果复杂度继续增长，再考虑前后端进一步拆分
