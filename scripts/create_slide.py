#!/usr/bin/env python3
"""
スライド作成スクリプト
入力ファイルからMarp形式のMarkdownスライドを生成します
"""

import sys
import os
import re
import yaml
from pathlib import Path


# 絵文字をFontAwesomeアイコンに置換するマッピング
EMOJI_TO_FONTAWESOME = {
    # ニュース・レポート関連
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


def remove_all_emojis(text):
    """
    テキストからすべての絵文字を削除する（日本語は保持）
    """
    # 絵文字パターン（より限定的 - 日本語を除外）
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002702-\U000027B0"  # dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F000-\U0001F02F"  # Mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # Playing cards
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


def replace_emojis_with_fontawesome(text):
    """
    絵文字をFontAwesomeアイコンに置換、マッピングにない絵文字は削除
    """
    for emoji, fa_icon in EMOJI_TO_FONTAWESOME.items():
        text = text.replace(emoji, fa_icon)
    # マッピングにない残りの絵文字を削除
    text = remove_all_emojis(text)
    return text.strip()


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
    # FontAwesome CDN
    content.append("  @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');")
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
    # FontAwesomeアイコンスタイル
    content.append("  h1 i.fa-solid, h1 i.fa-regular, h1 i.fa-brands {")
    content.append("    margin-right: 15px;")
    content.append("    color: var(--primary-cyan);")
    content.append("    text-shadow: 0 0 15px var(--glow-cyan);")
    content.append("  }")
    content.append("")
    # サマリースライド用の幅広スタイル（classで適用）
    content.append("  section.summary p {")
    content.append("    max-width: 85%;")
    content.append("    width: 85%;")
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

        # 絵文字をFontAwesomeアイコンに置換
        title = replace_emojis_with_fontawesome(title)
        slide_content = replace_emojis_with_fontawesome(slide_content)

        # サマリースライドかどうか判定
        is_summary = 'サマリー' in title or 'summary' in title.lower()

        # サマリースライドの場合、コンテンツを200字程度に制限
        if is_summary and len(slide_content) > 220:
            # 200字で切り、最後の文を完結させる試み
            truncated = slide_content[:200]
            # 句点や読点で区切る
            last_period = max(truncated.rfind('。'), truncated.rfind('、'), truncated.rfind('.'))
            if last_period > 150:
                truncated = truncated[:last_period + 1]
            slide_content = truncated + '...'

        # サマリースライドの場合、クラスを追加
        if is_summary:
            content.append("<!-- _class: summary -->")

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
