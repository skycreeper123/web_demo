# Prompt Tool Web Demo 使用说明

## 1. 这是什么

`web_demo` 是一个本地 Web 工具，当前有两个主入口：

- `Prompt 生成工作台`
- `视频剪辑工作台`

其中 Prompt 工作台又包含 3 个子模块：

- 图片 -> I2V Prompt
- 图片 -> 图生图 Prompt
- 视频 + 参考图 -> 视频编辑 Prompt

视频剪辑工作台则负责本地批量裁切和双文件夹视频合并。

## 2. 启动前准备

建议确认：

- 你在 Windows 环境下运行
- 已安装 Python
- 可以正常打开本地浏览器

如果你使用项目内虚拟环境，推荐使用：

```text
.venv\Scripts\python.exe
```

因为一键启动器会优先查找这个路径。

如果你计划使用视频剪辑工作台，建议先在项目目录下安装本地依赖：

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

## 3. 如何启动

### 3.1 命令行启动

在 `web_demo` 根目录运行：

```powershell
python .\backend\app\main.py
```

看到类似输出：

```text
Prompt tool demo running at http://127.0.0.1:8000
```

然后打开：

```text
http://127.0.0.1:8000
```

### 3.2 一键启动

也可以直接双击：

- `PromptToolLauncher.exe`

它会自动尝试启动后端，并在服务可用后打开浏览器。

## 4. 首页结构

首页现在有两个工作台入口：

- `Prompt 生成工作台`
- `视频剪辑工作台`

页面左上角有统一导航：

- 首页
- 返回上一级

补充说明：

- 当前 `返回上一级` 的行为与 `首页` 一致，都会回到首页视图

## 5. Prompt 生成工作台怎么用

进入 Prompt 工作台后，可以在同一个大模块里切换 3 个子模块：

- 图片 -> I2V Prompt
- 图片 -> 图生图 Prompt
- 视频 -> 视频编辑 Prompt

顶部切换区用于切子模块，下面的输入、配置、运行和输出区会跟着切换。

### 5.1 图片 -> I2V Prompt

适合根据输入图片生成图生视频前置 Prompt。

你可以：

- 点击上传区域选择图片
- 直接拖拽图片
- 直接选择文件夹批量导入
- 在真实 API 模式下填写图片 URL

页面支持配置：

- `API Key`
- `Base URL`
- `Model`
- `输出目录`
- `use_mock`
- `overwrite`

相关文件：

- API 配置：`backend/api_config.json` 的 `image`
- Prompt 配置：`backend/image_prompt_config.json`

点击 `开始生成` 后，通常会得到：

- `xxx.prompt.json`
- `xxx.prompt.txt`
- `prompts.csv`

### 5.2 图片 -> 图生图 Prompt

适合批量生成高保真、小改动的图片编辑 Prompt。

输入方式与图片模块类似：

- 图片文件
- 图片文件夹
- 图片 URL

相关文件：

- API 配置：`backend/api_config.json` 的 `image_edit`
- Prompt 配置：`backend/image_edit_prompt_config.json`

点击 `开始生成` 后，也会输出：

- `xxx.prompt.json`
- `xxx.prompt.txt`
- `prompts.csv`

### 5.3 视频 -> 视频编辑 Prompt

适合根据视频和参考图生成视频编辑 Prompt。

操作顺序建议是：

1. 导入视频文件或视频目录
2. 导入参考图目录
3. 点击 `扫描匹配`
4. 确认匹配摘要和预览结果
5. 配置 API 和 Prompt
6. 点击 `开始生成`

匹配规则当前是固定同名规则。

例如视频：

```text
a001.mp4
```

系统会尝试匹配：

- `a001.*` 作为主参考图
- `a001_1.*` 作为补充参考图 1
- `a001_2.*` 作为补充参考图 2

相关文件：

- API 配置：`backend/api_config.json` 的 `video`
- Prompt 配置：`backend/video_prompt_config.json`

结果通常会输出：

- `a001.prompt.json`
- `a001.prompt.txt`
- `prompts.csv`

### 5.4 一个重要说明

当前视频 Prompt 模块不是把整段视频直接提交给模型做原生视频理解。

它更适合“根据视频内容和参考图批量生成编辑 Prompt”的工作流，而不是视频剪辑或视频渲染本身。

## 6. 视频剪辑工作台怎么用

视频剪辑工作台直接处理本地视频目录，不走浏览器上传。

你只需要填写本地路径，后端会直接读取文件夹。

### 6.1 选择处理模式

有两种模式：

- `单文件夹裁切`
- `双文件夹合并`

单文件夹裁切适合固定规则批量裁切。

