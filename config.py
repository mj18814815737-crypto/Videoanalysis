from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input_videos"
FRAMES_DIR = BASE_DIR / "frames"
OUTPUT_DIR = BASE_DIR / "output"
PROMPT_OUTPUT_DIR = BASE_DIR / "output_prompts"

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}

FRAME_RATE = 1
MAX_FRAMES = 20
ANALYSIS_SIZE = (320, 240)
JPEG_QUALITY = 2

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

FRAME_FILENAME_PATTERN = "frame_%04d.jpg"
ANALYSIS_SUFFIX = "_analysis.json"
PROMPT_SUFFIX = "_prompt.txt"

DIFF_THRESHOLDS = {
    "static": 0.03,
    "slow": 0.10,
    "medium": 0.20,
    "fast": 0.35,
}

DIRECTION_EPSILON = 0.01

DEFAULT_PROMPT_CONTEXT = {
    "subject": "中心人物",
    "action": "自然站立",
    "quality": "4K，电影感，细节清晰，自然光影",
    "constraints": "不写复杂多人互动，不写剧烈跑跳，避免闪烁与变形",
}

SPEED_LEVELS = ["中速", "较快", "快"]
ACTION_SPEED_VARIANTS = ["较快", "快速"]
DEFAULT_ACTION = "人物缓慢转身"

CAMERA_PROMPT_MAP = {
    "static": "固定镜头，中景锁定主体，画面丝滑流畅，无抖动",
    "slow_pan_tilt": "缓慢横摇/竖摇，方向 {direction_cn}，画面丝滑流畅，无抖动",
    "horizontal_tracking": "稳定跟拍，水平{horizontal_move_cn}，画面丝滑流畅，无抖动",
    "vertical_tilt": "镜头缓慢{vertical_move_cn}，画面丝滑流畅，无抖动",
    "fast_movement": "跟拍移动，保持主体居中，画面丝滑流畅，无抖动",
    "dynamic_violent": "稳定环绕半圈，慢动作感，画面丝滑流畅，无抖动",
}


def ensure_directories():
    INPUT_DIR.mkdir(exist_ok=True)
    FRAMES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    PROMPT_OUTPUT_DIR.mkdir(exist_ok=True)
