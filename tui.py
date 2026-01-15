#!/usr/bin/env python3
"""
Coding-Agent-Harness TUI
========================

Simple, user-friendly terminal interface for the multi-agent orchestrator.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
except ImportError:
    print("Installing rich...")
    os.system("pip install rich")
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box

console = Console()

# Paths
HARNESS_DIR = Path(__file__).parent
PROJECTS_DIR = HARNESS_DIR / "projects"
PROMPTS_DIR = HARNESS_DIR / "prompts"


def clear():
    """Clear screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def banner():
    """Show welcome banner."""
    console.print(Panel.fit(
        "[bold cyan]🤖 CODING AGENT HARNESS[/bold cyan]\n"
        "[dim]Multi-Agent AI Development Platform[/dim]",
        border_style="cyan"
    ))


def check_env():
    """Check environment variables."""
    required = {
        "CLAUDE_CODE_OAUTH_TOKEN": "Run: claude setup-token",
        "E2B_API_KEY": "Get from: https://e2b.dev",
        "LINEAR_API_KEY": "Get from: https://linear.app/settings/api"
    }

    missing = []
    for key, hint in required.items():
        if os.environ.get(key):
            console.print(f"  [green]✓[/green] {key}")
        else:
            console.print(f"  [red]✗[/red] {key} - {hint}")
            missing.append(key)

    if missing:
        console.print("\n[red]Add missing keys to .env file[/red]")
        return False
    return True


def get_projects():
    """Get existing projects."""
    projects = []

    # Check projects/ directory
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir() and not p.name.startswith('.'):
                projects.append({"name": p.name, "path": p})

    # Check generations/ directory (legacy)
    gen_dir = HARNESS_DIR / "generations"
    if gen_dir.exists():
        for p in gen_dir.iterdir():
            if p.is_dir() and not p.name.startswith('.'):
                projects.append({"name": p.name, "path": p})

    return projects


def show_main_menu():
    """Show main menu and get choice."""
    projects = get_projects()

    console.print("\n[bold]What would you like to do?[/bold]\n")
    console.print("  [cyan]1[/cyan]  🆕  Start a NEW project")

    if projects:
        console.print("  [cyan]2[/cyan]  📂  Continue EXISTING project")

    console.print("  [cyan]3[/cyan]  🧠  Agent MEMORY dashboard")
    console.print("  [cyan]0[/cyan]  🚪  Exit")

    choices = ["0", "1", "2", "3"] if projects else ["0", "1", "3"]
    return Prompt.ask("\n[bold]Select[/bold]", choices=choices, default="1")


