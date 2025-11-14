#!/usr/bin/env python3
"""
Discord通知スクリプト (send_to_discord.py)
Markdownレポートを見やすく整形してDiscordに送信します。
"""

import sys
import os
import json
import requests
from datetime import datetime


def split_into_fields(content: str, max_length: int = 1024) -> list:
    """
    長いテキストを複数のフィールドに分割します。

    Args:
        content: 分割するテキスト
        max_length: 各フィールドの最大長

    Returns:
        分割されたテキストのリスト
    """
    if len(content) <= max_length:
        return [content]

    fields = []
    lines = content.split('\n')
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 <= max_length:
            current += line + '\n'
        else:
            if current:
                fields.append(current.rstrip())
            current = line + '\n'

    if current:
        fields.append(current.rstrip())

    return fields


def parse_markdown_report(file_path: str) -> dict:
    """
    Markdownレポートを解析してセクションに分割します。

    Args:
        file_path: Markdownファイルのパス

    Returns:
        セクション情報の辞書
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = {}
    current_section = "header"
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            # 前のセクションを保存
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            # 新しいセクション開始
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    # 最後のセクションを保存
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def create_weekly_summary_embed(title: str, sections: dict, color: int) -> dict:
    """
    週次レポート用の要約Embedを作成します（詳細はPDFを参照）。

    Args:
        title: Embedのタイトル
        sections: セクション情報
        color: Embedの色

    Returns:
        Discord Embed形式の辞書
    """
    embed = {
        "title": title,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "description": "📄 **詳細な分析はPDFファイルをご確認ください**\n\n以下は主要なポイントの要約です。",
        "fields": []
    }

    # 週次レポートの主要セクションのみを抽出（絵文字を含む可能性があるセクション名）
    key_sections = [
        "📊 ポートフォリオサマリー",
        "ポートフォリオサマリー",
        "🎯 今週の投資推奨銘柄",
        "今週の投資推奨銘柄",
        "📅 来週の注目イベント",
        "来週の注目イベント"
    ]

    for section_name in key_sections:
        if section_name in sections and sections[section_name]:
            content = sections[section_name].strip()
            if content:
                # 最初の500文字まで + 省略記号
                if len(content) > 500:
                    content = content[:500] + "...\n\n*(続きはPDFをご確認ください)*"

                # 絵文字を除去したセクション名を使用
                clean_name = section_name.replace("📊 ", "").replace("🎯 ", "").replace("📅 ", "")
                embed["fields"].append({
                    "name": clean_name,
                    "value": content,
                    "inline": False
                })

    # フィールドが空の場合はメッセージを追加
    if not embed["fields"]:
        embed["fields"].append({
            "name": "レポート",
            "value": "週次アクションレポートを生成しました。詳細はPDFファイルをご確認ください。",
            "inline": False
        })

    return embed


def create_discord_embed(title: str, sections: dict, color: int) -> dict:
    """
    Discord Embed形式のデータを作成します。

    Args:
        title: Embedのタイトル
        sections: セクション情報
        color: Embedの色

    Returns:
        Discord Embed形式の辞書
    """
    embed = {
        "title": title,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": []
    }

    # ヘッダー部分（エグゼクティブサマリーなど）
    if "header" in sections and sections["header"]:
        # タイトル行を除去
        header_lines = sections["header"].split('\n')
        header_content = '\n'.join([line for line in header_lines if not line.startswith('#')])
        if header_content.strip():
            embed["description"] = header_content.strip()[:4096]

    # セクションをfieldsに追加（最大25個まで）
    field_count = 0
    max_fields = 25

    section_order = [
        "エグゼクティブサマリー",
        "重要ファクト",
        "M&A・企業買収",
        "戦略的提携・パートナーシップ",
        "大型契約・受注",
        "新製品・新技術",
        "業績・財務情報",
        "その他の重要情報",
        "投資への示唆",
        "ポートフォリオサマリー",
        "📊 ポートフォリオサマリー",
        "今週の推奨アクション",
        "🎯 今週の投資推奨銘柄",
        "定期買い付けリマインド",
        "ポートフォリオ最適化の提案",
        "来週の注意事項",
        "📅 来週の注目イベント"
    ]

    # 順序に従ってセクションを追加
    for section_name in section_order:
        if section_name in sections and sections[section_name] and field_count < max_fields:
            content = sections[section_name]

            # 空のセクションはスキップ
            if not content.strip() or content.strip() == "（該当する情報がある場合のみ記載）":
                continue

            # 長いコンテンツは分割
            if len(content) > 1024:
                parts = split_into_fields(content, 1024)
                for i, part in enumerate(parts):
                    if field_count >= max_fields:
                        break
                    field_title = f"{section_name} ({i+1}/{len(parts)})" if len(parts) > 1 else section_name
                    embed["fields"].append({
                        "name": field_title,
                        "value": part,
                        "inline": False
                    })
                    field_count += 1
            else:
                embed["fields"].append({
                    "name": section_name,
                    "value": content,
                    "inline": False
                })
                field_count += 1

    # その他のセクション（順序にないもの）
    for section_name, content in sections.items():
        if section_name not in section_order and section_name != "header" and field_count < max_fields:
            if content and content.strip():
                if len(content) > 1024:
                    parts = split_into_fields(content, 1024)
                    for i, part in enumerate(parts):
                        if field_count >= max_fields:
                            break
                        field_title = f"{section_name} ({i+1}/{len(parts)})" if len(parts) > 1 else section_name
                        embed["fields"].append({
                            "name": field_title,
                            "value": part,
                            "inline": False
                        })
                        field_count += 1
                else:
                    embed["fields"].append({
                        "name": section_name,
                        "value": content,
                        "inline": False
                    })
                    field_count += 1

    return embed


def get_mime_type(file_path: str) -> str:
    """
    ファイル拡張子からMIMEタイプを取得します。

    Args:
        file_path: ファイルパス

    Returns:
        MIMEタイプ
    """
    extension = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.html': 'text/html',
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.csv': 'text/csv'
    }
    return mime_types.get(extension, 'application/octet-stream')


def send_to_discord(webhook_url: str, embed: dict, file_path: str = None):
    """
    Discordにメッセージを送信します。

    Args:
        webhook_url: Discord Webhook URL
        embed: Embed形式のデータ
        file_path: 添付するファイルのパス（オプション）
    """
    payload = {
        "embeds": [embed]
    }

    if file_path and os.path.exists(file_path):
        # ファイル添付あり
        mime_type = get_mime_type(file_path)
        print(f"Attaching file: {os.path.basename(file_path)} ({mime_type})")

        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, mime_type)
            }
            data = {
                'payload_json': json.dumps(payload)
            }
            response = requests.post(webhook_url, data=data, files=files)
    else:
        # ファイル添付なし
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

    if response.status_code in [200, 204]:
        print("✓ Successfully sent to Discord")
    else:
        print(f"✗ Failed to send to Discord: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)


def main():
    """メイン処理"""
    if len(sys.argv) < 4:
        print("Usage: python send_to_discord.py <webhook_url> <title> <report_file> [color] [attachment_file]")
        print("  report_file: Markdownファイル（プレビュー生成用）")
        print("  attachment_file: 添付ファイル（省略時はreport_fileを使用）")
        sys.exit(1)

    webhook_url = sys.argv[1]
    title = sys.argv[2]
    report_file = sys.argv[3]
    color = int(sys.argv[4]) if len(sys.argv) > 4 else 3066993
    attachment_file = sys.argv[5] if len(sys.argv) > 5 else report_file

    if not os.path.exists(report_file):
        print(f"✗ Report file not found: {report_file}")
        sys.exit(1)

    if not os.path.exists(attachment_file):
        print(f"✗ Attachment file not found: {attachment_file}")
        sys.exit(1)

    print(f"Parsing report: {report_file}")
    sections = parse_markdown_report(report_file)

    print(f"Creating Discord embed...")
    # 週次レポートの場合は要約版embedを使用
    if "週次" in title or "weekly" in title.lower():
        print("  Using summary format for weekly report")
        embed = create_weekly_summary_embed(title, sections, color)
    else:
        embed = create_discord_embed(title, sections, color)

    print(f"Sending to Discord...")
    send_to_discord(webhook_url, embed, attachment_file)


if __name__ == "__main__":
    main()
