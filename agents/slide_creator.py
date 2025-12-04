"""
SlideCreatorAgent（スライド作成役）
レポートの内容をスライドにするエージェント
"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from .base_agent import BaseAgent


class SlideCreatorAgent(BaseAgent):
    """レポートからスライドを作成するエージェント"""

    # 絵文字をFontAwesomeアイコンに置換するマッピング
    EMOJI_TO_FONTAWESOME = {
        '📋': '<i class="fa-solid fa-clipboard-list"></i>',
        '📰': '<i class="fa-solid fa-newspaper"></i>',
        '📊': '<i class="fa-solid fa-chart-bar"></i>',
        '📈': '<i class="fa-solid fa-chart-line"></i>',
        '📉': '<i class="fa-solid fa-chart-line-down"></i>',
        '🤖': '<i class="fa-solid fa-robot"></i>',
        '💡': '<i class="fa-solid fa-lightbulb"></i>',
        '🔍': '<i class="fa-solid fa-magnifying-glass"></i>',
        '⚡': '<i class="fa-solid fa-bolt"></i>',
        '🎯': '<i class="fa-solid fa-bullseye"></i>',
        '💰': '<i class="fa-solid fa-coins"></i>',
        '🏢': '<i class="fa-solid fa-building"></i>',
        '🌐': '<i class="fa-solid fa-globe"></i>',
        '🔒': '<i class="fa-solid fa-lock"></i>',
        '📱': '<i class="fa-solid fa-mobile-screen"></i>',
        '💻': '<i class="fa-solid fa-laptop"></i>',
        '🎬': '<i class="fa-solid fa-clapperboard"></i>',
        '🎥': '<i class="fa-solid fa-video"></i>',
        '✅': '<i class="fa-solid fa-check"></i>',
        '❌': '<i class="fa-solid fa-xmark"></i>',
        '⚠️': '<i class="fa-solid fa-triangle-exclamation"></i>',
        '🚀': '<i class="fa-solid fa-rocket"></i>',
        '📅': '<i class="fa-solid fa-calendar"></i>',
        '🔔': '<i class="fa-solid fa-bell"></i>',
        '💎': '<i class="fa-solid fa-gem"></i>',
        '🏆': '<i class="fa-solid fa-trophy"></i>',
        '📝': '<i class="fa-solid fa-pen-to-square"></i>',
        '🔧': '<i class="fa-solid fa-wrench"></i>',
        '⚙️': '<i class="fa-solid fa-gear"></i>',
        '🎉': '<i class="fa-solid fa-party-horn"></i>',
        '👍': '<i class="fa-solid fa-thumbs-up"></i>',
        '👎': '<i class="fa-solid fa-thumbs-down"></i>',
        '📌': '<i class="fa-solid fa-thumbtack"></i>',
        '🔗': '<i class="fa-solid fa-link"></i>',
        '📁': '<i class="fa-solid fa-folder"></i>',
        '📄': '<i class="fa-solid fa-file"></i>',
        '🖥️': '<i class="fa-solid fa-desktop"></i>',
        '🌟': '<i class="fa-solid fa-star"></i>',
        '⭐': '<i class="fa-solid fa-star"></i>',
    }

    def __init__(self, background_image: str = "images/slideBackground.png"):
        super().__init__(
            name="SlideCreatorAgent",
            description="スライド作成役 - レポートの内容をスライドにする"
        )
        self.skills = ["markdown_to_slide", "marp_generation", "layout_design"]
        self.background_image = background_image

    def remove_all_emojis(self, text: str) -> str:
        """テキストからすべての絵文字を削除（日本語は保持）"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002702-\U000027B0"
            "\U0000FE00-\U0000FE0F"
            "\U0001F000-\U0001F02F"
            "\U0001F0A0-\U0001F0FF"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    def replace_emojis_with_fontawesome(self, text: str) -> str:
        """絵文字をFontAwesomeアイコンに置換、マッピングにない絵文字は削除"""
        for emoji, fa_icon in self.EMOJI_TO_FONTAWESOME.items():
            text = text.replace(emoji, fa_icon)
        text = self.remove_all_emojis(text)
        return text.strip()

    def report_to_slides_prompt(self, report: str) -> str:
        """レポートからスライド構成を生成するプロンプト"""
        return f"""
あなたはプレゼンテーション作成の専門家です。
以下のレポートから、動画プレゼンテーション用のスライド構成を作成してください。

## レポート
{report}

## 要件
1. 5〜10枚程度のスライドで構成してください
2. 各スライドにはタイトルと内容を含めてください
3. 各スライドの内容は箇条書きで簡潔にしてください
4. 視聴者が理解しやすい順序で構成してください

## 出力フォーマット
以下のYAML形式で出力してください：

```yaml
topic: "プレゼンテーションのタイトル"
slides:
  - title: "スライド1のタイトル"
    content: |
      - ポイント1
      - ポイント2
      - ポイント3
  - title: "スライド2のタイトル"
    content: |
      - ポイント1
      - ポイント2
```

YAMLのみを出力してください。
"""

    def generate_marp_header(self) -> List[str]:
        """Marpスライドのヘッダーを生成"""
        content = []
        content.append("---")
        content.append("marp: true")
        content.append("theme: default")
        content.append("paginate: true")
        content.append("size: 16:9")
        content.append("style: |")
        content.append("  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');")
        content.append("  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');")
        content.append("")
        content.append("  :root {")
        content.append("    --primary-cyan: #00d4ff;")
        content.append("    --primary-cyan-dark: #0099cc;")
        content.append("    --glow-cyan: rgba(0, 212, 255, 0.6);")
        content.append("    --bg-dark: #0a0e1a;")
        content.append("    --bg-card: rgba(15, 23, 42, 0.85);")
        content.append("    --bg-content: rgba(8, 15, 30, 0.7);")
        content.append("    --text-white: #f8fafc;")
        content.append("    --text-gray: #cbd5e1;")
        content.append("  }")
        content.append("")
        content.append("  section {")
        content.append("    font-family: 'Noto Sans JP', 'Hiragino Sans', 'BIZ UDPGothic', sans-serif;")
        content.append(f"    background-image: url('{self.background_image}');")
        content.append("    background-size: cover;")
        content.append("    background-position: center;")
        content.append("    background-repeat: no-repeat;")
        content.append("    padding: 40px 60px;")
        content.append("    display: flex;")
        content.append("    flex-direction: column;")
        content.append("    justify-content: flex-start;")
        content.append("    position: relative;")
        content.append("    overflow: hidden;")
        content.append("  }")
        content.append("")
        content.append("  h1 {")
        content.append("    font-family: 'Noto Sans JP', sans-serif;")
        content.append("    font-weight: 900;")
        content.append("    font-size: 2.2em;")
        content.append("    color: var(--text-white);")
        content.append("    text-shadow:")
        content.append("      2px 2px 4px rgba(0, 0, 0, 0.9),")
        content.append("      4px 4px 8px rgba(0, 0, 0, 0.7),")
        content.append("      0 0 10px var(--glow-cyan),")
        content.append("      0 0 20px var(--glow-cyan);")
        content.append("    text-align: left;")
        content.append("    margin: 0 0 30px 0;")
        content.append("    padding-bottom: 15px;")
        content.append("    border-bottom: 2px solid var(--primary-cyan);")
        content.append("    position: relative;")
        content.append("    z-index: 10;")
        content.append("  }")
        content.append("")
        content.append("  p, ul, ol {")
        content.append("    background: var(--bg-card);")
        content.append("    backdrop-filter: blur(10px);")
        content.append("    -webkit-backdrop-filter: blur(10px);")
        content.append("    padding: 30px 40px;")
        content.append("    border-radius: 16px;")
        content.append("    border: 1px solid rgba(0, 212, 255, 0.3);")
        content.append("    box-shadow:")
        content.append("      0 0 20px rgba(0, 212, 255, 0.15),")
        content.append("      0 8px 32px rgba(0, 0, 0, 0.4),")
        content.append("      inset 0 1px 0 rgba(255, 255, 255, 0.05);")
        content.append("    color: var(--text-white);")
        content.append("    text-align: left;")
        content.append("    max-width: 90%;")
        content.append("    width: 90%;")
        content.append("    max-height: 65%;")
        content.append("    overflow: hidden;")
        content.append("    line-height: 1.8;")
        content.append("    font-size: 1.15em;")
        content.append("    font-weight: 400;")
        content.append("    position: relative;")
        content.append("    z-index: 10;")
        content.append("  }")
        content.append("")
        content.append("  ul, ol {")
        content.append("    margin-left: 0;")
        content.append("    padding-left: 60px;")
        content.append("  }")
        content.append("")
        content.append("  li {")
        content.append("    margin-bottom: 12px;")
        content.append("    position: relative;")
        content.append("  }")
        content.append("")
        content.append("  li::marker {")
        content.append("    color: var(--primary-cyan);")
        content.append("  }")
        content.append("")
        content.append("  strong {")
        content.append("    color: var(--primary-cyan);")
        content.append("    font-weight: 700;")
        content.append("  }")
        content.append("")
        content.append("  h1 i.fa-solid, h1 i.fa-regular, h1 i.fa-brands {")
        content.append("    margin-right: 15px;")
        content.append("    color: var(--primary-cyan);")
        content.append("    text-shadow: 0 0 15px var(--glow-cyan);")
        content.append("  }")
        content.append("")
        content.append("  section.summary p {")
        content.append("    max-width: 85%;")
        content.append("    width: 85%;")
        content.append("  }")
        content.append("")
        content.append("  section::after {")
        content.append("    font-size: 0.7em;")
        content.append("    color: var(--primary-cyan);")
        content.append("    text-shadow: 0 0 10px var(--glow-cyan);")
        content.append("  }")
        content.append("---")
        content.append("")
        return content

    def create_marp_slide(self, slides_data: Dict, output_dir: Path) -> str:
        """
        スライドデータからMarpスライドを作成

        Args:
            slides_data: スライドデータ（topic, slidesを含む）
            output_dir: 出力ディレクトリ

        Returns:
            生成されたスライドファイルのパス
        """
        topic = slides_data.get('topic', 'presentation')
        slides = slides_data.get('slides', [])

        # ファイル名を生成
        safe_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_file = output_dir / f"{safe_topic}_slide.md"

        content = self.generate_marp_header()

        # 各スライドを生成
        for i, slide in enumerate(slides):
            if i > 0:
                content.append("---")
                content.append("")

            title = slide.get('title', '')
            slide_content = slide.get('content', '')

            # 絵文字をFontAwesomeアイコンに置換
            title = self.replace_emojis_with_fontawesome(title)
            slide_content = self.replace_emojis_with_fontawesome(slide_content)

            # サマリースライドかどうか判定
            is_summary = 'サマリー' in title or 'summary' in title.lower()

            if is_summary and len(slide_content) > 220:
                truncated = slide_content[:200]
                last_period = max(truncated.rfind('。'), truncated.rfind('、'), truncated.rfind('.'))
                if last_period > 150:
                    truncated = truncated[:last_period + 1]
                slide_content = truncated + '...'

            if is_summary:
                content.append("<!-- _class: summary -->")

            if title:
                content.append(f"# {title}")
                content.append("")

            if slide_content:
                content.append(slide_content)
                content.append("")

        # ファイルに書き込む
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        self.log(f"Slide created: {output_file}")
        return str(output_file)

    def parse_yaml_from_response(self, response: str) -> Dict:
        """AIレスポンスからYAMLを抽出してパース"""
        # ```yaml ... ``` を抽出
        yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
        else:
            yaml_content = response

        return yaml.safe_load(yaml_content)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - report: レポート（Markdown形式）
                - slides_data: スライドデータ（YAMLから読み込んだ場合）

        Returns:
            実行結果
                - slide_file: 生成されたスライドファイルのパス
                - slides_data: スライドデータ
        """
        self.log("Starting slide creation...")

        slides_data = context.get("slides_data")

        if not slides_data:
            # レポートからスライドを生成
            report = context.get("report", "")
            if not report:
                raise ValueError("No report or slides_data provided")

            self.log("Generating slide structure from report...")
            prompt = self.report_to_slides_prompt(report)
            response = self.generate(prompt)
            slides_data = self.parse_yaml_from_response(response)

        # 出力ディレクトリ
        output_dir = self.base_dir / "presentations" / datetime.now().strftime("%Y_%m_%d")

        # Marpスライドを作成
        slide_file = self.create_marp_slide(slides_data, output_dir)

        result = {
            "slide_file": slide_file,
            "slides_data": slides_data,
            "output_dir": str(output_dir)
        }

        self.log("Slide creation completed.")
        return result
