"""
WorkflowOrchestrator（オーケストレーター）
すべてのサブエージェントを統括し、ワークフローを管理するメインエージェント
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from .researcher import ResearcherAgent
from .summarizer import SummarizerAgent
from .slide_creator import SlideCreatorAgent
from .image_generator import ImageGeneratorAgent
from .script_writer import ScriptWriterAgent
from .video_editor import VideoEditorAgent


class WorkflowOrchestrator(BaseAgent):
    """ワークフロー全体を統括するオーケストレーター"""

    def __init__(self, background_image: str = "images/slideBackground.png"):
        super().__init__(
            name="WorkflowOrchestrator",
            description="ワークフロー全体を統括し、各サブエージェントを適切な順序で実行する"
        )
        self.skills = ["workflow_management", "agent_coordination", "error_handling"]
        self.background_image = background_image

        # サブエージェントを初期化
        self.agents = {
            "researcher": ResearcherAgent(),
            "summarizer": SummarizerAgent(),
            "slide_creator": SlideCreatorAgent(background_image=background_image),
            "image_generator": ImageGeneratorAgent(),
            "script_writer": ScriptWriterAgent(),
            "video_editor": VideoEditorAgent(),
        }

        # ワークフロー定義
        self.workflow_steps = [
            {"agent": "researcher", "name": "情報収集", "required_context": []},
            {"agent": "summarizer", "name": "レポート作成", "required_context": ["articles"]},
            {"agent": "slide_creator", "name": "スライド作成", "required_context": ["report"]},
            {"agent": "image_generator", "name": "画像生成", "required_context": ["slides_data"]},
            {"agent": "script_writer", "name": "脚本作成", "required_context": ["slide_file"]},
            {"agent": "video_editor", "name": "動画編集", "required_context": ["scripts", "slides_data"]},
        ]

    def run_step(self, step: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        単一のワークフローステップを実行

        Args:
            step: ステップ定義
            context: 現在のコンテキスト

        Returns:
            ステップの実行結果
        """
        agent_name = step["agent"]
        step_name = step["name"]

        self.log(f"=== {step_name} ({agent_name}) ===")

        # 必要なコンテキストが揃っているか確認
        for required in step.get("required_context", []):
            if required not in context:
                self.log(f"Missing required context: {required}", "WARNING")

        # エージェントを取得して実行
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            result = agent.execute(context)

            # 結果をコンテキストにマージ
            context.update(result)
            self.log(f"{step_name} completed successfully")

            return result

        except Exception as e:
            self.log(f"{step_name} failed: {str(e)}", "ERROR")
            raise

    def run_full_workflow(self, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        完全なワークフローを実行

        Args:
            initial_context: 初期コンテキスト

        Returns:
            最終結果
        """
        self.log("Starting full workflow...")
        start_time = datetime.now()

        context = initial_context or {}
        results = {}

        for step in self.workflow_steps:
            try:
                result = self.run_step(step, context)
                results[step["agent"]] = result
            except Exception as e:
                self.log(f"Workflow stopped at {step['name']}: {str(e)}", "ERROR")
                results["error"] = {
                    "step": step["name"],
                    "message": str(e)
                }
                break

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        results["workflow_summary"] = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "completed_steps": len([s for s in self.workflow_steps if s["agent"] in results])
        }

        self.log(f"Workflow completed in {duration:.1f} seconds")
        return results

    def run_partial_workflow(self, start_from: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        途中からワークフローを実行

        Args:
            start_from: 開始するステップのエージェント名
            initial_context: 初期コンテキスト（前のステップの結果を含む）

        Returns:
            最終結果
        """
        self.log(f"Starting partial workflow from {start_from}...")

        # 開始位置を特定
        start_index = None
        for i, step in enumerate(self.workflow_steps):
            if step["agent"] == start_from:
                start_index = i
                break

        if start_index is None:
            raise ValueError(f"Unknown step: {start_from}")

        context = initial_context
        results = {}

        for step in self.workflow_steps[start_index:]:
            try:
                result = self.run_step(step, context)
                results[step["agent"]] = result
            except Exception as e:
                self.log(f"Workflow stopped at {step['name']}: {str(e)}", "ERROR")
                results["error"] = {
                    "step": step["name"],
                    "message": str(e)
                }
                break

        return results

    def run_single_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        単一のエージェントのみを実行

        Args:
            agent_name: エージェント名
            context: コンテキスト

        Returns:
            実行結果
        """
        self.log(f"Running single agent: {agent_name}")

        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        return agent.execute(context)

    def get_workflow_status(self) -> Dict[str, Any]:
        """ワークフローの状態を取得"""
        return {
            "orchestrator": self.name,
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "workflow_steps": [
                {"step": i + 1, "name": step["name"], "agent": step["agent"]}
                for i, step in enumerate(self.workflow_steps)
            ]
        }

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - mode: "full" | "partial" | "single"（デフォルト: "full"）
                - start_from: 部分実行時の開始ステップ
                - agent: 単一実行時のエージェント名

        Returns:
            実行結果
        """
        mode = context.get("mode", "full")

        if mode == "full":
            return self.run_full_workflow(context)

        elif mode == "partial":
            start_from = context.get("start_from")
            if not start_from:
                raise ValueError("start_from is required for partial mode")
            return self.run_partial_workflow(start_from, context)

        elif mode == "single":
            agent_name = context.get("agent")
            if not agent_name:
                raise ValueError("agent is required for single mode")
            return self.run_single_agent(agent_name, context)

        else:
            raise ValueError(f"Unknown mode: {mode}")


# 使用例
if __name__ == "__main__":
    # オーケストレーターを初期化
    orchestrator = WorkflowOrchestrator(background_image="images/slideBackground.png")

    # ワークフローの状態を表示
    print("\n=== Workflow Status ===")
    status = orchestrator.get_workflow_status()
    for step in status["workflow_steps"]:
        print(f"  {step['step']}. {step['name']} ({step['agent']})")

    print("\n=== Available Agents ===")
    for name, info in status["agents"].items():
        print(f"  - {name}: {info['description']}")
        print(f"    Skills: {', '.join(info['skills'])}")
