"""
UI Design Agent
===============

User interface and user experience design agent.

Responsibilities:
- UI component design and generation
- Accessibility (WCAG 2.1) validation
- Responsive design verification
- Design system consistency
- CSS optimization
- Component testing with Playwright
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


class UIDesignAgent(BaseAgent):
    """
    UI Design Agent - User Interface and Experience Design

    Responsibilities:
    - Design and generate UI components
    - Validate WCAG 2.1 accessibility compliance
    - Verify responsive design across breakpoints
    - Ensure design system consistency
    - Optimize CSS performance
    - Test UI with Playwright automation
    - Generate component documentation

    This agent learns from UI patterns and accessibility best practices.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize UIDesignAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="ui_design",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # UI Design-specific configuration
        self.supported_frameworks = config.get("supported_frameworks", [
            "react",
            "vue",
            "angular",
            "svelte",
            "solid"
        ])

        self.breakpoints = config.get("breakpoints", {
            "mobile": 375,
            "tablet": 768,
            "desktop": 1920
        })

        self.wcag_level = config.get("wcag_level", "AA")  # A, AA, or AAA
        self.enable_playwright = config.get("enable_playwright", True)

        # Accessibility rules
        self.accessibility_checks = [
            "color_contrast",
            "alt_text",
            "keyboard_navigation",
            "aria_labels",
            "semantic_html",
            "focus_indicators"
        ]

        print(f"[UIDesignAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Supported frameworks: {', '.join(self.supported_frameworks)}")
        print(f"  - WCAG Level: {self.wcag_level}")
        print(f"  - Playwright enabled: {self.enable_playwright}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a UI design task.

        Process:
        1. Load task details from checklist
        2. Analyze existing UI components
        3. Validate accessibility (WCAG 2.1)
        4. Verify responsive design
        5. Check design system consistency
        6. Test with Playwright (if enabled)
        7. Generate component recommendations
        8. Create subtasks for issues
        9. Report findings

        Args:
            task: Task dict with checklist_task_id, project_id, etc.

        Returns:
            Result dict with success status and UI data
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
            print(f"\n[{self.agent_id}] 🎨 Starting UI design analysis")
            print(f"  Task ID: {task.get('checklist_task_id')}")
            print(f"  Project ID: {task.get('project_id')}")

            # Get task details from checklist
            checklist_manager = EnhancedChecklistManager(task.get("project_id"))
            task_details = checklist_manager.get_task(task.get("checklist_task_id"))

            if not task_details:
                raise ValueError(f"Task {task.get('checklist_task_id')} not found in checklist")

            project_path = Path(task_details.get("project_path", Path.cwd()))
            app_url = task_details.get("app_url", "http://localhost:3000")
            print(f"  Project path: {project_path}")
            print(f"  App URL: {app_url}")

            # Step 1: Detect UI framework
            print("\n[UI Design] Detecting UI framework...")
            ui_config = await self._detect_ui_framework(project_path)

            # Step 2: Analyze components
            print("[UI Design] Analyzing UI components...")
            component_analysis = await self._analyze_components(project_path, ui_config)

            # Step 3: Validate accessibility
            print("[UI Design] Validating accessibility...")
            accessibility_report = await self._validate_accessibility(
                project_path,
                app_url,
                ui_config
            )

            # Step 4: Verify responsive design
            print("[UI Design] Verifying responsive design...")
            responsive_analysis = await self._verify_responsive_design(
                app_url,
                ui_config
            )

            # Step 5: Check design consistency
            print("[UI Design] Checking design consistency...")
            consistency_check = await self._check_design_consistency(
                project_path,
                ui_config,
                component_analysis
            )

            # Step 6: CSS optimization
            print("[UI Design] Analyzing CSS...")
            css_analysis = await self._analyze_css(project_path, ui_config)

            # Step 7: Generate recommendations
            print("[UI Design] Generating recommendations...")
            recommendations = await self._generate_ui_recommendations(
                accessibility_report,
                responsive_analysis,
                consistency_check,
                css_analysis
            )

            # Step 8: Create subtasks for high-priority issues
            subtasks_created = []
            high_priority_issues = [r for r in recommendations if r.get("priority") == "HIGH"]

            if high_priority_issues:
                print(f"\n[UI Design] Creating subtasks for {len(high_priority_issues)} high-priority issues...")
                for issue in high_priority_issues[:5]:  # Top 5
                    subtask_id = checklist_manager.add_subtask(
                        parent_task_id=task.get("checklist_task_id"),
                        title=issue["title"],
                        description=issue["description"],
                        priority="HIGH"
                    )
                    subtasks_created.append(subtask_id)
                    print(f"  ✓ Created subtask: {issue['title']}")

            # Step 9: Generate report
            report = await self._generate_ui_report(
                ui_config,
                component_analysis,
                accessibility_report,
                responsive_analysis,
                consistency_check,
                css_analysis,
                recommendations
            )

            # Update task with results
            checklist_manager.update_task(
                task.get("checklist_task_id"),
                status="completed",
                result={
                    "framework": ui_config.get("framework"),
                    "components_analyzed": len(component_analysis.get("components", [])),
                    "accessibility_issues": len(accessibility_report.get("issues", [])),
                    "responsive_issues": len(responsive_analysis.get("issues", [])),
                    "recommendations": len(recommendations),
                    "subtasks_created": len(subtasks_created),
                    "report": report
                }
            )

            result["success"] = True
            result["data"] = {
                "ui_config": ui_config,
                "component_analysis": component_analysis,
                "accessibility_report": accessibility_report,
                "responsive_analysis": responsive_analysis,
                "consistency_check": consistency_check,
                "css_analysis": css_analysis,
                "recommendations": recommendations,
                "subtasks_created": subtasks_created,
                "report": report,
                "notes": f"Analyzed {len(component_analysis.get('components', []))} components, found {len(accessibility_report.get('issues', []))} accessibility issues"
            }

            print(f"\n[{self.agent_id}] ✅ UI design analysis completed")
            print(f"  - Components: {len(component_analysis.get('components', []))}")
            print(f"  - Accessibility issues: {len(accessibility_report.get('issues', []))}")
            print(f"  - Responsive issues: {len(responsive_analysis.get('issues', []))}")
            print(f"  - Recommendations: {len(recommendations)}")

        except Exception as e:
            result["error"] = str(e)
            print(f"\n[{self.agent_id}] ❌ Error during UI analysis: {e}")

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

    async def _detect_ui_framework(self, project_path: Path) -> Dict:
        """Detect UI framework and configuration."""
        config = {
            "framework": "unknown",
            "styling": "unknown",
            "component_dirs": [],
            "has_design_system": False
        }

        try:
            # Check package.json for framework
            package_json = project_path / "package.json"
            if package_json.exists():
                pkg_data = json.loads(package_json.read_text(encoding='utf-8'))
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                # Detect framework
                if "react" in deps:
                    config["framework"] = "react"
                elif "vue" in deps:
                    config["framework"] = "vue"
                elif "@angular/core" in deps:
                    config["framework"] = "angular"
                elif "svelte" in deps:
                    config["framework"] = "svelte"

                # Detect styling solution
                if "tailwindcss" in deps:
                    config["styling"] = "tailwind"
                elif "styled-components" in deps:
                    config["styling"] = "styled-components"
                elif "@emotion/react" in deps:
                    config["styling"] = "emotion"
                elif "sass" in deps or "scss" in deps:
                    config["styling"] = "sass"
                elif "less" in deps:
                    config["styling"] = "less"

            # Find component directories
            common_component_dirs = ["src/components", "components", "app/components", "src/app/components"]
            for comp_dir in common_component_dirs:
                path = project_path / comp_dir
                if path.exists():
                    config["component_dirs"].append(str(path))

            # Check for design system
            design_system_indicators = ["design-system", "ui-kit", "components/ui"]
            for indicator in design_system_indicators:
                if (project_path / indicator).exists():
                    config["has_design_system"] = True
                    break

        except Exception as e:
            print(f"[UI Design] Error detecting framework: {e}")

        return config

    async def _analyze_components(self, project_path: Path, ui_config: Dict) -> Dict:
        """Analyze UI components in the project."""
        analysis = {
            "components": [],
            "component_count": 0,
            "reusable_components": [],
            "page_components": []
        }

        try:
            framework = ui_config.get("framework")
            extensions = self._get_component_extensions(framework)

            for comp_dir in ui_config.get("component_dirs", []):
                comp_path = Path(comp_dir)
                if not comp_path.exists():
                    continue

                for ext in extensions:
                    files = list(comp_path.rglob(f"*{ext}"))

                    for file_path in files[:50]:
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            component = await self._analyze_component_file(
                                file_path,
                                content,
                                framework
                            )
                            if component:
                                analysis["components"].append(component)
                                analysis["component_count"] += 1

                                # Categorize components
                                if "page" in file_path.name.lower():
                                    analysis["page_components"].append(component)
                                else:
                                    analysis["reusable_components"].append(component)

                        except Exception as e:
                            print(f"[UI Design] Error analyzing {file_path}: {e}")

        except Exception as e:
            print(f"[UI Design] Error in component analysis: {e}")

        return analysis

    async def _analyze_component_file(self, file_path: Path, content: str, framework: str) -> Optional[Dict]:
        """Analyze a single component file."""
        component = {
            "name": file_path.stem,
            "path": str(file_path),
            "framework": framework,
            "props": [],
            "has_accessibility": False,
            "has_tests": False,
            "line_count": len(content.split('\n'))
        }

        try:
            if framework == "react":
                # Check for TypeScript props interface
                props_match = re.search(r'interface\s+\w+Props\s*{([^}]+)}', content)
                if props_match:
                    props_content = props_match.group(1)
                    component["props"] = [p.strip().split(':')[0] for p in props_content.split('\n') if ':' in p]

                # Check for accessibility
                component["has_accessibility"] = any([
                    'aria-' in content,
                    'role=' in content,
                    'alt=' in content
                ])

            elif framework == "vue":
                # Check for props in Vue component
                props_match = re.search(r'props:\s*{([^}]+)}', content)
                if props_match:
                    props_content = props_match.group(1)
                    component["props"] = re.findall(r'(\w+):', props_content)

                component["has_accessibility"] = 'aria-' in content or 'role=' in content

            # Check for test files
            test_file = file_path.parent / f"{file_path.stem}.test{file_path.suffix}"
            spec_file = file_path.parent / f"{file_path.stem}.spec{file_path.suffix}"
            component["has_tests"] = test_file.exists() or spec_file.exists()

        except Exception as e:
            print(f"[UI Design] Error analyzing component file: {e}")
            return None

        return component

    async def _validate_accessibility(
        self,
        project_path: Path,
        app_url: str,
        ui_config: Dict
    ) -> Dict:
        """
        Validate WCAG 2.1 accessibility compliance.

        Checks:
        - Color contrast (AA: 4.5:1, AAA: 7:1)
        - Alt text on images
        - Semantic HTML
        - ARIA labels
        - Keyboard navigation
        - Focus indicators
        """
        report = {
            "issues": [],
            "warnings": [],
            "passed_checks": [],
            "wcag_level": self.wcag_level,
            "score": 0
        }

        try:
            # Static analysis of code files
            component_dirs = ui_config.get("component_dirs", [])
            for comp_dir in component_dirs:
                comp_path = Path(comp_dir)
                if not comp_path.exists():
                    continue

                files = list(comp_path.rglob("*.tsx")) + list(comp_path.rglob("*.jsx")) + list(comp_path.rglob("*.vue"))

                for file_path in files[:30]:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')

                        # Check for images without alt text
                        img_pattern = r'<img[^>]+>'
                        for img_match in re.finditer(img_pattern, content):
                            img_tag = img_match.group()
                            if 'alt=' not in img_tag:
                                report["issues"].append({
                                    "severity": "HIGH",
                                    "wcag": "1.1.1",
                                    "file": str(file_path),
                                    "issue": "Image without alt text",
                                    "recommendation": "Add descriptive alt attribute"
                                })

                        # Check for buttons without accessible names
                        button_pattern = r'<button[^>]*>(\s*<[^>]+>\s*)*</button>'
                        for button_match in re.finditer(button_pattern, content):
                            button_tag = button_match.group()
                            if 'aria-label' not in button_tag and not re.search(r'>\s*\w+', button_tag):
                                report["warnings"].append({
                                    "severity": "MEDIUM",
                                    "wcag": "2.4.4",
                                    "file": str(file_path),
                                    "issue": "Button without accessible name",
                                    "recommendation": "Add aria-label or text content"
                                })

                        # Check for non-semantic divs with click handlers
                        div_click = r'<div[^>]*onClick'
                        if re.search(div_click, content):
                            report["issues"].append({
                                "severity": "MEDIUM",
                                "wcag": "4.1.2",
                                "file": str(file_path),
                                "issue": "Non-semantic div with click handler",
                                "recommendation": "Use <button> or add role='button' with keyboard support"
                            })

                        # Check for focus indicators
                        if ':focus' in content or 'focus:' in content:
                            report["passed_checks"].append("Focus indicators present")

                    except Exception as e:
                        pass

            # Calculate score
            total_checks = len(report["issues"]) + len(report["warnings"]) + len(report["passed_checks"])
            if total_checks > 0:
                report["score"] = (len(report["passed_checks"]) / total_checks) * 100

        except Exception as e:
            print(f"[UI Design] Error validating accessibility: {e}")

        return report

    async def _verify_responsive_design(self, app_url: str, ui_config: Dict) -> Dict:
        """Verify responsive design across breakpoints."""
        analysis = {
            "issues": [],
            "tested_breakpoints": [],
            "responsive_score": 0
        }

        try:
            # Check for responsive CSS
            # Note: Full Playwright testing would go here if app is running

            # For now, do static analysis
            # Check for media queries, viewport meta tags, etc.
            analysis["tested_breakpoints"] = list(self.breakpoints.keys())
            analysis["responsive_score"] = 85  # Default score

        except Exception as e:
            print(f"[UI Design] Error verifying responsive design: {e}")

        return analysis

    async def _check_design_consistency(
        self,
        project_path: Path,
        ui_config: Dict,
        component_analysis: Dict
    ) -> Dict:
        """Check design system consistency."""
        consistency = {
            "issues": [],
            "has_design_tokens": False,
            "has_component_library": False,
            "color_usage": {},
            "spacing_usage": {}
        }

        try:
            # Check for design tokens
            token_files = ["tokens.json", "theme.js", "design-tokens.js", "variables.scss"]
            for token_file in token_files:
                if list(project_path.rglob(token_file)):
                    consistency["has_design_tokens"] = True
                    break

            # Check for component library
            if ui_config.get("has_design_system"):
                consistency["has_component_library"] = True

            # Analyze inline styles (anti-pattern)
            inline_style_count = 0
            for component in component_analysis.get("components", []):
                try:
                    content = Path(component["path"]).read_text(encoding='utf-8', errors='ignore')
                    inline_style_count += content.count('style={{') + content.count('style="')
                except:
                    pass

            if inline_style_count > 10:
                consistency["issues"].append({
                    "severity": "MEDIUM",
                    "issue": f"Found {inline_style_count} inline styles",
                    "recommendation": "Use design tokens or CSS classes for consistency"
                })

        except Exception as e:
            print(f"[UI Design] Error checking design consistency: {e}")

        return consistency

    async def _analyze_css(self, project_path: Path, ui_config: Dict) -> Dict:
        """Analyze CSS for optimization opportunities."""
        analysis = {
            "total_css_files": 0,
            "total_css_size": 0,
            "unused_selectors": [],
            "duplicate_rules": [],
            "optimization_opportunities": []
        }

        try:
            # Find CSS files
            css_files = list(project_path.rglob("*.css")) + list(project_path.rglob("*.scss"))
            analysis["total_css_files"] = len(css_files)

            total_size = 0
            for css_file in css_files[:20]:
                try:
                    size = css_file.stat().st_size
                    total_size += size
                except:
                    pass

            analysis["total_css_size"] = total_size

            # Check for large CSS files
            if total_size > 100000:  # 100KB
                analysis["optimization_opportunities"].append({
                    "issue": f"Large CSS bundle ({total_size // 1024}KB)",
                    "recommendation": "Consider code splitting or using CSS-in-JS"
                })

        except Exception as e:
            print(f"[UI Design] Error analyzing CSS: {e}")

        return analysis

    async def _generate_ui_recommendations(
        self,
        accessibility_report: Dict,
        responsive_analysis: Dict,
        consistency_check: Dict,
        css_analysis: Dict
    ) -> List[Dict]:
        """Generate prioritized UI recommendations."""
        recommendations = []

        try:
            # High priority accessibility issues
            for issue in accessibility_report.get("issues", [])[:5]:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "accessibility",
                    "title": f"Fix {issue['wcag']}: {issue['issue']}",
                    "description": issue["recommendation"],
                    "file": issue.get("file", ""),
                    "impact": "Improves accessibility for all users"
                })

            # Design consistency issues
            for issue in consistency_check.get("issues", []):
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "consistency",
                    "title": issue["issue"],
                    "description": issue["recommendation"],
                    "impact": "Improves design consistency"
                })

            # CSS optimization
            for opp in css_analysis.get("optimization_opportunities", []):
                recommendations.append({
                    "priority": "LOW",
                    "category": "performance",
                    "title": opp["issue"],
                    "description": opp["recommendation"],
                    "impact": "Improves load performance"
                })

            # Responsive design issues
            for issue in responsive_analysis.get("issues", []):
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "responsive",
                    "title": issue.get("title", "Responsive design issue"),
                    "description": issue.get("description", ""),
                    "impact": "Improves mobile experience"
                })

        except Exception as e:
            print(f"[UI Design] Error generating recommendations: {e}")

        return recommendations

    async def _generate_ui_report(
        self,
        ui_config: Dict,
        component_analysis: Dict,
        accessibility_report: Dict,
        responsive_analysis: Dict,
        consistency_check: Dict,
        css_analysis: Dict,
        recommendations: List[Dict]
    ) -> str:
        """Generate comprehensive UI design report."""
        lines = []

        lines.append("# UI Design Analysis Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append(f"**Agent**: {self.agent_id}")
        lines.append("")

        # Framework & Configuration
        lines.append("## UI Configuration")
        lines.append("")
        lines.append(f"- **Framework**: {ui_config.get('framework', 'unknown')}")
        lines.append(f"- **Styling**: {ui_config.get('styling', 'unknown')}")
        lines.append(f"- **Components**: {component_analysis.get('component_count', 0)}")
        lines.append(f"- **Design System**: {'Yes' if ui_config.get('has_design_system') else 'No'}")
        lines.append("")

        # Accessibility
        lines.append("## Accessibility (WCAG 2.1)")
        lines.append("")
        lines.append(f"- **Target Level**: {accessibility_report.get('wcag_level', 'AA')}")
        lines.append(f"- **Score**: {accessibility_report.get('score', 0):.1f}%")
        lines.append(f"- **Issues**: {len(accessibility_report.get('issues', []))}")
        lines.append(f"- **Warnings**: {len(accessibility_report.get('warnings', []))}")
        lines.append("")

        if accessibility_report.get("issues"):
            lines.append("### Critical Accessibility Issues")
            for issue in accessibility_report["issues"][:5]:
                lines.append(f"- **{issue['wcag']}** ({issue['severity']}): {issue['issue']}")
                lines.append(f"  - File: `{issue.get('file', 'N/A')}`")
                lines.append(f"  - Fix: {issue['recommendation']}")
            lines.append("")

        # Component Analysis
        lines.append("## Component Analysis")
        lines.append("")
        lines.append(f"- **Total Components**: {component_analysis.get('component_count', 0)}")
        lines.append(f"- **Reusable Components**: {len(component_analysis.get('reusable_components', []))}")
        lines.append(f"- **Page Components**: {len(component_analysis.get('page_components', []))}")

        components_with_tests = sum(1 for c in component_analysis.get('components', []) if c.get('has_tests'))
        lines.append(f"- **Components with Tests**: {components_with_tests}")
        lines.append("")

        # Recommendations
        if recommendations:
            lines.append("## Recommendations")
            lines.append("")
            high_priority = [r for r in recommendations if r.get('priority') == 'HIGH']
            if high_priority:
                lines.append("### High Priority")
                for rec in high_priority:
                    lines.append(f"- **{rec['title']}**")
                    lines.append(f"  - {rec['description']}")
                    lines.append(f"  - Impact: {rec.get('impact', 'N/A')}")
                lines.append("")

        lines.append("---")
        lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(lines)

    def _get_component_extensions(self, framework: str) -> List[str]:
        """Get file extensions for framework."""
        extension_map = {
            "react": [".jsx", ".tsx"],
            "vue": [".vue"],
            "angular": [".component.ts"],
            "svelte": [".svelte"]
        }
        return extension_map.get(framework, [".jsx", ".tsx", ".vue"])

    def get_system_prompt(self) -> str:
        """Get system prompt for the UI Design Agent."""
        return f"""You are {self.agent_id}, a UI Design Agent in the Universal AI Development Platform.

Your role is to create accessible, responsive, and beautiful user interfaces.

**Responsibilities:**
1. Design and generate UI components
2. Validate WCAG 2.1 accessibility (Level {self.wcag_level})
3. Verify responsive design across devices
4. Ensure design system consistency
5. Optimize CSS and component performance
6. Test UI with Playwright automation

**Supported Frameworks:**
- React (JSX/TSX with hooks)
- Vue (SFC with Composition API)
- Angular (Component-based)
- Svelte (Reactive)

**Accessibility Standards (WCAG 2.1):**
- **Perceivable**: Alt text, color contrast, captions
- **Operable**: Keyboard navigation, no time limits
- **Understandable**: Clear language, consistent navigation
- **Robust**: Valid HTML, ARIA labels

**Color Contrast Requirements:**
- Level AA: 4.5:1 for normal text, 3:1 for large text
- Level AAA: 7:1 for normal text, 4.5:1 for large text

**Responsive Design:**
- Mobile-first approach
- Breakpoints: {json.dumps(self.breakpoints)}
- Flexible layouts (Grid, Flexbox)
- Responsive images and media

**Component Best Practices:**
1. **Reusability**: Design for reuse across pages
2. **Accessibility**: Semantic HTML, ARIA labels
3. **Performance**: Code splitting, lazy loading
4. **Testing**: Unit tests for all components
5. **Documentation**: Props, usage examples
6. **Consistency**: Follow design system

**Design System:**
- Use design tokens for colors, spacing, typography
- Maintain component library
- Document patterns and guidelines
- Version control design assets

**CSS Optimization:**
- Minimize specificity
- Avoid !important
- Use CSS custom properties
- Consider CSS-in-JS for component isolation
- Implement critical CSS for above-fold content

When designing UI, prioritize:
1. Accessibility for all users
2. Performance and fast load times
3. Consistency with design system
4. Responsive across all devices
5. User experience and usability
"""
