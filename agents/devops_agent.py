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
import json
import re
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
            "dockerignore_created": False,
            "files_created": []
        }

        try:
            # Detect project information
            project_info = self._detect_project_info(project_path)

            # Generate Dockerfile from template
            dockerfile_template = self._load_template("Dockerfile.template")
            dockerfile_content = self._substitute_template_variables(dockerfile_template, project_info)

            # Write Dockerfile
            dockerfile_path = project_path / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content, encoding='utf-8')
            docker_config["dockerfile_created"] = True
            docker_config["files_created"].append("Dockerfile")
            print(f"[DevOps] Created Dockerfile for {project_info['language']} {project_info['framework']}")

            # Create .dockerignore file
            dockerignore_content = self._generate_dockerignore(project_info)
            dockerignore_path = project_path / ".dockerignore"
            dockerignore_path.write_text(dockerignore_content, encoding='utf-8')
            docker_config["dockerignore_created"] = True
            docker_config["files_created"].append(".dockerignore")
            print("[DevOps] Created .dockerignore file")

            # Create docker-compose.yml for local development (optional)
            compose_content = self._generate_docker_compose(project_info)
            compose_path = project_path / "docker-compose.yml"
            compose_path.write_text(compose_content, encoding='utf-8')
            docker_config["compose_created"] = True
            docker_config["files_created"].append("docker-compose.yml")
            print("[DevOps] Created docker-compose.yml")

        except Exception as e:
            print(f"[DevOps] Error creating Docker configuration: {e}")
            docker_config["error"] = str(e)

        return docker_config

    def _generate_dockerignore(self, project_info: Dict) -> str:
        """Generate .dockerignore file content."""
        ignore_patterns = [
            "# Dependencies",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            ".venv/",
            "venv/",
            "",
            "# Build outputs",
            "dist/",
            "build/",
            ".next/",
            "out/",
            "",
            "# Development files",
            ".git/",
            ".gitignore",
            ".env",
            ".env.local",
            "*.log",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "",
            "# Testing",
            "coverage/",
            ".pytest_cache/",
            "",
            "# Documentation",
            "README.md",
            "docs/",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db"
        ]
        return "\n".join(ignore_patterns)

    def _generate_docker_compose(self, project_info: Dict) -> str:
        """Generate docker-compose.yml for local development."""
        compose = f"""version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "{project_info['port']}:{project_info['port']}"
    environment:
      - NODE_ENV=development
      - PORT={project_info['port']}
    volumes:
      - .:/app
      - /app/node_modules
    command: {project_info.get('dev_command', 'npm run dev')}
"""
        return compose

    async def _create_cicd_pipeline(self, task_details: Dict, project_path: Path) -> Dict:
        """Create CI/CD pipeline configuration."""
        print("[DevOps] Creating CI/CD pipeline...")

        pipeline_config = {
            "platform": "github_actions",  # default
            "pipeline_file": ".github/workflows/deploy.yml",
            "stages": ["test", "security", "build", "deploy"],
            "created": False,
            "files_created": []
        }

        try:
            # Detect project information
            project_info = self._detect_project_info(project_path)

            # Determine CI/CD platform (default to GitHub Actions)
            platform = task_details.get("ci_platform", "github_actions")

            if platform == "github_actions":
                # Create .github/workflows directory
                workflows_dir = project_path / ".github" / "workflows"
                workflows_dir.mkdir(parents=True, exist_ok=True)

                # Generate GitHub Actions workflow from template
                workflow_template = self._load_template("github_actions.yaml")
                workflow_content = self._substitute_template_variables(workflow_template, project_info)

                # Write workflow file
                workflow_path = workflows_dir / "deploy.yml"
                workflow_path.write_text(workflow_content, encoding='utf-8')
                pipeline_config["created"] = True
                pipeline_config["files_created"].append(".github/workflows/deploy.yml")
                print(f"[DevOps] Created GitHub Actions workflow at {workflow_path}")

                # Create additional workflow for PR checks
                pr_workflow = self._generate_pr_workflow(project_info)
                pr_workflow_path = workflows_dir / "pr-checks.yml"
                pr_workflow_path.write_text(pr_workflow, encoding='utf-8')
                pipeline_config["files_created"].append(".github/workflows/pr-checks.yml")
                print("[DevOps] Created PR checks workflow")

            elif platform == "gitlab_ci":
                # Generate .gitlab-ci.yml
                gitlab_ci = self._generate_gitlab_ci(project_info)
                gitlab_ci_path = project_path / ".gitlab-ci.yml"
                gitlab_ci_path.write_text(gitlab_ci, encoding='utf-8')
                pipeline_config["created"] = True
                pipeline_config["files_created"].append(".gitlab-ci.yml")
                print("[DevOps] Created GitLab CI configuration")

            pipeline_config["platform"] = platform

        except Exception as e:
            print(f"[DevOps] Error creating CI/CD pipeline: {e}")
            pipeline_config["error"] = str(e)

        return pipeline_config

    def _generate_pr_workflow(self, project_info: Dict) -> str:
        """Generate a simple PR check workflow."""
        return f"""name: PR Checks

on:
  pull_request:
    branches:
      - main
      - develop

jobs:
  lint-and-test:
    name: Lint and Test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        if: contains('{project_info["language"]}', 'node')
        uses: actions/setup-node@v4
        with:
          node-version: {project_info['node_version']}
          cache: 'npm'

      - name: Install dependencies
        run: {project_info['install_command']}

      - name: Run linter
        run: {project_info['lint_command']}
        continue-on-error: false

      - name: Run tests
        run: {project_info['test_command']}
        env:
          CI: true

      - name: Comment PR
        uses: actions/github-script@v7
        if: always()
        with:
          script: |
            github.rest.issues.createComment({{
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ PR checks completed!'
            }})
"""

    def _generate_gitlab_ci(self, project_info: Dict) -> str:
        """Generate GitLab CI configuration."""
        return f"""stages:
  - test
  - build
  - deploy

variables:
  PROJECT_NAME: {project_info['project_name']}
  NODE_VERSION: {project_info['node_version']}

test:
  stage: test
  image: node:{project_info['node_version']}
  script:
    - {project_info['install_command']}
    - {project_info['lint_command']}
    - {project_info['test_command']}
  coverage: '/Statements\\s*:\\s*(\\d+\\.\\d+)%/'

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - develop

deploy:
  stage: deploy
  script:
    - echo "Deploying to production..."
  only:
    - main
  when: manual
"""

    async def _configure_environments(self, task_details: Dict, project_path: Path) -> Dict:
        """Configure multiple environments (dev, staging, production)."""
        print("[DevOps] Configuring environments...")

        env_config = {
            "environments": [],
            "env_files_created": [],
            "env_template_created": False
        }

        try:
            # Detect project information
            project_info = self._detect_project_info(project_path)

            # Create main .env.example template
            env_template = self._generate_env_template(project_info)
            env_example_path = project_path / ".env.example"
            env_example_path.write_text(env_template, encoding='utf-8')
            env_config["env_template_created"] = True
            env_config["env_files_created"].append(".env.example")
            print("[DevOps] Created .env.example template")

            # Create environment-specific files
            for env_name in self.default_environments:
                env_content = self._generate_env_file(project_info, env_name)
                env_file_path = project_path / f".env.{env_name}"
                env_file_path.write_text(env_content, encoding='utf-8')
                env_config["environments"].append(env_name)
                env_config["env_files_created"].append(f".env.{env_name}")
                print(f"[DevOps] Created .env.{env_name}")

            # Update .gitignore to exclude .env files
            self._update_gitignore(project_path)
            print("[DevOps] Updated .gitignore for environment files")

        except Exception as e:
            print(f"[DevOps] Error configuring environments: {e}")
            env_config["error"] = str(e)

        return env_config

    def _generate_env_template(self, project_info: Dict) -> str:
        """Generate .env.example template with common variables."""
        template_lines = [
            "# Application Configuration",
            f"NODE_ENV=development",
            f"PORT={project_info['port']}",
            "",
            "# Database Configuration",
            "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
            "# DATABASE_URL=mongodb://localhost:27017/dbname",
            "",
            "# Authentication",
            "JWT_SECRET=your-secret-key-here",
            "JWT_EXPIRATION=24h",
            "",
            "# API Keys (replace with actual keys)",
            "API_KEY=",
            "API_SECRET=",
            "",
            "# External Services",
            "REDIS_URL=redis://localhost:6379",
            "",
            "# Logging",
            "LOG_LEVEL=info",
            "",
            "# CORS",
            "CORS_ORIGIN=http://localhost:3000",
            "",
            "# Feature Flags",
            "ENABLE_DEBUG=false",
            ""
        ]
        return "\n".join(template_lines)

    def _generate_env_file(self, project_info: Dict, environment: str) -> str:
        """Generate environment-specific .env file."""
        env_map = {
            "development": {
                "NODE_ENV": "development",
                "PORT": project_info['port'],
                "LOG_LEVEL": "debug",
                "ENABLE_DEBUG": "true"
            },
            "staging": {
                "NODE_ENV": "staging",
                "PORT": project_info['port'],
                "LOG_LEVEL": "info",
                "ENABLE_DEBUG": "false"
            },
            "production": {
                "NODE_ENV": "production",
                "PORT": project_info['port'],
                "LOG_LEVEL": "error",
                "ENABLE_DEBUG": "false"
            }
        }

        env_vars = env_map.get(environment, env_map["development"])
        lines = [f"# {environment.upper()} Environment Configuration", ""]
        for key, value in env_vars.items():
            lines.append(f"{key}={value}")

        lines.extend([
            "",
            "# Database",
            "DATABASE_URL=",
            "",
            "# Authentication",
            "JWT_SECRET=",
            "",
            "# External Services",
            "API_KEY=",
            ""
        ])

        return "\n".join(lines)

    def _update_gitignore(self, project_path: Path) -> None:
        """Update .gitignore to exclude environment files."""
        gitignore_path = project_path / ".gitignore"
        gitignore_entries = [
            "# Environment files",
            ".env",
            ".env.local",
            ".env.development",
            ".env.staging",
            ".env.production",
            ".env.*.local",
            ""
        ]

        if gitignore_path.exists():
            current_content = gitignore_path.read_text(encoding='utf-8')
            if ".env" not in current_content:
                # Append to existing .gitignore
                with gitignore_path.open('a', encoding='utf-8') as f:
                    f.write("\n" + "\n".join(gitignore_entries))
        else:
            # Create new .gitignore
            gitignore_path.write_text("\n".join(gitignore_entries), encoding='utf-8')

    async def _setup_monitoring(self, task_details: Dict, project_path: Path) -> Dict:
        """Set up monitoring and logging."""
        print("[DevOps] Setting up monitoring...")

        monitoring_config = {
            "monitoring_enabled": False,
            "logging_enabled": False,
            "health_checks_configured": False,
            "alerts_configured": False,
            "files_created": []
        }

        try:
            # Detect project information
            project_info = self._detect_project_info(project_path)

            # Create health check endpoint
            health_check_created = await self._create_health_check_endpoint(project_info, project_path)
            if health_check_created:
                monitoring_config["health_checks_configured"] = True
                monitoring_config["files_created"].append("Health check endpoint")
                print("[DevOps] Created health check endpoint")

            # Create logging configuration
            logging_config_created = await self._create_logging_config(project_info, project_path)
            if logging_config_created:
                monitoring_config["logging_enabled"] = True
                monitoring_config["files_created"].append("Logging configuration")
                print("[DevOps] Created logging configuration")

            # Create monitoring dashboard config (for Grafana/Prometheus)
            if self.enable_monitoring:
                dashboard_created = await self._create_monitoring_dashboard(project_info, project_path)
                if dashboard_created:
                    monitoring_config["monitoring_enabled"] = True
                    monitoring_config["files_created"].append("Monitoring dashboard")
                    print("[DevOps] Created monitoring dashboard configuration")

            # Create alert rules
            alerts_created = await self._create_alert_rules(project_info, project_path)
            if alerts_created:
                monitoring_config["alerts_configured"] = True
                monitoring_config["files_created"].append("Alert rules")
                print("[DevOps] Created alert rules")

        except Exception as e:
            print(f"[DevOps] Error setting up monitoring: {e}")
            monitoring_config["error"] = str(e)

        return monitoring_config

    async def _create_health_check_endpoint(self, project_info: Dict, project_path: Path) -> bool:
        """Create health check endpoint based on framework."""
        try:
            if project_info["language"] == "node":
                if project_info["framework"] == "express":
                    # Create Express health check route
                    health_check = """
// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV
  });
});

app.get('/readiness', (req, res) => {
  // Add checks for database, external services, etc.
  res.status(200).json({
    status: 'ready',
    checks: {
      database: 'connected',
      cache: 'connected'
    }
  });
});
"""
                    health_file = project_path / "health-check.js"
                    health_file.write_text(health_check, encoding='utf-8')
                    return True

            elif project_info["language"] == "python":
                if project_info["framework"] in ["fastapi", "flask"]:
                    # Create Python health check
                    health_check = """
from datetime import datetime
import psutil

@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent
    }

@app.get('/readiness')
async def readiness_check():
    # Add checks for database, external services, etc.
    return {
        'status': 'ready',
        'checks': {
            'database': 'connected',
            'cache': 'connected'
        }
    }
"""
                    health_file = project_path / "health_check.py"
                    health_file.write_text(health_check, encoding='utf-8')
                    return True

        except Exception as e:
            print(f"[DevOps] Error creating health check: {e}")
            return False

        return False

    async def _create_logging_config(self, project_info: Dict, project_path: Path) -> bool:
        """Create logging configuration."""
        try:
            if project_info["language"] == "node":
                # Create Winston logging config
                logging_config = """
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: '""" + project_info['project_name'] + """' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
  ],
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple(),
  }));
}

module.exports = logger;
"""
                logging_file = project_path / "logger.js"
                logging_file.write_text(logging_config, encoding='utf-8')
                return True

            elif project_info["language"] == "python":
                # Create Python logging config
                logging_config = f"""
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger('{project_info['project_name']}')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
"""
                logging_file = project_path / "logging_config.py"
                logging_file.write_text(logging_config, encoding='utf-8')
                return True

        except Exception as e:
            print(f"[DevOps] Error creating logging config: {e}")
            return False

        return False

    async def _create_monitoring_dashboard(self, project_info: Dict, project_path: Path) -> bool:
        """Create monitoring dashboard configuration for Prometheus/Grafana."""
        try:
            monitoring_dir = project_path / "monitoring"
            monitoring_dir.mkdir(exist_ok=True)

            # Create Prometheus configuration
            prometheus_config = f"""
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: '{project_info['project_name']}'
    static_configs:
      - targets: ['localhost:{project_info['port']}']
    metrics_path: '/metrics'
"""
            prometheus_file = monitoring_dir / "prometheus.yml"
            prometheus_file.write_text(prometheus_config, encoding='utf-8')

            # Create Grafana dashboard JSON (basic template)
            grafana_dashboard = {
                "dashboard": {
                    "title": f"{project_info['project_name']} Dashboard",
                    "panels": [
                        {
                            "title": "Request Rate",
                            "type": "graph",
                            "targets": [{"expr": "rate(http_requests_total[5m])"}]
                        },
                        {
                            "title": "Error Rate",
                            "type": "graph",
                            "targets": [{"expr": "rate(http_errors_total[5m])"}]
                        },
                        {
                            "title": "Response Time",
                            "type": "graph",
                            "targets": [{"expr": "http_request_duration_seconds"}]
                        }
                    ]
                }
            }
            grafana_file = monitoring_dir / "grafana-dashboard.json"
            grafana_file.write_text(json.dumps(grafana_dashboard, indent=2), encoding='utf-8')

            return True

        except Exception as e:
            print(f"[DevOps] Error creating monitoring dashboard: {e}")
            return False

    async def _create_alert_rules(self, project_info: Dict, project_path: Path) -> bool:
        """Create alerting rules for monitoring."""
        try:
            monitoring_dir = project_path / "monitoring"
            monitoring_dir.mkdir(exist_ok=True)

            # Create Prometheus alert rules
            alert_rules = f"""
groups:
  - name: {project_info['project_name']}_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: HighResponseTime
        expr: http_request_duration_seconds > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "Response time is above 1 second"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 500MB"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Service has been down for 1 minute"
"""
            alert_file = monitoring_dir / "alert-rules.yml"
            alert_file.write_text(alert_rules, encoding='utf-8')

            return True

        except Exception as e:
            print(f"[DevOps] Error creating alert rules: {e}")
            return False

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

    def _load_template(self, template_name: str) -> str:
        """Load deployment template from devops_templates directory."""
        template_path = Path(__file__).parent / "devops_templates" / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        return template_path.read_text(encoding='utf-8')

    def _substitute_template_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Replace {{variable}} placeholders with actual values."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def _detect_project_info(self, project_path: Path) -> Dict[str, str]:
        """Detect project language, framework, and other metadata."""
        info = {
            "project_name": project_path.name,
            "language": "unknown",
            "framework": "unknown",
            "node_version": "18",
            "python_version": "3.11",
            "port": "3000",
            "region": "us-east-1",
            "environment": "production"
        }

        # Detect Node.js projects
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                package_data = json.loads(package_json.read_text(encoding='utf-8'))
                info["language"] = "node"

                # Detect framework from dependencies
                deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                if "next" in deps:
                    info["framework"] = "nextjs"
                    info["build_src"] = "package.json"
                    info["build_use"] = "@vercel/next"
                elif "react" in deps:
                    info["framework"] = "react"
                    info["build_src"] = "package.json"
                    info["build_use"] = "@vercel/static-build"
                elif "vue" in deps:
                    info["framework"] = "vue"
                elif "express" in deps:
                    info["framework"] = "express"

                # Get Node version from engines
                if "engines" in package_data and "node" in package_data["engines"]:
                    node_version = package_data["engines"]["node"]
                    # Extract version number (e.g., ">=18.0.0" -> "18")
                    match = re.search(r'\d+', node_version)
                    if match:
                        info["node_version"] = match.group()

                # Build commands
                scripts = package_data.get("scripts", {})
                info["install_command"] = "npm ci"
                info["build_command"] = scripts.get("build", "npm run build")
                info["test_command"] = scripts.get("test", "npm test")
                info["dev_command"] = scripts.get("dev", "npm run dev")
                info["lint_command"] = scripts.get("lint", "npm run lint")
                info["type_check_command"] = scripts.get("type-check", "npm run type-check")
                info["coverage_command"] = scripts.get("coverage", "npm run coverage")

            except (json.JSONDecodeError, OSError):
                pass

        # Detect Python projects
        requirements_txt = project_path / "requirements.txt"
        pyproject_toml = project_path / "pyproject.toml"
        if requirements_txt.exists() or pyproject_toml.exists():
            info["language"] = "python"
            info["port"] = "8000"
            info["install_command"] = "pip install -r requirements.txt"
            info["build_command"] = "python -m build"
            info["test_command"] = "pytest"
            info["lint_command"] = "pylint ."
            info["type_check_command"] = "mypy ."
            info["coverage_command"] = "pytest --cov=."

            # Detect Python framework
            if requirements_txt.exists():
                req_content = requirements_txt.read_text(encoding='utf-8').lower()
                if "django" in req_content:
                    info["framework"] = "django"
                elif "flask" in req_content:
                    info["framework"] = "flask"
                elif "fastapi" in req_content:
                    info["framework"] = "fastapi"

        # Detect Go projects
        if (project_path / "go.mod").exists():
            info["language"] = "go"
            info["port"] = "8080"
            info["install_command"] = "go mod download"
            info["build_command"] = "go build -o app ."
            info["test_command"] = "go test ./..."

        # Detect Docker configuration
        dockerfile = project_path / "Dockerfile"
        if dockerfile.exists():
            info["has_dockerfile"] = "true"

        # Set container registry based on detected language
        info["container_registry"] = "ghcr.io"
        info["container_image"] = f"ghcr.io/{info['project_name']}:latest"

        # Docker-specific variables
        if info["language"] == "node":
            info["base_image"] = f"node:{info['node_version']}-alpine"
            info["runtime_image"] = f"node:{info['node_version']}-alpine"
            info["dependency_files"] = "package*.json"
            info["build_output"] = "dist"
            info["health_check_command"] = f"curl -f http://localhost:${{PORT}}/health || exit 1"
            info["start_command"] = '"node", "dist/index.js"'
        elif info["language"] == "python":
            info["base_image"] = f"python:{info['python_version']}-slim"
            info["runtime_image"] = f"python:{info['python_version']}-slim"
            info["dependency_files"] = "requirements.txt"
            info["build_output"] = "."
            info["health_check_command"] = f"curl -f http://localhost:${{PORT}}/health || exit 1"
            info["start_command"] = '"python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"'
        elif info["language"] == "go":
            info["base_image"] = "golang:1.21-alpine"
            info["runtime_image"] = "alpine:latest"
            info["dependency_files"] = "go.mod go.sum"
            info["build_output"] = "app"
            info["health_check_command"] = "/app/app health || exit 1"
            info["start_command"] = '"./app"'

        # Output directory for builds
        if info["framework"] == "nextjs":
            info["output_dir"] = ".next"
        elif info["framework"] == "react":
            info["output_dir"] = "build"
        else:
            info["output_dir"] = "dist"

        return info

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
