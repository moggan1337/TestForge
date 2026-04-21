"""
Time-travel debugging for mutation testing.

Provides detailed debugging information for surviving mutations,
allowing developers to understand why mutations weren't caught.
"""

from typing import List, Dict, Optional, Any, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json
import subprocess
import ast
import re

from ..core.mutation import Mutation, MutationResult, MutationStatus


@dataclass
class DebugSnapshot:
    """A snapshot of program state at a specific point."""
    mutation: Mutation
    timestamp: str
    variables: Dict[str, Any] = field(default_factory=dict)
    call_stack: List[str] = field(default_factory=list)
    coverage_info: Set[int] = field(default_factory=set)
    test_output: str = ""
    stack_trace: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mutation": self.mutation.to_dict(),
            "timestamp": self.timestamp,
            "variables": self.variables,
            "call_stack": self.call_stack,
            "coverage_info": sorted(list(self.coverage_info)),
            "test_output": self.test_output,
            "stack_trace": self.stack_trace,
        }


@dataclass
class DebugSession:
    """A debugging session for a specific mutation."""
    mutation: Mutation
    snapshots: List[DebugSnapshot] = field(default_factory=list)
    breakpoints: List[Dict[str, Any]] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    status: str = "active"
    
    def add_snapshot(self, snapshot: DebugSnapshot) -> None:
        """Add a debug snapshot."""
        self.snapshots.append(snapshot)
    
    def add_breakpoint(self, file: str, line: int, condition: Optional[str] = None) -> None:
        """Add a breakpoint."""
        self.breakpoints.append({
            "file": file,
            "line": line,
            "condition": condition,
        })
    
    def add_annotation(self, annotation: str) -> None:
        """Add a debug annotation."""
        self.annotations.append(annotation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mutation": self.mutation.to_dict(),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "breakpoints": self.breakpoints,
            "annotations": self.annotations,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
        }


