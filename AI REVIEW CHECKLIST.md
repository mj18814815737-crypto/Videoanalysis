# AI Review Checklist

本文件用于把整个项目文件夹打包交给其他 AI 或人工审查者时，快速核对“视频运镜分析 -> Seedance 2.0 提示词系统”的框架内容、代码职责和规范符合度。

## 0. 维护要求

以后凡是对项目框架、模块职责、输入输出规范、提示词格式、JSON 格式、运镜映射表、依赖、运行方式或审核标准做修改，都必须同步更新本文件。

本文件应始终反映当前项目的最新框架状态，方便直接交给其他 AI 做审核、核对和校验。

## 1. 审核目标

请审查当前文件夹是否实现了一个 Python 命令行工具，能够：

1. 从 `input_videos/` 读取 `.mp4`、`.mov`、`.avi` 视频。
2. 使用 FFmpeg 每秒抽取 1 帧，最多 20 帧。
3. 将中间帧保存到 `frames/<视频名>/frame_%04d.jpg`。
4. 使用帧差和 Farneback 光流检测运镜。
5. 输出 JSON 分析报告到 `output/<视频名>_analysis.json`。
6. 输出 Seedance 2.0 五段式提示词到 `output/<视频名>_prompt.txt`。

## 2. 必须存在的文件

请确认项目根目录包含以下文件：

```text
config.py
preprocess.py
camera_motion.py
prompt_builder.py
main.py
requirements.txt
README.md
AI REVIEW CHECKLIST.md
.gitignore
```

目录应包含：

```text
input_videos/
frames/
output/
```

## 2.1 Git 同步与隐私核对

第一次同步到 GitHub 前，请确认 `.gitignore` 已排除以下内容：

```text
tools/
input_videos/*
frames/*
output/*
__pycache__/
*.zip
*.log
```

只保留 `input_videos/.gitkeep`、`frames/.gitkeep`、`output/.gitkeep` 作为目录占位。

审核者应确认仓库中不包含：

1. 用户原始视频。
2. 抽帧图片。
3. 生成的 JSON/TXT 输出结果。
4. 本地 Python/FFmpeg 工具包。
5. 下载中的 zip 压缩包。
6. API key、token、password、secret、私钥等敏感信息。

## 3. 文件职责核对

| 文件 | 应承担职责 | 审核重点 |
|---|---|---|
| `config.py` | 统一配置路径、抽帧参数、阈值、输出后缀、提示词映射表 | 不应散落硬编码核心参数 |
| `preprocess.py` | FFprobe 获取时长和分辨率；FFmpeg 抽帧 | 帧命名必须为 `frame_%04d.jpg` |
| `camera_motion.py` | 帧差 + Farneback 光流；输出英文运镜类型和方向 | `camera.type` 不得输出中文 |
| `prompt_builder.py` | 生成 Seedance 五段式提示词 | 必须使用 `[主体]` 这种英文方括号标签 |
| `main.py` | CLI 主流程；支持批量和 `--video`；写 JSON/TXT | 输出文件名必须符合规范 |
| `requirements.txt` | Python 依赖 | 只能包含 `opencv-python>=4.8` 和 `numpy>=1.24` |

## 4. 输入输出规范核对

| 项目 | 必须满足 |
|---|---|
| 输入目录 | `./input_videos/` |
| 支持格式 | `.mp4`, `.mov`, `.avi` |
| 中间帧目录 | `./frames/<视频名>/` |
| 中间帧命名 | `frame_%04d.jpg` |
| JSON 输出 | `./output/<视频名>_analysis.json` |
| 提示词输出 | `./output/<视频名>_prompt.txt` |

## 5. 运镜检测算法核对

当前实现应位于 `camera_motion.py`。

必须满足：

- 每帧转灰度。
- 分析前缩放到 `320x240`。
- 连续两帧计算绝对差均值 `diff_rate`，并归一化到 `0~1`。
- 使用 `cv2.calcOpticalFlowFarneback()` 计算光流。
- 统计平均水平位移 `dx` 和垂直位移 `dy`。

分类规则必须输出以下英文标识：

| diff_rate | 位移条件 | `camera.type` |
|---|---|---|
| `< 0.03` | - | `static` |
| `0.03 ~ 0.10` | - | `slow_pan_tilt` |
| `0.10 ~ 0.20` | `abs(dx) >= abs(dy)` | `horizontal_tracking` |
| `0.10 ~ 0.20` | `abs(dx) < abs(dy)` | `vertical_tilt` |
| `0.20 ~ 0.35` | - | `fast_movement` |
| `> 0.35` | - | `dynamic_violent` |

