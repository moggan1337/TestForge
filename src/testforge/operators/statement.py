"""Statement mutation operators."""

from typing import List, Dict, Optional, Any
import ast
import re

from .base import MutationOperator, OperatorConfig
from ..core.mutation import Mutation, OperatorType


class StatementOperators(MutationOperator):
    """
    Statement Operator Deletion (SOD) mutations.
    
    Removes or modifies statement-level constructs.
    """
    
    operator_type = OperatorType.SOD
    description = "Deletes or modifies statements"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find statements that can be deleted or modified."""
        mutations = []
        
        if language == "python":
            mutations.extend(self._find_python_statements(source_code, file_path))
        
        return mutations
    
    def _find_python_statements(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find Python statements for deletion."""
        mutations = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return mutations
        
        lines = source_code.split("\n")
        
        for node in ast.walk(tree):
            # Find return statements
            if isinstance(node, ast.Return):
                line_num = node.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num].strip()
                    if line.startswith("return"):
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.SOD,
                            source_file=file_path,
                            line_number=line_num + 1,
                            original_code=line,
                            mutated_code="pass",
                            target_node="Return",
                        ))
            
            # Find assert statements
            elif isinstance(node, ast.Assert):
                line_num = node.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num].strip()
                    if line.startswith("assert"):
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.SOD,
                            source_file=file_path,
                            line_number=line_num + 1,
                            original_code=line,
                            mutated_code="",
                            target_node="Assert",
                        ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply statement deletion mutation."""
        lines = source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            lines[line_idx] = mutation.mutated_code
        
        return "\n".join(lines)


class BreakContinueReplacement(MutationOperator):
    """
    Break and Continue statement replacements.
    
    - break becomes continue
    - continue becomes break
    """
    
    operator_type = OperatorType.SOD
    description = "Replaces break/continue statements"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    REPLACEMENTS = {
        "break": "continue",
        "continue": "break",
    }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find break/continue for mutation."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for break/continue
            for keyword, replacement in self.REPLACEMENTS.items():
                if stripped == keyword or stripped.startswith(f"{keyword};"):
                    mutations.append(Mutation(
                        id="",
                        operator_type=OperatorType.SOD,
                        source_file=file_path,
                        line_number=i + 1,
                        original_code=keyword,
                        mutated_code=replacement,
                        target_node="loop_control",
                    ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply break/continue mutation."""
        lines = source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            if mutation.original_code in line:
                lines[line_idx] = line.replace(
                    mutation.original_code,
                    mutation.mutated_code,
                    1,
                )
        
        return "\n".join(lines)


class EmptyBlockReplacement(MutationOperator):
    """
    Empty Block Replacement mutations.
    
    Removes or fills empty blocks (if, while, for bodies).
    """
    
    operator_type = OperatorType.SOD
    description = "Replaces empty blocks"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find empty blocks for mutation."""
        mutations = []
        lines = source_code.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Python: pass statements
            if language == "python":
                if line == "pass":
                    mutations.append(Mutation(
                        id="",
                        operator_type=OperatorType.SOD,
                        source_file=file_path,
                        line_number=i + 1,
                        original_code="pass",
                        mutated_code="# pass removed",
                        target_node="pass_statement",
                    ))
            
            # C-style: empty braces
            if language in ["javascript", "java", "c", "cpp", "go"]:
                if line == "{":
                    # Check if next non-empty line is }
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and lines[j].strip() == "}":
                        # Empty block found
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.SOD,
                            source_file=file_path,
                            line_number=i + 1,
                            original_code="{",
                            mutated_code="{ /* empty */ }",
                            target_node="empty_block",
                        ))
            
            i += 1
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply empty block mutation."""
        lines = source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            if mutation.original_code in line:
                lines[line_idx] = line.replace(
                    mutation.original_code,
                    mutation.mutated_code,
                    1,
                )
        
        return "\n".join(lines)
