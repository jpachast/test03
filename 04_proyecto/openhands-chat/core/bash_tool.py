"""
Herramienta Bash para ejecutar comandos de terminal.
Permite al agente ejecutar comandos bash incluyendo el browser CLI.
"""
import subprocess
import shlex
from collections.abc import Sequence
from typing import TYPE_CHECKING, Self

from pydantic import Field
from rich.text import Text

from openhands.sdk.tool.tool import (
    Action,
    Observation,
    ToolAnnotations,
    ToolDefinition,
    ToolExecutor,
)
from openhands.sdk.tool import register_tool


if TYPE_CHECKING:
    from openhands.sdk.conversation.base import BaseConversation
    from openhands.sdk.conversation.state import ConversationState


class BashAction(Action):
    """Action for executing a bash command."""

    command: str = Field(description="The bash command to execute.")
    timeout: int = Field(default=60, description="Timeout in seconds for the command.")

    @property
    def visualize(self) -> Text:
        """Return Rich Text representation."""
        content = Text()
        content.append("$ ", style="green bold")
        content.append(self.command, style="white")
        return content


class BashObservation(Observation):
    """Observation returned after executing a bash command."""

    stdout: str = Field(default="", description="Standard output of the command.")
    stderr: str = Field(default="", description="Standard error of the command.")
    exit_code: int = Field(default=0, description="Exit code of the command.")

    @property
    def visualize(self) -> Text:
        """Return Rich Text representation of command output."""
        content = Text()
        
        if self.stdout:
            content.append(self.stdout, style="white")
        
        if self.stderr:
            if content:
                content.append("\n")
            content.append(self.stderr, style="red")
        
        if self.exit_code != 0:
            if content:
                content.append("\n")
            content.append(f"Exit code: {self.exit_code}", style="yellow")
        
        return content


BASH_DESCRIPTION = """Execute a bash command in the terminal.

Use this tool to run shell commands, scripts, or any terminal operations.
The command will be executed and you'll receive the stdout, stderr, and exit code.

Examples:
- List files: command="ls -la"
- Run Python: command="python script.py"
- Navigate browser: command="cd /path && python -m core.browser navigate 'https://example.com'"

Note: Commands have a default timeout of 60 seconds."""


class BashExecutor(ToolExecutor):
    """Executor that runs bash commands."""

    def __call__(
        self,
        action: BashAction,
        conversation: "BaseConversation | None" = None,  # noqa: ARG002
    ) -> BashObservation:
        """Execute the bash command."""
        try:
            result = subprocess.run(
                action.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=action.timeout,
                cwd="/workspace/project/test03/04_proyecto/openhands-chat"
            )
            return BashObservation(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return BashObservation(
                stdout="",
                stderr=f"Command timed out after {action.timeout} seconds",
                exit_code=-1,
            )
        except Exception as e:
            return BashObservation(
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )


class BashTool(ToolDefinition[BashAction, BashObservation]):
    """Tool for executing bash commands."""

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState | None" = None,  # noqa: ARG003
        **params,
    ) -> Sequence[Self]:
        """Create BashTool instance."""
        return [
            cls(
                description=BASH_DESCRIPTION,
                action_type=BashAction,
                observation_type=BashObservation,
                executor=BashExecutor(),
                annotations=ToolAnnotations(
                    readOnlyHint=False,
                    destructiveHint=True,
                    idempotentHint=False,
                    openWorldHint=True,
                ),
            )
        ]


# Registrar la herramienta para que esté disponible
register_tool("bash", BashTool)
