"""Main orchestrator for test data generation."""

import sys
import time
from typing import Dict, List, Optional

import httpx

from .config import GeneratorConfig
from .data_validator import DataValidator
from .dependency_assigner import DependencyAssigner
from .docker_manager import DockerManager
from .metadata_enricher import MetadataEnricher
from .project_generator import ProjectGenerator
from .status_assigner import StatusAssigner
from .task_generator import TaskGenerator
from .task_list_generator import TaskListGenerator


class DataGenerator:
    """Main orchestrator for test data generation.
    
    Coordinates all phases of data generation:
    1. Database Reset
    2. Entity Creation (projects, task lists, tasks)
    3. Dependency Assignment
    4. Status Assignment
    5. Metadata Enrichment
    6. Validation
    """

    def __init__(self, config: GeneratorConfig):
        """Initialize the data generator.
        
        Args:
            config: Generator configuration
        """
        self.config = config
        
        # Initialize all components
        self.docker_manager = DockerManager(
            db_connection_string=self._build_db_connection_string()
        )
        self.project_generator = ProjectGenerator(config)
        self.task_list_generator = TaskListGenerator(config)
        self.task_generator = TaskGenerator(config)
        self.dependency_assigner = DependencyAssigner(config)
        self.status_assigner = StatusAssigner(config)
        self.metadata_enricher = MetadataEnricher(config)
        self.data_validator = DataValidator(config)
        
        # Track generated entities
        self.projects: List[Dict] = []
        self.task_lists: List[Dict] = []
        self.tasks: List[Dict] = []

    def generate(self) -> bool:
        """Execute all phases of data generation.
        
        Returns:
            True if generation and validation succeeded, False otherwise
        """
        try:
            print("Phase 1: Resetting database...")
            self._reset_database()
            print("✓ Database reset complete\n")
            
            print("Phase 2: Creating entities...")
            self._create_entities()
            print(f"✓ Created {len(self.projects)} projects, "
                  f"{len(self.task_lists)} task lists, "
                  f"{len(self.tasks)} tasks\n")
            
            print("Phase 3: Assigning dependencies...")
            self._assign_dependencies()
            print("✓ Dependencies assigned\n")
            
            print("Phase 4: Assigning statuses...")
            self._assign_statuses()
            print("✓ Statuses assigned\n")
            
            print("Phase 5: Enriching metadata...")
            self._enrich_metadata()
            print("✓ Metadata enriched\n")
            
            print("Phase 6: Validating data...")
            validation_report = self._validate_data()
            print(validation_report)
            
            if not validation_report.success:
                print("\n❌ Data validation failed!", file=sys.stderr)
                return False
            
            print("\n✓ Data generation completed successfully!")
            self._print_summary()
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠ Generation interrupted by user", file=sys.stderr)
            return False
        except Exception as e:
            print(f"\n\n❌ Generation failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def _reset_database(self) -> None:
        """Reset the Docker database with retry logic.
        
        Raises:
            RuntimeError: If database reset fails after retries
            TimeoutError: If database connection verification times out
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.docker_manager.reset_database()
                
                # Wait for API to be ready
                self._wait_for_api()
                return
                
            except (RuntimeError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠ Attempt {attempt + 1} failed: {e}")
                    print(f"  Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(
                        f"Failed to reset database after {max_retries} attempts: {e}"
                    )

    def _wait_for_api(self, timeout: int = 60) -> None:
        """Wait for the REST API to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Raises:
            TimeoutError: If API doesn't become ready within timeout
        """
        start_time = time.time()
        last_error: Optional[Exception] = None
        
        print("  Waiting for API to be ready...")
        
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(
                    f"{self.config.api_base_url}/health",
                    timeout=5.0
                )
                if response.status_code == 200:
                    print("  ✓ API is ready")
                    return
            except Exception as e:
                last_error = e
            
            time.sleep(2)
        
        error_msg = f"API did not become ready within {timeout}s"
        if last_error:
            error_msg += f": {last_error}"
        raise TimeoutError(error_msg)

    def _clear_existing_projects(self) -> None:
        """Clear all existing non-default projects from the database.
        
        This ensures a clean slate before generating new test data.
        Default projects (Chore, Repeatable) cannot be deleted.
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                # Get all projects
                response = client.get(f"{self.config.api_base_url}/projects")
                response.raise_for_status()
                data = response.json()
                
                # Extract projects list from response
                projects = data.get("projects", []) if isinstance(data, dict) else data
                
                # Delete all non-default projects
                for project in projects:
                    # Skip default projects
                    if project.get("name") in ["Chore", "Repeatable"]:
                        continue
                    
                    try:
                        delete_response = client.delete(
                            f"{self.config.api_base_url}/projects/{project['id']}"
                        )
                        # Ignore 404 errors (project already deleted)
                        if delete_response.status_code not in [200, 204, 404]:
                            delete_response.raise_for_status()
                    except httpx.HTTPError:
                        # Continue even if deletion fails
                        pass
        except httpx.HTTPError:
            # If we can't clear projects, continue anyway
            # The database reset should have handled this
            pass

    def _create_entities(self) -> None:
        """Create projects, task lists, and tasks.
        
        Raises:
            httpx.HTTPError: If API requests fail
        """
        # Delete all existing projects (except defaults which can't be deleted)
        print("  Clearing existing projects...")
        self._clear_existing_projects()
        
        # Create projects
        print("  Creating projects...")
        self.projects = self._retry_with_backoff(
            self.project_generator.generate_projects,
            "create projects"
        )
        
        # Create task lists for each project
        print("  Creating task lists...")
        self.task_lists = []
        for project in self.projects:
            task_lists = self._retry_with_backoff(
                lambda: self.task_list_generator.generate_task_lists(
                    project["id"],
                    project["task_list_count"]
                ),
                f"create task lists for project {project['name']}"
            )
            self.task_lists.extend(task_lists)
        
        # Create tasks for each task list
        print("  Creating tasks...")
        self.tasks = []
        for task_list in self.task_lists:
            tasks = self._retry_with_backoff(
                lambda: self.task_generator.generate_tasks(
                    task_list["id"],
                    task_list["task_count"]
                ),
                f"create tasks for task list {task_list['name']}"
            )
            
            # Add task_list_id to each task for later reference
            for task in tasks:
                task["task_list_id"] = task_list["id"]
            
            self.tasks.extend(tasks)
            
            # Store tasks in task_list for later use
            task_list["tasks"] = tasks

    def _assign_dependencies(self) -> None:
        """Assign dependencies to tasks.
        
        Raises:
            httpx.HTTPError: If API requests fail
        """
        self.tasks = self._retry_with_backoff(
            lambda: self.dependency_assigner.assign_dependencies(self.tasks),
            "assign dependencies"
        )

    def _assign_statuses(self) -> None:
        """Assign statuses to tasks respecting dependencies.
        
        Raises:
            httpx.HTTPError: If API requests fail
        """
        self._retry_with_backoff(
            lambda: self.status_assigner.assign_statuses(self.task_lists),
            "assign statuses"
        )

    def _enrich_metadata(self) -> None:
        """Enrich tasks with tags, priorities, notes, and action plans.
        
        Raises:
            httpx.HTTPError: If API requests fail
        """
        self._retry_with_backoff(
            lambda: self.metadata_enricher.enrich_tasks(self.tasks),
            "enrich metadata"
        )

    def _validate_data(self):
        """Validate generated data against correctness properties.
        
        Returns:
            ValidationReport with results
        """
        return self._retry_with_backoff(
            self.data_validator.validate,
            "validate data"
        )

    def _retry_with_backoff(
        self,
        operation: callable,
        operation_name: str,
        max_retries: int = 3,
        initial_backoff: float = 1.0
    ):
        """Retry an operation with exponential backoff.
        
        Args:
            operation: The operation to retry
            operation_name: Name of the operation for error messages
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails after max retries
        """
        backoff = initial_backoff
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"  ⚠ Failed to {operation_name}: {e}")
                    print(f"  Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
        
        error_msg = f"Failed to {operation_name} after {max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        raise RuntimeError(error_msg)

    def _print_summary(self) -> None:
        """Print a summary of generated entities."""
        print("\n" + "=" * 70)
        print("Generation Summary")
        print("=" * 70)
        print(f"Projects created: {len(self.projects)}")
        print(f"Task lists created: {len(self.task_lists)}")
        print(f"Tasks created: {len(self.tasks)}")
        
        # Count tasks by status
        status_counts = {}
        for task in self.tasks:
            status = task.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nTask status distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        # Count tasks with dependencies
        tasks_with_deps = sum(
            1 for task in self.tasks if task.get("dependencies")
        )
        print(f"\nTasks with dependencies: {tasks_with_deps}")
        
        print("=" * 70)

    def _build_db_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment or defaults.
        
        Returns:
            PostgreSQL connection string
        """
        # Use default connection string for Docker Compose setup
        return "postgresql://taskmanager:taskmanager@localhost:5432/taskmanager"
