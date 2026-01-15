#!/usr/bin/env python3
"""
Setup Checklist - Universal Template
====================================

This script initializes a project checklist based on your app_spec.txt.
Customize the tasks below to match your project requirements, or let the
initializer agent create tasks automatically from your specification.

Usage:
    python setup_checklist.py

The script will:
1. Read project configuration from environment or use defaults
2. Initialize the checklist with defined tasks
3. Export to CHECKLIST.md for human-readable tracking
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from checklist_manager import ChecklistManager

# Load environment variables
load_dotenv()

# Get project name from environment or use default
project_name = os.getenv("PROJECT_NAME", "My Project")

# Initialize the manager
project_dir = Path.cwd()
manager = ChecklistManager(project_dir)

# ============================================
# CUSTOMIZE YOUR TASKS BELOW
# ============================================
# These are example/template tasks. Replace with your actual project tasks
# or let the initializer agent generate them from app_spec.txt

tasks = [
    # ===========================================
    # PHASE 0: PROJECT SETUP
    # ===========================================
    {
        "title": "Initialize project structure",
        "description": "Set up the basic project directory structure, initialize version control, and create configuration files."
    },
    {
        "title": "Add core dependencies",
        "description": "Add required dependencies to the project's package manager (Cargo.toml, package.json, requirements.txt, etc.)."
    },
    {
        "title": "Create development environment setup script",
        "description": "Create init.sh/init.bat scripts to set up the development environment with required tools and configurations."
    },

    # ===========================================
    # PHASE 1: CORE FEATURES
    # ===========================================
    {
        "title": "Implement core module structure",
        "description": "Create the main application modules and establish the basic architecture patterns."
    },
    {
        "title": "Implement error handling",
        "description": "Create comprehensive error types and handling mechanisms for the application."
    },
    {
        "title": "Create unit tests for core modules",
        "description": "Write unit tests covering the main functionality of core modules. Target >80% code coverage."
    },

    # ===========================================
    # PHASE 2: ADDITIONAL FEATURES
    # ===========================================
    {
        "title": "Implement secondary features",
        "description": "Build out additional features as specified in app_spec.txt."
    },
    {
        "title": "Create integration tests",
        "description": "Write integration tests covering end-to-end workflows."
    },

    # ===========================================
    # PHASE 3: USER INTERFACE
    # ===========================================
    {
        "title": "Implement CLI interface",
        "description": "Create command-line interface with argument parsing, help text, and user feedback."
    },
    {
        "title": "Implement GUI (if applicable)",
        "description": "Create graphical user interface as specified in app_spec.txt."
    },

    # ===========================================
    # PHASE 4: DOCUMENTATION & RELEASE
    # ===========================================
    {
        "title": "Write README.md",
        "description": "Create comprehensive README with project overview, installation, usage, and contribution guidelines."
    },
    {
        "title": "Write user documentation",
        "description": "Create detailed user guides and API documentation."
    },
    {
        "title": "Final testing and validation",
        "description": "Run full test suite, fix any remaining issues, verify all features work as specified."
    },
    {
        "title": "Create release v1.0.0",
        "description": "Tag release, build distribution packages, publish documentation."
    },
]

# Initialize the checklist
manager.initialize(project_name=project_name, tasks=tasks)

# Export to markdown
manager.export_to_markdown()

print(f"\nChecklist initialized for: {project_name}")
print(f"Total tasks: {len(tasks)}")
print("\nFiles created:")
print("  - .project_checklist.json (machine-readable)")
print("  - CHECKLIST.md (human-readable)")
print("\nNote: These are template tasks. For your specific project,")
print("      either edit this file or use the TUI to load your app_spec.txt")
print("      and let the initializer agent generate tasks automatically.")
