"""
SlideGenerationSkill
Marp形式のスライドを生成するスキル
"""

import re
from pathlib import Path
from typing import Dict, Any, List
from .base_skill import BaseSkill


class SlideGenerationSkill(BaseSkill):
    """Marpスライドを生成するスキル"""

    # 絵文字からFontAwesomeへのマッピング
    EMOJI_MAP = {
        '📋': '<i class="fa-solid fa-clipboard-list"></i>',
        '📰': '<i class="fa-solid fa-newspaper"></i>',
        '📊': '<i class="fa-solid fa-chart-bar"></i>',
        '📈': '<i class="fa-solid fa-chart-line"></i>',
        '🤖': '<i class="fa-solid fa-robot"></i>',
        '💡': '<i class="fa-solid fa-lightbulb"></i>',
        '🔍': '<i class="fa-solid fa-magnifying-glass"></i>',
        '⚡': '<i class="fa-solid fa-bolt"></i>',
        '🎯': '<i class="fa-solid fa-bullseye"></i>',
        '💰': '<i class="fa-solid fa-coins"></i>',
        '🏢': '<i class="fa-solid fa-building"></i>',
        '🌐': '<i class="fa-solid fa-globe"></i>',
        '🚀': '<i class="fa-solid fa-rocket"></i>',
        '✅': '<i class="fa-solid fa-check"></i>',
        '❌': '<i class="fa-solid fa-xmark"></i>',
        '⚠️': '<i class="fa-solid fa-triangle-exclamation"></i>',
    }

    def __init__(self, background_image: str = "images/slideBackground.png"):
        super().__init__(
            name="slide_generation",
            description="Marp形式のスライドを生成する"
        )
        self.background_image = background_image

    def replace_emojis(self, text: str) -> str:
        """絵文字をFontAwesomeアイコンに置換"""
        for emoji, icon in self.EMOJI_MAP.items():
            text = text.replace(emoji, icon)

        # 残りの絵文字を削除
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U0001F900-\U0001F9FF"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text).strip()

    def generate_header(self) -> str:
        """Marpスライドのヘッダーを生成"""
        # スライドがslidesディレクトリに生成されるため、相対パスを調整
        bg_path = self.background_image
        if not bg_path.startswith('../') and not bg_path.startswith('/'):
            bg_path = f"../{bg_path}"
        return f"""---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');

  :root {{
    --primary-cyan: #00d4ff;
    --glow-cyan: rgba(0, 212, 255, 0.6);
    --bg-card: rgba(15, 23, 42, 0.85);
    --text-white: #f8fafc;
  }}

  section {{
    font-family: 'Noto Sans JP', sans-serif;
    background-image: url('{bg_path}');
    background-size: cover;
    background-position: center;
    padding: 40px 60px;
  }}

  h1 {{
    font-weight: 900;
    font-size: 2.2em;
    color: var(--text-white);
    text-shadow: 0 0 10px var(--glow-cyan), 0 0 20px var(--glow-cyan);
    border-bottom: 2px solid var(--primary-cyan);
    padding-bottom: 15px;
    margin-bottom: 30px;
  }}

  p, ul, ol {{
    background: var(--bg-card);
    backdrop-filter: blur(10px);
    padding: 30px 40px;
    border-radius: 16px;
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: var(--text-white);
    line-height: 1.8;
    font-size: 1.15em;
  }}

  strong {{
    color: var(--primary-cyan);
  }}

  li::marker {{
    color: var(--primary-cyan);
  }}
---

"""

    def generate_slide(self, title: str, content: str) -> str:
        """単一のスライドを生成"""
        title = self.replace_emojis(title)
        content = self.replace_emojis(content)

        slide = ""
        if title:
            slide += f"# {title}\n\n"
        if content:
            slide += f"{content}\n"

        return slide

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルを実行

        Args:
            params:
                - slides: スライドデータのリスト [{title, content}, ...]
                - topic: プレゼンテーションのトピック
                - output_path: 出力ファイルパス（オプション）

        Returns:
            実行結果
                - markdown: 生成されたMarkdown
                - output_file: 保存されたファイルパス（output_pathが指定された場合）
        """
        if not self.validate_params(params, ["slides"]):
            raise ValueError("Missing required parameter: slides")

        slides = params["slides"]
        output_path = params.get("output_path")

        self.log(f"Generating {len(slides)} slides")

        # Markdownを生成
        markdown = self.generate_header()

        for i, slide_data in enumerate(slides):
            if i > 0:
                markdown += "---\n\n"

            title = slide_data.get("title", "")
            content = slide_data.get("content", "")
            markdown += self.generate_slide(title, content)
            markdown += "\n"

        result = {
            "markdown": markdown,
            "slide_count": len(slides)
        }

        # ファイルに保存（オプション）
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            result["output_file"] = str(output_file)
            self.log(f"Saved to: {output_file}")

        return result
