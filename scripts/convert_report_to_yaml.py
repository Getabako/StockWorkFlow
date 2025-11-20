#!/usr/bin/env python3
"""
Daily ReportのMarkdownファイルをYAML形式に変換するスクリプト
SlideMovie_WorkFlowの入力形式に対応（YouTube動画用に最適化）
"""

import re
import yaml
import sys
from datetime import datetime
from pathlib import Path


def extract_news_headlines(content: str) -> list:
    """
    ニュースセクションから見出しと詳細を抽出

    Returns:
        list of dict: [{'headline': '見出し', 'detail': '詳細説明'}, ...]
    """
    news_items = []

    # 番号付きリスト項目を抽出（例: 1. **タイトル**: 説明）
    pattern = r'\d+\.\s+\*\*([^*]+)\*\*[：:]\s*(.+?)(?=\n\d+\.|$)'
    matches = re.findall(pattern, content, re.DOTALL)

    for title, detail in matches:
        # 見出しを簡潔に（最初の重要な情報のみ）
        headline = title.strip()

        # 詳細から余計な部分を削除
        detail = detail.strip()
        detail = re.sub(r'\(記事\d+\)', '', detail).strip()

        # 見出しが長すぎる場合は切り詰め
        if len(headline) > 50:
            headline = headline[:47] + '...'

        news_items.append({
            'headline': headline,
            'detail': detail
        })

    return news_items


def parse_markdown_to_slides(md_content: str, date_str: str) -> dict:
    """
    MarkdownをSlideMovie用のYAML形式に変換（YouTube最適化版）
    """
    slides = []
    script_notes = []  # 音声用の詳細情報

    # 日付をフォーマット
    formatted_date = date_str.replace('_', '/')

    # タイトルスライド
    slides.append({
        'title': 'AI/IT株式ニュース',
        'content': f'{formatted_date}\n\n本日の注目トピック'
    })
    script_notes.append({
        'slide': 1,
        'script': f'{formatted_date}のAI・IT株式ニュースをお届けします。'
    })

    # セクションを分割
    sections = re.split(r'\n## ', md_content)

    slide_num = 2

    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines:
            continue

        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()

        # ポートフォリオセクションはスキップ
        if 'ポートフォリオ' in title or 'portfolio' in title.lower():
            continue

        # 免責事項はスキップ（音声で毎回読み上げ）
        if '免責' in title or '注意' in title or 'AI' in title and '生成' in content:
            continue

        # ニュースセクションの処理
        if 'ニュース' in title or 'NEWS' in title.upper():
            news_items = extract_news_headlines(content)

            # 最大5件まで表示
            for i, item in enumerate(news_items[:5]):
                slides.append({
                    'title': f'📰 ニュース {i+1}',
                    'content': item['headline']
                })
                script_notes.append({
                    'slide': slide_num,
                    'script': f"{item['headline']}。{item['detail']}"
                })
                slide_num += 1

        # 市場概況セクション
        elif '市場' in title or 'マーケット' in title:
            # 簡潔なサマリーを抽出
            summary_lines = []
            for line in content.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    clean_line = line.strip().lstrip('-•').strip()
                    if len(clean_line) < 60:
                        summary_lines.append(f'• {clean_line}')
                    if len(summary_lines) >= 4:
                        break

            if summary_lines:
                slides.append({
                    'title': '📈 市場概況',
                    'content': '\n'.join(summary_lines)
                })
                script_notes.append({
                    'slide': slide_num,
                    'script': f"本日の市場概況です。{' '.join([l.lstrip('• ') for l in summary_lines])}"
                })
                slide_num += 1

        # 投資示唆セクション
        elif '投資' in title or '示唆' in title or 'アクション' in title:
            # 重要なポイントのみ抽出
            key_points = []
            for line in content.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    clean_line = line.strip().lstrip('-•').strip()
                    if len(clean_line) < 50:
                        key_points.append(f'• {clean_line}')
                    if len(key_points) >= 3:
                        break

            if key_points:
                slides.append({
                    'title': '💡 投資のポイント',
                    'content': '\n'.join(key_points)
                })
                script_notes.append({
                    'slide': slide_num,
                    'script': f"投資のポイントです。{' '.join([p.lstrip('• ') for p in key_points])}"
                })
                slide_num += 1

    # 締めスライド
    slides.append({
        'title': '📊 まとめ',
        'content': '本日のレポートは以上です\n\nご視聴ありがとうございました'
    })
    script_notes.append({
        'slide': slide_num,
        'script': '本日のAI・IT株式ニュースは以上です。このレポートはAI、Geminiにより自動生成されています。投資判断は必ずご自身で行ってください。ご視聴ありがとうございました。'
    })

    return {
        'topic': f'AI_IT株式日次レポート_{date_str}',
        'slides': slides,
        'script_notes': script_notes,
        'disclaimer': 'このレポートはAI（Gemini）により自動生成されています。投資判断は必ずご自身で行ってください。'
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_report_to_yaml.py <input_md> <output_dir>")
        print("Example: python convert_report_to_yaml.py output/daily_report.md inputs/")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    # 日付を取得
    date_str = datetime.now().strftime('%Y_%m_%d')
    if len(sys.argv) > 3:
        date_str = sys.argv[3]

    # 入力ファイルを読み込み
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 変換
    yaml_data = parse_markdown_to_slides(md_content, date_str)

    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # YAMLファイルを保存
    output_file = output_dir / f'daily_report_{date_str}.yml'

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✓ Created YAML file: {output_file}")
    print(f"  - Topic: {yaml_data['topic']}")
    print(f"  - Slides: {len(yaml_data['slides'])}")
    print(f"  - Script notes: {len(yaml_data.get('script_notes', []))}")

    return str(output_file)


if __name__ == '__main__':
    main()
