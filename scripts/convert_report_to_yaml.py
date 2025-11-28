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
        'script': f'うぃっすー！if塾AIニュースのお時間です。{formatted_date}のAI・IT株式ニュースをお届けします。'
    })

    slide_num = 2

    # セクションを分割（## で分割）
    sections = re.split(r'\n## ', md_content)

    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines:
            continue

        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()

        # ポートフォリオセクションはスキップ
        if 'ポートフォリオ' in title:
            continue

        # 免責事項はスキップ
        if '免責' in title or '注意' in title:
            continue

        # エグゼクティブサマリー
        if 'サマリー' in title or 'エグゼクティブ' in title:
            # 最初の3文を抽出
            sentences = re.split(r'[。]', content)
            summary_sentences = [s.strip() for s in sentences if s.strip()][:3]
            summary_text = '。'.join(summary_sentences)
            if summary_text and not summary_text.endswith('。'):
                summary_text += '。'

            # 長すぎる場合は切り詰め
            if len(summary_text) > 200:
                summary_text = summary_text[:197] + '...'

            slides.append({
                'title': '本日のサマリー',
                'content': summary_text
            })
            script_notes.append({
                'slide': slide_num,
                'script': content
            })
            slide_num += 1

        # 重要ファクトセクション
        elif '重要ファクト' in title or 'ファクト' in title:
            # ### サブセクションを解析
            subsections = re.split(r'\n### ', content)

            facts_collected = []

            for subsection in subsections:
                if not subsection.strip():
                    continue

                sub_lines = subsection.strip().split('\n')
                sub_title = sub_lines[0].strip() if sub_lines else ''
                # ### マーカーを削除
                sub_title = sub_title.lstrip('#').strip()
                sub_content = '\n'.join(sub_lines[1:]).strip()

                # 箇条書きから重要な項目を抽出
                for line in sub_content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # * や - で始まる箇条書きを処理
                    if line.startswith('*') or line.startswith('-'):
                        clean_line = re.sub(r'^[\*\-]\s*', '', line).strip()

                        # **太字**を抽出
                        bold_match = re.search(r'\*\*([^*]+)\*\*', clean_line)
                        if bold_match:
                            headline = bold_match.group(1).strip()
                            # 詳細部分を抽出
                            detail = re.sub(r'\*\*[^*]+\*\*[：:]?\s*', '', clean_line).strip()

                            # 見出しが長すぎる場合は切り詰め
                            if len(headline) > 60:
                                headline = headline[:57] + '...'

                            facts_collected.append({
                                'headline': headline,
                                'detail': detail,
                                'category': sub_title
                            })

            # 最大5件のファクトをスライドに
            for i, fact in enumerate(facts_collected[:5]):
                slides.append({
                    'title': f'{fact["category"]}' if fact['category'] else f'ニュース {i+1}',
                    'content': fact['headline']
                })
                script_notes.append({
                    'slide': slide_num,
                    'script': f"{fact['headline']}。{fact['detail']}"
                })
                slide_num += 1

        # 投資への示唆セクション
        elif '投資' in title or '示唆' in title:
            # 文を抽出
            sentences = re.split(r'[。\n]', content)
            key_points = []

            for sentence in sentences:
                sentence = sentence.strip()
                # 空や短すぎる文はスキップ
                if not sentence or len(sentence) < 15:
                    continue
                # 免責事項をスキップ
                if 'AI' in sentence and '生成' in sentence:
                    continue

                # 長い場合は切り詰め
                if len(sentence) > 100:
                    sentence = sentence[:97] + '...'

                key_points.append(f'• {sentence}')
                if len(key_points) >= 3:
                    break

            if key_points:
                slides.append({
                    'title': '投資のポイント',
                    'content': '\n'.join(key_points)
                })
                script_notes.append({
                    'slide': slide_num,
                    'script': f"投資のポイントです。{content}"
                })
                slide_num += 1

    # 締めスライド
    slides.append({
        'title': 'まとめ',
        'content': '本日のレポートは以上です\n\nご視聴ありがとうございました'
    })
    script_notes.append({
        'slide': slide_num,
        'script': '本日のAI・IT株式ニュースは以上です。'
    })
    slide_num += 1

    # 免責事項とCTAスライドを追加
    slides.append({
        'title': '塾頭高崎の完全自動化への挑戦',
        'content': '※このコンテンツはAIが自動生成しています\n\nAI技術の限界に挑戦中！\n共感いただけたらチャンネル登録・グッドボタンを\nよろしくお願いします！'
    })
    script_notes.append({
        'slide': slide_num,
        'script': 'ご視聴いただきありがとうございました。実はこのレポート、if塾の塾頭高崎による「完全自動化への挑戦」プロジェクトの一環として、AIが自動生成しています。将来的には塾頭が執筆しているような自然な記事になることを目指しており、現時点では事実と異なる内容が含まれる可能性もあります。この挑戦に共感していただけたら、ぜひチャンネル登録とグッドボタンをよろしくお願いします！また、無料のAI教育や導入コンサルも受け付けています。詳しくは概要欄のリンクからお問い合わせください。'
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
