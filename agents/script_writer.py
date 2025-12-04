"""
ScriptWriterAgent（脚本家）
スライドから動画のシナリオを考えるエージェント
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ScriptWriterAgent(BaseAgent):
    """スライドから動画脚本を作成するエージェント"""

    def __init__(self):
        super().__init__(
            name="ScriptWriterAgent",
            description="脚本家 - スライドから動画のシナリオを考える"
        )
        self.skills = ["script_writing", "narration_generation", "timing_planning"]

    def parse_marp_slides(self, slide_file: str) -> List[Dict]:
        """
        Marp形式のMarkdownスライドを解析してスライドごとに分割

        Args:
            slide_file: スライドファイルのパス

        Returns:
            スライドのリスト
        """
        with open(slide_file, 'r', encoding='utf-8') as f:
            content = f.read()

        slides_raw = content.split('---')
        slides = []

        for slide_raw in slides_raw:
            slide_raw = slide_raw.strip()
            if not slide_raw or slide_raw.startswith('marp:'):
                continue

            lines = slide_raw.split('\n')
            title = ''
            content_lines = []

            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                elif line.strip():
                    if not (line.strip().startswith('<style>') or
                            line.strip().startswith('</style>') or
                            line.strip().startswith('![') or
                            line.strip().startswith('@import') or
                            line.strip().startswith('section {') or
                            line.strip().startswith('h1,') or
                            line.strip().startswith('font-family:') or
                            line.strip() == '}'):
                        content_lines.append(line)

            content_text = '\n'.join(content_lines).strip()
            if not title and not content_text:
                continue

            slides.append({
                'index': len(slides) + 1,
                'title': title,
                'content': content_text
            })

        return slides

    def clean_declarative_phrases(self, script: str) -> str:
        """原稿から不要な宣言的フレーズを削除"""
        patterns_to_remove = [
            r'^.*?原稿を作成.*?[。\n]',
            r'^.*?スライド\d+.*?[。\n]',
            r'^(では|それでは|次に|続いて|さて|それから)[、，]?.*?[。\n]',
            r'^.*?(このスライド|今回|今日|本日|ここ)(では|で|から|について).*?[。\n]',
            r'^.*?(ご紹介|説明|見て|ご覧|解説)(します|いたします|しましょう|ください).*?[。\n]',
        ]

        cleaned = script
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        return cleaned.lstrip('\n').strip()

    def generate_script_for_slide(self, slide: Dict, total_slides: int, max_retries: int = 3) -> str:
        """
        1枚のスライドに対する原稿を生成

        Args:
            slide: スライド情報
            total_slides: 総スライド数
            max_retries: 最大リトライ回数

        Returns:
            生成された原稿テキスト
        """
        prompt = f"""
あなたはプレゼンテーションの原稿を作成する専門家です。
以下のスライド情報から、自然で分かりやすい原稿を日本語で作成してください。

スライド番号: {slide['index']} / {total_slides}
タイトル: {slide['title']}
内容:
{slide['content']}

要件:
1. 自然な話し言葉で書いてください
2. 1スライドあたり30〜60秒程度の長さにしてください
3. 箇条書きは自然な文章に変換してください
4. 聞き手に語りかけるような口調にしてください
5. 「えー」「あのー」などの言葉は入れないでください
6. スライド番号や「このスライドでは」などの言及は避けてください

原稿のみを出力してください（説明や補足は不要です）。
"""

        for attempt in range(max_retries):
            try:
                script = self.generate(prompt)
                return self.clean_declarative_phrases(script)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 45 if "ResourceExhausted" in str(e) else 10
                    self.log(f"Error (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}", "WARNING")
                    self.log(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    self.log(f"Max retries reached. Error: {e}", "ERROR")
                    raise

    def generate_full_script(self, slides: List[Dict]) -> List[Dict]:
        """
        すべてのスライドの原稿を生成

        Args:
            slides: スライドのリスト

        Returns:
            各スライドの原稿を含むリスト
        """
        scripts = []
        total_slides = len(slides)

        for i, slide in enumerate(slides):
            self.log(f"Generating script: Slide {slide['index']} - {slide['title']}")
            script = self.generate_script_for_slide(slide, total_slides)

            scripts.append({
                'index': slide['index'],
                'title': slide['title'],
                'script': script
            })

            self.log(f"Generated: {len(script)} characters")

            # レート制限対策
            if i < len(slides) - 1:
                time.sleep(7)

        return scripts

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - slide_file: スライドファイルのパス
                - script_notes: 既存のスクリプトノート（オプション）

        Returns:
            実行結果
                - scripts: 生成された原稿のリスト
                - script_file: 保存されたスクリプトファイルのパス
        """
        self.log("Starting script writing...")

        # 既存のスクリプトノートがあれば使用
        script_notes = context.get("script_notes")
        if script_notes:
            self.log(f"Using provided script_notes ({len(script_notes)} slides)")
            scripts = script_notes
        else:
            # スライドファイルから生成
            slide_file = context.get("slide_file")
            if not slide_file:
                raise ValueError("No slide_file or script_notes provided")

            self.log(f"Parsing slides: {slide_file}")
            slides = self.parse_marp_slides(slide_file)
            self.log(f"Found {len(slides)} slides")

            scripts = self.generate_full_script(slides)

        # 結果を保存
        output_data = {
            'slides': scripts,
            'total_slides': len(scripts)
        }

        script_file = self.save_output(output_data, "scripts/script.json")

        # テキスト版も保存
        text_content = ""
        for script in scripts:
            text_content += f"=== スライド {script['index']}: {script['title']} ===\n\n"
            text_content += script['script']
            text_content += "\n\n"

        self.save_output(text_content, "scripts/script.txt", as_json=False)

        result = {
            "scripts": scripts,
            "script_file": str(script_file),
            "total_slides": len(scripts)
        }

        self.log("Script writing completed.")
        return result
