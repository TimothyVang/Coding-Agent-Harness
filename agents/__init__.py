"""
Agent Army - Specialized Agents
================================

Collection of specialized agents for the Universal AI Development Platform.

Agent Types:
- BaseAgent: Foundation class for all agents
- ArchitectAgent: Planning and design (✅ IMPLEMENTED)
- BuilderAgent: Feature implementation (✅ IMPLEMENTED)
- TestGeneratorAgent: Automated test creation (✅ IMPLEMENTED)
- VerifierAgent: Quality assurance and verification (✅ IMPLEMENTED)
- ReviewerAgent: Code review (✅ IMPLEMENTED)
- DevOpsAgent: Infrastructure and deployment (✅ IMPLEMENTED)
- DocumentationAgent: Documentation generation (✅ IMPLEMENTED)
- ReporterAgent: Markdown report generation (✅ IMPLEMENTED)
- AnalyticsAgent: Pattern analysis and insights (✅ IMPLEMENTED)
- RefactorAgent: Code quality and refactoring (✅ IMPLEMENTED)
- DatabaseAgent: Schema design and optimization (✅ IMPLEMENTED)
- UIDesignAgent: UI/UX and accessibility (✅ IMPLEMENTED)
- E2BSandboxAgent: E2B sandbox execution (✅ IMPLEMENTED)

All 13 specialized agents implemented! 🎉
"""

from .base_agent import BaseAgent
from .architect_agent import ArchitectAgent
from .builder_agent import BuilderAgent
from .test_generator_agent import TestGeneratorAgent
from .verifier_agent import VerifierAgent
from .reviewer_agent import ReviewerAgent
from .devops_agent import DevOpsAgent
from .documentation_agent import DocumentationAgent
from .reporter_agent import ReporterAgent
from .analytics_agent import AnalyticsAgent
from .refactor_agent import RefactorAgent
from .database_agent import DatabaseAgent
from .ui_design_agent import UIDesignAgent
from .e2b_sandbox_agent import E2BSandboxAgent

__all__ = [
    'BaseAgent',
    'ArchitectAgent',
    'BuilderAgent',
    'TestGeneratorAgent',
    'VerifierAgent',
    'ReviewerAgent',
    'DevOpsAgent',
    'DocumentationAgent',
    'ReporterAgent',
    'AnalyticsAgent',
    'RefactorAgent',
    'DatabaseAgent',
    'UIDesignAgent',
    'E2BSandboxAgent',
]
