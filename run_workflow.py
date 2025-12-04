#!/usr/bin/env python3
"""
ワークフロー実行スクリプト

サブエージェントとスキルを使用してワークフローを実行します。

使用方法:
    # 完全なワークフローを実行
    python run_workflow.py

    # 特定のエージェントのみ実行
    python run_workflow.py --agent researcher

    # 途中から実行
    python run_workflow.py --start-from slide_creator --report output/daily_report.md

    # ワークフローの状態を表示
    python run_workflow.py --status
"""

import argparse
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents import WorkflowOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description='AI/IT株式レポートワークフローを実行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
    # 完全なワークフローを実行（情報収集→レポート→スライド→脚本→動画）
    python run_workflow.py

    # 情報収集エージェントのみ実行
    python run_workflow.py --agent researcher

    # レポートが既にある場合、スライド作成から開始
    python run_workflow.py --start-from slide_creator --report output/daily_report.md

    # 利用可能なエージェントとスキルを表示
    python run_workflow.py --status

エージェント一覧:
    researcher       - 日々の情勢調べ役（RSSフィードから情報収集）
    summarizer       - まとめ役（収集した情報をレポートに）
    slide_creator    - スライド作成役（レポートからMarpスライドを生成）
    image_generator  - 画像生成役（スライドに挿入する画像を生成）
    script_writer    - 脚本家（スライドから動画用の脚本を作成）
    video_editor     - 動画編集者（スライド+音声+キャラで動画を作成）
"""
    )

    parser.add_argument(
        '--agent', '-a',
        type=str,
        choices=['researcher', 'summarizer', 'slide_creator', 'image_generator', 'script_writer', 'video_editor'],
        help='特定のエージェントのみを実行'
    )

    parser.add_argument(
        '--start-from', '-s',
        type=str,
        choices=['researcher', 'summarizer', 'slide_creator', 'image_generator', 'script_writer', 'video_editor'],
        help='指定したエージェントからワークフローを開始'
    )

    parser.add_argument(
        '--report', '-r',
        type=str,
        help='既存のレポートファイルを使用（--start-from slide_creator と共に使用）'
    )

    parser.add_argument(
        '--articles', '-i',
        type=str,
        help='既存の記事JSONファイルを使用（--start-from summarizer と共に使用）'
    )

    parser.add_argument(
        '--slide-file',
        type=str,
        help='既存のスライドファイルを使用（--start-from script_writer と共に使用）'
    )

    parser.add_argument(
        '--background', '-b',
        type=str,
        default='images/slideBackground.png',
        help='スライドの背景画像パス（デフォルト: images/slideBackground.png）'
    )

    parser.add_argument(
        '--hours-ago',
        type=int,
        default=24,
        help='何時間前までの記事を取得するか（デフォルト: 24）'
    )

    parser.add_argument(
        '--no-video',
        action='store_true',
        help='動画レンダリングをスキップ'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='ワークフローの状態を表示して終了'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='結果を保存するJSONファイルパス'
    )

    args = parser.parse_args()

    # オーケストレーターを初期化
    orchestrator = WorkflowOrchestrator(background_image=args.background)

    # ステータス表示
    if args.status:
        print("\n" + "=" * 60)
        print("ワークフローステータス")
        print("=" * 60)

        status = orchestrator.get_workflow_status()

        print("\n【ワークフローステップ】")
        for step in status["workflow_steps"]:
            print(f"  {step['step']}. {step['name']} ({step['agent']})")

        print("\n【エージェント詳細】")
        for name, info in status["agents"].items():
            print(f"\n  {name}:")
            print(f"    説明: {info['description']}")
            print(f"    スキル: {', '.join(info['skills'])}")

        return

    # コンテキストを構築
    context = {
        "hours_ago": args.hours_ago,
        "render_video": not args.no_video,
    }

    # 既存のファイルを読み込む
    if args.articles:
        with open(args.articles, 'r', encoding='utf-8') as f:
            data = json.load(f)
            context["articles"] = data.get("articles", [])
        print(f"記事ファイルを読み込みました: {args.articles}")

    if args.report:
        with open(args.report, 'r', encoding='utf-8') as f:
            context["report"] = f.read()
        print(f"レポートファイルを読み込みました: {args.report}")

    if args.slide_file:
        context["slide_file"] = args.slide_file
        print(f"スライドファイルを使用: {args.slide_file}")

    # 実行モードを決定
    if args.agent:
        context["mode"] = "single"
        context["agent"] = args.agent
        print(f"\n単一エージェントモード: {args.agent}")
    elif args.start_from:
        context["mode"] = "partial"
        context["start_from"] = args.start_from
        print(f"\n部分実行モード: {args.start_from} から開始")
    else:
        context["mode"] = "full"
        print("\n完全ワークフローモード")

    print("=" * 60)

    # ワークフローを実行
    try:
        results = orchestrator.execute(context)

        print("\n" + "=" * 60)
        print("実行完了")
        print("=" * 60)

        # サマリーを表示
        if "workflow_summary" in results:
            summary = results["workflow_summary"]
            print(f"\n開始時刻: {summary['start_time']}")
            print(f"終了時刻: {summary['end_time']}")
            print(f"所要時間: {summary['duration_seconds']:.1f}秒")
            print(f"完了ステップ: {summary['completed_steps']}")

        # エラーがあれば表示
        if "error" in results:
            print(f"\nエラー発生: {results['error']['step']}")
            print(f"メッセージ: {results['error']['message']}")

        # 結果を保存
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n結果を保存しました: {args.output}")

    except Exception as e:
        print(f"\nエラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
