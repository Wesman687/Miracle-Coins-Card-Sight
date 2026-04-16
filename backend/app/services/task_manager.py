import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages AI tasks using the standardized template system"""
    
    def __init__(self, tasks_dir: str = "AI/tasks"):
        self.tasks_dir = Path(tasks_dir)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = Path("AI/memory/coinsync/task_memory.json")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task following the template format"""
        task_id = task_data.get("task_id", self._generate_task_id())
        
        # Validate required fields
        required_fields = ["summary", "context", "goals", "implementation_plan"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create task file
        task_file = self.tasks_dir / f"{task_id}.md"
        
        # Generate task content
        content = self._generate_task_content(task_id, task_data)
        
        # Write task file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update memory
        self._update_task_memory(task_id, task_data)
        
        logger.info(f"Created task {task_id}: {task_data['summary']}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task information"""
        task_file = self.tasks_dir / f"{task_id}.md"
        if not task_file.exists():
            return None
        
        # Parse task file (simplified - in real implementation, would parse markdown)
        return self._parse_task_file(task_file)
    
    def update_task_status(self, task_id: str, status: str, notes: str = "") -> bool:
        """Update task status"""
        task_data = self.get_task(task_id)
        if not task_data:
            return False
        
        task_data["status"] = status
        task_data["updated_at"] = datetime.now().isoformat()
        if notes:
            task_data["notes"] = notes
        
        # Update memory
        self._update_task_memory(task_id, task_data)
        
        logger.info(f"Updated task {task_id} status to {status}")
        return True
    
    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status"""
        tasks = []
        
        for task_file in self.tasks_dir.glob("*.md"):
            task_data = self._parse_task_file(task_file)
            if task_data and (not status or task_data.get("status") == status):
                tasks.append(task_data)
        
        return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next task to work on based on priority and dependencies"""
        tasks = self.list_tasks("pending")
        
        # Sort by priority (high -> medium -> low) and creation date
        priority_order = {"high": 1, "medium": 2, "low": 3}
        tasks.sort(key=lambda x: (
            priority_order.get(x.get("priority", "low"), 3),
            x.get("created_at", "")
        ))
        
        return tasks[0] if tasks else None
    
    def _generate_task_id(self) -> str:
        """Generate a unique task ID"""
        existing_tasks = list(self.tasks_dir.glob("MC-*.md"))
        next_number = len(existing_tasks) + 1
        return f"MC-{next_number:03d}"
    
    def _generate_task_content(self, task_id: str, task_data: Dict[str, Any]) -> str:
        """Generate task content in markdown format"""
        content = f"""# {task_id}: {task_data['summary']}

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | {task_id} |
| **Owner / Agent** | {task_data.get('owner', 'BuilderAgent')} |
| **Date** | {task_data.get('date', datetime.now().strftime('%Y-%m-%d'))} |
| **Branch / Repo** | {task_data.get('branch', 'miracle-coins')} |
| **Dependencies** | {task_data.get('dependencies', 'None')} |
| **Related Issues** | {task_data.get('issues', 'None')} |
| **Priority** | {task_data.get('priority', 'Medium')} |
| **Status** | {task_data.get('status', 'Pending')} |

---

## 1️⃣ 🎯 Task Summary
> {task_data['summary']}

---

## 2️⃣ 🧩 Current Context
{task_data['context']}

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
{self._format_list(task_data['goals'])}

### Acceptance Criteria
{self._format_list(task_data.get('acceptance_criteria', []))}

---

## 4️⃣ 🏗️ Implementation Plan
{self._format_list(task_data['implementation_plan'])}

---

## 5️⃣ 🧪 Testing

| Type | Description | Test Cases |
|------|-------------|------------|
{self._format_testing_table(task_data.get('testing', []))}

---

## 6️⃣ 📂 Deliverables
{self._format_list(task_data.get('deliverables', []))}

---

## 7️⃣ 🔄 Review Criteria
{self._format_list(task_data.get('review_criteria', []))}

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{json.dumps(task_data.get('memory_notes', {}), indent=2)}
```

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist
{self._format_list(task_data.get('devops_checklist', []))}

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Task Version:** v1.0  
**Date:** {datetime.now().strftime('%Y-%m-%d')}
"""
        return content
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as markdown"""
        if not items:
            return "- [ ] No items specified"
        return "\n".join(f"- [ ] {item}" for item in items)
    
    def _format_testing_table(self, testing_items: List[Dict[str, str]]) -> str:
        """Format testing items as a markdown table"""
        if not testing_items:
            return "| Unit | Basic functionality | Core features |"
        
        rows = []
        for item in testing_items:
            test_type = item.get('type', 'Unit')
            description = item.get('description', 'Basic functionality')
            test_cases = item.get('test_cases', 'Core features')
            rows.append(f"| {test_type} | {description} | {test_cases} |")
        
        return "\n".join(rows)
    
    def _parse_task_file(self, task_file: Path) -> Dict[str, Any]:
        """Parse task file (simplified implementation)"""
        # In a real implementation, this would parse the markdown file
        # For now, return basic info
        return {
            "task_id": task_file.stem,
            "file_path": str(task_file),
            "created_at": datetime.fromtimestamp(task_file.stat().st_mtime).isoformat()
        }
    
    def _update_task_memory(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Update task memory file"""
        memory = self._load_memory()
        memory[task_id] = {
            "summary": task_data.get("summary", ""),
            "status": task_data.get("status", "pending"),
            "priority": task_data.get("priority", "medium"),
            "updated_at": datetime.now().isoformat(),
            "dependencies": task_data.get("dependencies", []),
            "deliverables": task_data.get("deliverables", [])
        }
        self._save_memory(memory)
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load task memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_memory(self, memory: Dict[str, Any]) -> None:
        """Save task memory to file"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save task memory: {e}")

# Task execution helper functions
def create_auth_integration_task() -> str:
    """Create the Stream-Line authentication integration task"""
    task_manager = TaskManager()
    
    task_data = {
        "summary": "Replace mock JWT authentication with real Stream-Line authentication integration",
        "context": "The system currently uses mock JWT authentication for development purposes. Production deployment requires real Stream-Line integration.",
        "goals": [
            "Integrate with Stream-Line JWT authentication",
            "Verify user.isAdmin status from JWT token",
            "Implement proper token validation and refresh",
            "Secure all admin-only endpoints",
            "Handle authentication errors gracefully"
        ],
        "acceptance_criteria": [
            "Works with real Stream-Line JWT tokens",
            "Passes TypeScript type checks and linting",
            "All endpoints properly authenticated",
            "Admin-only access enforced",
            "Token expiration handled correctly"
        ],
        "implementation_plan": [
            "Create JWT service for token validation",
            "Update authentication middleware",
            "Add User model for Stream-Line integration",
            "Update repositories with user management",
            "Create auth context for frontend",
            "Update login page with Stream-Line flow",
            "Add auth guards for route protection"
        ],
        "testing": [
            {"type": "Unit", "description": "JWT validation", "test_cases": "Valid token, invalid token, expired token"},
            {"type": "Integration", "description": "API authentication", "test_cases": "Authenticated request, unauthenticated request"},
            {"type": "End-to-end", "description": "Login flow", "test_cases": "Successful login, failed login, admin access"}
        ],
        "deliverables": [
            "app/services/jwt_service.py",
            "app/models/user.py",
            "contexts/AuthContext.tsx",
            "components/AuthGuard.tsx",
            "types/auth.ts"
        ],
        "review_criteria": [
            "TypeScript types properly defined",
            "Error handling comprehensive",
            "Security best practices implemented",
            "Test coverage above 90%"
        ],
        "priority": "high",
        "dependencies": "MC-001",
        "memory_notes": {
            "authentication": {
                "provider": "streamline",
                "method": "jwt",
                "admin_claim": "isAdmin"
            }
        }
    }
    
    return task_manager.create_task(task_data)

def create_silver_price_api_task() -> str:
    """Create the silver price API integration task"""
    task_manager = TaskManager()
    
    task_data = {
        "summary": "Integrate with real silver price API service to replace mock spot prices",
        "context": "The system currently uses mock silver prices ($25.50) in Celery tasks. Production requires real market data for accurate pricing.",
        "goals": [
            "Integrate with reliable silver price API service",
            "Implement robust error handling for API failures",
            "Add fallback mechanisms for price data",
            "Store price history for analytics",
            "Update pricing engine with live data"
        ],
        "acceptance_criteria": [
            "Fetches real silver spot prices from API",
            "Handles API failures gracefully with fallbacks",
            "Stores price data in spot_prices table",
            "Updates pricing calculations automatically",
            "Provides price history for analysis"
        ],
        "implementation_plan": [
            "Create price API service",
            "Update Celery task with real API calls",
            "Add price validation service",
            "Enhance spot price model",
            "Add price history service",
            "Update pricing endpoints",
            "Configure API credentials"
        ],
        "testing": [
            {"type": "Unit", "description": "API service", "test_cases": "Successful fetch, API failure, rate limiting"},
            {"type": "Integration", "description": "Database operations", "test_cases": "Price storage, history tracking"},
            {"type": "End-to-end", "description": "Complete flow", "test_cases": "API fetch → storage → pricing → dashboard"}
        ],
        "deliverables": [
            "app/services/price_api_service.py",
            "app/services/price_validation.py",
            "app/services/price_history_service.py",
            "app/config/price_api.py"
        ],
        "review_criteria": [
            "API integration follows best practices",
            "Error handling comprehensive",
            "Price validation prevents invalid data",
            "Test coverage above 90%"
        ],
        "priority": "high",
        "dependencies": "MC-001",
        "memory_notes": {
            "price_api": {
                "service": "metals_api",
                "rate_limit": "100_requests_per_hour",
                "fallback_price": "last_known_price"
            }
        }
    }
    
    return task_manager.create_task(task_data)

if __name__ == "__main__":
    # Example usage
    task_manager = TaskManager()
    
    # Create tasks
    auth_task_id = create_auth_integration_task()
    price_task_id = create_silver_price_api_task()
    
    # List tasks
    tasks = task_manager.list_tasks()
    print(f"Created {len(tasks)} tasks")
    
    # Get next task
    next_task = task_manager.get_next_task()
    if next_task:
        print(f"Next task: {next_task['task_id']} - {next_task.get('summary', 'No summary')}")