class TimeTravelDebugger:
    """
    Time-travel debugging for surviving mutations.
    
    Provides capabilities to:
    - Trace execution path for mutations
    - Record variable states
    - Step through mutation execution
    - Generate detailed debug reports
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self._sessions: Dict[str, DebugSession] = {}
        self._trace_enabled = False
    
    def create_debug_session(
        self,
        mutation: Mutation,
        result: MutationResult,
    ) -> DebugSession:
        """
        Create a new debug session for a mutation.
        
        Args:
            mutation: The mutation to debug
            result: The result of testing this mutation
            
        Returns:
            DebugSession for this mutation
        """
        session = DebugSession(
            mutation=mutation,
            start_time=datetime.now().isoformat(),
        )
        
        self._sessions[mutation.id] = session
        return session
    
    def trace_execution(
        self,
        mutation: Mutation,
        test_files: List[Path],
    ) -> DebugSnapshot:
        """
        Trace execution of tests against a mutation.
        
        Records detailed execution information including
        variable states and coverage.
        """
        # Enable Python tracing
        snapshot = DebugSnapshot(
            mutation=mutation,
            timestamp=datetime.now().isoformat(),
        )
        
        # Run with tracing enabled
        cmd = [
            "python", "-m", "pytest",
            "-v", "-s", "--tb=long",
            "-k", mutation.source_file.name,
        ]
        cmd.extend([str(f) for f in test_files])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )
            
            snapshot.test_output = result.stdout + "\n" + result.stderr
            snapshot.stack_trace = self._extract_stack_trace(result.stderr)
            
        except subprocess.TimeoutExpired:
            snapshot.test_output = "Execution timed out"
        except Exception as e:
            snapshot.test_output = f"Error: {str(e)}"
        
        return snapshot
    
    def _extract_stack_trace(self, stderr: str) -> str:
        """Extract relevant stack trace from output."""
        # Look for Python traceback
        traceback_pattern = re.compile(
            r'(Traceback \(most recent call last\):.*?(?:\n\s+\w+.*)+)',
            re.MULTILINE | re.DOTALL
        )
        
        matches = traceback_pattern.findall(stderr)
        if matches:
            return matches[-1]  # Return last traceback
        
        return ""
    
    def analyze_survivor(
        self,
        mutation: Mutation,
        result: MutationResult,
    ) -> Dict[str, Any]:
        """
        Analyze why a mutation survived.
        
        Performs deep analysis to understand why the mutation
        wasn't killed by any test.
        """
        analysis = {
            "mutation": mutation.to_dict(),
            "result": result.to_dict(),
            "survival_reasons": [],
            "suggestions": [],
            "code_context": {},
        }
        
        # Check 1: Was the mutated code even reached?
        analysis["survival_reasons"].append(
            self._check_coverage_reached(mutation)
        )
        
        # Check 2: What was the actual value?
        analysis["survival_reasons"].append(
            self._check_value_difference(mutation)
        )
        
        # Check 3: Were there any failing assertions?
        analysis["survival_reasons"].append(
            self._check_assertion_presence(mutation, result)
        )
        
        # Generate suggestions
        analysis["suggestions"] = self._generate_suggestions(
            mutation,
            analysis["survival_reasons"]
        )
        
        # Get code context
        analysis["code_context"] = self._get_code_context(mutation)
        
        return analysis
    
    def _check_coverage_reached(self, mutation: Mutation) -> Dict[str, Any]:
        """Check if the mutated code was actually reached during testing."""
        # Try to run coverage analysis
        cmd = [
            "python", "-m", "pytest",
            "--cov", str(mutation.source_file.parent),
            "--cov-report=json",
            "-v",
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )
            
            # Parse coverage report
            try:
                with open("coverage.json") as f:
                    coverage_data = json.load(f)
                    file_coverage = coverage_data.get("files", {}).get(
                        str(mutation.source_file), {}
                    )
                    
                    executed_lines = file_coverage.get("executed_lines", [])
                    if mutation.line_number in executed_lines:
                        return {
                            "reason": "Code was reached",
                            "reached": True,
                            "detail": f"Line {mutation.line_number} was executed",
                        }
                    else:
                        return {
                            "reason": "Code was NOT reached",
                            "reached": False,
                            "detail": f"Line {mutation.line_number} was never executed",
                        }
            except:
                pass
                
        except:
            pass
        
        return {
            "reason": "Could not determine coverage",
            "reached": None,
            "detail": "Coverage analysis failed",
        }
    
    def _check_value_difference(self, mutation: Mutation) -> Dict[str, Any]:
        """Check if the mutation actually changes observable behavior."""
        # Analyze the mutation type
        op_type = mutation.operator_type.value
        
        if op_type in ["AOR", "LOR", "ROR"]:
            # These should change values - analyze the context
            return {
                "reason": "Value changed",
                "value_changed": True,
                "detail": f"Operator type {op_type} should change behavior",
            }
        elif op_type in ["SOD", "CRP"]:
            # These remove statements - might not be observable
            return {
                "reason": "Statement removed/changed",
                "value_changed": True,
                "detail": "Removing/changing statements may not affect output",
            }
        
        return {
            "reason": "Unknown mutation type",
            "value_changed": None,
            "detail": f"Mutation type {op_type} analysis not implemented",
        }
    
    def _check_assertion_presence(
        self,
        mutation: Mutation,
        result: MutationResult,
    ) -> Dict[str, Any]:
        """Check if there are proper assertions for this code path."""
        # Analyze test files
        test_files = list(self.project_root.glob("**/test*.py"))
        
        found_assertions = []
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    # Look for assertions related to this mutation
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assert):
                            found_assertions.append({
                                "file": str(test_file),
                                "line": node.lineno,
                            })
            except:
                continue
        
        return {
            "reason": "Assertion coverage",
            "has_assertions": len(found_assertions) > 0,
            "assertions_found": found_assertions,
        }
    
    def _generate_suggestions(
        self,
        mutation: Mutation,
        reasons: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate suggestions for fixing weak test coverage."""
        suggestions = []
        
        # Analyze reasons
        for reason in reasons:
            if reason.get("reached") == False:
                suggestions.append(
                    f"⚠️ Line {mutation.line_number} was not executed. "
                    f"Add tests that exercise this code path."
                )
            
            if reason.get("value_changed") == False:
                suggestions.append(
                    f"⚠️ Mutation may not change observable behavior. "
                    f"Check if the function output is actually tested."
                )
            
            if reason.get("has_assertions") == False:
                suggestions.append(
                    f"⚠️ No assertions found for this code. "
                    f"Add specific assertions to catch this mutation."
                )
        
        # Specific suggestions based on operator type
        op_type = mutation.operator_type.value
        
        if op_type == "AOR":
            suggestions.append(
                "💡 Consider testing edge cases like zero, negative numbers, "
                "and overflow scenarios."
            )
        elif op_type == "ROR":
            suggestions.append(
                "💡 Add boundary tests that specifically check comparison operators."
            )
        elif op_type == "LOR":
            suggestions.append(
                "💡 Test both branches of logical expressions with various combinations."
            )
        
        return suggestions
    
    def _get_code_context(self, mutation: Mutation) -> Dict[str, Any]:
        """Get surrounding code context for the mutation."""
        try:
            with open(mutation.source_file) as f:
                lines = f.readlines()
            
            context = {
                "before": [],
                "current": "",
                "after": [],
                "function": "",
            }
            
            # Get lines around mutation
            start = max(0, mutation.line_number - 3)
            end = min(len(lines), mutation.line_number + 2)
            
            context["before"] = [
                (i + 1, lines[i].rstrip())
                for i in range(start, mutation.line_number - 1)
            ]
            
            if mutation.line_number <= len(lines):
                context["current"] = lines[mutation.line_number - 1].rstrip()
            
            context["after"] = [
                (i + 1, lines[i].rstrip())
                for i in range(mutation.line_number, end)
            ]
            
            # Try to find enclosing function
            tree = ast.parse("".join(lines))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.lineno <= mutation.line_number <= node.end_lineno:
                        context["function"] = node.name
                        break
            
            return context
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_debug_report(
        self,
        session: DebugSession,
        output_path: Optional[Path] = None,
    ) -> str:
        """Generate a detailed debug report for a mutation session."""
        analysis = self.analyze_survivor(
            session.mutation,
            MutationResult(
                mutation=session.mutation,
                status=MutationStatus.SURVIVED,
            )
        )
        
        lines = [
            "# Time-Travel Debug Report",
            "",
            f"**Mutation ID:** {session.mutation.id}",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "## Mutation Details",
            "",
            f"- **Type:** {session.mutation.operator_type.value}",
            f"- **File:** {session.mutation.source_file}",
            f"- **Line:** {session.mutation.line_number}",
            f"- **Original:** `{session.mutation.original_code}`",
            f"- **Mutated:** `{session.mutation.mutated_code}`",
            "",
            "## Code Context",
            "",
            "```python",
        ]
        
        context = analysis.get("code_context", {})
        for line_num, line in context.get("before", []):
            lines.append(f"  {line_num}: {line}")
        
        if context.get("current"):
            lines.append(f"> {mutation.line_number}: {context['current']}")
        
        for line_num, line in context.get("after", []):
            lines.append(f"  {line_num}: {line}")
        
        lines.extend([
            "```",
            "",
            "## Analysis",
            "",
        ])
        
        for reason in analysis.get("survival_reasons", []):
            lines.append(f"- **{reason.get('reason', 'Unknown')}**: {reason.get('detail', '')}")
        
        if analysis.get("suggestions"):
            lines.extend([
                "",
                "## Suggestions",
                "",
            ])
            for suggestion in analysis["suggestions"]:
                lines.append(f"- {suggestion}")
        
        if session.snapshots:
            lines.extend([
                "",
                "## Execution Traces",
                "",
            ])
            for i, snapshot in enumerate(session.snapshots, 1):
                lines.append(f"### Snapshot {i} ({snapshot.timestamp})")
                if snapshot.stack_trace:
                    lines.append("```")
                    lines.append(snapshot.stack_trace)
                    lines.append("```")
        
        if session.annotations:
            lines.extend([
                "",
                "## Developer Notes",
                "",
            ])
            for annotation in session.annotations:
                lines.append(f"- {annotation}")
        
        report = "\n".join(lines)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(report)
        
        return report
    
    def export_debug_data(
        self,
        output_path: Path,
    ) -> None:
        """Export all debug data to a file."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "sessions": {
                mutation_id: session.to_dict()
                for mutation_id, session in self._sessions.items()
            },
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def import_debug_data(
        self,
        input_path: Path,
    ) -> None:
        """Import debug data from a file."""
        with open(input_path) as f:
            data = json.load(f)
        
        for mutation_id, session_data in data.get("sessions", {}).items():
            mutation = Mutation.from_dict(session_data["mutation"])
            session = DebugSession(
                mutation=mutation,
                start_time=session_data.get("start_time", ""),
                end_time=session_data.get("end_time", ""),
                status=session_data.get("status", "complete"),
            )
            session.breakpoints = session_data.get("breakpoints", [])
            session.annotations = session_data.get("annotations", [])
            
            for snapshot_data in session_data.get("snapshots", []):
                snapshot = DebugSnapshot(
                    mutation=Mutation.from_dict(snapshot_data["mutation"]),
                    timestamp=snapshot_data["timestamp"],
                    variables=snapshot_data.get("variables", {}),
                    call_stack=snapshot_data.get("call_stack", []),
                    coverage_info=set(snapshot_data.get("coverage_info", [])),
                    test_output=snapshot_data.get("test_output", ""),
                    stack_trace=snapshot_data.get("stack_trace", ""),
                )
                session.add_snapshot(snapshot)
            
            self._sessions[mutation_id] = session
