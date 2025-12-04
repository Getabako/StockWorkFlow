"""
AudioSynthesisSkill
テキストから音声を合成するスキル
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List
from .base_skill import BaseSkill


class AudioSynthesisSkill(BaseSkill):
    """テキストから音声を合成するスキル"""

    # 利用可能な日本語音声
    JAPANESE_VOICES = {
        "nanami": "ja-JP-NanamiNeural",  # 女性
        "keita": "ja-JP-KeitaNeural",    # 男性
    }

    def __init__(self, default_voice: str = "nanami"):
        super().__init__(
            name="audio_synthesis",
            description="テキストから音声を合成する（Edge TTS使用）"
        )
        self.default_voice = self.JAPANESE_VOICES.get(default_voice, default_voice)

    async def synthesize_single(self, text: str, output_file: Path, voice: str) -> Dict[str, Any]:
        """
        単一のテキストを音声に変換

        Args:
            text: 変換するテキスト
            output_file: 出力ファイルパス
            voice: 使用する音声

        Returns:
            生成結果
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge_tts is required. Install with: pip install edge-tts")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_file))

        return {
            "file": str(output_file),
            "text_length": len(text),
            "voice": voice
        }

    def synthesize_batch(self, texts: List[Dict], output_dir: Path, voice: str = None) -> List[Dict]:
        """
        複数のテキストを音声に変換

        Args:
            texts: テキストのリスト [{index, text}, ...]
            output_dir: 出力ディレクトリ
            voice: 使用する音声

        Returns:
            生成結果のリスト
        """
        voice = voice or self.default_voice
        output_dir.mkdir(parents=True, exist_ok=True)

        async def process_all():
            results = []
            for item in texts:
                idx = item.get("index", len(results) + 1)
                text = item.get("text", "")
                output_file = output_dir / f"audio_{idx:02d}.mp3"

                result = await self.synthesize_single(text, output_file, voice)
                result["index"] = idx
                results.append(result)
                self.log(f"Generated audio {idx}: {output_file.name}")

            return results

        return asyncio.run(process_all())

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルを実行

        Args:
            params:
                - texts: テキストのリスト [{index, text}, ...]
                - output_dir: 出力ディレクトリ
                - voice: 使用する音声（オプション）

        Returns:
            実行結果
                - audio_files: 生成された音声ファイルのリスト
                - total_count: 生成数
        """
        if not self.validate_params(params, ["texts", "output_dir"]):
            raise ValueError("Missing required parameters: texts, output_dir")

        texts = params["texts"]
        output_dir = Path(params["output_dir"])
        voice = params.get("voice", self.default_voice)

        self.log(f"Synthesizing {len(texts)} audio files")

        audio_files = self.synthesize_batch(texts, output_dir, voice)

        return {
            "audio_files": audio_files,
            "total_count": len(audio_files),
            "output_dir": str(output_dir)
        }
