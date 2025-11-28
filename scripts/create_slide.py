#!/usr/bin/env python3
"""
スライド作成スクリプト
入力ファイルからMarp形式のMarkdownスライドを生成します
"""

import sys
import os
import yaml
from pathlib import Path


def create_marp_slide(input_file, output_dir):
    """
    入力ファイルからMarpスライドを作成

    Args:
        input_file: 入力YAMLファイルのパス
        output_dir: 出力ディレクトリ

    Returns:
        生成されたスライドファイルのパス
    """
    # 入力ファイルを読み込む
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    topic = data.get('topic', 'presentation')
    slides = data.get('slides', [])

    # ファイル名を生成（トピック名からスペースやスラッシュを除去）
    safe_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_')
    output_file = Path(output_dir) / f"{safe_topic}_slide.md"

    # Marpスライドの内容を生成
    content = []

    # Marp設定ヘッダー with サイバーパンク/テックニュース風カスタムスタイル
    content.append("---")
    content.append("marp: true")
    content.append("theme: default")
    content.append("paginate: true")
    content.append("size: 16:9")
    content.append("style: |")
    # Google Fonts インポート
    content.append("  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');")
    content.append("")
    # CSS変数定義
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
    # メインセクション - ダークテック背景
    content.append("  section {")
    content.append("    font-family: 'Noto Sans JP', 'Hiragino Sans', 'BIZ UDPGothic', sans-serif;")
    content.append("    background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 50%, #0d1525 100%);")
    content.append("    padding: 40px 60px;")
    content.append("    display: flex;")
    content.append("    flex-direction: column;")
    content.append("    justify-content: flex-start;")
    content.append("    position: relative;")
    content.append("    overflow: hidden;")
    content.append("  }")
    content.append("")
    # 背景装飾 - グリッドパターン
    content.append("  section::before {")
    content.append("    content: '';")
    content.append("    position: absolute;")
    content.append("    top: 0;")
    content.append("    left: 0;")
    content.append("    right: 0;")
    content.append("    bottom: 0;")
    content.append("    background-image:")
    content.append("      linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),")
    content.append("      linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);")
    content.append("    background-size: 50px 50px;")
    content.append("    pointer-events: none;")
    content.append("  }")
    content.append("")
    # タイトル（h1）- ネオン光彩効果
    content.append("  h1 {")
    content.append("    font-family: 'Noto Sans JP', sans-serif;")
    content.append("    font-weight: 900;")
    content.append("    font-size: 2.2em;")
    content.append("    color: var(--text-white);")
    content.append("    text-shadow:")
    content.append("      0 0 10px var(--glow-cyan),")
    content.append("      0 0 20px var(--glow-cyan),")
    content.append("      0 0 40px rgba(0, 212, 255, 0.3);")
    content.append("    text-align: left;")
    content.append("    margin: 0 0 30px 0;")
    content.append("    padding-bottom: 15px;")
    content.append("    border-bottom: 2px solid var(--primary-cyan);")
    content.append("    position: relative;")
    content.append("    z-index: 10;")
    content.append("  }")
    content.append("")
    # コンテンツカード - ガラスモーフィズム効果
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
    # リスト専用スタイル
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
    # 強調テキスト
    content.append("  strong {")
    content.append("    color: var(--primary-cyan);")
    content.append("    font-weight: 700;")
    content.append("  }")
    content.append("")
    # ページネーション
    content.append("  section::after {")
    content.append("    font-size: 0.7em;")
    content.append("    color: var(--primary-cyan);")
    content.append("    text-shadow: 0 0 10px var(--glow-cyan);")
    content.append("  }")
    content.append("")
    # コーナーアクセント装飾
    content.append("  section > *:first-child::before {")
    content.append("    content: '';")
    content.append("    position: absolute;")
    content.append("    top: -2px;")
    content.append("    left: -2px;")
    content.append("    width: 30px;")
    content.append("    height: 30px;")
    content.append("    border-top: 3px solid var(--primary-cyan);")
    content.append("    border-left: 3px solid var(--primary-cyan);")
    content.append("    box-shadow: -5px -5px 15px var(--glow-cyan);")
    content.append("  }")
    content.append("")
    content.append("  section > *:first-child::after {")
    content.append("    content: '';")
    content.append("    position: absolute;")
    content.append("    bottom: -2px;")
    content.append("    right: -2px;")
    content.append("    width: 30px;")
    content.append("    height: 30px;")
    content.append("    border-bottom: 3px solid var(--primary-cyan);")
    content.append("    border-right: 3px solid var(--primary-cyan);")
    content.append("    box-shadow: 5px 5px 15px var(--glow-cyan);")
    content.append("  }")
    content.append("---")
    content.append("")

    # 各スライドを生成
    for i, slide in enumerate(slides):
        if i > 0:
            content.append("---")
            content.append("")

        title = slide.get('title', '')
        slide_content = slide.get('content', '')

        # タイトル
        if title:
            content.append(f"# {title}")
            content.append("")

        # コンテンツ
        if slide_content:
            content.append(slide_content)
            content.append("")

    # ファイルに書き込む
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    print(f"スライドを作成しました: {output_file}")
    return str(output_file)


def main():
    if len(sys.argv) < 2:
        print("使用方法: python create_slide.py <input_yaml_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        sys.exit(1)

    # 出力ディレクトリ
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "slides"
    output_dir.mkdir(exist_ok=True)

    # スライドを作成
    slide_file = create_marp_slide(input_file, output_dir)

    # 次のステップのために環境変数に保存
    if 'GITHUB_ENV' in os.environ:
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"SLIDE_FILE={slide_file}\n")
            # トピック名も保存
            with open(input_file, 'r', encoding='utf-8') as input_f:
                data = yaml.safe_load(input_f)
                topic = data.get('topic', 'presentation')
                safe_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_')
                f.write(f"TOPIC_NAME={safe_topic}\n")


if __name__ == "__main__":
    main()