def get_project_goals():
    """Get project goals from user - multiple input methods."""
    console.print("\n[bold cyan]📝 Project Goals & Plan[/bold cyan]")
    console.print("[dim]Tell the AI what you want to build[/dim]\n")

    console.print("  [cyan]1[/cyan]  ✏️   Type it now (simple description)")
    console.print("  [cyan]2[/cyan]  📋  Paste multi-line text")
    console.print("  [cyan]3[/cyan]  📄  Load from file")
    console.print("  [cyan]4[/cyan]  📝  Use template (fill in later)")

    choice = Prompt.ask("\n[bold]How do you want to add your plan?[/bold]",
                        choices=["1", "2", "3", "4"], default="1")

    if choice == "1":
        # Simple one-liner
        console.print("\n[dim]Describe what you want to build in 1-2 sentences:[/dim]")
        goal = Prompt.ask("[cyan]Goal[/cyan]")

        console.print("\n[dim]What language/framework? (e.g., Python, React, Rust)[/dim]")
        tech = Prompt.ask("[cyan]Tech[/cyan]", default="Python")

        console.print("\n[dim]Any specific features? (comma-separated, or press Enter to skip)[/dim]")
        features = Prompt.ask("[cyan]Features[/cyan]", default="")

        content = f"""# Project Goals

## What I Want to Build
{goal}

## Technology
{tech}

## Key Features
{features if features else "- To be defined during development"}

## Notes
- Created via TUI on {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return content

    elif choice == "2":
        # Multi-line paste
        console.print("\n[dim]Paste your project plan below.[/dim]")
        console.print("[dim]When done, type [bold]END[/bold] on a new line and press Enter.[/dim]\n")

        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break

        if not lines:
            console.print("[yellow]No content entered, using template[/yellow]")
            return None

        return "\n".join(lines)

    elif choice == "3":
        # Load from file
        console.print("\n[dim]Enter path to your spec/plan file:[/dim]")
        file_path = Prompt.ask("[cyan]File path[/cyan]")

        try:
            path = Path(file_path).expanduser()
            if path.exists():
                content = path.read_text(encoding='utf-8')
                console.print(f"[green]✓ Loaded {len(content)} characters from {path.name}[/green]")
                return content
            else:
                console.print(f"[red]File not found: {path}[/red]")
                return None
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            return None

    else:
        # Use template
        return None


def create_project():
    """Create a new project."""
    clear()
    console.print(Panel.fit("[bold cyan]🆕 Create New Project[/bold cyan]", border_style="cyan"))

    # Get project name
    console.print("\n[bold]Project Name[/bold]")
    console.print("[dim]Use a short, descriptive name (e.g., 'todo-app', 'api-server')[/dim]")

    while True:
        name = Prompt.ask("\n[cyan]Name[/cyan]").strip()
        if not name:
            console.print("[red]Name cannot be empty[/red]")
            continue

        # Sanitize
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)
        project_path = PROJECTS_DIR / safe_name

        if project_path.exists():
            if Confirm.ask(f"[yellow]'{safe_name}' exists. Use it?[/yellow]"):
                break
            continue
        break

    # Get goals
    goals_content = get_project_goals()

    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)

    # Create spec file
    spec_file = project_path / "GOALS.md"

    if goals_content:
        spec_file.write_text(goals_content, encoding='utf-8')
        console.print(f"\n[green]✓ Created: {spec_file}[/green]")
    else:
        # Default template
        template = f"""# {name}

## Goal
[Describe what you want to build]

## Features
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## Tech Stack
- Language:
- Framework:
- Database:

## Notes
Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        spec_file.write_text(template, encoding='utf-8')
        console.print(f"\n[yellow]Created template: {spec_file}[/yellow]")
        console.print("[dim]Edit this file to add your project details[/dim]")

    console.print(f"[green]✓ Project created at: {project_path}[/green]")

    return {
        "name": name,
        "path": project_path,
        "spec_file": spec_file,
        "is_new": True
    }


def select_project():
    """Select an existing project."""
    clear()
    console.print(Panel.fit("[bold cyan]📂 Select Project[/bold cyan]", border_style="cyan"))

    projects = get_projects()

    if not projects:
        console.print("\n[yellow]No existing projects found[/yellow]")
        if Confirm.ask("Create a new project?"):
            return create_project()
        return None

    # Show projects table
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Location", style="dim")

    for i, proj in enumerate(projects, 1):
        table.add_row(str(i), proj["name"], str(proj["path"].parent.name))

    console.print("\n")
    console.print(table)

    # Get selection
    while True:
        choice = Prompt.ask(
            "\n[bold]Select project number[/bold] (0 to go back)",
            default="1"
        )

        if choice == "0":
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                proj = projects[idx]

                # Find spec file
                spec_file = proj["path"] / "GOALS.md"
                if not spec_file.exists():
                    spec_file = proj["path"] / "PROJECT_SPEC.txt"
                if not spec_file.exists():
                    spec_file = PROMPTS_DIR / "app_spec.txt"

                return {
                    "name": proj["name"],
                    "path": proj["path"],
                    "spec_file": spec_file,
                    "is_new": False
                }
        except ValueError:
            pass

        console.print("[red]Invalid selection[/red]")


