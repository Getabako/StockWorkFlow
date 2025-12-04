"""
VideoEditorAgent（動画編集者）
スライドの画像にキャラや字幕、音声を載せて動画にするエージェント
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class VideoEditorAgent(BaseAgent):
    """動画を編集・作成するエージェント"""

    def __init__(self):
        super().__init__(
            name="VideoEditorAgent",
            description="動画編集者 - スライドの画像にキャラや字幕、音声を載せて動画にする"
        )
        self.skills = [
            "audio_generation",
            "timing_extraction",
            "video_composition",
            "subtitle_overlay",
            "character_animation"
        ]

    def generate_audio(self, scripts: List[Dict], output_dir: Path, voice: str = "ja-JP-NanamiNeural") -> List[Dict]:
        """
        スクリプトから音声を生成

        Args:
            scripts: スクリプトのリスト
            output_dir: 出力ディレクトリ
            voice: 使用する音声

        Returns:
            音声ファイル情報のリスト
        """
        audio_files = []
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            import edge_tts
            import asyncio
        except ImportError:
            self.log("edge_tts not installed. Please install it with: pip install edge-tts", "ERROR")
            raise

        async def generate_single_audio(script: Dict, idx: int) -> Dict:
            text = script.get('script', '')
            output_file = output_dir / f"slide_{idx + 1:02d}.mp3"

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_file))

            return {
                "index": idx + 1,
                "title": script.get('title', ''),
                "audio_file": str(output_file),
                "text": text
            }

        async def generate_all():
            tasks = [generate_single_audio(script, idx) for idx, script in enumerate(scripts)]
            return await asyncio.gather(*tasks)

        audio_files = asyncio.run(generate_all())
        self.log(f"Generated {len(audio_files)} audio files")
        return audio_files

    def extract_timings(self, audio_files: List[Dict]) -> List[Dict]:
        """
        音声ファイルからタイミング情報を抽出

        Args:
            audio_files: 音声ファイル情報のリスト

        Returns:
            タイミング情報のリスト
        """
        timings = []

        try:
            from pydub import AudioSegment
        except ImportError:
            self.log("pydub not installed. Please install it with: pip install pydub", "ERROR")
            raise

        for audio_info in audio_files:
            audio_path = audio_info.get('audio_file')
            if audio_path and os.path.exists(audio_path):
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
                duration_sec = duration_ms / 1000.0

                timings.append({
                    "index": audio_info.get('index'),
                    "title": audio_info.get('title'),
                    "duration_ms": duration_ms,
                    "duration_sec": duration_sec,
                    "audio_file": audio_path
                })

        self.log(f"Extracted timings for {len(timings)} audio files")
        return timings

    def prepare_video_data(self, slides_data: Dict, scripts: List[Dict], timings: List[Dict], output_dir: Path) -> Dict:
        """
        Remotion用のビデオデータを準備

        Args:
            slides_data: スライドデータ
            scripts: スクリプトのリスト
            timings: タイミング情報のリスト
            output_dir: 出力ディレクトリ

        Returns:
            ビデオ生成用のデータ
        """
        fps = 30
        slides_info = []
        total_duration_frames = 0

        for i, timing in enumerate(timings):
            duration_frames = int(timing['duration_sec'] * fps) + fps  # 1秒のバッファを追加

            script_text = ""
            if i < len(scripts):
                script_text = scripts[i].get('script', '')

            slides_info.append({
                "index": i + 1,
                "title": timing.get('title', f'Slide {i + 1}'),
                "audioFile": timing.get('audio_file', ''),
                "durationFrames": duration_frames,
                "startFrame": total_duration_frames,
                "script": script_text
            })

            total_duration_frames += duration_frames

        video_data = {
            "fps": fps,
            "totalFrames": total_duration_frames,
            "totalDurationSec": total_duration_frames / fps,
            "slides": slides_info,
            "outputDir": str(output_dir)
        }

        # タイミングファイルを保存
        timings_file = output_dir / "video_timings.json"
        with open(timings_file, 'w', encoding='utf-8') as f:
            json.dump(video_data, f, ensure_ascii=False, indent=2)

        self.log(f"Video data prepared: {total_duration_frames} frames ({total_duration_frames / fps:.1f}s)")
        return video_data

    def render_video(self, video_data: Dict, remotion_project_dir: Path, output_file: Path) -> str:
        """
        Remotionを使用して動画をレンダリング

        Args:
            video_data: ビデオデータ
            remotion_project_dir: Remotionプロジェクトディレクトリ
            output_file: 出力ファイルパス

        Returns:
            生成された動画ファイルのパス
        """
        self.log("Starting video rendering with Remotion...")

        # Remotionプロジェクトがあるか確認
        if not remotion_project_dir.exists():
            self.log(f"Remotion project not found: {remotion_project_dir}", "ERROR")
            raise FileNotFoundError(f"Remotion project not found: {remotion_project_dir}")

        # npxでremotion renderを実行
        cmd = [
            "npx",
            "remotion",
            "render",
            "Video",
            str(output_file),
            f"--props={json.dumps(video_data)}"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(remotion_project_dir),
                capture_output=True,
                text=True,
                check=True
            )
            self.log(f"Video rendered successfully: {output_file}")
            return str(output_file)
        except subprocess.CalledProcessError as e:
            self.log(f"Video rendering failed: {e.stderr}", "ERROR")
            raise

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - scripts: スクリプトのリスト
                - slides_data: スライドデータ
                - slide_images_dir: スライド画像のディレクトリ
                - output_dir: 出力ディレクトリ

        Returns:
            実行結果
                - video_file: 生成された動画ファイルのパス
                - audio_files: 音声ファイルのリスト
                - timings: タイミング情報
        """
        self.log("Starting video editing...")

        scripts = context.get("scripts", [])
        slides_data = context.get("slides_data", {})
        output_dir = Path(context.get("output_dir", self.output_dir / "video"))
        output_dir.mkdir(parents=True, exist_ok=True)

        if not scripts:
            raise ValueError("No scripts provided")

        # 1. 音声を生成
        self.log("Step 1: Generating audio...")
        audio_dir = output_dir / "audio"
        audio_files = self.generate_audio(scripts, audio_dir)

        # 2. タイミングを抽出
        self.log("Step 2: Extracting timings...")
        timings = self.extract_timings(audio_files)

        # 3. ビデオデータを準備
        self.log("Step 3: Preparing video data...")
        video_data = self.prepare_video_data(slides_data, scripts, timings, output_dir)

        # 4. 動画をレンダリング（Remotionプロジェクトがある場合）
        remotion_project_dir = self.base_dir / "remotion-project"
        video_file = None

        if remotion_project_dir.exists() and context.get("render_video", True):
            self.log("Step 4: Rendering video...")
            output_video = output_dir / "output.mp4"
            try:
                video_file = self.render_video(video_data, remotion_project_dir, output_video)
            except Exception as e:
                self.log(f"Video rendering skipped: {e}", "WARNING")
        else:
            self.log("Step 4: Video rendering skipped (Remotion project not found or disabled)")

        result = {
            "video_file": video_file,
            "audio_files": audio_files,
            "timings": timings,
            "video_data": video_data,
            "output_dir": str(output_dir)
        }

        self.log("Video editing completed.")
        return result
