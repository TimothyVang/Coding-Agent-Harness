"""
Memory Dashboard
================

Rich console visualization for agent memory system.

Features:
- Overview stats panel
- Pattern browser with similarity scores
- Mistake tracker
- Interactive search
"""

from pathlib import Path
from typing import List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.columns import Columns
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .agent_memory import AgentMemory
from .embeddings import EMBEDDINGS_AVAILABLE


class MemoryDashboard:
    """
    Rich console dashboard for agent memory visualization.
    """

    def __init__(self, memory: Optional[AgentMemory] = None):
        """
        Initialize dashboard.

        Args:
            memory: AgentMemory instance to visualize
        """
        self.memory = memory
        self.console = Console() if RICH_AVAILABLE else None

    def set_memory(self, memory: AgentMemory):
        """Set the memory instance to visualize."""
        self.memory = memory

    def show_overview(self):
        """Display summary stats panel."""
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        summary = self.memory.get_summary()
        data = self.memory.data

        # Create stats table
        stats_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        stats_table.add_column("Stat", style="dim")
        stats_table.add_column("Value", style="cyan")

        stats_table.add_row("Agent ID", summary["agent_id"])
        stats_table.add_row("Agent Type", summary["agent_type"])
        stats_table.add_row("Total Tasks", str(summary["total_tasks"]))
        stats_table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")
        stats_table.add_row("Patterns Learned", str(summary["patterns_learned"]))
        stats_table.add_row("Mistakes Recorded", str(summary["mistakes_recorded"]))
        stats_table.add_row("Knowledge Items", str(summary["knowledge_items"]))
        stats_table.add_row("Active Goals", str(summary["active_goals"]))
        stats_table.add_row("Embeddings", "Enabled" if EMBEDDINGS_AVAILABLE else "Disabled")

        # Create success rate bar
        success_rate = summary["success_rate"]
        bar_width = 20
        filled = int(success_rate / 100 * bar_width)
        bar = "[green]" + "█" * filled + "[/green][dim]" + "░" * (bar_width - filled) + "[/dim]"

        # Main panel
        self.console.print(Panel(
            stats_table,
            title=f"[bold cyan]Agent Memory: {summary['agent_id']}[/bold cyan]",
            border_style="cyan"
        ))

        # Success rate bar
        self.console.print(f"\n  Success Rate: {bar} {success_rate:.1f}%\n")

    def show_patterns(self, context: Optional[str] = None, limit: int = 10):
        """
        List patterns, optionally ranked by similarity to context.

        Args:
            context: Optional context string to rank patterns by similarity
            limit: Maximum number of patterns to show
        """
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        if context:
            patterns = self.memory.find_similar_patterns(context, top_k=limit)
            title = f"Patterns Similar to: '{context[:30]}...'" if len(context) > 30 else f"Patterns Similar to: '{context}'"
        else:
            patterns = self.memory.data["patterns"][:limit]
            title = "Learned Patterns"

        if not patterns:
            self.console.print(Panel("[dim]No patterns learned yet[/dim]", title=title))
            return

        table = Table(box=box.ROUNDED, title=title, show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Pattern", style="green", max_width=40)
        table.add_column("Score", style="cyan", width=8)
        table.add_column("Success", style="yellow", width=8)
        table.add_column("Uses", style="dim", width=5)

        for i, pattern in enumerate(patterns, 1):
            score = pattern.get("similarity_score", 0)
            score_str = f"{score:.0%}" if score else "-"
            success = f"{pattern.get('success_rate', 100):.0f}%"
            uses = str(pattern.get("use_count", 1))

            table.add_row(
                str(i),
                pattern["title"],
                score_str,
                success,
                uses
            )

        self.console.print(table)

    def show_mistakes(self, limit: int = 10):
        """
        Display mistake tracker.

        Args:
            limit: Maximum number of mistakes to show
        """
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        mistakes = self.memory.data["mistakes"][:limit]

        if not mistakes:
            self.console.print(Panel("[dim]No mistakes recorded yet[/dim]", title="Mistakes to Avoid"))
            return

        table = Table(box=box.ROUNDED, title="Mistakes to Avoid", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Mistake", style="red", max_width=30)
        table.add_column("Error", style="yellow", max_width=40)
        table.add_column("Cost", style="dim", width=8)

        for i, mistake in enumerate(mistakes, 1):
            cost = f"{mistake.get('cost_minutes', 0)} min"
            error = mistake.get("error", "")[:40]
            if len(mistake.get("error", "")) > 40:
                error += "..."

            table.add_row(
                str(i),
                mistake["title"],
                error,
                cost
            )

        self.console.print(table)

    def show_knowledge(self, limit: int = 15):
        """
        Display knowledge base.

        Args:
            limit: Maximum number of items to show
        """
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        knowledge = self.memory.data["knowledge"][:limit]

        if not knowledge:
            self.console.print(Panel("[dim]No knowledge items yet[/dim]", title="Knowledge Base"))
            return

        table = Table(box=box.SIMPLE, title="Knowledge Base")
        table.add_column("#", style="dim", width=3)
        table.add_column("Knowledge Item", style="cyan")

        for i, item in enumerate(knowledge, 1):
            table.add_row(str(i), item)

        self.console.print(table)

    def show_goals(self):
        """Display self-improvement goals."""
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        goals = self.memory.data["goals"]

        if not goals:
            self.console.print(Panel("[dim]No goals set yet[/dim]", title="Self-Improvement Goals"))
            return

        table = Table(box=box.SIMPLE, title="Self-Improvement Goals")
        table.add_column("Status", width=3)
        table.add_column("Goal", style="cyan")

        for goal in goals:
            status = "[green]✓[/green]" if goal.get("completed") else "[yellow]☐[/yellow]"
            table.add_row(status, goal["goal"])

        self.console.print(table)

    def show_search(self, query: str):
        """
        Interactive similarity search results.

        Args:
            query: Search query
        """
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        self.console.print(f"\n[bold cyan]Search Results for:[/bold cyan] '{query}'\n")

        # Search patterns
        self.console.print("[bold]Matching Patterns:[/bold]")
        patterns = self.memory.find_similar_patterns(query, top_k=5)
        if patterns:
            for p in patterns:
                score = p.get("similarity_score", 0)
                self.console.print(f"  [green]•[/green] {p['title']} [dim]({score:.0%} match)[/dim]")
        else:
            self.console.print("  [dim]No matching patterns[/dim]")

        # Search mistakes
        self.console.print("\n[bold]Relevant Mistakes:[/bold]")
        mistakes = self.memory.get_relevant_mistakes(query, top_k=5)
        if mistakes:
            for m in mistakes:
                score = m.get("similarity_score", 0)
                self.console.print(f"  [red]•[/red] {m['title']} [dim]({score:.0%} match)[/dim]")
        else:
            self.console.print("  [dim]No relevant mistakes[/dim]")

        self.console.print()

    def show_full_dashboard(self):
        """Display complete dashboard with all sections."""
        if not RICH_AVAILABLE or not self.memory:
            print("Dashboard not available")
            return

        self.console.clear()
        self.show_overview()
        self.console.print()
        self.show_patterns(limit=5)
        self.console.print()
        self.show_mistakes(limit=5)
        self.console.print()
        self.show_goals()


def list_agents_with_memory(memory_base_dir: Optional[Path] = None) -> List[str]:
    """
    List all agents that have memory stored.

    Args:
        memory_base_dir: Base directory for agent memories

    Returns:
        List of agent IDs
    """
    if memory_base_dir is None:
        memory_base_dir = Path(__file__).parent.parent / "AGENT_MEMORY"

    if not memory_base_dir.exists():
        return []

    agents = []
    for agent_dir in memory_base_dir.iterdir():
        if agent_dir.is_dir() and (agent_dir / "memory.md").exists():
            agents.append(agent_dir.name)

    return sorted(agents)


def show_all_agents_summary(memory_base_dir: Optional[Path] = None):
    """
    Show summary of all agents with memory.

    Args:
        memory_base_dir: Base directory for agent memories
    """
    if not RICH_AVAILABLE:
        print("Rich library not available")
        return

    console = Console()
    agents = list_agents_with_memory(memory_base_dir)

    if not agents:
        console.print(Panel("[dim]No agent memories found[/dim]", title="Agent Memories"))
        return

    table = Table(box=box.ROUNDED, title="Agent Memory Summary")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Tasks", style="green")
    table.add_column("Success", style="yellow")
    table.add_column("Patterns", style="blue")
    table.add_column("Mistakes", style="red")

    for agent_id in agents:
        memory = AgentMemory(agent_id, memory_base_dir)
        summary = memory.get_summary()

        table.add_row(
            agent_id,
            summary["agent_type"],
            str(summary["total_tasks"]),
            f"{summary['success_rate']:.1f}%",
            str(summary["patterns_learned"]),
            str(summary["mistakes_recorded"])
        )

    console.print(table)
