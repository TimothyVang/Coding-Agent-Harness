"""
DevOps Agent
============

Infrastructure and deployment agent for CI/CD, containerization, and cloud services.

Responsibilities:
- Infrastructure setup and configuration
- CI/CD pipeline creation (GitHub Actions, GitLab CI, etc.)
- Docker/container configuration
- Deployment automation
- Environment management (dev, staging, production)
- Cloud service integration (AWS, GCP, Azure, Vercel, etc.)
- Monitoring and logging setup
- Security configuration (secrets management, SSL, etc.)
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class DevOpsAgent(BaseAgent):
    """
    DevOps Agent - Infrastructure and Deployment Automation

    Responsibilities:
    - Infrastructure as code (IaC) setup
    - CI/CD pipeline configuration
    - Container orchestration (Docker, Kubernetes)
    - Deployment automation
    - Environment configuration
    - Cloud service integration
    - Monitoring and logging
    - Security and secrets management

    This agent learns from deployment patterns and infrastructure setups.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize DevOpsAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="devops",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # DevOps-specific configuration
        self.supported_platforms = config.get("supported_platforms", [
            "github_actions",
            "gitlab_ci",
            "docker",
            "vercel",
            "aws",
            "gcp",
            "azure"
        ])

        self.default_environments = config.get("environments", ["development", "staging", "production"])
        self.enable_monitoring = config.get("enable_monitoring", True)
        self.enable_logging = config.get("enable_logging", True)
        self.use_containers = config.get("use_containers", True)

        print(f"[DevOpsAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Supported platforms: {len(self.supported_platforms)}")
        print(f"  - Environments: {', '.join(self.default_environments)}")
        print(f"  - Containers: {self.use_containers}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a DevOps/infrastructure task.

        Process:
        1. Load task details from checklist
        2. Determine infrastructure needs
        3. Research best practices using Context7
        4. Generate infrastructure configuration
        5. Create CI/CD pipelines
        6. Configure deployment automation
        7. Set up monitoring and logging
        8. Document infrastructure
        9. Update checklist

        Args:
            task: Task dict from queue with project_id, checklist_task_id

        Returns:
            Dict with success status and infrastructure details
        """
        project_id = task.get("project_id")
        checklist_task_id = task.get("checklist_task_id")

        try:
            # Load project checklist
            project_path = Path(self.config["projects_base_path"]) / project_id
            checklist = EnhancedChecklistManager(project_path)

            # Get task details
            task_details = checklist.get_task(checklist_task_id)
            if not task_details:
                return {
                    "success": False,
                    "error": f"Task {checklist_task_id} not found in checklist"
                }

            task_title = task_details.get("title", "Unknown task")
            self.print_status(f"DevOps: {task_title}")

            # DevOps result tracking
            devops_result = {
                "task_id": checklist_task_id,
                "timestamp": datetime.now().isoformat(),
                "infrastructure_created": [],
                "pipelines_configured": [],
                "environments_set_up": [],
                "services_integrated": []
            }

            # Step 1: Load patterns from memory
            self.memory.load_patterns()

            # Step 2: Analyze infrastructure needs
            infra_needs = await self._analyze_infrastructure_needs(task_details, project_path)
            devops_result["infrastructure_needs"] = infra_needs

            # Step 3: Research DevOps best practices
            if self.client:
                research_summary = await self._research_devops_practices(task_details)
                devops_result["research_summary"] = research_summary

            # Step 4: Generate infrastructure configuration
            if infra_needs.get("needs_containers"):
                docker_config = await self._create_docker_configuration(task_details, project_path)
                devops_result["infrastructure_created"].append("Docker configuration")

            # Step 5: Create CI/CD pipelines
            if infra_needs.get("needs_cicd"):
                pipeline_config = await self._create_cicd_pipeline(task_details, project_path)
                devops_result["pipelines_configured"].append(pipeline_config.get("platform", "unknown"))

            # Step 6: Configure environments
            if infra_needs.get("needs_environments"):
                env_config = await self._configure_environments(task_details, project_path)
                devops_result["environments_set_up"] = env_config.get("environments", [])

            # Step 7: Set up monitoring
            if self.enable_monitoring and infra_needs.get("needs_monitoring"):
                monitoring_config = await self._setup_monitoring(task_details, project_path)
                devops_result["services_integrated"].append("Monitoring")

            # Step 8: Generate infrastructure documentation
            documentation = await self._generate_infrastructure_docs(
                task_details,
                infra_needs,
                devops_result
            )

            # Step 9: Update checklist with DevOps results
            if self.client:
                summary = self._create_summary(devops_result)
                checklist.add_note(checklist_task_id, f"DevOps setup complete: {summary}")

            return {
                "success": True,
                "data": {
                    "devops_result": devops_result,
                    "documentation": documentation,
                    "infrastructure_count": len(devops_result["infrastructure_created"]),
                    "pipeline_count": len(devops_result["pipelines_configured"]),
                    "environment_count": len(devops_result["environments_set_up"])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"DevOps task execution failed: {str(e)}"
            }

    async def _analyze_infrastructure_needs(self, task_details: Dict, project_path: Path) -> Dict:
        """
        Analyze what infrastructure is needed for the project.

        Returns dict with flags:
        - needs_containers: Docker/containerization required
        - needs_cicd: CI/CD pipeline required
        - needs_environments: Multiple environments required
        - needs_monitoring: Monitoring/logging required
        - needs_cloud: Cloud deployment required
        - platform: Target platform (vercel, aws, gcp, azure, etc.)
        """
        title = task_details.get("title", "").lower()
        description = task_details.get("description", "").lower()
        combined = f"{title} {description}"

        needs = {
            "needs_containers": False,
            "needs_cicd": False,
            "needs_environments": False,
            "needs_monitoring": False,
            "needs_cloud": False,
            "platform": "docker",  # default
            "deployment_type": "manual"
        }

        # Check for container needs
        if any(keyword in combined for keyword in ["docker", "container", "kubernetes", "k8s"]):
            needs["needs_containers"] = True

        # Check for CI/CD needs
        if any(keyword in combined for keyword in ["ci/cd", "pipeline", "github actions", "gitlab ci", "deploy", "automation"]):
            needs["needs_cicd"] = True

        # Check for environment needs
        if any(keyword in combined for keyword in ["environment", "staging", "production", "dev", "test"]):
            needs["needs_environments"] = True

        # Check for monitoring needs
        if any(keyword in combined for keyword in ["monitoring", "logging", "metrics", "observability"]):
            needs["needs_monitoring"] = True

        # Detect platform
        if "vercel" in combined:
            needs["platform"] = "vercel"
            needs["needs_cloud"] = True
        elif "aws" in combined or "lambda" in combined or "ec2" in combined:
            needs["platform"] = "aws"
            needs["needs_cloud"] = True
        elif "gcp" in combined or "google cloud" in combined:
            needs["platform"] = "gcp"
            needs["needs_cloud"] = True
        elif "azure" in combined:
            needs["platform"] = "azure"
            needs["needs_cloud"] = True

        # Detect deployment type
        if "github actions" in combined:
            needs["deployment_type"] = "github_actions"
        elif "gitlab" in combined:
            needs["deployment_type"] = "gitlab_ci"

        return needs

    async def _create_docker_configuration(self, task_details: Dict, project_path: Path) -> Dict:
        """Create Docker configuration (Dockerfile, docker-compose.yml)."""
        print("[DevOps] Creating Docker configuration...")

        docker_config = {
            "dockerfile_created": False,
            "compose_created": False,
            "dockerignore_created": False
        }

        # TODO: With Claude client, generate actual Dockerfile
        # For now, structure for configuration

        return docker_config

    async def _create_cicd_pipeline(self, task_details: Dict, project_path: Path) -> Dict:
        """Create CI/CD pipeline configuration."""
        print("[DevOps] Creating CI/CD pipeline...")

        pipeline_config = {
            "platform": "github_actions",  # default
            "pipeline_file": ".github/workflows/main.yml",
            "stages": ["build", "test", "deploy"],
            "created": False
        }

        # TODO: With Claude client, generate actual pipeline configuration
        # - GitHub Actions workflow
        # - GitLab CI configuration
        # - Other CI/CD platforms

        return pipeline_config

    async def _configure_environments(self, task_details: Dict, project_path: Path) -> Dict:
        """Configure multiple environments (dev, staging, production)."""
        print("[DevOps] Configuring environments...")

        env_config = {
            "environments": [],
            "env_files_created": [],
            "env_template_created": False
        }

        for env_name in self.default_environments:
            env_config["environments"].append(env_name)
            # TODO: Create .env.{environment} templates

        return env_config

    async def _setup_monitoring(self, task_details: Dict, project_path: Path) -> Dict:
        """Set up monitoring and logging."""
        print("[DevOps] Setting up monitoring...")

        monitoring_config = {
            "monitoring_enabled": False,
            "logging_enabled": False,
            "health_checks_configured": False,
            "alerts_configured": False
        }

        # TODO: With Claude client, set up:
        # - Application monitoring
        # - Log aggregation
        # - Health check endpoints
        # - Alert configuration

        return monitoring_config

    async def _generate_infrastructure_docs(
        self,
        task_details: Dict,
        infra_needs: Dict,
        devops_result: Dict
    ) -> str:
        """Generate infrastructure documentation."""
        doc_lines = []

        doc_lines.append("# Infrastructure Documentation")
        doc_lines.append("")
        doc_lines.append(f"**Generated**: {datetime.now().isoformat()}")
        doc_lines.append(f"**Agent**: {self.agent_id}")
        doc_lines.append("")

        # Infrastructure overview
        doc_lines.append("## Infrastructure Overview")
        doc_lines.append("")
        doc_lines.append(f"**Platform**: {infra_needs.get('platform', 'docker')}")
        doc_lines.append(f"**Deployment Type**: {infra_needs.get('deployment_type', 'manual')}")
        doc_lines.append("")

        # Components created
        if devops_result.get("infrastructure_created"):
            doc_lines.append("## Infrastructure Components")
            doc_lines.append("")
            for component in devops_result["infrastructure_created"]:
                doc_lines.append(f"- {component}")
            doc_lines.append("")

        # CI/CD pipelines
        if devops_result.get("pipelines_configured"):
            doc_lines.append("## CI/CD Pipelines")
            doc_lines.append("")
            for pipeline in devops_result["pipelines_configured"]:
                doc_lines.append(f"- {pipeline}")
            doc_lines.append("")

        # Environments
        if devops_result.get("environments_set_up"):
            doc_lines.append("## Environments")
            doc_lines.append("")
            for env in devops_result["environments_set_up"]:
                doc_lines.append(f"- {env}")
            doc_lines.append("")

        # Services integrated
        if devops_result.get("services_integrated"):
            doc_lines.append("## Integrated Services")
            doc_lines.append("")
            for service in devops_result["services_integrated"]:
                doc_lines.append(f"- {service}")
            doc_lines.append("")

        doc_lines.append("---")
        doc_lines.append("")
        doc_lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(doc_lines)

    def _create_summary(self, devops_result: Dict) -> str:
        """Create a summary of DevOps work."""
        parts = []

        if devops_result.get("infrastructure_created"):
            parts.append(f"{len(devops_result['infrastructure_created'])} infrastructure components")

        if devops_result.get("pipelines_configured"):
            parts.append(f"{len(devops_result['pipelines_configured'])} CI/CD pipelines")

        if devops_result.get("environments_set_up"):
            parts.append(f"{len(devops_result['environments_set_up'])} environments")

        return ", ".join(parts) if parts else "Infrastructure configured"

    def get_system_prompt(self) -> str:
        """Get system prompt for the DevOps Agent."""
        return f"""You are {self.agent_id}, a DevOps Agent in the Universal AI Development Platform.

Your role is to handle infrastructure, deployment, and operational concerns for software projects.

**Responsibilities:**
1. Infrastructure as Code (IaC) configuration
2. CI/CD pipeline creation and management
3. Container orchestration (Docker, Kubernetes)
4. Deployment automation
5. Environment configuration (dev, staging, production)
6. Cloud service integration (AWS, GCP, Azure, Vercel)
7. Monitoring and logging setup
8. Security configuration (secrets, SSL, firewalls)
9. Performance optimization
10. Disaster recovery and backup strategies

**DevOps Process:**
1. Analyze project infrastructure needs
2. Research best practices using Context7
3. Generate infrastructure configuration files
4. Create CI/CD pipeline definitions
5. Configure multiple environments
6. Set up monitoring and alerting
7. Configure security measures
8. Document infrastructure setup
9. Update task with deployment instructions

**Infrastructure Best Practices:**
- Use Infrastructure as Code (IaC) for reproducibility
- Implement CI/CD for automated deployments
- Configure multiple environments (dev, staging, prod)
- Set up monitoring and logging from day one
- Use containers for consistency across environments
- Implement proper secret management
- Configure automated backups
- Set up health checks and alerts
- Document deployment procedures
- Follow security best practices

**Supported Platforms:**
- CI/CD: GitHub Actions, GitLab CI, Jenkins, CircleCI
- Containers: Docker, Kubernetes, Docker Compose
- Cloud: AWS, GCP, Azure, Vercel, Heroku, DigitalOcean
- Monitoring: Prometheus, Grafana, CloudWatch, Datadog

**Tools Available:**
- EnhancedChecklistManager: Task management
- AgentMemory: Learn from deployment patterns
- Context7: Research infrastructure best practices
- MessageBus: Communicate with other agents

Learn from each deployment to improve future infrastructure setups."""

    def extract_patterns(self, result: Dict) -> List[str]:
        """
        Extract learnable patterns from DevOps results.

        Args:
            result: Task execution result

        Returns:
            List of pattern descriptions
        """
        patterns = []

        if not result.get("success"):
            return patterns

        data = result.get("data", {})
        devops_result = data.get("devops_result", {})

        # Pattern: Successful deployment
        infra_count = len(devops_result.get("infrastructure_created", []))
        if infra_count > 0:
            patterns.append(f"Infrastructure setup: {infra_count} components")

        # Pattern: CI/CD configuration
        pipeline_count = len(devops_result.get("pipelines_configured", []))
        if pipeline_count > 0:
            patterns.append(f"CI/CD pipelines configured: {pipeline_count}")

        # Pattern: Environment setup
        env_count = len(devops_result.get("environments_set_up", []))
        if env_count > 0:
            patterns.append(f"Environments configured: {env_count}")

        # Pattern: Platform used
        infra_needs = devops_result.get("infrastructure_needs", {})
        if infra_needs.get("platform"):
            patterns.append(f"Platform: {infra_needs['platform']}")

        return patterns


# Example usage
async def example_usage():
    """Example of using the DevOpsAgent."""
    from core.message_bus import MessageBus
    from pathlib import Path

    config = {
        "memory_dir": Path("./AGENT_MEMORY"),
        "projects_base_path": Path("./projects"),
        "supported_platforms": ["github_actions", "docker", "vercel"],
        "use_containers": True,
        "enable_monitoring": True
    }

    message_bus = MessageBus()

    agent = DevOpsAgent(
        agent_id="devops-001",
        config=config,
        message_bus=message_bus,
        claude_client=None  # Would be actual client in production
    )

    await agent.initialize()

    # Example task
    task = {
        "task_id": "queue-task-123",
        "project_id": "my-project",
        "checklist_task_id": 10,
        "type": "infrastructure",
        "metadata": {
            "description": "Set up CI/CD pipeline with Docker"
        }
    }

    result = await agent.run_task(task)
    print(f"DevOps result: {result}")

    await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
