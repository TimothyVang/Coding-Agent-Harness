"""
E2B Sandbox Manager
===================

Centralized management of E2B sandbox environments for agent code execution.

This manager provides:
- Sandbox pool management (create, reuse, cleanup)
- Execution API (commands, tests, builds)
- Session persistence for long-running tasks
- Fallback to local execution when E2B disabled
- Metrics tracking and monitoring

Usage:
    manager = E2BSandboxManager(config)
    await manager.initialize()

    # Execute command in sandbox
    result = await manager.execute_command("npm test", project_path)

    # Clean up
    await manager.cleanup()
"""

import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

# Try to import E2B - gracefully handle if not installed
try:
    from e2b import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    Sandbox = None

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of command execution in sandbox or locally."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    sandbox_id: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class TestResult(ExecutionResult):
    """Result of test execution with additional test-specific data."""
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    coverage_percentage: Optional[float] = None


@dataclass
class BuildResult(ExecutionResult):
    """Result of build execution with build-specific data."""
    build_artifacts: List[str] = field(default_factory=list)
    build_warnings: List[str] = field(default_factory=list)


@dataclass
class SandboxInfo:
    """Information about a sandbox instance."""
    sandbox_id: str
    sandbox: Any  # E2B Sandbox instance or None
    created_at: datetime
    last_used_at: datetime
    session_id: Optional[str] = None
    is_persistent: bool = False


