#!/usr/bin/env python3
"""
Daily ReportのMarkdownファイルをYAML形式に変換するスクリプト
SlideMovie_WorkFlowの入力形式に対応
"""

import re
import yaml
import sys
from datetime import datetime
from pathlib import Path


def parse_markdown_to_slides(md_content: str, date_str: str) -> dict:
    """
    MarkdownをSlideMovie用のYAML形式に変換
    """
    slides = []

    # タイトルスライド
    slides.append({
        'title': f'AI/IT株式投資 日次レポート',
        'content': f'{date_str}\n\n最新のAI・IT関連ニュースと投資分析'
    })

    # セクションを分割
    sections = re.split(r'\n## ', md_content)

    for section in sections[1:]:  # 最初の空要素をスキップ
        lines = section.strip().split('\n')
        if not lines:
            continue

        title = lines[0].strip()
        content_lines = lines[1:]

        # コンテンツを整形
        content = '\n'.join(content_lines).strip()

        # 長すぎるコンテンツは分割
        if len(content) > 1000:
            # サブセクションで分割
            subsections = re.split(r'\n### ', content)
            if len(subsections) > 1:
                # メインスライド
                slides.append({
                    'title': title,
                    'content': subsections[0].strip() if subsections[0].strip() else f'{title}の詳細'
                })
                # サブスライド
                for subsection in subsections[1:]:
                    sub_lines = subsection.strip().split('\n')
                    if sub_lines:
                        sub_title = sub_lines[0].strip()
                        sub_content = '\n'.join(sub_lines[1:]).strip()
                        if sub_content:
                            slides.append({
                                'title': f'{title} - {sub_title}',
                                'content': sub_content[:800]  # 長すぎる場合は切り詰め
                            })
            else:
                # 分割できない場合は要約
                slides.append({
                    'title': title,
                    'content': content[:800] + '...' if len(content) > 800 else content
                })
        else:
            if content:
                slides.append({
                    'title': title,
                    'content': content
                })

    # まとめスライド
    slides.append({
        'title': 'まとめ',
        'content': f'''## 本日のポイント

- AI・IT関連の最新ニュースを分析
- 市場動向と投資機会を評価
- 重要なトレンドを把握

{date_str} レポート終了'''
    })

    return {
        'topic': f'AI_IT株式日次レポート_{date_str}',
        'slides': slides
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

    return str(output_file)


if __name__ == '__main__':
    main()