双文件夹合并适合把两个目录里的视频按排序后一一配对，顺序拼接成一个输出视频。

### 6.2 选择剪辑预设

当前已经集成了 `batch_editing` 中的常用预设，包括：

- 保留前 50%（ffmpeg）
- 保留前 50%（OpenCV）
- 保留前 30%
- 保留前 70%
- 保留前 3 秒 / 5 秒 / 7 秒
- 保留后 3 秒 / 5 秒 / 7 秒
- 保留后 30% / 50% / 70%
- 双文件夹顺序合并

说明：

- ffmpeg 版本更快
- OpenCV 版本更偏帧级稳定
- 双文件夹合并会以文件名排序结果作为配对顺序

### 6.3 填写输入路径

单文件夹裁切模式下，填写：

- `视频输入文件夹`

双文件夹合并模式下，填写：

- `文件夹 A`
- `文件夹 B`

建议确保目录中主要包含：

- `mp4`
- `mov`
- `avi`
- `mkv`
- `webm`

### 6.4 填写输出目录

输出目录建议写相对路径，例如：

```text
output/video_clip
```

每次运行都会自动创建一个新的时间戳子目录，避免覆盖上一轮结果。

### 6.5 开始运行

点击：

- `开始剪辑`

运行过程中页面会展示：

- 当前预设
- 任务状态
- 进度
- 实时日志
- 结果列表

### 6.6 查看结果

剪辑任务通常会生成：

- 裁切后的视频文件
- 预览帧图片
- `manifest.json`
- `summary.csv`

如果是单文件夹裁切，结果目录下通常还会有：

- `trimmed/`
- `last_frames/` 或 `first_frames/`

如果是双文件夹合并，结果会直接写出合并后的视频文件。

## 7. 三类 Prompt 结果文件怎么理解

### 7.1 `.json`

适合：

- 保存结构化结果
- 后续程序继续读取
- 排查模型返回和解析问题

### 7.2 `.txt`

适合：

- 直接阅读
- 复制到其他平台或工作流

### 7.3 `.csv`

适合：

- 批量汇总
- 表格整理
- 横向对比多条结果

## 8. 配置文件说明

### 8.1 API 配置文件

路径：

- `backend/api_config.json`

包含 3 个 Prompt 模块：

- `image`
- `image_edit`
- `video`

每个模块包含：

- `api_key`
- `base_url`
- `model`
- `output_dir`
- `use_mock`
- `overwrite`

补充说明：

- 默认 `base_url` 示例值可能是 `https://apinebula.ai/v1`
- 运行时如果使用这个旧地址，后端会自动规范为 `https://api.yhlxj.ai/v1`
- 视频剪辑工作台不使用这份 API 配置

### 8.2 Prompt 配置文件

- `backend/image_prompt_config.json`
- `backend/image_edit_prompt_config.json`
- `backend/video_prompt_config.json`

每个文件都包含：

- `system_prompt`
- `user_text`
- `mock_result`

## 9. 推荐使用方式

建议按这个顺序使用：

1. 先配置 Prompt 工作台 3 个子模块各自的 API 和 Prompt
2. 生成 Prompt 时优先使用相对输出目录
3. 需要处理本地大视频时，再进入视频剪辑工作台
4. 视频剪辑首次使用前先确认 `.venv` 已安装本地依赖

## 10. 常见问题

### 10.1 没填 API Key 为什么也能跑

因为 Prompt 工作台支持 `mock` 模式。

当以下任一条件满足时，会走模拟结果：

- `use_mock = true`
- `API Key` 为空

### 10.2 为什么视频模块不等于原生视频理解

因为它当前更适合批量生成视频编辑 Prompt，不是直接上传整段视频做原生视频理解或视频剪辑。

### 10.3 为什么视频剪辑模块启动了但跑不动

最常见原因是本地依赖未安装。

建议先执行：

```powershell
.venv\Scripts\python.exe -m pip install opencv-python imageio-ffmpeg
```

### 10.4 为什么匹配成功率不高

因为当前视频 Prompt 模块只支持固定同名匹配规则，不支持手动改配对关系。

### 10.5 为什么双文件夹合并的配对不符合预期

因为当前按两个文件夹各自的排序结果一一配对，不是按内容识别配对。

## 11. 当前还没做的内容

目前仍未实现：

- 手动修正视频匹配关系
- 失败任务重跑
- 历史任务管理
- Prompt 结果页二次编辑
- 视频剪辑的任意时间轴参数编辑
- 登录与权限控制

## 12. 文档对应关系

- 项目总览：[README.md](./README.md)
- 技术实现：[TECHNICAL.md](./TECHNICAL.md)
