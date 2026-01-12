"""
E2B Sandbox Agent
=================

Specialized agent for handling E2B sandbox execution requests via message bus.

This agent provides:
- Message-based E2B execution for other agents
- Concurrent request handling with internal queue
- Result publishing to execution_results channel
- Optional E2B integration (gracefully handles when disabled)

Usage:
    agent = E2BSandboxAgent(
        agent_id="e2b-001",
        config=config,
        message_bus=message_bus,
        sandbox_manager=sandbox_manager
    )
    await agent.initialize()
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent
from core.message_bus import MessageBus, MessageTypes
from core.e2b_sandbox_manager import E2BSandboxManager, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRequest:
    """Request for E2B command execution."""
    request_id: str
    project_id: str
    task_id: Optional[str]
    command: str
    cwd: str = "/"
    timeout_seconds: int = 300
    env: Optional[Dict[str, str]] = None
    persistent_session: bool = False
    session_id: Optional[str] = None
    requester_agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class E2BSandboxAgent(BaseAgent):
    """
    Agent that handles E2B sandbox execution requests via message bus.

    Subscribes to "execution_requests" channel and processes execution
    requests from other agents. Results are published to "execution_results"
    channel for requesters to consume.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: MessageBus,
        sandbox_manager: Optional[E2BSandboxManager] = None
    ):
        """
        Initialize E2B Sandbox Agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Message bus for communication
            sandbox_manager: Optional E2BSandboxManager instance
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="e2b_sandbox",
            config=config,
            message_bus=message_bus
        )

        self.sandbox_manager = sandbox_manager
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self.active_executions: Dict[str, ExecutionRequest] = {}

        logger.info(f"[{self.agent_id}] E2BSandboxAgent initialized")

    async def initialize(self):
        """Initialize agent and start execution worker."""
        await super().initialize()

        # Subscribe to execution requests channel
        if self.message_bus:
            self.message_bus.subscribe(
                "execution_requests",
                self.agent_id,
                self._handle_execution_request
            )
            logger.info(f"[{self.agent_id}] Subscribed to execution_requests channel")

        # Start execution worker
        self._worker_task = asyncio.create_task(self._execution_worker())
        logger.info(f"[{self.agent_id}] Execution worker started")

        self.status = "idle"

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a task (not typically called directly for this agent).

        This agent primarily responds to message bus requests, but this
        method is kept for compatibility with the BaseAgent interface.

        Args:
            task: Task details

        Returns:
            Task result
        """
        logger.warning(f"[{self.agent_id}] execute_task called directly - "
                      "E2BSandboxAgent typically operates via message bus")

        return {
            "success": True,
            "message": "E2BSandboxAgent operates via message bus",
            "active_executions": len(self.active_executions),
            "queue_size": self.execution_queue.qsize()
        }

    async def _handle_execution_request(self, message: Dict):
        """
        Handle incoming execution request message.

        Args:
            message: Message containing execution request
        """
        try:
            # Parse execution request
            request = ExecutionRequest(
                request_id=message.get("request_id", f"req-{datetime.now().timestamp()}"),
                project_id=message.get("project_id", ""),
                task_id=message.get("task_id"),
                command=message["command"],
                cwd=message.get("cwd", "/"),
                timeout_seconds=message.get("timeout_seconds", 300),
                env=message.get("env"),
                persistent_session=message.get("persistent_session", False),
                session_id=message.get("session_id"),
                requester_agent_id=message.get("from_agent_id")
            )

            logger.info(f"[{self.agent_id}] Received execution request: {request.request_id}")
            logger.debug(f"[{self.agent_id}] Command: {request.command}")

            # Add to execution queue
            await self.execution_queue.put(request)

            # Publish acknowledgment
            if self.message_bus:
                self.message_bus.publish(
                    "execution_results",
                    self.agent_id,
                    {
                        "request_id": request.request_id,
                        "status": "queued",
                        "queue_position": self.execution_queue.qsize(),
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except KeyError as e:
            logger.error(f"[{self.agent_id}] Invalid execution request: missing {e}")
            # Publish error
            if self.message_bus:
                self.message_bus.publish(
                    "execution_results",
                    self.agent_id,
                    {
                        "request_id": message.get("request_id", "unknown"),
                        "success": False,
                        "error": f"Invalid request: missing {e}",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling execution request: {e}")

    async def _execution_worker(self):
        """
        Background worker that processes execution requests from queue.

        Runs continuously, processing requests one at a time.
        """
        logger.info(f"[{self.agent_id}] Execution worker loop started")

        while True:
            try:
                # Get next request from queue (blocks until available)
                request = await self.execution_queue.get()

                # Update status
                self.status = "working"
                self.active_executions[request.request_id] = request

                logger.info(f"[{self.agent_id}] Processing request: {request.request_id}")

                # Execute command
                result = await self._execute_request(request)

                # Publish result
                await self._publish_result(request, result)

                # Cleanup
                del self.active_executions[request.request_id]
                self.execution_queue.task_done()

                # Update status
                if self.execution_queue.empty():
                    self.status = "idle"

            except asyncio.CancelledError:
                logger.info(f"[{self.agent_id}] Execution worker cancelled")
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in execution worker: {e}")
                # Don't crash the worker - continue processing
                await asyncio.sleep(1)

    async def _execute_request(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a single execution request.

        Args:
            request: Execution request to process

        Returns:
            ExecutionResult with command output
        """
        if not self.sandbox_manager:
            # No sandbox manager - return error
            logger.warning(f"[{self.agent_id}] No sandbox manager available")
            from core.e2b_sandbox_manager import ExecutionResult
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="E2B Sandbox Manager not initialized",
                duration_seconds=0.0,
                error="No sandbox manager"
            )

        if not self.sandbox_manager.is_available():
            logger.warning(f"[{self.agent_id}] E2B not available, falling back to local execution")

        try:
            # Execute command using sandbox manager
            result = await self.sandbox_manager.execute_command(
                command=request.command,
                cwd=request.cwd,
                timeout_seconds=request.timeout_seconds,
                env=request.env,
                persistent_session=request.persistent_session,
                session_id=request.session_id
            )

            # Update metrics
            self.task_count += 1
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1
            self.total_duration_seconds += result.duration_seconds

            logger.info(f"[{self.agent_id}] Request {request.request_id} completed: "
                       f"exit_code={result.exit_code}, duration={result.duration_seconds:.2f}s")

            return result

        except Exception as e:
            logger.error(f"[{self.agent_id}] Execution failed: {e}")
            self.failure_count += 1

            from core.e2b_sandbox_manager import ExecutionResult
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=0.0,
                error=str(e)
            )

    async def _publish_result(self, request: ExecutionRequest, result: ExecutionResult):
        """
        Publish execution result to message bus.

        Args:
            request: Original execution request
            result: Execution result to publish
        """
        if not self.message_bus:
            return

        result_message = {
            "request_id": request.request_id,
            "project_id": request.project_id,
            "task_id": request.task_id,
            "success": result.success,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": result.duration_seconds,
            "sandbox_id": result.sandbox_id,
            "files_modified": result.files_modified,
            "error": result.error,
            "timestamp": datetime.now().isoformat(),
            "executor_agent_id": self.agent_id
        }

        # Publish to general results channel
        self.message_bus.publish(
            "execution_results",
            self.agent_id,
            result_message
        )

        # Also publish to requester-specific channel if specified
        if request.requester_agent_id:
            self.message_bus.publish(
                f"agent.{request.requester_agent_id}",
                self.agent_id,
                result_message
            )

        logger.debug(f"[{self.agent_id}] Published result for request {request.request_id}")

    async def cleanup(self):
        """Clean up agent resources."""
        logger.info(f"[{self.agent_id}] Cleaning up...")

        # Stop execution worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Wait for pending executions to complete (with timeout)
        if not self.execution_queue.empty():
            logger.info(f"[{self.agent_id}] Waiting for {self.execution_queue.qsize()} "
                       "pending executions...")
            try:
                await asyncio.wait_for(
                    self.execution_queue.join(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"[{self.agent_id}] Timeout waiting for pending executions")

        # Call parent cleanup
        await super().cleanup()

        logger.info(f"[{self.agent_id}] Cleanup complete")

    def get_system_prompt(self) -> str:
        """
        Get system prompt for this agent.

        Returns:
            System prompt string
        """
        return f"""You are the E2B Sandbox Agent ({self.agent_id}).

Your role:
- Process E2B execution requests from other agents via message bus
- Execute commands in isolated E2B sandboxes
- Publish execution results back to requesters
- Handle concurrent requests efficiently
- Provide graceful fallback when E2B unavailable

Current status:
- Status: {self.status}
- Active executions: {len(self.active_executions)}
- Queue size: {self.execution_queue.qsize()}
- E2B available: {self.sandbox_manager.is_available() if self.sandbox_manager else False}
- Tasks completed: {self.task_count}
- Success rate: {self.success_count / max(self.task_count, 1):.1%}
"""

    def get_metrics(self) -> Dict:
        """Get agent performance metrics."""
        return {
            **super().get_metrics() if hasattr(super(), 'get_metrics') else {},
            "active_executions": len(self.active_executions),
            "queue_size": self.execution_queue.qsize(),
            "e2b_available": self.sandbox_manager.is_available() if self.sandbox_manager else False,
            "sandbox_metrics": self.sandbox_manager.get_metrics() if self.sandbox_manager else {}
        }
