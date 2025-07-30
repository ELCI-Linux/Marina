#!/usr/bin/env python3
"""
Autonomous Code Implementation Agent for Marina
Executes code implementation tasks with Claude integration and safety measures
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Add Marina's root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.action_engine import execute_command
from brain.code_implementer import CodeImplementer
from brain.git_logic import GitLogic
from brain.integrated_automated_testing import AutomatedTester
from llm.llm_router import route_request, route_task
from brain.module_analyzer import ModuleAnalyzer

@dataclass
class ImplementationTask:
    """Represents a code implementation task"""
    id: str
    description: str
    priority: str  # low, medium, high, critical
    target_files: List[str]
    requirements: List[str]
    validation_criteria: List[str]
    estimated_complexity: float
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ImplementationResult:
    """Result of an implementation task"""
    task_id: str
    success: bool
    files_modified: List[str]
    backup_paths: List[str]
    test_results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: float
    committed: bool
    
class AutoCodeAgent:
    """
    Autonomous Code Implementation Agent
    Executes code implementation tasks using Claude and other LLMs
    """
    
    def __init__(self, marina_root: str = "/home/adminx/Marina"):
        self.marina_root = os.path.abspath(marina_root)
        self.backup_dir = os.path.join(self.marina_root, "auto_agent_backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize components
        self.code_implementer = CodeImplementer(backup_dir=self.backup_dir)
        self.git_logic = GitLogic(repo_path=self.marina_root)
        self.tester = AutomatedTester()
        self.module_analyzer = ModuleAnalyzer(marina_root=self.marina_root)
        
        # Safety settings
        self.command_whitelist = {
            # File operations
            "ls", "cat", "head", "tail", "grep", "find", "wc", "diff",
            # Git operations  
            "git add", "git commit", "git status", "git diff", "git log",
            # Python operations
            "python3", "python", "pip", "pip3",
            # Development tools
            "pylint", "flake8", "black", "pytest",
            # System info (read-only)
            "ps", "top", "df", "free", "uname", "whoami", "pwd"
        }
        
        # Execution limits
        self.max_execution_time = 600  # 10 minutes per task
        self.max_files_per_task = 10
        self.require_validation = True
        
        # Task tracking
        self.active_tasks = {}
        self.completed_tasks = []
        
    def _validate_command_safety(self, command: str) -> Tuple[bool, str]:
        """Validate that a command is safe to execute"""
        command_parts = command.strip().split()
        if not command_parts:
            return False, "Empty command"
        
        primary_command = command_parts[0]
        
        # Check against whitelist
        for allowed in self.command_whitelist:
            if command.startswith(allowed):
                return True, "Command is whitelisted"
        
        # Explicit denials
        dangerous_commands = [
            "rm", "del", "sudo", "su", "chmod +x", "mv", "cp",
            "curl", "wget", "ssh", "scp", "rsync", 
            "shutdown", "reboot", "kill", "killall",
            "mkfs", "dd", "fdisk", "parted"  
        ]
        
        for dangerous in dangerous_commands:
            if command.startswith(dangerous):
                return False, f"Dangerous command blocked: {dangerous}"
        
        return False, f"Command not in whitelist: {primary_command}"
    
    def _execute_safe_command(self, command: str) -> Tuple[str, str, bool]:
        """Execute a command safely with validation"""
        safe, reason = self._validate_command_safety(command)
        if not safe:
            return "", f"Command blocked: {reason}", False
        
        try:
            stdout, stderr = execute_command(command)
            return stdout, stderr, True
        except Exception as e:
            return "", f"Execution failed: {e}", False
    
    def _route_to_claude(self, prompt: str) -> str:
        """Route a prompt specifically to Claude for code implementation"""
        try:
            # Try Claude first (as per user preference)
            response = route_request("code_implementation", prompt, model_preference="claude")
            
            if response and not response.startswith("[ERROR]"):
                return response
            
            # Fallback to general routing if Claude fails
            model, result = route_task(prompt, len(prompt.split()) * 1.3, run=True, force_model="claude")
            return result if result else "[ERROR] All models failed"
            
        except Exception as e:
            return f"[ERROR] LLM routing failed: {e}"
    
    def parse_implementation_steps(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into actionable implementation steps"""
        steps = []
        
        try:
            # Try to parse as JSON first
            if llm_response.strip().startswith('[') or llm_response.strip().startswith('{'):
                try:
                    parsed = json.loads(llm_response)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict):
                        return [parsed]
                except json.JSONDecodeError:
                    pass
            
            # Parse text-based response
            lines = llm_response.split('\n')
            current_step = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_step:
                        steps.append(current_step)
                        current_step = {}
                    continue
                
                # Look for step indicators
                if line.lower().startswith(('step', '1.', '2.', '3.', '4.', '5.')):
                    if current_step:
                        steps.append(current_step)
                    current_step = {'description': line, 'commands': []}
                
                # Look for commands
                elif line.startswith('```') and 'bash' in line.lower():
                    continue
                elif line.startswith('```'):
                    continue
                elif any(line.startswith(cmd) for cmd in ['python', 'pip', 'git', 'touch', 'mkdir']):
                    if 'commands' not in current_step:
                        current_step['commands'] = []
                    current_step['commands'].append(line)
                elif current_step and 'description' not in current_step:
                    current_step['description'] = line
            
            if current_step:
                steps.append(current_step)
            
            # If no structured steps found, create a single step
            if not steps:
                steps = [{
                    'description': 'Implementation task',
                    'commands': [],
                    'code': llm_response
                }]
            
            return steps
            
        except Exception as e:
            print(f"[AutoCodeAgent] Error parsing steps: {e}")
            return [{'description': 'Failed to parse implementation', 'error': str(e)}]
    
    def validate_implementation(self, task: ImplementationTask, 
                              modified_files: List[str]) -> Dict[str, Any]:
        """Validate the implementation meets requirements"""
        validation_results = {
            'passed': False,
            'tests_passed': False,
            'syntax_valid': True,
            'requirements_met': [],
            'issues': [],
            'recommendations': []
        }
        
        try:
            # 1. Syntax validation for Python files
            for file_path in modified_files:
                if file_path.endswith('.py'):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        compile(content, file_path, 'exec')
                    except SyntaxError as e:
                        validation_results['syntax_valid'] = False  
                        validation_results['issues'].append(f"Syntax error in {file_path}: {e}")
            
            # 2. Run automated tests if available
            if self.require_validation:
                try:
                    test_result = self.tester.run_comprehensive_test()
                    validation_results['tests_passed'] = test_result.get('passed', False)
                    if not validation_results['tests_passed']:
                        validation_results['issues'].append("Automated tests failed")
                except Exception as e:
                    validation_results['issues'].append(f"Test execution failed: {e}")
            
            # 3. Check requirements fulfillment
            for requirement in task.requirements:
                # Simple keyword matching for now
                requirement_met = False
                for file_path in modified_files:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                        if any(keyword in content for keyword in requirement.lower().split()):
                            requirement_met = True
                            break
                    except Exception:
                        continue
                
                if requirement_met:
                    validation_results['requirements_met'].append(requirement)
                else:
                    validation_results['issues'].append(f"Requirement not met: {requirement}")
            
            # 4. Overall validation
            validation_results['passed'] = (
                validation_results['syntax_valid'] and 
                (validation_results['tests_passed'] or not self.require_validation) and
                len(validation_results['requirements_met']) >= len(task.requirements) * 0.7  # 70% requirement threshold
            )
            
        except Exception as e:
            validation_results['issues'].append(f"Validation error: {e}")
        
        return validation_results
    
    def implement_task(self, task: ImplementationTask) -> ImplementationResult:
        """Implement a complete task using Claude for code generation"""
        print(f"[AutoCodeAgent] Starting implementation: {task.description}")
        start_time = time.time()
        
        result = ImplementationResult(
            task_id=task.id,
            success=False,
            files_modified=[],
            backup_paths=[],
            test_results=None,
            error_message=None,
            execution_time=0,
            committed=False
        )
        
        try:
            # Generate implementation prompt for Claude
            implementation_prompt = self._create_implementation_prompt(task)
            
            # Get implementation plan from Claude
            print(f"[AutoCodeAgent] Requesting implementation from Claude...")
            claude_response = self._route_to_claude(implementation_prompt)
            
            if claude_response.startswith("[ERROR]"):
                result.error_message = f"Claude request failed: {claude_response}"
                return result
            
            # Parse implementation steps
            steps = self.parse_implementation_steps(claude_response)
            print(f"[AutoCodeAgent] Parsed {len(steps)} implementation steps")
            
            # Execute each step
            for i, step in enumerate(steps):
                print(f"[AutoCodeAgent] Executing step {i+1}/{len(steps)}: {step.get('description', 'Unknown')}")
                
                success = self._execute_implementation_step(step, result)
                if not success:
                    print(f"[AutoCodeAgent] Step {i+1} failed, stopping implementation")
                    break
            
            # Validate implementation if files were modified
            if result.files_modified:
                print(f"[AutoCodeAgent] Validating implementation...")
                validation = self.validate_implementation(task, result.files_modified)
                result.test_results = validation
                
                if validation['passed']:
                    result.success = True
                    print(f"[AutoCodeAgent] Implementation validated successfully")
                    
                    # Commit changes if validation passed
                    if self.git_logic.has_uncommitted_changes():
                        commit_message = f"Auto-implementation: {task.description}"
                        if self.git_logic.commit(commit_message):
                            result.committed = True
                            print(f"[AutoCodeAgent] Changes committed to git")
                        else:
                            print(f"[AutoCodeAgent] Git commit failed")
                else:
                    result.error_message = f"Validation failed: {validation['issues']}"
                    print(f"[AutoCodeAgent] Implementation validation failed")
            else:
                result.error_message = "No files were modified"
            
        except Exception as e:
            result.error_message = f"Implementation failed: {e}"
            print(f"[AutoCodeAgent] Implementation error: {e}")
        
        finally:
            result.execution_time = time.time() - start_time
            print(f"[AutoCodeAgent] Implementation completed in {result.execution_time:.2f}s")
        
        return result
    
    def _create_implementation_prompt(self, task: ImplementationTask) -> str:
        """Create a detailed prompt for Claude to implement the task"""
        
        # Analyze current codebase context
        context_info = ""
        if task.target_files:
            context_info = "Current relevant files:\n"
            for file_path in task.target_files[:3]:  # Limit context
                full_path = os.path.join(self.marina_root, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r') as f:
                            content = f.read()[:2000]  # First 2000 chars
                        context_info += f"\n--- {file_path} ---\n{content}\n"
                    except Exception:
                        context_info += f"\n--- {file_path} --- (Could not read)\n"
        
        prompt = f"""
You are Marina's autonomous code implementation agent. Implement the following task:

TASK: {task.description}

REQUIREMENTS:
{chr(10).join(f"- {req}" for req in task.requirements)}

VALIDATION CRITERIA:
{chr(10).join(f"- {criteria}" for criteria in task.validation_criteria)}

TARGET FILES: {', '.join(task.target_files) if task.target_files else 'To be determined'}

MARINA CODEBASE CONTEXT:
{context_info}

MARINA SYSTEM INFO:
- Root directory: {self.marina_root}
- Python environment: Available with standard libraries
- Available modules: brain/, core/, llm/, perception/, etc.
- Git repository: Available for version control

IMPLEMENTATION GUIDELINES:
1. Write production-ready Python code with proper error handling
2. Include comprehensive docstrings and type hints
3. Follow Marina's existing code patterns and conventions
4. Add appropriate logging statements using Python's logging module
5. Ensure code integrates well with Marina's existing architecture
6. Include necessary imports and dependencies
7. Make incremental changes that are safe and testable

SAFETY REQUIREMENTS:
- Only modify files that are necessary for the implementation
- Do not delete or overwrite critical system files
- Include validation and rollback mechanisms where appropriate
- Test code before deployment

Please provide a step-by-step implementation plan with the actual code to be written or modified. 
Format your response as actionable steps with clear code snippets that can be directly implemented.

Respond with either:
1. A JSON array of implementation steps, OR
2. Clear numbered steps with code blocks

Each step should include:
- Description of what the step does
- Target file path (relative to Marina root)
- Complete code to add/modify
- Any shell commands needed (if safe and necessary)
"""
        
        return prompt
    
    def _execute_implementation_step(self, step: Dict[str, Any], 
                                   result: ImplementationResult) -> bool:
        """Execute a single implementation step"""
        try:
            # Execute any safe commands
            if 'commands' in step:
                for command in step['commands']:
                    stdout, stderr, success = self._execute_safe_command(command)
                    if not success:
                        result.error_message = f"Command failed: {command} - {stderr}"
                        return False
            
            # Handle code implementation
            if 'code' in step and 'file' in step:
                file_path = step['file']
                if not file_path.startswith('/'):
                    file_path = os.path.join(self.marina_root, file_path)
                
                # Create backup
                backup_path = self.code_implementer.create_backup(file_path)  
                if backup_path:
                    result.backup_paths.append(backup_path)
                
                # Implement code
                impl_result = self.code_implementer.inject_code(
                    file_path=file_path,
                    code_to_inject=step['code'],
                    insertion_point=step.get('insertion_point', 'end_of_file')
                )
                
                if impl_result['success']:
                    result.files_modified.append(file_path)
                    return True
                else:
                    result.error_message = impl_result['error']
                    return False
            
            return True
            
        except Exception as e:
            result.error_message = f"Step execution failed: {e}"
            return False
    
    def create_task_from_description(self, description: str, 
                                   priority: str = "medium") -> ImplementationTask:
        """Create an implementation task from a description using LLM analysis"""
        
        analysis_prompt = f"""
Analyze this implementation request for Marina's autonomous development:

REQUEST: {description}

Please provide a structured analysis in JSON format with:
{{
    "target_files": ["list", "of", "files", "to", "modify"],
    "requirements": ["specific", "requirements", "to", "fulfill"],
    "validation_criteria": ["how", "to", "validate", "success"],
    "estimated_complexity": 0.7,
    "metadata": {{
        "category": "enhancement|bugfix|feature|refactor",
        "estimated_time": "time in minutes",
        "risk_level": "low|medium|high"
    }}
}}

Focus on Marina's existing architecture and provide specific, actionable requirements.
"""
        
        try:
            analysis_response = self._route_to_claude(analysis_prompt)
            
            # Try to parse JSON response
            try:
                if analysis_response.strip().startswith('{'):
                    analysis = json.loads(analysis_response)
                else:
                    # Extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError):
                # Fallback analysis
                analysis = {
                    "target_files": ["brain/autonomous_enhancement.py"],
                    "requirements": [description],
                    "validation_criteria": ["Code compiles without errors", "Basic functionality works"],
                    "estimated_complexity": 0.5,
                    "metadata": {"category": "enhancement", "estimated_time": "30", "risk_level": "medium"}
                }
            
            # Generate unique task ID
            task_id = hashlib.md5(
                f"{description}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            return ImplementationTask(
                id=task_id,
                description=description,
                priority=priority,
                target_files=analysis.get("target_files", []),
                requirements=analysis.get("requirements", [description]),
                validation_criteria=analysis.get("validation_criteria", []),
                estimated_complexity=analysis.get("estimated_complexity", 0.5),
                created_at=datetime.now(),
                metadata=analysis.get("metadata", {})
            )
            
        except Exception as e:
            print(f"[AutoCodeAgent] Error creating task analysis: {e}")
            
            # Fallback task creation
            task_id = hashlib.md5(
                f"{description}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            return ImplementationTask(
                id=task_id,
                description=description,
                priority=priority,
                target_files=[],
                requirements=[description],
                validation_criteria=["Implementation completes without errors"],
                estimated_complexity=0.5,
                created_at=datetime.now(),
                metadata={"category": "unknown", "risk_level": "medium"}
            )

# Example usage and testing
if __name__ == "__main__":
    print("🤖 Marina Autonomous Code Agent - Test Mode")
    
    agent = AutoCodeAgent()
    
    # Create a test task
    test_description = "Add a simple logging enhancement to the curiosity interface"
    task = agent.create_task_from_description(test_description, priority="low")
    
    print(f"📋 Created task: {task.id}")
    print(f"📝 Description: {task.description}")
    print(f"🎯 Requirements: {task.requirements}")
    print(f"📊 Estimated complexity: {task.estimated_complexity}")
    
    # Execute the task (commented out for safety)
    # result = agent.implement_task(task)
    # print(f"✅ Result: {'Success' if result.success else 'Failed'}")
    # if result.error_message:
    #     print(f"❌ Error: {result.error_message}")