方向规则：

| 条件 | 输出 |
|---|---|
| `abs(dx) < 0.01` 且 `abs(dy) < 0.01` | `horizontal_trend = none`, `vertical_trend = none` |
| `dx > 0` | `horizontal_trend = right` |
| `dx < 0` | `horizontal_trend = left` |
| `dy > 0` | `vertical_trend = down` |
| `dy < 0` | `vertical_trend = up` |

## 6. Seedance 提示词格式核对

提示词 TXT 必须严格为五段式，使用英文方括号标签，换行分隔：

```text
[主体] 中心人物
[动作] 自然站立
[运镜] 固定镜头，中景锁定主体，画面丝滑流畅，无抖动
[画质] 4K，电影感，细节清晰，自然光影
[约束] 不写复杂多人互动，不写剧烈跑跳，避免闪烁与变形
```

严禁输出以下旧格式：

```text
主体：...
动作：...
运镜：...
画质：...
约束：...
```

## 7. 运镜映射表核对

请确认 `config.py` 或等价配置中存在并使用以下映射：

| 检测类型 | `[运镜]` 字段内容 |
|---|---|
| `static` | `固定镜头，中景锁定主体，画面丝滑流畅，无抖动` |
| `slow_pan_tilt` | `缓慢横摇/竖摇，方向 ` + 向左/向右/向上/向下 + `，画面丝滑流畅，无抖动` |
| `horizontal_tracking` | `稳定跟拍，水平` + 左移/右移 + `，画面丝滑流畅，无抖动` |
| `vertical_tilt` | `镜头缓慢` + 上升/下降 + `，画面丝滑流畅，无抖动` |
| `fast_movement` | `跟拍移动，保持主体居中，画面丝滑流畅，无抖动` |
| `dynamic_violent` | `稳定环绕半圈，慢动作感，画面丝滑流畅，无抖动` |

特别注意：`dynamic_violent` 不得写成“降低剧烈抖动”等其他表述。所有 `[运镜]` 字段末尾都必须包含“，画面丝滑流畅，无抖动”。

## 8. JSON 报告格式核对

每个视频必须生成：

```json
{
  "video": "video_name.mp4",
  "duration_sec": 12.5,
  "resolution": "1920x1080",
  "camera": {
    "type": "static",
    "intensity": 0.02,
    "horizontal_trend": "none",
    "vertical_trend": "none"
  }
}
```

审核重点：

- `video` 必须是视频文件名，不应是完整绝对路径。
- `duration_sec` 必须位于 JSON 顶层。
- `resolution` 必须位于 JSON 顶层，格式类似 `1920x1080`。
- `camera.type` 必须是英文标识。
- `camera.intensity` 应为 `diff_rate` 数值。

## 9. CLI 与异常处理核对

`main.py` 必须满足：

- `python main.py`：处理 `input_videos/` 下全部视频。
- `python main.py --video .\input_videos\demo.mp4`：处理指定单个视频。
- 支持 `--subject`、`--action`、`--quality`、`--constraints` 覆盖提示词默认内容。
- `input_videos/` 为空时，提示用户放入视频。
- FFmpeg/FFprobe 未找到时，打印清晰错误并退出。
- 抽帧数量少于 2 时，打印警告并按 `static` 处理。
- 处理完成后保留中间帧，不在流程结束时自动删除。

## 10. 依赖核对

`requirements.txt` 必须只包含：

```text
opencv-python>=4.8
numpy>=1.24
```

除 Python 标准库外，不应引入其他 Python 包。

系统依赖：

```text
ffmpeg
ffprobe
```

## 11. 建议运行验证

如果审核环境已安装 Python、FFmpeg 和 FFprobe，建议执行：

```powershell
pip install -r requirements.txt
python main.py
python main.py --video .\input_videos\demo.mp4
```

建议用一个短视频检查：

1. 是否生成 `frames/<视频名>/frame_0001.jpg`。
2. 是否生成 `output/<视频名>_analysis.json`。
3. 是否生成 `output/<视频名>_prompt.txt`。
4. TXT 是否严格使用 `[主体]` 五段式。
5. TXT 中 `[运镜]` 行是否以“，画面丝滑流畅，无抖动”结尾。
6. JSON 是否严格包含顶层 `duration_sec` 和 `resolution`。

## 12. 已知本机验证限制

当前开发环境此前未检测到：

```text
python
ffmpeg
ffprobe
```

因此如果其他 AI 或审核者具备完整运行环境，请优先补做真实视频运行验证。