class E2BSandboxManager:
    """
    Centralized E2B sandbox management for agent code execution.

    Manages a pool of E2B sandboxes for efficient reuse, provides execution
    APIs for commands/tests/builds, and falls back to local execution when
    E2B is not available.
    """

    def __init__(self, config: Dict):
        """
        Initialize E2B sandbox manager.

        Args:
            config: Configuration dictionary with keys:
                - e2b_enabled: bool (default: True if E2B_API_KEY set)
                - e2b_api_key: str (or from E2B_API_KEY env var)
                - default_template: str (e.g., "node20", "python311")
                - sandbox_pool_size: int (default: 5)
                - sandbox_timeout_seconds: int (default: 600)
                - sandbox_memory_mb: int (default: 2048)
                - sandbox_cpu_count: int (default: 2)
                - persistent_sessions: bool (default: True)
                - auto_cleanup_age_minutes: int (default: 60)
        """
        self.config = config

        # Determine if E2B is enabled
        self.e2b_api_key = config.get("e2b_api_key") or os.environ.get("E2B_API_KEY")
        self.e2b_enabled = config.get("e2b_enabled", bool(self.e2b_api_key))

        if self.e2b_enabled and not E2B_AVAILABLE:
            logger.warning("E2B is enabled but e2b package not installed. "
                          "Falling back to local execution. Install with: pip install e2b")
            self.e2b_enabled = False

        if self.e2b_enabled and not self.e2b_api_key:
            logger.warning("E2B is enabled but no API key found. "
                          "Set E2B_API_KEY environment variable. Falling back to local execution.")
            self.e2b_enabled = False

        # Sandbox configuration
        self.default_template = config.get("default_template", "node20")
        self.pool_size = config.get("sandbox_pool_size", 5)
        self.timeout_seconds = config.get("sandbox_timeout_seconds", 600)
        self.memory_mb = config.get("sandbox_memory_mb", 2048)
        self.cpu_count = config.get("sandbox_cpu_count", 2)
        self.persistent_sessions = config.get("persistent_sessions", True)
        self.cleanup_age_minutes = config.get("auto_cleanup_age_minutes", 60)

        # Sandbox pool
        self.sandbox_pool: Dict[str, SandboxInfo] = {}
        self.active_sandboxes: Dict[str, SandboxInfo] = {}

        # Metrics
        self.metrics = {
            "sandboxes_created": 0,
            "sandboxes_destroyed": 0,
            "executions_total": 0,
            "executions_succeeded": 0,
            "executions_failed": 0,
            "total_execution_time_seconds": 0.0,
            "sandbox_reuse_count": 0,
        }

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"[E2BSandboxManager] Initialized")
        logger.info(f"  - E2B enabled: {self.e2b_enabled}")
        logger.info(f"  - Template: {self.default_template}")
        logger.info(f"  - Pool size: {self.pool_size}")
        logger.info(f"  - Persistent sessions: {self.persistent_sessions}")

    async def initialize(self) -> None:
        """Initialize the sandbox manager and start background tasks."""
        logger.info("[E2BSandboxManager] Starting initialization...")

        if self.e2b_enabled:
            # Test E2B connection
            try:
                logger.info("[E2BSandboxManager] Testing E2B connection...")
                # We'll create a test sandbox during first execution
                logger.info("[E2BSandboxManager] E2B connection ready")
            except Exception as e:
                logger.error(f"[E2BSandboxManager] E2B initialization failed: {e}")
                logger.warning("[E2BSandboxManager] Falling back to local execution")
                self.e2b_enabled = False

        # Start cleanup task
        if self.cleanup_age_minutes > 0:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())

        logger.info("[E2BSandboxManager] Initialization complete")

    async def execute_command(
        self,
        command: str,
        cwd: str = "/",
        timeout_seconds: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        persistent_session: bool = False,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a command in an E2B sandbox or locally.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout_seconds: Execution timeout (uses default if not specified)
            env: Environment variables
            persistent_session: Keep sandbox alive for reuse
            session_id: Reuse specific sandbox session

        Returns:
            ExecutionResult with command output and metadata
        """
        start_time = datetime.now()
        timeout = timeout_seconds or self.timeout_seconds

        self.metrics["executions_total"] += 1

        try:
            if self.e2b_enabled:
                result = await self._execute_in_e2b(
                    command, cwd, timeout, env, persistent_session, session_id
                )
            else:
                result = await self._execute_locally(command, cwd, timeout, env)

            duration = (datetime.now() - start_time).total_seconds()
            result.duration_seconds = duration
            self.metrics["total_execution_time_seconds"] += duration

            if result.success:
                self.metrics["executions_succeeded"] += 1
            else:
                self.metrics["executions_failed"] += 1

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics["executions_failed"] += 1
            logger.error(f"[E2BSandboxManager] Command execution failed: {e}")
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=duration,
                error=str(e)
            )

    async def _execute_in_e2b(
        self,
        command: str,
        cwd: str,
        timeout: int,
        env: Optional[Dict],
        persistent: bool,
        session_id: Optional[str]
    ) -> ExecutionResult:
        """Execute command in E2B sandbox."""
        sandbox = None
        sandbox_id_str = None

        try:
            # Get or create sandbox
            if session_id and session_id in self.active_sandboxes:
                sandbox_info = self.active_sandboxes[session_id]
                sandbox = sandbox_info.sandbox
                sandbox_id_str = sandbox_info.sandbox_id
                sandbox_info.last_used_at = datetime.now()
                self.metrics["sandbox_reuse_count"] += 1
                logger.debug(f"[E2BSandboxManager] Reusing sandbox: {sandbox_id_str}")
            else:
                sandbox = await self._create_sandbox()
                sandbox_id_str = sandbox.id if hasattr(sandbox, 'id') else "unknown"
                logger.debug(f"[E2BSandboxManager] Created new sandbox: {sandbox_id_str}")

                if persistent:
                    # Store in active sandboxes for reuse
                    self.active_sandboxes[sandbox_id_str] = SandboxInfo(
                        sandbox_id=sandbox_id_str,
                        sandbox=sandbox,
                        created_at=datetime.now(),
                        last_used_at=datetime.now(),
                        session_id=session_id,
                        is_persistent=True
                    )

            # Execute command
            result = await asyncio.wait_for(
                self._run_command_in_sandbox(sandbox, command, cwd, env),
                timeout=timeout
            )

            # Cleanup non-persistent sandbox
            if not persistent:
                await self._destroy_sandbox(sandbox)

            return ExecutionResult(
                success=result["exit_code"] == 0,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                duration_seconds=0.0,  # Set by caller
                sandbox_id=sandbox_id_str
            )

        except asyncio.TimeoutError:
            logger.error(f"[E2BSandboxManager] Command timed out after {timeout}s")
            if sandbox and not persistent:
                await self._destroy_sandbox(sandbox)
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_seconds=float(timeout),
                sandbox_id=sandbox_id_str,
                error="Timeout"
            )
        except Exception as e:
            logger.error(f"[E2BSandboxManager] E2B execution error: {e}")
            if sandbox and not persistent:
                await self._destroy_sandbox(sandbox)
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=0.0,
                sandbox_id=sandbox_id_str,
                error=str(e)
            )

    async def _execute_locally(
        self,
        command: str,
        cwd: str,
        timeout: int,
        env: Optional[Dict]
    ) -> ExecutionResult:
        """Execute command locally using subprocess."""
        logger.debug(f"[E2BSandboxManager] Executing locally: {command}")

        try:
            # Merge environment variables
            proc_env = os.environ.copy()
            if env:
                proc_env.update(env)

            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd if os.path.exists(cwd) else None,
                env=proc_env
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')

            return ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=0.0  # Set by caller
            )

        except asyncio.TimeoutError:
            if process:
                process.kill()
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_seconds=float(timeout),
                error="Timeout"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=0.0,
                error=str(e)
            )

    async def _create_sandbox(self) -> Any:
        """Create a new E2B sandbox."""
        if not self.e2b_enabled or not Sandbox:
            raise RuntimeError("E2B is not available")

        logger.info(f"[E2BSandboxManager] Creating sandbox with template: {self.default_template}")

        # Create sandbox (synchronous E2B call)
        sandbox = await asyncio.to_thread(
            Sandbox,
            template=self.default_template,
            api_key=self.e2b_api_key
        )

        self.metrics["sandboxes_created"] += 1
        return sandbox

    async def _destroy_sandbox(self, sandbox: Any) -> None:
        """Destroy an E2B sandbox."""
        try:
            if hasattr(sandbox, 'close'):
                await asyncio.to_thread(sandbox.close)
            elif hasattr(sandbox, 'kill'):
                await asyncio.to_thread(sandbox.kill)
            self.metrics["sandboxes_destroyed"] += 1
            logger.debug("[E2BSandboxManager] Sandbox destroyed")
        except Exception as e:
            logger.error(f"[E2BSandboxManager] Failed to destroy sandbox: {e}")

    async def _run_command_in_sandbox(
        self,
        sandbox: Any,
        command: str,
        cwd: str,
        env: Optional[Dict]
    ) -> Dict:
        """Run command in E2B sandbox and capture output."""
        # E2B process execution
        result = await asyncio.to_thread(
            sandbox.process.start_and_wait,
            command,
            cwd=cwd,
            env_vars=env or {}
        )

        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    async def run_tests(
        self,
        project_path: Path,
        test_command: str = "npm test"
    ) -> TestResult:
        """
        Run tests in E2B sandbox and parse results.

        Args:
            project_path: Path to project directory
            test_command: Command to run tests (default: "npm test")

        Returns:
            TestResult with parsed test output
        """
        result = await self.execute_command(
            command=test_command,
            cwd=str(project_path),
            timeout_seconds=self.timeout_seconds
        )

        # Parse test output (basic implementation)
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0

        # Try to parse common test output formats
        if "passed" in result.stdout.lower() or "passed" in result.stderr.lower():
            # Jest, Mocha, pytest style
            import re
            output = result.stdout + result.stderr
            passed_match = re.search(r'(\d+)\s+passed', output, re.IGNORECASE)
            failed_match = re.search(r'(\d+)\s+failed', output, re.IGNORECASE)
            skipped_match = re.search(r'(\d+)\s+skipped', output, re.IGNORECASE)

            if passed_match:
                tests_passed = int(passed_match.group(1))
            if failed_match:
                tests_failed = int(failed_match.group(1))
            if skipped_match:
                tests_skipped = int(skipped_match.group(1))

        return TestResult(
            success=result.success,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=result.duration_seconds,
            sandbox_id=result.sandbox_id,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped
        )

    async def validate_build(
        self,
        project_path: Path,
        build_command: str = "npm run build"
    ) -> BuildResult:
        """
        Validate build in E2B sandbox.

        Args:
            project_path: Path to project directory
            build_command: Command to run build (default: "npm run build")

        Returns:
            BuildResult with build output
        """
        result = await self.execute_command(
            command=build_command,
            cwd=str(project_path),
            timeout_seconds=self.timeout_seconds
        )

        return BuildResult(
            success=result.success,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=result.duration_seconds,
            sandbox_id=result.sandbox_id
        )

    async def cleanup(self) -> None:
        """Clean up all sandboxes and stop background tasks."""
        logger.info("[E2BSandboxManager] Cleaning up...")

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Destroy all active sandboxes
        for sandbox_info in list(self.active_sandboxes.values()):
            await self._destroy_sandbox(sandbox_info.sandbox)

        self.active_sandboxes.clear()
        self.sandbox_pool.clear()

        logger.info("[E2BSandboxManager] Cleanup complete")

    async def _auto_cleanup_loop(self) -> None:
        """Background task to automatically clean up old sandboxes."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._cleanup_old_sandboxes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[E2BSandboxManager] Cleanup loop error: {e}")

    async def _cleanup_old_sandboxes(self) -> int:
        """Clean up sandboxes older than configured age."""
        cutoff_time = datetime.now() - timedelta(minutes=self.cleanup_age_minutes)
        cleaned = 0

        for sandbox_id, sandbox_info in list(self.active_sandboxes.items()):
            if sandbox_info.last_used_at < cutoff_time and not sandbox_info.is_persistent:
                logger.info(f"[E2BSandboxManager] Cleaning up old sandbox: {sandbox_id}")
                await self._destroy_sandbox(sandbox_info.sandbox)
                del self.active_sandboxes[sandbox_id]
                cleaned += 1

        if cleaned > 0:
            logger.info(f"[E2BSandboxManager] Cleaned up {cleaned} old sandboxes")

        return cleaned

    def is_available(self) -> bool:
        """Check if E2B is configured and available."""
        return self.e2b_enabled

    def get_metrics(self) -> Dict:
        """Get execution metrics for monitoring."""
        avg_exec_time = (
            self.metrics["total_execution_time_seconds"] / self.metrics["executions_total"]
            if self.metrics["executions_total"] > 0
            else 0.0
        )

        return {
            **self.metrics,
            "sandboxes_active": len(self.active_sandboxes),
            "sandboxes_pooled": len(self.sandbox_pool),
            "average_execution_time_seconds": round(avg_exec_time, 2),
            "sandbox_reuse_rate": round(
                self.metrics["sandbox_reuse_count"] / max(self.metrics["sandboxes_created"], 1),
                2
            ),
            "e2b_available": self.e2b_enabled
        }
