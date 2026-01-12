"""
Agent Army - Specialized Agents
================================

Collection of specialized agents for the Universal AI Development Platform.

Agent Types:
- BaseAgent: Foundation class for all agents
- BuilderAgent: Feature implementation (✅ IMPLEMENTED)
- VerifierAgent: Quality assurance and verification (✅ IMPLEMENTED)
- TestGeneratorAgent: Automated test creation (✅ IMPLEMENTED)
- ArchitectAgent: Planning and design
- ReviewerAgent: Code review
- DevOpsAgent: Infrastructure and deployment
- DocumentationAgent: Documentation generation
- ReporterAgent: Markdown report generation
- AnalyticsAgent: Pattern analysis and insights
"""

from .base_agent import BaseAgent
from .builder_agent import BuilderAgent
from .verifier_agent import VerifierAgent
from .test_generator_agent import TestGeneratorAgent

__all__ = [
    'BaseAgent',
    'BuilderAgent',
    'VerifierAgent',
    'TestGeneratorAgent',
]
