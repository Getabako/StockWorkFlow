"""
ワークフロー管理用サブエージェント

役割:
1. ResearcherAgent (日々の情勢調べ役) - AI関係の企業の動向や世界情勢を調べる
2. SummarizerAgent (まとめ役) - 日々の情勢をまとめ、レポートに仕立て上げる
3. SlideCreatorAgent (スライド作成役) - レポートの内容をスライドにする
4. ScriptWriterAgent (脚本家) - スライドから動画のシナリオを考える
5. VideoEditorAgent (動画編集者) - スライドの画像にキャラや字幕、音声を載せて動画にする
"""

from .base_agent import BaseAgent
from .researcher import ResearcherAgent
from .summarizer import SummarizerAgent
from .slide_creator import SlideCreatorAgent
from .script_writer import ScriptWriterAgent
from .video_editor import VideoEditorAgent
from .orchestrator import WorkflowOrchestrator

__all__ = [
    'BaseAgent',
    'ResearcherAgent',
    'SummarizerAgent',
    'SlideCreatorAgent',
    'ScriptWriterAgent',
    'VideoEditorAgent',
    'WorkflowOrchestrator',
]
