"""
ImageGeneratorAgent（画像生成役）
スライドに挿入する画像を生成するエージェント
"""

import os
import csv
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from io import BytesIO
from .base_agent import BaseAgent


class ImageGeneratorAgent(BaseAgent):
    """スライド用の画像を生成するエージェント"""

    def __init__(self, character_dir: str = "presentations/character"):
        super().__init__(
            name="ImageGeneratorAgent",
            description="画像生成役 - スライドに挿入する画像を生成する"
        )
        self.skills = ["image_generation", "character_integration", "prompt_enhancement"]
        self.character_dir = Path(character_dir) if character_dir else None
        self._genai_client = None
        self.character_images: Dict[str, Path] = {}

    def _init_genai_client(self):
        """Google GenAI クライアントを初期化"""
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            self._genai_client = genai.Client(api_key=api_key)
            self._load_character_images()
        except ImportError:
            self.log("google-genai not installed. Install with: pip install google-genai", "ERROR")
            raise

    @property
    def genai_client(self):
        """遅延初期化されたGenAIクライアント"""
        if self._genai_client is None:
            self._init_genai_client()
        return self._genai_client

    def _load_character_images(self):
        """キャラクター画像を読み込む"""
        if not self.character_dir or not self.character_dir.exists():
            self.log(f"Character directory not found: {self.character_dir}", "WARNING")
            return

        for char_folder in self.character_dir.iterdir():
            if not char_folder.is_dir() or char_folder.name == 'ロゴ':
                continue

            image_files = list(char_folder.glob('*.png')) + list(char_folder.glob('*.jpg'))
            if image_files:
                self.character_images[char_folder.name] = image_files[0]

        self.log(f"Loaded {len(self.character_images)} character images")

    def get_character_image_path(self, character_name: str) -> Optional[Path]:
        """キャラクター名から画像パスを取得"""
        for name, path in self.character_images.items():
            if character_name in name:
                return path
        return None

    def generate_image_prompts(self, slides_data: Dict) -> List[Dict]:
        """
        スライドデータから画像生成用のプロンプトを生成

        Args:
            slides_data: スライドデータ

        Returns:
            画像プロンプトのリスト
        """
        slides = slides_data.get('slides', [])
        prompts = []

        prompt_template = """
以下のスライド情報から、スライドに挿入する画像の生成プロンプトを英語で作成してください。

スライドタイトル: {title}
スライド内容: {content}

要件:
1. シンプルでクリーンなビジュアルを生成するプロンプトを作成
2. テキストや文字は含めない
3. ビジネス/テクノロジーの文脈に適した画像
4. 16:9のアスペクト比に適したレイアウト

プロンプトのみを出力してください。
"""

        for i, slide in enumerate(slides):
            title = slide.get('title', f'Slide {i+1}')
            content = slide.get('content', '')

            prompt = prompt_template.format(title=title, content=content)
            response = self.generate(prompt)

            prompts.append({
                'slide_number': f"{i+1:03d}",
                'title': title,
                'prompt': response.strip(),
                'character': slide.get('character', 'なし'),
                'aspect_ratio': '16:9'
            })

            # レート制限対策
            if i < len(slides) - 1:
                time.sleep(2)

        return prompts

    def generate_single_image(
        self,
        prompt: str,
        character: str,
        aspect_ratio: str,
        output_path: Path
    ) -> bool:
        """
        単一の画像を生成

        Args:
            prompt: 画像生成プロンプト
            character: キャラクター名
            aspect_ratio: アスペクト比
            output_path: 出力パス

        Returns:
            成功した場合True
        """
        try:
            from google.genai import types
            from PIL import Image
        except ImportError:
            self.log("Required packages not installed", "ERROR")
            return False

        character_image_path = None
        if character and character != 'なし':
            character_image_path = self.get_character_image_path(character)

        no_text_instruction = "\n\nIMPORTANT: Do not include any text, letters, words, signs, labels, or written content in the image. Keep the image purely visual without any typography. When generating people, default to Japanese people unless otherwise specified."

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.log(f"Generating image (attempt {attempt + 1}/{max_retries})...")

                if character_image_path and character_image_path.exists():
                    # Image-to-image生成（キャラクター付き）
                    self.log(f"Using character: {character_image_path.name}")

                    with open(character_image_path, 'rb') as f:
                        character_image_data = f.read()

                    enhanced_prompt = f"{prompt}\n\nInclude the character from the reference image in the scene.{no_text_instruction}"

                    response = self.genai_client.models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=[
                            types.Part.from_bytes(
                                data=character_image_data,
                                mime_type="image/png"
                            ),
                            enhanced_prompt
                        ],
                        config=types.GenerateContentConfig(
                            image_config=types.ImageConfig(
                                aspect_ratio=aspect_ratio,
                            )
                        )
                    )
                else:
                    # Text-to-image生成
                    text_prompt = f"{prompt}{no_text_instruction}"
                    response = self.genai_client.models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=[text_prompt],
                        config=types.GenerateContentConfig(
                            image_config=types.ImageConfig(
                                aspect_ratio=aspect_ratio,
                            )
                        )
                    )

                # 画像を保存
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        image = Image.open(BytesIO(part.inline_data.data))
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image.save(output_path)
                        self.log(f"Image saved: {output_path.name} ({image.size[0]}x{image.size[1]})")
                        return True

                self.log("No image data in response", "WARNING")
                time.sleep(2)

            except Exception as e:
                self.log(f"Error: {type(e).__name__}: {str(e)[:100]}", "ERROR")
                if attempt < max_retries - 1:
                    self.log("Retrying in 2 seconds...")
                    time.sleep(2)

        return False

    def generate_images_from_prompts(self, prompts: List[Dict], output_dir: Path) -> List[Dict]:
        """
        プロンプトリストから画像を生成

        Args:
            prompts: プロンプトのリスト
            output_dir: 出力ディレクトリ

        Returns:
            生成結果のリスト
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for i, prompt_data in enumerate(prompts):
            slide_number = prompt_data.get('slide_number', f"{i+1:03d}")
            title = prompt_data.get('title', f'Slide {i+1}')
            prompt = prompt_data.get('prompt', '')
            character = prompt_data.get('character', 'なし')
            aspect_ratio = prompt_data.get('aspect_ratio', '16:9')

            output_path = output_dir / f"{slide_number}.png"

            self.log(f"[{i+1}/{len(prompts)}] {title}")

            success = self.generate_single_image(
                prompt=prompt,
                character=character,
                aspect_ratio=aspect_ratio,
                output_path=output_path
            )

            results.append({
                'slide_number': slide_number,
                'title': title,
                'success': success,
                'output_path': str(output_path) if success else None
            })

            # API rate limit対策
            if i < len(prompts) - 1:
                time.sleep(2)

        return results

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - slides_data: スライドデータ
                - image_prompts: 画像プロンプトのリスト（オプション）
                - prompts_csv: プロンプトCSVファイルパス（オプション）
                - output_dir: 出力ディレクトリ

        Returns:
            実行結果
                - generated_images: 生成された画像のリスト
                - success_count: 成功数
                - output_dir: 出力ディレクトリ
        """
        self.log("Starting image generation...")

        output_dir = Path(context.get("output_dir", self.output_dir / "images"))

        # プロンプトの取得方法を決定
        prompts = context.get("image_prompts")

        if not prompts:
            # CSVファイルから読み込む
            prompts_csv = context.get("prompts_csv")
            if prompts_csv and Path(prompts_csv).exists():
                self.log(f"Loading prompts from CSV: {prompts_csv}")
                prompts = []
                with open(prompts_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        prompts.append({
                            'slide_number': row.get('slide_number', '001'),
                            'title': row.get('title', ''),
                            'prompt': row.get('prompt', ''),
                            'character': row.get('character', 'なし'),
                            'aspect_ratio': row.get('aspect_ratio', '16:9')
                        })

        if not prompts:
            # スライドデータから生成
            slides_data = context.get("slides_data")
            if slides_data:
                self.log("Generating prompts from slides data...")
                prompts = self.generate_image_prompts(slides_data)
            else:
                raise ValueError("No image_prompts, prompts_csv, or slides_data provided")

        # 画像を生成
        self.log(f"Generating {len(prompts)} images...")
        results = self.generate_images_from_prompts(prompts, output_dir)

        success_count = sum(1 for r in results if r['success'])

        result = {
            "generated_images": results,
            "success_count": success_count,
            "total_count": len(prompts),
            "output_dir": str(output_dir)
        }

        # プロンプトも保存
        prompts_output = output_dir / "image_prompts.csv"
        with open(prompts_output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['slide_number', 'title', 'prompt', 'character', 'aspect_ratio'])
            writer.writeheader()
            writer.writerows(prompts)

        self.log(f"Image generation completed: {success_count}/{len(prompts)} succeeded")
        return result
