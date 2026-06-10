# 视频运镜分析到 Seedance 2.0 提示词系统

这是一个 Python 命令行工具，用于从参考视频中抽帧、检测运镜，并生成 Seedance 2.0 五段式提示词和 JSON 分析报告。

## 依赖

- Python 3.8+
- FFmpeg / FFprobe，并加入系统 PATH
- Python 包：

```powershell
pip install -r requirements.txt
```

`requirements.txt` 仅包含：

```text
opencv-python>=4.8
numpy>=1.24
```

## 目录

```text
input_videos/             放入 .mp4 / .mov / .avi
frames/<视频名>/           输出 frame_%04d.jpg
output/<视频名>_analysis.json
output/<视频名>_prompt.txt
```

## 使用

批量处理 `input_videos/` 下所有视频：

```powershell
python main.py
```

处理单个视频：

```powershell
python main.py --video .\input_videos\demo.mp4
```

覆盖提示词默认内容：

```powershell
python main.py --subject "中心人物" --action "自然站立" --quality "4K，电影感，细节清晰，自然光影" --constraints "避免闪烁与变形"
```

## 提示词格式

输出严格为五段式，使用英文方括号标记：

```text
[主体] 中心人物
[动作] 自然站立
[运镜] 固定镜头，中景锁定主体，画面丝滑流畅，无抖动
[画质] 4K，电影感，细节清晰，自然光影
[约束] 不写复杂多人互动，不写剧烈跑跳，避免闪烁与变形
```

## 运镜映射表

| 检测类型 | `[运镜]` 字段内容 |
|---|---|
| `static` | 固定镜头，中景锁定主体，画面丝滑流畅，无抖动 |
| `slow_pan_tilt` | 缓慢横摇/竖摇，方向 + 向左/向右/向上/向下，画面丝滑流畅，无抖动 |
| `horizontal_tracking` | 稳定跟拍，水平 + 左移/右移，画面丝滑流畅，无抖动 |
| `vertical_tilt` | 镜头缓慢 + 上升/下降，画面丝滑流畅，无抖动 |
| `fast_movement` | 跟拍移动，保持主体居中，画面丝滑流畅，无抖动 |
| `dynamic_violent` | 稳定环绕半圈，慢动作感，画面丝滑流畅，无抖动 |

## JSON 报告格式

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
