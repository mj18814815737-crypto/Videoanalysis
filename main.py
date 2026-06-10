import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import config
from camera_motion import analyze_camera_motion
from preprocess import (
    DependencyError,
    extract_frames,
    find_input_videos,
    get_video_metadata,
    validate_video_path,
)
from prompt_builder import build_seedance_prompt


def process_video(video_path, args):
    # type: (Path, argparse.Namespace) -> Dict[str, Any]
    print("正在处理：{}".format(video_path.name))

    metadata = get_video_metadata(video_path)
    frames = extract_frames(video_path)
    print("抽帧数量：{}".format(len(frames)))

    motion = analyze_camera_motion(frames)
    print(
        "检测结果：type={type}, intensity={intensity}, horizontal={horizontal_trend}, vertical={vertical_trend}".format(
            **motion
        )
    )

    prompt = build_seedance_prompt(
        motion,
        subject=args.subject,
        action=args.action,
        quality=args.quality,
        constraints=args.constraints,
    )

    report = {
        "video": video_path.name,
        "duration_sec": metadata["duration_sec"],
        "resolution": metadata["resolution"],
        "camera": {
            "type": motion["type"],
            "intensity": motion["intensity"],
            "horizontal_trend": motion["horizontal_trend"],
            "vertical_trend": motion["vertical_trend"],
        },
    }

    analysis_path = config.OUTPUT_DIR / "{}{}".format(video_path.stem, config.ANALYSIS_SUFFIX)
    prompt_path = config.OUTPUT_DIR / "{}{}".format(video_path.stem, config.PROMPT_SUFFIX)

    analysis_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt_path.write_text(prompt, encoding="utf-8")

    print("JSON 输出：{}".format(analysis_path))
    print("提示词输出：{}".format(prompt_path))
    return {
        "video": video_path.name,
        "analysis_path": str(analysis_path),
        "prompt_path": str(prompt_path),
        "camera_type": motion["type"],
    }


def collect_videos(args):
    # type: (argparse.Namespace) -> List[Path]
    if args.video:
        video_path = args.video
        error = validate_video_path(video_path)
        if error:
            raise ValueError(error)
        return [video_path]
    return find_input_videos()


def parse_args():
    parser = argparse.ArgumentParser(description="视频运镜分析到 Seedance 2.0 五段式提示词生成器")
    parser.add_argument("--video", type=Path, help="指定单个视频文件；默认处理 input_videos 下全部视频")
    parser.add_argument("--subject", help="覆盖 [主体] 内容")
    parser.add_argument("--action", help="覆盖 [动作] 内容")
    parser.add_argument("--quality", help="覆盖 [画质] 内容")
    parser.add_argument("--constraints", help="覆盖 [约束] 内容")
    return parser.parse_args()


def main():
    config.ensure_directories()
    args = parse_args()

    try:
        videos = collect_videos(args)
        if not videos:
            print("未发现视频。请将 .mp4/.mov/.avi 放入：{}".format(config.INPUT_DIR))
            return 0

        results = []
        for video_path in videos:
            results.append(process_video(video_path.resolve(), args))

        print("处理完成，共处理 {} 个视频。".format(len(results)))
        return 0
    except DependencyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print("FFmpeg/FFprobe 执行失败：{}".format(exc), file=sys.stderr)
        return 3
    except Exception as exc:
        print("处理失败：{}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
