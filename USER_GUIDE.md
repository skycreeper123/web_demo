# Prompt Tool Web Demo 使用说明

## 1. 这是什么

`web_demo` 是一个本地 Web 工具，帮助你批量生成两类 Prompt：

- 图片 -> I2V Prompt
- 视频 + 参考图 -> 视频编辑 Prompt

它适合个人在本机快速跑通素材整理、Prompt 配置、批量生成和结果导出。

## 2. 启动前准备

建议确认：

- 你在 Windows 环境下运行
- 已安装 Python
- 可以正常打开本地浏览器

如果你使用虚拟环境，建议把依赖放在：

```text
.venv\Scripts\python.exe
```

因为一键启动器会优先查找这个路径。

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

首页有两个功能入口：

- 图片 -> I2V Prompt
- 视频 -> 视频编辑 Prompt

页面左上角有统一导航：

- 首页
- 返回上一层

## 5. 图片模块怎么用

### 5.1 选择图片

进入图片模块后，可以：

- 点击上传区域选择图片
- 直接拖拽图片
- 直接选择文件夹批量导入

页面会显示已选文件数量和摘要预览，不会默认把超长列表全部展开。

### 5.2 配置图片模块 API

图片模块的 API 面板支持读取和保存本地配置。

你可以设置：

- `API Key`
- `Base URL`
- `Model`
- `输出目录`
- `use_mock`
- `overwrite`

对应配置文件：

- `backend/api_config.json` 里的 `image` 节点

建议输出目录优先写相对路径，例如：

```text
outputs/image
```

### 5.3 配置图片模块 Prompt

图片模块 Prompt 配置文件：

- `backend/image_prompt_config.json`

页面里可以直接编辑：

- `System Prompt`
- `User Prompt`

点击保存后会写回配置文件。

### 5.4 开始生成

点击：

- `开始生成`

生成过程中页面会展示：

- 当前状态
- 进度
- 日志
- 输出文件列表

### 5.5 查看结果

每张图片通常会生成：

- `xxx.prompt.json`
- `xxx.prompt.txt`
- `prompts.csv`

你也可以使用页面中的输出区查看文件内容，或打开输出目录。

## 6. 视频模块怎么用

### 6.1 选择视频

先导入视频文件或视频目录。

常见支持格式：

- `mp4`
- `mov`
- `avi`
- `mkv`
- `webm`

### 6.2 选择参考图

再导入参考图目录。

常见支持格式：

- `jpg`
- `jpeg`
- `png`
- `webp`

### 6.3 理解匹配规则

视频模块当前使用固定的同名匹配规则。

例如视频：

```text
a001.mp4
```

系统会尝试查找：

- `a001.*` 作为主参考图
- `a001_1.*` 作为补充参考图 1
- `a001_2.*` 作为补充参考图 2

### 6.4 扫描匹配

点击：

- `扫描匹配`

系统会返回：

- 总数
- 成功数
- 部分匹配数
- 缺失数
- 命名冲突数

匹配结果预览当前是“摘要 + 前几条预览 + 展开全部”的模式，不会默认一次性完整展开。

### 6.5 配置视频模块 API

视频模块也有独立的 API 配置读写能力。

对应位置：

- `backend/api_config.json` 里的 `video` 节点

建议输出目录写为：

```text
outputs/video
```

### 6.6 配置视频模块 Prompt

视频模块 Prompt 配置文件：

- `backend/video_prompt_config.json`

页面里可以编辑：

- `System Prompt`
- `User Prompt`

### 6.7 开始生成

点击：

- `开始生成`

当前实现会按下面的流程工作：

1. 先找出可生成的视频匹配项
2. 为每个视频准备一张视频帧图
3. 把“视频帧 + 参考图”一起作为图像输入发送给模型
4. 生成视频编辑 Prompt
5. 落盘到对应输出目录

这里要特别注意：

当前实现不是“把整段视频直接上传给模型做原生视频理解”，而是“视频帧 + 参考图”的多图输入方案。

### 6.8 查看结果

每个视频通常会生成：

- `a001.prompt.json`
- `a001.prompt.txt`
- `prompts.csv`

## 7. 三类结果文件怎么理解

### 7.1 `.json`

适合：

- 保存结构化结果
- 后续程序继续读取
- 保留模型原始返回内容
- 排查解析问题

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

包含两个模块：

- `image`
- `video`

每个模块包含：

- `api_key`
- `base_url`
- `model`
- `output_dir`
- `use_mock`
- `overwrite`

### 8.2 Prompt 配置文件

- `backend/image_prompt_config.json`
- `backend/video_prompt_config.json`

每个文件都包含：

- `system_prompt`
- `user_text`
- `mock_result`

## 9. 推荐使用方式

建议按这个顺序使用：

1. 先保存图片模块和视频模块各自的 API 配置
2. 再分别保存两套 Prompt 配置
3. 每次使用时只需要重新读取配置、选择素材、扫描匹配或直接生成

## 10. 常见问题

### 10.1 没填 API Key 为什么也能跑

因为项目支持 `mock` 模式。

当以下任一条件满足时，会走模拟结果：

- `use_mock = true`
- `API Key` 为空

### 10.2 为什么视频模块不等于原生视频理解

因为它当前不是直接上传视频文件给模型。

实际发送给模型的是：

- 1 张视频帧
- 1 到 2 张参考图

所以它本质上还是多图输入，而不是原生整视频接口。

### 10.3 为什么生成失败

常见原因：

- `API Key` 不正确
- `Base URL` 不可用
- `Model` 名称不正确
- 模型返回的不是可解析 JSON
- 视频没有匹配到主参考图

### 10.4 为什么匹配成功率不高

因为当前只支持固定同名匹配规则，不支持手动改配对关系。

## 11. 当前还没做的内容

目前仍未实现：

- 手动修正视频匹配关系
- 失败任务重跑
- 历史任务管理
- 结果页二次编辑
- 登录与权限控制

## 12. 文档对应关系

- 项目总览：[README.md](D:/AIGC数据库/prompt_tool/prompt_tool/web_demo/README.md)
- 技术实现：[TECHNICAL.md](D:/AIGC数据库/prompt_tool/prompt_tool/web_demo/TECHNICAL.md)