def show_project_menu(project):
    """Show project options menu."""
    clear()
    console.print(Panel.fit(
        f"[bold cyan]📁 {project['name']}[/bold cyan]",
        border_style="cyan"
    ))

    # Show current goals if they exist
    if project["spec_file"].exists():
        content = project["spec_file"].read_text(encoding='utf-8')
        preview = content[:500] + "..." if len(content) > 500 else content
        console.print(Panel(preview, title="[dim]Current Goals[/dim]", border_style="dim"))

    console.print("\n[bold]What would you like to do?[/bold]\n")
    console.print("  [cyan]1[/cyan]  🚀  Start building (run agents)")
    console.print("  [cyan]2[/cyan]  ✏️   Edit goals/plan")
    console.print("  [cyan]3[/cyan]  👁️   View full plan")
    console.print("  [cyan]0[/cyan]  ◀️   Go back")

    return Prompt.ask("\n[bold]Select[/bold]", choices=["0", "1", "2", "3"], default="1")


def edit_goals(project):
    """Edit project goals."""
    console.print("\n[bold cyan]✏️ Edit Goals[/bold cyan]")
    console.print("[dim]Enter new content (type END when done)[/dim]\n")

    # Show current content
    if project["spec_file"].exists():
        current = project["spec_file"].read_text(encoding='utf-8')
        console.print(Panel(current, title="[dim]Current[/dim]", border_style="dim"))

        if not Confirm.ask("\n[bold]Replace with new content?[/bold]"):
            return

    console.print("\n[dim]Type your new goals/plan. Type END when finished:[/dim]\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    if lines:
        content = "\n".join(lines)
        project["spec_file"].write_text(content, encoding='utf-8')
        console.print(f"\n[green]✓ Updated {project['spec_file'].name}[/green]")
    else:
        console.print("[yellow]No changes made[/yellow]")


def view_goals(project):
    """View full project goals."""
    clear()
    console.print(Panel.fit(f"[bold cyan]📄 {project['name']} - Goals[/bold cyan]", border_style="cyan"))

    if project["spec_file"].exists():
        content = project["spec_file"].read_text(encoding='utf-8')
        console.print(Panel(content, border_style="dim"))
    else:
        console.print("[yellow]No goals file found[/yellow]")

    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def configure_run():
    """Configure run options."""
    console.print("\n[bold cyan]⚙️ Run Configuration[/bold cyan]\n")

    console.print("  [cyan]1[/cyan]  ♾️   Run until stopped (Ctrl+C)")
    console.print("  [cyan]2[/cyan]  🔢  Run for N iterations")

    choice = Prompt.ask("\n[bold]Select[/bold]", choices=["1", "2"], default="1")

    if choice == "2":
        return IntPrompt.ask("Number of iterations", default=10)
    return None


async def run_orchestrator(project, max_iterations):
    """Run the orchestrator."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]🚀 Starting Agent Orchestrator[/bold green]\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        border_style="green"
    ))

    try:
        from orchestrator import AgentOrchestrator

        config = {
            "project_dir": str(project["path"]),
            "model": os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-20250514"),
            "max_iterations": max_iterations,
        }

        orchestrator = AgentOrchestrator(config=config)

        project_id = orchestrator.register_project(
            name=project["name"],
            path=project["path"],
            spec_file=project["spec_file"],
            priority=1
        )

        console.print(f"[green]✓[/green] Project registered: {project_id}")
        console.print("[dim]Initializing agents...[/dim]")

        await orchestrator.start()

        agent_count = len(orchestrator.agents) if hasattr(orchestrator, 'agents') else 0
        console.print(f"[green]✓[/green] {agent_count} agents ready")

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def show_memory_dashboard():
    """Display agent memory dashboard."""
    clear()
    console.print(Panel.fit("[bold cyan]🧠 Agent Memory Dashboard[/bold cyan]", border_style="cyan"))

    try:
        from core.memory_dashboard import (
            MemoryDashboard, list_agents_with_memory,
            show_all_agents_summary, AgentMemory
        )
        from core.embeddings import check_embedding_dependencies
    except ImportError as e:
        console.print(f"\n[red]Error loading memory dashboard: {e}[/red]")
        console.print("[dim]Make sure core/memory_dashboard.py exists[/dim]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
        return

    # Check embedding status
    embed_status = check_embedding_dependencies()
    if embed_status["available"]:
        console.print(f"\n[green]✓[/green] Embeddings enabled (sentence-transformers {embed_status.get('sentence_transformers_version', 'unknown')})")
    else:
        console.print("\n[yellow]![/yellow] Embeddings not available")
        console.print(f"[dim]Install with: {embed_status['install_command']}[/dim]")

    # List agents with memory
    agents = list_agents_with_memory()

    if not agents:
        console.print("\n[yellow]No agent memories found yet.[/yellow]")
        console.print("[dim]Memories are created when agents complete tasks.[/dim]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
        return

    # Show summary of all agents
    console.print()
    show_all_agents_summary()

    # Menu
    while True:
        console.print("\n[bold]Dashboard Options:[/bold]")
        console.print("  [cyan]1[/cyan]  View agent details")
        console.print("  [cyan]2[/cyan]  Search patterns/mistakes")
        console.print("  [cyan]0[/cyan]  Back to main menu")

        choice = Prompt.ask("\n[bold]Select[/bold]", choices=["0", "1", "2"], default="0")

        if choice == "0":
            break

        elif choice == "1":
            # Select agent
            console.print("\n[bold]Select agent:[/bold]")
            for i, agent_id in enumerate(agents, 1):
                console.print(f"  [cyan]{i}[/cyan]  {agent_id}")

            agent_choice = Prompt.ask("\n[bold]Agent #[/bold]", default="1")
            try:
                idx = int(agent_choice) - 1
                if 0 <= idx < len(agents):
                    memory = AgentMemory(agents[idx])
                    dashboard = MemoryDashboard(memory)
                    clear()
                    dashboard.show_full_dashboard()
                    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            except ValueError:
                console.print("[red]Invalid selection[/red]")

        elif choice == "2":
            # Search
            query = Prompt.ask("\n[cyan]Search query[/cyan]")
            if query.strip():
                console.print()
                for agent_id in agents:
                    memory = AgentMemory(agent_id)
                    dashboard = MemoryDashboard(memory)
                    console.print(f"[bold]Results for {agent_id}:[/bold]")
                    dashboard.show_search(query)
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def main():
    """Main entry point."""
    clear()
    banner()

    console.print("\n[bold]Checking environment...[/bold]")
    if not check_env():
        console.print("\n[red]Please fix environment issues and restart[/red]")
        sys.exit(1)

    while True:
        console.print("\n" + "─" * 50)
        choice = show_main_menu()

        if choice == "0":
            console.print("\n[cyan]Goodbye! 👋[/cyan]")
            break

        if choice == "3":
            show_memory_dashboard()
            continue

        if choice == "1":
            project = create_project()
        else:
            project = select_project()

        if not project:
            continue

        # Project menu loop
        while True:
            action = show_project_menu(project)

            if action == "0":
                break
            elif action == "1":
                # Run
                max_iterations = configure_run()

                console.print("\n[bold]Ready to start?[/bold]")
                table = Table(box=box.SIMPLE)
                table.add_column("Setting", style="dim")
                table.add_column("Value", style="cyan")
                table.add_row("Project", project["name"])
                table.add_row("Path", str(project["path"]))
                table.add_row("Duration", "Unlimited" if not max_iterations else f"{max_iterations} iterations")
                console.print(table)

                if Confirm.ask("\n[bold]Start?[/bold]", default=True):
                    asyncio.run(run_orchestrator(project, max_iterations))
                    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")

            elif action == "2":
                edit_goals(project)

            elif action == "3":
                view_goals(project)

    console.print("\n")


if __name__ == "__main__":
    main()
