import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


class DependencyError(RuntimeError):
    pass


def require_binary(binary):
    if shutil.which(binary) is None:
        raise DependencyError("未找到依赖：{}。请先安装并加入 PATH。".format(binary))


def get_video_metadata(video_path):
    # type: (Path) -> Dict[str, Any]
    require_binary(config.FFPROBE_BIN)
    cmd = [
        config.FFPROBE_BIN,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    data = json.loads(result.stdout)

    video_stream = next(
        (stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"),
        {},
    )
    duration = float(video_stream.get("duration") or data.get("format", {}).get("duration") or 0)
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)

    return {
        "duration_sec": round(duration, 3),
        "width": width,
        "height": height,
        "resolution": "{}x{}".format(width, height) if width and height else "unknown",
    }


def extract_frames(video_path, sample_rate=None):
    # type: (Path, Optional[int]) -> List[Any]
    if sample_rate is not None:
        return _extract_frames_cv2(video_path, sample_rate)

    require_binary(config.FFMPEG_BIN)
    config.ensure_directories()

    video_frame_dir = config.FRAMES_DIR / video_path.stem
    video_frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in video_frame_dir.glob("*.jpg"):
        old_frame.unlink()

    output_pattern = video_frame_dir / config.FRAME_FILENAME_PATTERN
    cmd = [
        config.FFMPEG_BIN,
        "-y",
        "-i",
        str(video_path),
        "-vf",
        "fps={}".format(config.FRAME_RATE),
        "-frames:v",
        str(config.MAX_FRAMES),
        "-q:v",
        str(config.JPEG_QUALITY),
        str(output_pattern),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

    return sorted(video_frame_dir.glob("*.jpg"))


def _extract_frames_cv2(video_path, sample_rate):
    # type: (Path, int) -> List[Any]
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("未找到 Python 依赖：opencv-python。请先运行 pip install -r requirements.txt。") from exc

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("无法打开视频：{}".format(video_path))

    frames = []
    count = 0
    interval = max(1, int(sample_rate))
    while len(frames) < config.MAX_FRAMES:
        ok, frame = cap.read()
        if not ok:
            break
        if count % interval == 0:
            frames.append(frame)
        count += 1
    cap.release()
    return frames


def find_input_videos():
    # type: () -> List[Path]
    config.ensure_directories()
    return sorted(
        path
        for path in config.INPUT_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in config.SUPPORTED_VIDEO_EXTENSIONS
    )


def validate_video_path(video_path):
    # type: (Path) -> Optional[str]
    if not video_path.exists():
        return "视频不存在：{}".format(video_path)
    if not video_path.is_file():
        return "不是有效文件：{}".format(video_path)
    if video_path.suffix.lower() not in config.SUPPORTED_VIDEO_EXTENSIONS:
        return "不支持的视频格式：{}".format(video_path.suffix)
    return None
