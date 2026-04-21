"""Relational mutation operators."""

from typing import List, Dict, Optional, Any
import ast
import re

from .base import MutationOperator, OperatorConfig
from ..core.mutation import Mutation, OperatorType


class RelationalOperators(MutationOperator):
    """
    Relational Operator Replacement (ROR) mutations.
    
    Replaces relational operators with alternatives:
    - < becomes <=, >, >=
    - > becomes <=, <, >=
    - == becomes !=, <, >
    - != becomes ==, <, >
    """
    
    operator_type = OperatorType.ROR
    description = "Replaces relational operators with alternatives"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    # Standard replacements
    REPLACEMENTS = {
        "==": ["!=", "<", ">"],
        "!=": ["==", "<", ">"],
        "<": ["<=", ">", ">="],
        "<=": ["<", ">", ">="],
        ">": [">=", "<", "<="],
        ">=": [">", "<", "<="],
    }
    
    # For Python-specific operators
    PYTHON_REPLACEMENTS = {
        ast.Eq: [ast.NotEq, ast.Lt, ast.LtE],
        ast.NotEq: [ast.Eq, ast.Lt, ast.Gt],
        ast.Lt: [ast.LtE, ast.Gt, ast.GtE],
        ast.LtE: [ast.Lt, ast.Gt, ast.GtE],
        ast.Gt: [ast.GtE, ast.Lt, ast.LtE],
        ast.GtE: [ast.Gt, ast.Lt, ast.LtE],
        ast.Is: [ast.IsNot],
        ast.IsNot: [ast.Is],
        ast.In: [ast.NotIn],
        ast.NotIn: [ast.In],
    }
    
    def __init__(self, config: Optional[OperatorConfig] = None):
        super().__init__(config)
        self._op_to_symbol = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "is",
            ast.IsNot: "is not",
            ast.In: "in",
            ast.NotIn: "not in",
        }
        self._symbol_to_op = {v: k for k, v in self._op_to_symbol.items()}
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find relational operators that can be mutated."""
        if language == "python":
            return self._find_python_mutations(source_code, file_path)
        else:
            return self._find_generic_mutations(source_code, file_path)
    
    def _find_python_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find mutations in Python code using AST."""
        mutations = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return self._find_generic_mutations(source_code, file_path)
        
        lines = source_code.split("\n")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Get the first operator and left operand
                left = node.left
                comparators = node.comparators
                ops = node.ops
                
                for i, op in enumerate(ops):
                    op_type = type(op)
                    if op_type in self.PYTHON_REPLACEMENTS:
                        symbol = self._op_to_symbol.get(op_type, "")
                        alternatives = self.PYTHON_REPLACEMENTS[op_type]
                        
                        if symbol in self.REPLACEMENTS:
                            line_num = node.lineno - 1
                            if 0 <= line_num < len(lines):
                                line = lines[line_num]
                                
                                for alt_op in alternatives:
                                    alt_symbol = self._op_to_symbol.get(alt_op, "")
                                    if alt_symbol and alt_symbol != symbol:
                                        mutations.append(Mutation(
                                            id="",
                                            operator_type=OperatorType.ROR,
                                            source_file=file_path,
                                            line_number=line_num + 1,
                                            original_code=symbol,
                                            mutated_code=alt_symbol,
                                            target_node="Compare",
                                        ))
        
        return mutations
    
    def _find_generic_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find relational mutations using regex."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith(("#", "//")):
                continue
            
            # Find relational operators (not in strings)
            for op, replacements in self.REPLACEMENTS.items():
                if op in line:
                    # Simple check: not inside string
                    if not self._in_string(line, op):
                        for replacement in replacements:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.ROR,
                                source_file=file_path,
                                line_number=i + 1,
                                original_code=op,
                                mutated_code=replacement,
                                target_node="relational",
                            ))
        
        return mutations
    
    def _in_string(self, line: str, pattern: str) -> bool:
        """Check if pattern is inside a string literal."""
        # Simplified check - would need proper parsing for production
        return False
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply the relational mutation."""
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


class NullCheckOperators(MutationOperator):
    """
    Null Value Replacement (NVR) mutations.
    
    Replaces null checks and null values:
    - null becomes undefined/non-null
    - Check removal or modification
    """
    
    operator_type = OperatorType.NVR
    description = "Replaces null values and checks"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    REPLACEMENTS = {
        "null": ["undefined", "0", "\"\""],
        "None": ["False", "0", "\"\""],
        "undefined": ["null", "0"],
        "nil": ["0", "False"],
    }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find null values for mutation."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            for null_val, replacements in self.REPLACEMENTS.items():
                if null_val in line:
                    for replacement in replacements:
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.NVR,
                            source_file=file_path,
                            line_number=i + 1,
                            original_code=null_val,
                            mutated_code=replacement,
                            target_node="null_check",
                        ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply null mutation."""
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


class ExceptionHandlingOperators(MutationOperator):
    """
    Exception Context Replacement (ECR) mutations.
    
    Modifies exception handling:
    - Catches wrong exception types
    - Removes exception handling
    - Changes exception values
    """
    
    operator_type = OperatorType.ECR
    description = "Modifies exception handling"
    languages = ["python", "javascript", "java", "go"]
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find exception handling for mutation."""
        mutations = []
        
        if language == "python":
            mutations.extend(self._find_python_exceptions(source_code, file_path))
        
        return mutations
    
    def _find_python_exceptions(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find Python exception handling."""
        mutations = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return mutations
        
        lines = source_code.split("\n")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                line_num = node.lineno - 1
                if 0 <= line_num < len(lines) and node.type:
                    # Get exception type
                    if isinstance(node.type, ast.Name):
                        exc_name = node.type.id
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.ECR,
                            source_file=file_path,
                            line_number=line_num + 1,
                            original_code=f"except {exc_name}",
                            mutated_code="except Exception",
                            target_node="ExceptHandler",
                        ))
                        # Also try removing the handler entirely
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.SOD,
                            source_file=file_path,
                            line_number=line_num + 1,
                            original_code=f"except {exc_name}:",
                            mutated_code="",
                            target_node="ExceptHandler",
                        ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply exception mutation."""
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
