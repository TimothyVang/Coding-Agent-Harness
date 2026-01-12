"""
Agent Army - Specialized Agents
================================

Collection of specialized agents for the Universal AI Development Platform.

Agent Types:
- BaseAgent: Foundation class for all agents
- BuilderAgent: Feature implementation (✅ IMPLEMENTED)
- ArchitectAgent: Planning and design
- TestGeneratorAgent: Automated test creation
- VerifierAgent: Quality assurance and verification
- ReviewerAgent: Code review
- DevOpsAgent: Infrastructure and deployment
- DocumentationAgent: Documentation generation
- ReporterAgent: Markdown report generation
- AnalyticsAgent: Pattern analysis and insights
"""

from .base_agent import BaseAgent
from .builder_agent import BuilderAgent

__all__ = [
    'BaseAgent',
    'BuilderAgent',
]
