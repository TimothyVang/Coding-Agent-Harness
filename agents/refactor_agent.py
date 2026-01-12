"""
Refactor Agent
==============

Code quality and refactoring agent focused on technical debt reduction.

Responsibilities:
- Code smell detection (long functions, high complexity, duplication)
- Technical debt identification (TODO, FIXME, deprecated APIs)
- Complexity analysis (cyclomatic complexity, cognitive complexity)
- Refactoring recommendations with priority and effort estimation
- Code quality metrics tracking
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class RefactorAgent(BaseAgent):
    """
    Refactor Agent - Code Quality and Technical Debt Management

    Responsibilities:
    - Detect code smells (long methods, god classes, duplicated code)
    - Identify technical debt (TODO/FIXME comments, deprecated APIs)
    - Analyze code complexity (cyclomatic, cognitive)
    - Generate prioritized refactoring plans
    - Track code quality metrics over time
    - Suggest specific refactoring strategies

    This agent learns from successful refactorings and code patterns.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize RefactorAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="refactor",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Refactoring-specific configuration
        self.complexity_threshold = config.get("complexity_threshold", 10)
        self.function_length_threshold = config.get("function_length_threshold", 50)
        self.duplication_threshold = config.get("duplication_threshold", 5)
        self.enable_auto_refactor = config.get("enable_auto_refactor", False)

        # Code quality metrics
        self.smell_categories = [
            "long_method",
            "large_class",
            "duplicate_code",
            "long_parameter_list",
            "feature_envy",
            "data_clumps",
            "primitive_obsession"
        ]

        print(f"[RefactorAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Complexity threshold: {self.complexity_threshold}")
        print(f"  - Function length threshold: {self.function_length_threshold}")
        print(f"  - Auto-refactor: {self.enable_auto_refactor}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a refactoring task.

        Process:
        1. Load task details from checklist
        2. Analyze codebase for code smells
        3. Detect technical debt
        4. Measure code complexity
        5. Generate refactoring plan
        6. Create subtasks for high-priority refactorings
        7. Report findings

        Args:
            task: Task dict with checklist_task_id, project_id, etc.

        Returns:
            Result dict with success status and refactoring data
        """
        self.status = "working"
        self.current_task = task

        # Execute before-task hook
        await self.before_task(task)

        result = {
            "success": False,
            "data": {},
            "error": None
        }

        try:
            print(f"\n[{self.agent_id}] 🔧 Starting refactoring analysis")
            print(f"  Task ID: {task.get('checklist_task_id')}")
            print(f"  Project ID: {task.get('project_id')}")

            # Get task details from checklist
            checklist_manager = EnhancedChecklistManager(task.get("project_id"))
            task_details = checklist_manager.get_task(task.get("checklist_task_id"))

            if not task_details:
                raise ValueError(f"Task {task.get('checklist_task_id')} not found in checklist")

            project_path = Path(task_details.get("project_path", Path.cwd()))
            print(f"  Project path: {project_path}")

            # Step 1: Analyze codebase structure
            print("\n[Refactor] Analyzing codebase structure...")
            codebase_analysis = await self._analyze_codebase(project_path)

            # Step 2: Detect code smells
            print("[Refactor] Detecting code smells...")
            code_smells = await self._detect_code_smells(project_path, codebase_analysis)

            # Step 3: Analyze complexity
            print("[Refactor] Analyzing code complexity...")
            complexity_analysis = await self._analyze_complexity(project_path, codebase_analysis)

            # Step 4: Identify technical debt
            print("[Refactor] Identifying technical debt...")
            tech_debt = await self._identify_technical_debt(project_path, codebase_analysis)

            # Step 5: Generate refactoring plan
            print("[Refactor] Generating refactoring plan...")
            refactoring_plan = await self._generate_refactoring_plan(
                code_smells,
                complexity_analysis,
                tech_debt,
                codebase_analysis
            )

            # Step 6: Create subtasks for high-priority refactorings
            subtasks_created = []
            if refactoring_plan.get("high_priority_items"):
                print(f"\n[Refactor] Creating subtasks for {len(refactoring_plan['high_priority_items'])} high-priority refactorings...")
                for item in refactoring_plan["high_priority_items"][:5]:  # Top 5
                    subtask_id = checklist_manager.add_subtask(
                        parent_task_id=task.get("checklist_task_id"),
                        title=item["title"],
                        description=item["description"],
                        priority="HIGH" if item["priority"] == "CRITICAL" else "MEDIUM"
                    )
                    subtasks_created.append(subtask_id)
                    print(f"  ✓ Created subtask: {item['title']}")

            # Step 7: Generate refactoring report
            report = await self._generate_refactoring_report(
                codebase_analysis,
                code_smells,
                complexity_analysis,
                tech_debt,
                refactoring_plan
            )

            # Update task with results
            checklist_manager.update_task(
                task.get("checklist_task_id"),
                status="completed",
                result={
                    "code_smells_found": len(code_smells),
                    "complexity_issues": len(complexity_analysis.get("high_complexity_functions", [])),
                    "tech_debt_items": len(tech_debt),
                    "refactoring_items": len(refactoring_plan.get("items", [])),
                    "subtasks_created": len(subtasks_created),
                    "report": report
                }
            )

            result["success"] = True
            result["data"] = {
                "codebase_analysis": codebase_analysis,
                "code_smells": code_smells,
                "complexity_analysis": complexity_analysis,
                "tech_debt": tech_debt,
                "refactoring_plan": refactoring_plan,
                "subtasks_created": subtasks_created,
                "report": report,
                "notes": f"Found {len(code_smells)} code smells, {len(tech_debt)} tech debt items"
            }

            print(f"\n[{self.agent_id}] ✅ Refactoring analysis completed")
            print(f"  - Code smells: {len(code_smells)}")
            print(f"  - Complexity issues: {len(complexity_analysis.get('high_complexity_functions', []))}")
            print(f"  - Tech debt items: {len(tech_debt)}")
            print(f"  - Refactoring recommendations: {len(refactoring_plan.get('items', []))}")

        except Exception as e:
            result["error"] = str(e)
            print(f"\n[{self.agent_id}] ❌ Error during refactoring: {e}")

            # Update task with error
            try:
                checklist_manager = EnhancedChecklistManager(task.get("project_id"))
                checklist_manager.update_task(
                    task.get("checklist_task_id"),
                    status="failed",
                    result={"error": str(e)}
                )
            except:
                pass

        finally:
            self.status = "idle"
            self.current_task = None

            # Execute after-task hook
            await self.after_task(task, result)

        return result

    async def _detect_code_smells(self, project_path: Path, codebase_analysis: Dict) -> List[Dict]:
        """
        Detect code smells in the codebase.

        Detects:
        - Long methods (> function_length_threshold lines)
        - Large classes (> 500 lines)
        - Duplicate code
        - Long parameter lists (> 5 parameters)
        - Deep nesting (> 4 levels)

        Args:
            project_path: Path to project
            codebase_analysis: Codebase analysis from _analyze_codebase()

        Returns:
            List of code smell dicts
        """
        code_smells = []
        language = codebase_analysis.get("language", "unknown")

        try:
            # Determine file extensions based on language
            extensions = self._get_code_extensions(language)

            # Analyze code files
            for ext in extensions:
                files = list(project_path.rglob(f"*{ext}"))[:50]  # Limit to 50 files

                for file_path in files:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        smells = await self._analyze_file_for_smells(file_path, content, language)
                        code_smells.extend(smells)
                    except Exception as e:
                        print(f"[Refactor] Error analyzing {file_path}: {e}")

        except Exception as e:
            print(f"[Refactor] Error detecting code smells: {e}")

        return code_smells

    async def _analyze_file_for_smells(self, file_path: Path, content: str, language: str) -> List[Dict]:
        """Analyze a single file for code smells."""
        smells = []
        lines = content.split('\n')

        # Long Method Detection
        if language in ["python", "javascript", "typescript"]:
            functions = self._extract_functions(content, language)
            for func in functions:
                if func["lines"] > self.function_length_threshold:
                    smells.append({
                        "type": "long_method",
                        "severity": "MEDIUM" if func["lines"] < 100 else "HIGH",
                        "file": str(file_path),
                        "function": func["name"],
                        "line": func["start_line"],
                        "metric": func["lines"],
                        "description": f"Function '{func['name']}' has {func['lines']} lines (threshold: {self.function_length_threshold})",
                        "recommendation": "Break down into smaller, focused functions"
                    })

        # Large Class Detection
        if len(lines) > 500:
            smells.append({
                "type": "large_class",
                "severity": "MEDIUM" if len(lines) < 1000 else "HIGH",
                "file": str(file_path),
                "line": 1,
                "metric": len(lines),
                "description": f"File has {len(lines)} lines (threshold: 500)",
                "recommendation": "Consider splitting into multiple classes/modules"
            })

        # Long Parameter List Detection
        if language in ["python", "javascript", "typescript"]:
            param_issues = self._detect_long_parameter_lists(content, language)
            smells.extend([{
                "type": "long_parameter_list",
                "severity": "LOW",
                "file": str(file_path),
                **issue
            } for issue in param_issues])

        # Deep Nesting Detection
        deep_nesting = self._detect_deep_nesting(content)
        if deep_nesting:
            smells.extend([{
                "type": "deep_nesting",
                "severity": "MEDIUM",
                "file": str(file_path),
                **nesting
            } for nesting in deep_nesting])

        # Duplicate Code Detection (simple hash-based)
        duplicate_blocks = self._detect_duplicate_blocks(content)
        if duplicate_blocks:
            smells.extend([{
                "type": "duplicate_code",
                "severity": "LOW",
                "file": str(file_path),
                **dup
            } for dup in duplicate_blocks])

        return smells

    def _extract_functions(self, content: str, language: str) -> List[Dict]:
        """Extract functions from code content."""
        functions = []
        lines = content.split('\n')

        if language == "python":
            # Match Python function definitions
            pattern = r'^(\s*)def\s+(\w+)\s*\('
            for i, line in enumerate(lines, 1):
                match = re.match(pattern, line)
                if match:
                    indent = len(match.group(1))
                    func_name = match.group(2)

                    # Count lines until next function at same or lower indent
                    func_lines = 1
                    for j in range(i, len(lines)):
                        next_line = lines[j]
                        if next_line.strip() and not next_line.strip().startswith('#'):
                            next_indent = len(next_line) - len(next_line.lstrip())
                            if j > i and next_indent <= indent and (next_line.strip().startswith('def ') or next_line.strip().startswith('class ')):
                                break
                        func_lines += 1

                    functions.append({
                        "name": func_name,
                        "start_line": i,
                        "lines": func_lines
                    })

        elif language in ["javascript", "typescript"]:
            # Match JavaScript/TypeScript function definitions
            patterns = [
                r'function\s+(\w+)\s*\(',  # function name()
                r'(\w+)\s*[=:]\s*function\s*\(',  # name = function()
                r'(\w+)\s*[=:]\s*\([^)]*\)\s*=>',  # name = () =>
                r'async\s+function\s+(\w+)\s*\('  # async function name()
            ]

            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    match = re.search(pattern, line)
                    if match:
                        func_name = match.group(1)

                        # Count lines until closing brace
                        brace_count = line.count('{') - line.count('}')
                        func_lines = 1
                        for j in range(i, min(i + 200, len(lines))):
                            next_line = lines[j]
                            brace_count += next_line.count('{') - next_line.count('}')
                            func_lines += 1
                            if brace_count == 0:
                                break

                        functions.append({
                            "name": func_name,
                            "start_line": i,
                            "lines": func_lines
                        })

        return functions

    def _detect_long_parameter_lists(self, content: str, language: str) -> List[Dict]:
        """Detect functions with too many parameters."""
        issues = []

        if language == "python":
            pattern = r'def\s+(\w+)\s*\(([^)]+)\)'
        elif language in ["javascript", "typescript"]:
            pattern = r'function\s+(\w+)\s*\(([^)]+)\)|(\w+)\s*=\s*\(([^)]+)\)\s*=>'
        else:
            return issues

        for i, line in enumerate(content.split('\n'), 1):
            match = re.search(pattern, line)
            if match:
                params = match.group(2) if match.group(2) else match.group(4)
                if params:
                    param_count = len([p.strip() for p in params.split(',') if p.strip()])
                    if param_count > 5:
                        func_name = match.group(1) or match.group(3)
                        issues.append({
                            "function": func_name,
                            "line": i,
                            "metric": param_count,
                            "description": f"Function '{func_name}' has {param_count} parameters",
                            "recommendation": "Consider using a configuration object"
                        })

        return issues

    def _detect_deep_nesting(self, content: str) -> List[Dict]:
        """Detect deeply nested code blocks."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip():
                indent_level = (len(line) - len(line.lstrip())) // 4
                if indent_level > 4:
                    issues.append({
                        "line": i,
                        "metric": indent_level,
                        "description": f"Code nested {indent_level} levels deep",
                        "recommendation": "Extract nested logic into separate functions"
                    })

        return issues

    def _detect_duplicate_blocks(self, content: str) -> List[Dict]:
        """Detect duplicate code blocks (simplified)."""
        duplicates = []
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]

        # Check for duplicate consecutive lines
        for i in range(len(lines) - self.duplication_threshold):
            block = '\n'.join(lines[i:i+self.duplication_threshold])
            for j in range(i + self.duplication_threshold, len(lines) - self.duplication_threshold):
                other_block = '\n'.join(lines[j:j+self.duplication_threshold])
                if block == other_block:
                    duplicates.append({
                        "line": i + 1,
                        "duplicate_line": j + 1,
                        "metric": self.duplication_threshold,
                        "description": f"Duplicate code block found at lines {i+1} and {j+1}",
                        "recommendation": "Extract duplicate code into a reusable function"
                    })
                    break

        return duplicates[:10]  # Limit to 10 duplicates

    async def _analyze_complexity(self, project_path: Path, codebase_analysis: Dict) -> Dict:
        """
        Analyze code complexity metrics.

        Analyzes:
        - Cyclomatic complexity (approximate)
        - Cognitive complexity
        - Nesting depth
        - Number of branches

        Args:
            project_path: Path to project
            codebase_analysis: Codebase analysis

        Returns:
            Complexity analysis dict
        """
        complexity_data = {
            "high_complexity_functions": [],
            "average_complexity": 0.0,
            "max_complexity": 0
        }

        try:
            language = codebase_analysis.get("language", "unknown")
            extensions = self._get_code_extensions(language)

            total_complexity = 0
            function_count = 0

            for ext in extensions:
                files = list(project_path.rglob(f"*{ext}"))[:30]

                for file_path in files:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        functions = self._extract_functions(content, language)

                        for func in functions:
                            # Extract function content
                            lines = content.split('\n')
                            func_content = '\n'.join(lines[func["start_line"]-1:func["start_line"]+func["lines"]-1])

                            # Calculate approximate cyclomatic complexity
                            complexity = self._calculate_cyclomatic_complexity(func_content)

                            total_complexity += complexity
                            function_count += 1

                            if complexity > self.complexity_threshold:
                                complexity_data["high_complexity_functions"].append({
                                    "file": str(file_path),
                                    "function": func["name"],
                                    "line": func["start_line"],
                                    "complexity": complexity,
                                    "severity": "HIGH" if complexity > 20 else "MEDIUM"
                                })

                                complexity_data["max_complexity"] = max(
                                    complexity_data["max_complexity"],
                                    complexity
                                )

                    except Exception as e:
                        print(f"[Refactor] Error analyzing complexity in {file_path}: {e}")

            if function_count > 0:
                complexity_data["average_complexity"] = total_complexity / function_count

        except Exception as e:
            print(f"[Refactor] Error in complexity analysis: {e}")

        return complexity_data

    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """
        Calculate approximate cyclomatic complexity.

        Formula: E - N + 2P (edges - nodes + 2*components)
        Simplified: Count decision points + 1
        """
        complexity = 1  # Base complexity

        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']

        for keyword in decision_keywords:
            if keyword in ['&&', '||', '?']:
                complexity += code.count(keyword)
            else:
                # Count keyword as whole word
                complexity += len(re.findall(rf'\b{keyword}\b', code))

        return complexity

    async def _identify_technical_debt(self, project_path: Path, codebase_analysis: Dict) -> List[Dict]:
        """
        Identify technical debt in the codebase.

        Identifies:
        - TODO/FIXME comments
        - Deprecated API usage
        - Commented-out code
        - Magic numbers
        - Hardcoded values

        Args:
            project_path: Path to project
            codebase_analysis: Codebase analysis

        Returns:
            List of technical debt items
        """
        tech_debt = []
        language = codebase_analysis.get("language", "unknown")
        extensions = self._get_code_extensions(language)

        try:
            for ext in extensions:
                files = list(project_path.rglob(f"*{ext}"))[:50]

                for file_path in files:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')

                        for i, line in enumerate(lines, 1):
                            # TODO/FIXME comments
                            if 'TODO' in line:
                                tech_debt.append({
                                    "type": "todo_comment",
                                    "severity": "LOW",
                                    "file": str(file_path),
                                    "line": i,
                                    "description": f"TODO: {line.strip()}",
                                    "recommendation": "Address or create a task to handle this TODO"
                                })

                            if 'FIXME' in line:
                                tech_debt.append({
                                    "type": "fixme_comment",
                                    "severity": "MEDIUM",
                                    "file": str(file_path),
                                    "line": i,
                                    "description": f"FIXME: {line.strip()}",
                                    "recommendation": "High priority - address this issue"
                                })

                            # Deprecated API patterns
                            if 'deprecated' in line.lower():
                                tech_debt.append({
                                    "type": "deprecated_api",
                                    "severity": "MEDIUM",
                                    "file": str(file_path),
                                    "line": i,
                                    "description": "Use of deprecated API",
                                    "recommendation": "Update to use current API"
                                })

                            # Magic numbers (simple detection)
                            if language == "python":
                                # Look for numeric literals (excluding 0, 1, -1)
                                magic_numbers = re.findall(r'\b(?!0\b|1\b|-1\b)\d+\b', line)
                                if magic_numbers and not line.strip().startswith('#'):
                                    tech_debt.append({
                                        "type": "magic_number",
                                        "severity": "LOW",
                                        "file": str(file_path),
                                        "line": i,
                                        "description": f"Magic number(s) found: {', '.join(magic_numbers)}",
                                        "recommendation": "Extract to named constant"
                                    })

                    except Exception as e:
                        print(f"[Refactor] Error analyzing tech debt in {file_path}: {e}")

        except Exception as e:
            print(f"[Refactor] Error identifying technical debt: {e}")

        return tech_debt[:100]  # Limit to 100 items

    async def _generate_refactoring_plan(
        self,
        code_smells: List[Dict],
        complexity_analysis: Dict,
        tech_debt: List[Dict],
        codebase_analysis: Dict
    ) -> Dict:
        """
        Generate a prioritized refactoring plan.

        Args:
            code_smells: Detected code smells
            complexity_analysis: Complexity metrics
            tech_debt: Technical debt items
            codebase_analysis: Overall codebase analysis

        Returns:
            Refactoring plan dict with prioritized items
        """
        plan = {
            "items": [],
            "high_priority_items": [],
            "medium_priority_items": [],
            "low_priority_items": [],
            "estimated_effort_hours": 0.0
        }

        try:
            all_issues = []

            # Add high complexity functions as critical priority
            for func in complexity_analysis.get("high_complexity_functions", []):
                all_issues.append({
                    "priority": "CRITICAL" if func["complexity"] > 20 else "HIGH",
                    "category": "complexity",
                    "title": f"Reduce complexity in {func['function']}",
                    "description": f"Function has cyclomatic complexity of {func['complexity']} (threshold: {self.complexity_threshold})",
                    "file": func["file"],
                    "line": func["line"],
                    "effort_hours": 3 if func["complexity"] > 20 else 2
                })

            # Add code smells
            for smell in code_smells:
                priority = "HIGH" if smell["severity"] == "HIGH" else "MEDIUM" if smell["severity"] == "MEDIUM" else "LOW"
                effort = 2 if priority == "HIGH" else 1

                all_issues.append({
                    "priority": priority,
                    "category": smell["type"],
                    "title": f"Fix {smell['type'].replace('_', ' ')}: {Path(smell['file']).name}",
                    "description": smell["description"],
                    "file": smell["file"],
                    "line": smell.get("line", 0),
                    "recommendation": smell.get("recommendation", ""),
                    "effort_hours": effort
                })

            # Add technical debt (only MEDIUM and HIGH severity)
            for debt in tech_debt:
                if debt["severity"] in ["HIGH", "MEDIUM"]:
                    all_issues.append({
                        "priority": debt["severity"],
                        "category": "tech_debt",
                        "title": f"Resolve {debt['type'].replace('_', ' ')}",
                        "description": debt["description"],
                        "file": debt["file"],
                        "line": debt["line"],
                        "recommendation": debt.get("recommendation", ""),
                        "effort_hours": 0.5
                    })

            # Sort by priority
            priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            all_issues.sort(key=lambda x: priority_order[x["priority"]])

            # Categorize and calculate effort
            for issue in all_issues:
                plan["items"].append(issue)
                plan["estimated_effort_hours"] += issue["effort_hours"]

                if issue["priority"] in ["CRITICAL", "HIGH"]:
                    plan["high_priority_items"].append(issue)
                elif issue["priority"] == "MEDIUM":
                    plan["medium_priority_items"].append(issue)
                else:
                    plan["low_priority_items"].append(issue)

        except Exception as e:
            print(f"[Refactor] Error generating refactoring plan: {e}")

        return plan

    async def _generate_refactoring_report(
        self,
        codebase_analysis: Dict,
        code_smells: List[Dict],
        complexity_analysis: Dict,
        tech_debt: List[Dict],
        refactoring_plan: Dict
    ) -> str:
        """Generate comprehensive refactoring report."""
        lines = []

        lines.append("# Refactoring Analysis Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append(f"**Agent**: {self.agent_id}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Code Smells Found**: {len(code_smells)}")
        lines.append(f"- **High Complexity Functions**: {len(complexity_analysis.get('high_complexity_functions', []))}")
        lines.append(f"- **Technical Debt Items**: {len(tech_debt)}")
        lines.append(f"- **Refactoring Recommendations**: {len(refactoring_plan.get('items', []))}")
        lines.append(f"- **Estimated Effort**: {refactoring_plan.get('estimated_effort_hours', 0):.1f} hours")
        lines.append("")

        # Code Quality Metrics
        lines.append("## Code Quality Metrics")
        lines.append("")
        lines.append(f"- **Total Files**: {codebase_analysis.get('file_count', 0)}")
        lines.append(f"- **Lines of Code**: {codebase_analysis.get('lines_of_code', 0):,}")
        lines.append(f"- **Average Complexity**: {complexity_analysis.get('average_complexity', 0):.2f}")
        lines.append(f"- **Max Complexity**: {complexity_analysis.get('max_complexity', 0)}")
        lines.append("")

        # High Priority Refactorings
        if refactoring_plan.get("high_priority_items"):
            lines.append("## High Priority Refactorings")
            lines.append("")
            for item in refactoring_plan["high_priority_items"][:10]:
                lines.append(f"### {item['title']}")
                lines.append(f"- **File**: `{item['file']}`:{item.get('line', 0)}")
                lines.append(f"- **Category**: {item['category']}")
                lines.append(f"- **Description**: {item['description']}")
                if item.get('recommendation'):
                    lines.append(f"- **Recommendation**: {item['recommendation']}")
                lines.append(f"- **Estimated Effort**: {item['effort_hours']:.1f} hours")
                lines.append("")

        # Code Smell Summary
        if code_smells:
            lines.append("## Code Smell Summary")
            lines.append("")
            smell_counts = {}
            for smell in code_smells:
                smell_type = smell['type']
                smell_counts[smell_type] = smell_counts.get(smell_type, 0) + 1

            for smell_type, count in sorted(smell_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{smell_type.replace('_', ' ').title()}**: {count}")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(lines)

    def _get_code_extensions(self, language: str) -> List[str]:
        """Get file extensions for language."""
        extension_map = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "javascript/typescript": [".js", ".jsx", ".ts", ".tsx"],
            "go": [".go"],
            "java": [".java"],
            "ruby": [".rb"],
            "php": [".php"],
            "rust": [".rs"]
        }
        return extension_map.get(language.lower(), [".py", ".js", ".ts"])

    def get_system_prompt(self) -> str:
        """Get system prompt for the Refactor Agent."""
        return f"""You are {self.agent_id}, a Refactor Agent in the Universal AI Development Platform.

Your role is to improve code quality, reduce technical debt, and maintain clean, maintainable code.

**Responsibilities:**
1. Detect code smells (long methods, large classes, duplicated code)
2. Identify technical debt (TODO/FIXME, deprecated APIs)
3. Analyze code complexity (cyclomatic, cognitive)
4. Generate prioritized refactoring plans
5. Recommend specific refactoring strategies
6. Track code quality metrics over time

**Code Quality Principles:**
- Follow SOLID principles
- Prefer composition over inheritance
- Keep functions small and focused (Single Responsibility)
- Reduce cyclomatic complexity
- Eliminate code duplication (DRY)
- Use meaningful names
- Write self-documenting code

**Refactoring Strategies:**
- Extract Method: Break long functions into smaller ones
- Extract Class: Split large classes
- Rename: Improve naming clarity
- Simplify Conditionals: Reduce nested if/else
- Replace Magic Numbers: Use named constants
- Remove Dead Code: Delete unused code

**Complexity Thresholds:**
- Function length: {self.function_length_threshold} lines
- Cyclomatic complexity: {self.complexity_threshold}
- Parameters per function: 5
- Nesting depth: 4 levels

When analyzing code, provide:
1. Clear identification of issues
2. Severity assessment (CRITICAL/HIGH/MEDIUM/LOW)
3. Specific recommendations
4. Effort estimation

Your goal is to continuously improve codebase quality and maintainability.
"""
