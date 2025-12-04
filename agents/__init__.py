"""
ワークフロー管理用サブエージェント

役割:
1. ResearcherAgent (日々の情勢調べ役) - AI関係の企業の動向や世界情勢を調べる
2. SummarizerAgent (まとめ役) - 日々の情勢をまとめ、レポートに仕立て上げる
3. SlideCreatorAgent (スライド作成役) - レポートの内容をスライドにする
4. ImageGeneratorAgent (画像生成役) - スライドに挿入する画像を生成する
5. ScriptWriterAgent (脚本家) - スライドから動画のシナリオを考える
6. VideoEditorAgent (動画編集者) - スライドの画像にキャラや字幕、音声を載せて動画にする

Claude Code版:
- CCSummarizerAgent - Claude Code CLIを使用してレポート作成
- CCSlideCreatorAgent - Claude Code CLIを使用してスライド作成
- CCScriptWriterAgent - Claude Code CLIを使用して脚本作成
- CCWorkflowOrchestrator - 調査と画像生成はGemini、それ以外はClaude Codeを使用
"""

from .base_agent import BaseAgent
from .researcher import ResearcherAgent
from .summarizer import SummarizerAgent
from .slide_creator import SlideCreatorAgent
from .image_generator import ImageGeneratorAgent
from .script_writer import ScriptWriterAgent
from .video_editor import VideoEditorAgent
from .orchestrator import WorkflowOrchestrator

# Claude Code版
from .claude_code_base_agent import ClaudeCodeBaseAgent
from .cc_summarizer import CCSummarizerAgent
from .cc_slide_creator import CCSlideCreatorAgent
from .cc_script_writer import CCScriptWriterAgent
from .cc_orchestrator import CCWorkflowOrchestrator

__all__ = [
    # 通常版（Gemini使用）
    'BaseAgent',
    'ResearcherAgent',
    'SummarizerAgent',
    'SlideCreatorAgent',
    'ImageGeneratorAgent',
    'ScriptWriterAgent',
    'VideoEditorAgent',
    'WorkflowOrchestrator',
    # Claude Code版
    'ClaudeCodeBaseAgent',
    'CCSummarizerAgent',
    'CCSlideCreatorAgent',
    'CCScriptWriterAgent',
    'CCWorkflowOrchestrator',
]
