"""
Database Agent
==============

Database design, migration, and optimization agent.

Responsibilities:
- Database schema design and normalization
- Migration script generation (Prisma, Alembic, Flyway)
- Query optimization and N+1 detection
- Index recommendations
- Data model validation
- Database performance analysis
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


class DatabaseAgent(BaseAgent):
    """
    Database Agent - Schema Design and Query Optimization

    Responsibilities:
    - Design normalized database schemas
    - Generate migration scripts for various ORMs
    - Detect N+1 query problems
    - Recommend indexes for performance
    - Validate data models and relationships
    - Analyze query performance
    - Support multiple databases (PostgreSQL, MySQL, MongoDB)

    This agent learns from schema patterns and optimization strategies.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize DatabaseAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="database",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Database-specific configuration
        self.supported_databases = config.get("supported_databases", [
            "postgresql",
            "mysql",
            "sqlite",
            "mongodb"
        ])

        self.supported_orms = config.get("supported_orms", [
            "prisma",
            "typeorm",
            "sequelize",
            "sqlalchemy",
            "alembic"
        ])

        self.enable_normalization_checks = config.get("enable_normalization", True)
        self.enable_index_recommendations = config.get("enable_indexes", True)

        print(f"[DatabaseAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Supported databases: {', '.join(self.supported_databases)}")
        print(f"  - Supported ORMs: {', '.join(self.supported_orms)}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a database task.

        Process:
        1. Load task details from checklist
        2. Analyze existing schema (if any)
        3. Design or validate schema
        4. Generate migration scripts
        5. Analyze queries for optimization
        6. Recommend indexes
        7. Create subtasks for implementation
        8. Report findings

        Args:
            task: Task dict with checklist_task_id, project_id, etc.

        Returns:
            Result dict with success status and database data
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
            print(f"\n[{self.agent_id}] 🗄️  Starting database analysis")
            print(f"  Task ID: {task.get('checklist_task_id')}")
            print(f"  Project ID: {task.get('project_id')}")

            # Get task details from checklist
            checklist_manager = EnhancedChecklistManager(task.get("project_id"))
            task_details = checklist_manager.get_task(task.get("checklist_task_id"))

            if not task_details:
                raise ValueError(f"Task {task.get('checklist_task_id')} not found in checklist")

            project_path = Path(task_details.get("project_path", Path.cwd()))
            print(f"  Project path: {project_path}")

            # Step 1: Detect database type and ORM
            print("\n[Database] Detecting database configuration...")
            db_config = await self._detect_database_config(project_path)

            # Step 2: Analyze existing schema
            print("[Database] Analyzing existing schema...")
            schema_analysis = await self._analyze_existing_schema(project_path, db_config)

            # Step 3: Design/validate schema
            print("[Database] Validating schema design...")
            schema_validation = await self._validate_schema_design(schema_analysis, db_config)

            # Step 4: Analyze queries
            print("[Database] Analyzing queries...")
            query_analysis = await self._analyze_queries(project_path, db_config)

            # Step 5: Generate index recommendations
            print("[Database] Generating index recommendations...")
            index_recommendations = await self._recommend_indexes(
                schema_analysis,
                query_analysis,
                db_config
            )

            # Step 6: Generate migration scripts
            print("[Database] Generating migration scripts...")
            migrations = await self._generate_migrations(
                schema_validation,
                db_config,
                project_path
            )

            # Step 7: Create subtasks for high-priority issues
            subtasks_created = []
            if schema_validation.get("critical_issues") or query_analysis.get("n_plus_one_queries"):
                critical_count = len(schema_validation.get("critical_issues", []))
                query_issues = len(query_analysis.get("n_plus_one_queries", []))

                if critical_count > 0:
                    for issue in schema_validation["critical_issues"][:5]:
                        subtask_id = checklist_manager.add_subtask(
                            parent_task_id=task.get("checklist_task_id"),
                            title=f"Fix schema issue: {issue['title']}",
                            description=issue["description"],
                            priority="HIGH"
                        )
                        subtasks_created.append(subtask_id)

                if query_issues > 0:
                    subtask_id = checklist_manager.add_subtask(
                        parent_task_id=task.get("checklist_task_id"),
                        title=f"Optimize {query_issues} N+1 query problem(s)",
                        description="Detected N+1 query patterns that could cause performance issues",
                        priority="MEDIUM"
                    )
                    subtasks_created.append(subtask_id)

            # Step 8: Generate report
            report = await self._generate_database_report(
                db_config,
                schema_analysis,
                schema_validation,
                query_analysis,
                index_recommendations,
                migrations
            )

            # Update task with results
            checklist_manager.update_task(
                task.get("checklist_task_id"),
                status="completed",
                result={
                    "database_type": db_config.get("database_type"),
                    "tables_analyzed": len(schema_analysis.get("tables", [])),
                    "schema_issues": len(schema_validation.get("issues", [])),
                    "query_issues": len(query_analysis.get("issues", [])),
                    "index_recommendations": len(index_recommendations),
                    "migrations_generated": len(migrations),
                    "subtasks_created": len(subtasks_created),
                    "report": report
                }
            )

            result["success"] = True
            result["data"] = {
                "db_config": db_config,
                "schema_analysis": schema_analysis,
                "schema_validation": schema_validation,
                "query_analysis": query_analysis,
                "index_recommendations": index_recommendations,
                "migrations": migrations,
                "subtasks_created": subtasks_created,
                "report": report,
                "notes": f"Analyzed {len(schema_analysis.get('tables', []))} tables, found {len(schema_validation.get('issues', []))} schema issues"
            }

            print(f"\n[{self.agent_id}] ✅ Database analysis completed")
            print(f"  - Tables analyzed: {len(schema_analysis.get('tables', []))}")
            print(f"  - Schema issues: {len(schema_validation.get('issues', []))}")
            print(f"  - Query issues: {len(query_analysis.get('issues', []))}")
            print(f"  - Index recommendations: {len(index_recommendations)}")

        except Exception as e:
            result["error"] = str(e)
            print(f"\n[{self.agent_id}] ❌ Error during database analysis: {e}")

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

    async def _detect_database_config(self, project_path: Path) -> Dict:
        """
        Detect database configuration from project files.

        Returns:
            Dict with database type, ORM, and connection info
        """
        config = {
            "database_type": "unknown",
            "orm": "unknown",
            "schema_files": [],
            "migration_dir": None
        }

        try:
            # Check for Prisma
            prisma_schema = project_path / "prisma" / "schema.prisma"
            if prisma_schema.exists():
                config["orm"] = "prisma"
                config["schema_files"].append(str(prisma_schema))
                config["migration_dir"] = str(project_path / "prisma" / "migrations")

                # Parse provider from schema
                content = prisma_schema.read_text(encoding='utf-8')
                provider_match = re.search(r'provider\s*=\s*"(\w+)"', content)
                if provider_match:
                    config["database_type"] = provider_match.group(1)

            # Check for TypeORM
            elif (project_path / "ormconfig.json").exists():
                config["orm"] = "typeorm"
                ormconfig = json.loads((project_path / "ormconfig.json").read_text())
                config["database_type"] = ormconfig.get("type", "unknown")
                config["migration_dir"] = str(project_path / ormconfig.get("migrations", ["src/migrations"])[0])

            # Check for Sequelize
            elif (project_path / "config" / "config.json").exists():
                config["orm"] = "sequelize"
                seq_config = json.loads((project_path / "config" / "config.json").read_text())
                config["database_type"] = seq_config.get("development", {}).get("dialect", "unknown")

            # Check for SQLAlchemy (Python)
            elif list(project_path.rglob("*models.py")):
                config["orm"] = "sqlalchemy"
                config["database_type"] = "postgresql"  # Default assumption
                config["schema_files"] = [str(f) for f in project_path.rglob("*models.py")]

                # Check for Alembic migrations
                alembic_dir = project_path / "alembic"
                if alembic_dir.exists():
                    config["migration_dir"] = str(alembic_dir / "versions")

            # Check for Django
            elif list(project_path.rglob("*models.py")) and (project_path / "manage.py").exists():
                config["orm"] = "django"
                config["database_type"] = "postgresql"
                config["schema_files"] = [str(f) for f in project_path.rglob("*models.py")]
                config["migration_dir"] = "migrations"

        except Exception as e:
            print(f"[Database] Error detecting config: {e}")

        return config

    async def _analyze_existing_schema(self, project_path: Path, db_config: Dict) -> Dict:
        """
        Analyze existing database schema.

        Returns:
            Dict with tables, columns, relationships, indexes
        """
        schema = {
            "tables": [],
            "relationships": [],
            "indexes": []
        }

        try:
            orm = db_config.get("orm")

            if orm == "prisma":
                schema = await self._parse_prisma_schema(db_config.get("schema_files", [])[0])

            elif orm == "sqlalchemy":
                schema = await self._parse_sqlalchemy_models(db_config.get("schema_files", []))

            elif orm == "typeorm":
                schema = await self._parse_typeorm_entities(project_path)

        except Exception as e:
            print(f"[Database] Error analyzing schema: {e}")

        return schema

    async def _parse_prisma_schema(self, schema_file: str) -> Dict:
        """Parse Prisma schema file."""
        schema = {"tables": [], "relationships": [], "indexes": []}

        try:
            content = Path(schema_file).read_text(encoding='utf-8')

            # Parse models
            model_pattern = r'model\s+(\w+)\s*\{([^}]+)\}'
            for model_match in re.finditer(model_pattern, content):
                table_name = model_match.group(1)
                fields_content = model_match.group(2)

                columns = []
                # Parse fields
                field_pattern = r'(\w+)\s+(\w+)(\?)?(\s+@\w+.*)?'
                for field_match in re.finditer(field_pattern, fields_content):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    is_optional = field_match.group(3) == '?'
                    attributes = field_match.group(4) or ''

                    columns.append({
                        "name": field_name,
                        "type": field_type,
                        "nullable": is_optional,
                        "primary_key": "@id" in attributes,
                        "unique": "@unique" in attributes,
                        "default": "@default" in attributes
                    })

                schema["tables"].append({
                    "name": table_name,
                    "columns": columns
                })

        except Exception as e:
            print(f"[Database] Error parsing Prisma schema: {e}")

        return schema

    async def _parse_sqlalchemy_models(self, model_files: List[str]) -> Dict:
        """Parse SQLAlchemy model files."""
        schema = {"tables": [], "relationships": [], "indexes": []}

        try:
            for model_file in model_files[:10]:
                content = Path(model_file).read_text(encoding='utf-8', errors='ignore')

                # Parse class definitions
                class_pattern = r'class\s+(\w+)\([^)]*\):\s*\n((?:\s{4}.*\n)*)'
                for class_match in re.finditer(class_pattern, content):
                    table_name = class_match.group(1)
                    class_body = class_match.group(2)

                    columns = []
                    # Parse Column definitions
                    column_pattern = r'(\w+)\s*=\s*Column\(([^)]+)\)'
                    for col_match in re.finditer(column_pattern, class_body):
                        col_name = col_match.group(1)
                        col_def = col_match.group(2)

                        columns.append({
                            "name": col_name,
                            "type": col_def.split(',')[0].strip() if ',' in col_def else col_def,
                            "nullable": "nullable=False" not in col_def,
                            "primary_key": "primary_key=True" in col_def,
                            "unique": "unique=True" in col_def
                        })

                    if columns:
                        schema["tables"].append({
                            "name": table_name,
                            "columns": columns
                        })

        except Exception as e:
            print(f"[Database] Error parsing SQLAlchemy models: {e}")

        return schema

    async def _parse_typeorm_entities(self, project_path: Path) -> Dict:
        """Parse TypeORM entity files."""
        schema = {"tables": [], "relationships": [], "indexes": []}

        try:
            # Find entity files
            entity_files = list(project_path.rglob("*.entity.ts"))

            for entity_file in entity_files[:10]:
                content = entity_file.read_text(encoding='utf-8', errors='ignore')

                # Parse @Entity decorator
                entity_match = re.search(r'@Entity\([\'"]?(\w+)?[\'"]?\)', content)
                if entity_match:
                    table_name = entity_match.group(1) or entity_file.stem.replace('.entity', '')

                    columns = []
                    # Parse @Column decorators
                    column_pattern = r'@Column\(([^)]*)\)\s+(\w+):\s*(\w+)'
                    for col_match in re.finditer(column_pattern, content):
                        col_options = col_match.group(1)
                        col_name = col_match.group(2)
                        col_type = col_match.group(3)

                        columns.append({
                            "name": col_name,
                            "type": col_type,
                            "nullable": "nullable: true" in col_options,
                            "unique": "unique: true" in col_options
                        })

                    # Parse @PrimaryGeneratedColumn
                    pk_pattern = r'@PrimaryGeneratedColumn\(\)\s+(\w+):'
                    pk_match = re.search(pk_pattern, content)
                    if pk_match:
                        columns.append({
                            "name": pk_match.group(1),
                            "type": "number",
                            "primary_key": True,
                            "nullable": False
                        })

                    schema["tables"].append({
                        "name": table_name,
                        "columns": columns
                    })

        except Exception as e:
            print(f"[Database] Error parsing TypeORM entities: {e}")

        return schema

    async def _validate_schema_design(self, schema_analysis: Dict, db_config: Dict) -> Dict:
        """
        Validate schema design and detect issues.

        Checks for:
        - Missing primary keys
        - Missing foreign keys
        - Denormalization issues
        - Missing indexes on foreign keys
        - Wide tables (too many columns)
        """
        validation = {
            "valid": True,
            "issues": [],
            "critical_issues": [],
            "warnings": []
        }

        try:
            for table in schema_analysis.get("tables", []):
                table_name = table["name"]
                columns = table.get("columns", [])

                # Check for primary key
                has_pk = any(col.get("primary_key") for col in columns)
                if not has_pk:
                    issue = {
                        "severity": "CRITICAL",
                        "title": f"Missing primary key in {table_name}",
                        "description": f"Table {table_name} does not have a primary key defined",
                        "recommendation": "Add a primary key column (id, uuid, or composite key)"
                    }
                    validation["issues"].append(issue)
                    validation["critical_issues"].append(issue)
                    validation["valid"] = False

                # Check for wide tables (> 20 columns)
                if len(columns) > 20:
                    validation["issues"].append({
                        "severity": "MEDIUM",
                        "title": f"Wide table: {table_name}",
                        "description": f"Table {table_name} has {len(columns)} columns",
                        "recommendation": "Consider normalizing into multiple tables"
                    })

                # Check for potential missing indexes (columns ending in _id without index)
                for col in columns:
                    if col["name"].endswith("_id") and not col.get("primary_key") and not col.get("unique"):
                        validation["warnings"].append({
                            "severity": "LOW",
                            "title": f"Potential missing index in {table_name}.{col['name']}",
                            "description": f"Foreign key column {col['name']} may need an index",
                            "recommendation": "Add index for better join performance"
                        })

        except Exception as e:
            print(f"[Database] Error validating schema: {e}")

        return validation

    async def _analyze_queries(self, project_path: Path, db_config: Dict) -> Dict:
        """
        Analyze queries for N+1 problems and optimization opportunities.

        Returns:
            Dict with query issues and recommendations
        """
        analysis = {
            "issues": [],
            "n_plus_one_queries": [],
            "missing_eager_loading": []
        }

        try:
            orm = db_config.get("orm")

            # Search for query patterns in code
            code_files = list(project_path.rglob("*.ts")) + list(project_path.rglob("*.js")) + list(project_path.rglob("*.py"))

            for code_file in code_files[:50]:
                try:
                    content = code_file.read_text(encoding='utf-8', errors='ignore')

                    # Detect N+1 patterns (loops with queries inside)
                    if orm in ["prisma", "typeorm", "sqlalchemy"]:
                        # Look for patterns like: for item in items: item.related
                        n_plus_one_patterns = [
                            r'for.*in.*:\s*\n\s+.*\.findMany',  # Prisma
                            r'for.*in.*:\s*\n\s+.*\.find\(',  # TypeORM
                            r'for.*in.*:\s*\n\s+.*\.query\.',  # SQLAlchemy
                        ]

                        for pattern in n_plus_one_patterns:
                            if re.search(pattern, content):
                                analysis["n_plus_one_queries"].append({
                                    "file": str(code_file),
                                    "description": "Potential N+1 query detected",
                                    "recommendation": "Use eager loading or batch queries"
                                })
                                break

                    # Detect missing includes/joins
                    if orm == "prisma":
                        # Look for findMany/findUnique without include
                        if ".findMany(" in content or ".findUnique(" in content:
                            if "include:" not in content:
                                analysis["missing_eager_loading"].append({
                                    "file": str(code_file),
                                    "description": "Query without eager loading",
                                    "recommendation": "Add 'include' to load related data efficiently"
                                })

                except Exception as e:
                    pass

        except Exception as e:
            print(f"[Database] Error analyzing queries: {e}")

        analysis["issues"] = analysis["n_plus_one_queries"] + analysis["missing_eager_loading"]
        return analysis

    async def _recommend_indexes(
        self,
        schema_analysis: Dict,
        query_analysis: Dict,
        db_config: Dict
    ) -> List[Dict]:
        """Generate index recommendations."""
        recommendations = []

        try:
            for table in schema_analysis.get("tables", []):
                table_name = table["name"]
                columns = table.get("columns", [])

                # Recommend indexes on foreign keys
                for col in columns:
                    if col["name"].endswith("_id") and not col.get("primary_key"):
                        recommendations.append({
                            "table": table_name,
                            "column": col["name"],
                            "type": "single_column",
                            "reason": "Foreign key column",
                            "priority": "HIGH"
                        })

                    # Recommend indexes on frequently queried columns
                    if col["name"] in ["email", "username", "slug"]:
                        if not col.get("unique"):
                            recommendations.append({
                                "table": table_name,
                                "column": col["name"],
                                "type": "single_column",
                                "reason": "Frequently queried field",
                                "priority": "MEDIUM"
                            })

        except Exception as e:
            print(f"[Database] Error recommending indexes: {e}")

        return recommendations[:20]  # Top 20 recommendations

    async def _generate_migrations(
        self,
        schema_validation: Dict,
        db_config: Dict,
        project_path: Path
    ) -> List[Dict]:
        """Generate migration scripts for schema changes."""
        migrations = []

        try:
            orm = db_config.get("orm")
            critical_issues = schema_validation.get("critical_issues", [])

            for issue in critical_issues:
                if "Missing primary key" in issue["title"]:
                    table_name = issue["title"].split()[-1]

                    if orm == "prisma":
                        migration_code = f"""
model {table_name} {{
  id Int @id @default(autoincrement())
  // ... existing fields
}}
"""
                    elif orm == "sqlalchemy":
                        migration_code = f"""
def upgrade():
    op.add_column('{table_name.lower()}', sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True))

def downgrade():
    op.drop_column('{table_name.lower()}', 'id')
"""
                    else:
                        migration_code = f"ALTER TABLE {table_name} ADD COLUMN id SERIAL PRIMARY KEY;"

                    migrations.append({
                        "type": "add_primary_key",
                        "table": table_name,
                        "orm": orm,
                        "code": migration_code
                    })

        except Exception as e:
            print(f"[Database] Error generating migrations: {e}")

        return migrations

    async def _generate_database_report(
        self,
        db_config: Dict,
        schema_analysis: Dict,
        schema_validation: Dict,
        query_analysis: Dict,
        index_recommendations: List[Dict],
        migrations: List[Dict]
    ) -> str:
        """Generate comprehensive database analysis report."""
        lines = []

        lines.append("# Database Analysis Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append(f"**Agent**: {self.agent_id}")
        lines.append("")

        # Configuration
        lines.append("## Database Configuration")
        lines.append("")
        lines.append(f"- **Database Type**: {db_config.get('database_type', 'unknown')}")
        lines.append(f"- **ORM**: {db_config.get('orm', 'unknown')}")
        lines.append(f"- **Tables**: {len(schema_analysis.get('tables', []))}")
        lines.append("")

        # Schema Issues
        if schema_validation.get("critical_issues"):
            lines.append("## Critical Schema Issues")
            lines.append("")
            for issue in schema_validation["critical_issues"]:
                lines.append(f"### {issue['title']}")
                lines.append(f"- **Severity**: {issue['severity']}")
                lines.append(f"- **Description**: {issue['description']}")
                lines.append(f"- **Recommendation**: {issue['recommendation']}")
                lines.append("")

        # Query Analysis
        if query_analysis.get("n_plus_one_queries"):
            lines.append("## Query Performance Issues")
            lines.append("")
            lines.append(f"Found {len(query_analysis['n_plus_one_queries'])} potential N+1 query problems:")
            lines.append("")
            for issue in query_analysis["n_plus_one_queries"][:5]:
                lines.append(f"- **File**: `{issue['file']}`")
                lines.append(f"  - {issue['description']}")
                lines.append(f"  - **Fix**: {issue['recommendation']}")
                lines.append("")

        # Index Recommendations
        if index_recommendations:
            lines.append("## Index Recommendations")
            lines.append("")
            high_priority = [r for r in index_recommendations if r.get('priority') == 'HIGH']
            if high_priority:
                lines.append("### High Priority")
                for rec in high_priority[:5]:
                    lines.append(f"- `{rec['table']}.{rec['column']}` - {rec['reason']}")
                lines.append("")

        # Migrations
        if migrations:
            lines.append("## Suggested Migrations")
            lines.append("")
            for migration in migrations:
                lines.append(f"### {migration['type']} - {migration['table']}")
                lines.append("```sql")
                lines.append(migration['code'].strip())
                lines.append("```")
                lines.append("")

        lines.append("---")
        lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(lines)

    def get_system_prompt(self) -> str:
        """Get system prompt for the Database Agent."""
        return f"""You are {self.agent_id}, a Database Agent in the Universal AI Development Platform.

Your role is to design efficient database schemas, optimize queries, and ensure data integrity.

**Responsibilities:**
1. Database schema design and normalization (1NF, 2NF, 3NF, BCNF)
2. Generate migration scripts for various ORMs
3. Detect and fix N+1 query problems
4. Recommend indexes for performance
5. Validate data models and relationships
6. Analyze query performance

**Supported Databases:**
- PostgreSQL (recommended for ACID, JSON, full-text search)
- MySQL (high performance, wide adoption)
- SQLite (lightweight, embedded)
- MongoDB (NoSQL, document store)

**Supported ORMs:**
- Prisma (Node.js, type-safe)
- TypeORM (TypeScript, decorator-based)
- Sequelize (Node.js, mature)
- SQLAlchemy (Python, powerful)
- Django ORM (Python, batteries-included)

**Database Design Principles:**
1. **Normalization**: Eliminate redundancy, ensure data integrity
2. **Primary Keys**: Every table must have a primary key
3. **Foreign Keys**: Maintain referential integrity
4. **Indexes**: Add indexes on foreign keys and frequently queried columns
5. **Data Types**: Choose appropriate types (avoid TEXT for everything)
6. **Constraints**: Use NOT NULL, UNIQUE, CHECK constraints

**Query Optimization:**
- Avoid N+1 queries (use eager loading/joins)
- Use proper indexes
- Limit result sets
- Avoid SELECT *
- Use connection pooling
- Cache frequently accessed data

**Migration Best Practices:**
- Make migrations reversible
- Test migrations on staging first
- Backup data before migrations
- Use transactions for safety
- Version control all migrations

When designing schemas, prioritize:
1. Data integrity
2. Query performance
3. Scalability
4. Maintainability
"""
