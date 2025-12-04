"""
VideoRenderingSkill
動画をレンダリングするスキル
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from .base_skill import BaseSkill


class VideoRenderingSkill(BaseSkill):
    """動画をレンダリングするスキル"""

    def __init__(self):
        super().__init__(
            name="video_rendering",
            description="Remotionを使用して動画をレンダリングする"
        )

    def get_audio_duration(self, audio_file: str) -> float:
        """
        音声ファイルの長さを取得

        Args:
            audio_file: 音声ファイルパス

        Returns:
            長さ（秒）
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_file)
            return len(audio) / 1000.0
        except ImportError:
            self.log("pydub not installed. Using ffprobe instead.", "WARNING")

            # ffprobeを使用
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                audio_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return 0.0

    def prepare_video_props(self, slides: List[Dict], audio_files: List[str], fps: int = 30) -> Dict:
        """
        Remotion用のpropsを準備

        Args:
            slides: スライドデータのリスト
            audio_files: 音声ファイルのリスト
            fps: フレームレート

        Returns:
            Remotion props
        """
        slides_info = []
        total_frames = 0

        for i, slide in enumerate(slides):
            audio_file = audio_files[i] if i < len(audio_files) else None
            duration_sec = 5.0  # デフォルト

            if audio_file and os.path.exists(audio_file):
                duration_sec = self.get_audio_duration(audio_file) + 1.0  # 1秒のバッファ

            duration_frames = int(duration_sec * fps)

            slides_info.append({
                "index": i + 1,
                "title": slide.get("title", f"Slide {i + 1}"),
                "content": slide.get("content", ""),
                "audioFile": audio_file,
                "durationFrames": duration_frames,
                "startFrame": total_frames
            })

            total_frames += duration_frames

        return {
            "fps": fps,
            "totalFrames": total_frames,
            "totalDurationSec": total_frames / fps,
            "slides": slides_info
        }

    def render_with_remotion(self, props: Dict, project_dir: Path, output_file: Path) -> str:
        """
        Remotionで動画をレンダリング

        Args:
            props: Remotion props
            project_dir: Remotionプロジェクトディレクトリ
            output_file: 出力ファイルパス

        Returns:
            出力ファイルパス
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # propsファイルを一時保存
        props_file = project_dir / "temp_props.json"
        with open(props_file, 'w', encoding='utf-8') as f:
            json.dump(props, f, ensure_ascii=False)

        cmd = [
            "npx",
            "remotion",
            "render",
            "Video",
            str(output_file),
            f"--props={props_file}"
        ]

        self.log(f"Rendering video: {output_file}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                check=True
            )
            self.log("Video rendering completed successfully")

            # 一時ファイルを削除
            if props_file.exists():
                props_file.unlink()

            return str(output_file)

        except subprocess.CalledProcessError as e:
            self.log(f"Rendering failed: {e.stderr}", "ERROR")
            raise

    def render_with_ffmpeg(self, slides: List[Dict], audio_files: List[str], output_file: Path) -> str:
        """
        FFmpegで簡易動画を生成（Remotionがない場合のフォールバック）

        Args:
            slides: スライドデータ
            audio_files: 音声ファイル
            output_file: 出力ファイルパス

        Returns:
            出力ファイルパス
        """
        self.log("Using FFmpeg fallback for video rendering")

        # 音声ファイルを結合
        concat_list = output_file.parent / "concat_list.txt"
        with open(concat_list, 'w') as f:
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    f.write(f"file '{audio_file}'\n")

        # 音声を結合
        combined_audio = output_file.parent / "combined_audio.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(combined_audio)
        ]

        subprocess.run(cmd, capture_output=True, check=True)

        # シンプルな動画を生成（背景色のみ）
        duration = self.get_audio_duration(str(combined_audio))
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0a0e1a:s=1920x1080:d={duration}",
            "-i", str(combined_audio),
            "-shortest",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output_file)
        ]

        subprocess.run(cmd, capture_output=True, check=True)

        # 一時ファイルを削除
        concat_list.unlink()
        combined_audio.unlink()

        self.log(f"Video created: {output_file}")
        return str(output_file)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルを実行

        Args:
            params:
                - slides: スライドデータのリスト
                - audio_files: 音声ファイルのリスト
                - output_file: 出力ファイルパス
                - remotion_project_dir: Remotionプロジェクトディレクトリ（オプション）
                - fps: フレームレート（デフォルト: 30）

        Returns:
            実行結果
                - video_file: 生成された動画ファイルパス
                - duration_sec: 動画の長さ（秒）
        """
        if not self.validate_params(params, ["slides", "audio_files", "output_file"]):
            raise ValueError("Missing required parameters")

        slides = params["slides"]
        audio_files = params["audio_files"]
        output_file = Path(params["output_file"])
        remotion_project_dir = params.get("remotion_project_dir")
        fps = params.get("fps", 30)

        # Remotionプロジェクトがあれば使用
        if remotion_project_dir and Path(remotion_project_dir).exists():
            props = self.prepare_video_props(slides, audio_files, fps)
            video_file = self.render_with_remotion(
                props,
                Path(remotion_project_dir),
                output_file
            )
            duration_sec = props["totalDurationSec"]
        else:
            # FFmpegフォールバック
            self.log("Remotion project not found, using FFmpeg fallback", "WARNING")
            video_file = self.render_with_ffmpeg(slides, audio_files, output_file)
            duration_sec = sum(
                self.get_audio_duration(f) for f in audio_files if os.path.exists(f)
            )

        return {
            "video_file": video_file,
            "duration_sec": duration_sec
        }
