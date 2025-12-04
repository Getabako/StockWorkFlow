"""
ワークフロー用スキル定義

スキルは各エージェントが使用する特定の機能を提供します。
"""

from .base_skill import BaseSkill
from .rss_fetch import RSSFetchSkill
from .text_summarization import TextSummarizationSkill
from .slide_generation import SlideGenerationSkill
from .audio_synthesis import AudioSynthesisSkill
from .video_rendering import VideoRenderingSkill

__all__ = [
    'BaseSkill',
    'RSSFetchSkill',
    'TextSummarizationSkill',
    'SlideGenerationSkill',
    'AudioSynthesisSkill',
    'VideoRenderingSkill',
]
