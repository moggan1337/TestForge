"""Logical mutation operators."""

from typing import List, Dict, Optional, Any
import ast
import re

from .base import MutationOperator, OperatorConfig
from ..core.mutation import Mutation, OperatorType


class LogicalOperators(MutationOperator):
    """
    Logical Operator Replacement (LOR) mutations.
    
    Replaces logical operators with alternatives:
    - AND becomes OR
    - OR becomes AND
    - NOT inverts conditions
    """
    
    operator_type = OperatorType.LOR
    description = "Replaces logical operators with alternatives"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    REPLACEMENTS = {
        "and": ["or"],
        "or": ["and"],
        "&&": ["||"],
        "||": ["&&"],
    }
    
    NOT_REPLACEMENTS = {
        "not ": [""],
        "!": [""],
        "!!": [""],
    }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find logical operators that can be mutated."""
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
            # Boolean operations (and/or)
            if isinstance(node, ast.BoolOp):
                op_name = "and" if isinstance(node.op, ast.And) else "or"
                for value in node.values:
                    if isinstance(value, ast.BoolOp):
                        continue
                    # Find the position in source
                    line_num = value.lineno - 1
                    if 0 <= line_num < len(lines):
                        for replacement in self.REPLACEMENTS.get(op_name, []):
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.LOR,
                                source_file=file_path,
                                line_number=line_num + 1,
                                original_code=f" {op_name} ",
                                mutated_code=f" {replacement} ",
                                target_node="BoolOp",
                            ))
            
            # Unary not
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                line_num = node.lineno - 1
                if 0 <= line_num < len(lines):
                    mutations.append(Mutation(
                        id="",
                        operator_type=OperatorType.UOD,
                        source_file=file_path,
                        line_number=line_num + 1,
                        original_code="not ",
                        mutated_code="",
                        target_node="UnaryOp",
                    ))
        
        return mutations
    
    def _find_generic_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find logical mutations using regex."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith(("#", "//")):
                continue
            
            # Find && and ||
            for op, replacements in [("&&", ["||"]), ("||", ["&&"])]:
                if op in line:
                    for replacement in replacements:
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.LOR,
                            source_file=file_path,
                            line_number=i + 1,
                            original_code=op,
                            mutated_code=replacement,
                            target_node="logical",
                        ))
            
            # Find ! (not)
            if "!" in line:
                # Be careful with !=
                not_pattern = r'!\s*([a-zA-Z_])'
                matches = list(re.finditer(not_pattern, line))
                for match in matches:
                    mutations.append(Mutation(
                        id="",
                        operator_type=OperatorType.UOD,
                        source_file=file_path,
                        line_number=i + 1,
                        original_code=match.group(0),
                        mutated_code="",
                        start_pos=match.start(),
                        end_pos=match.end(),
                        target_node="logical",
                    ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply the logical mutation."""
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


class ConditionalReplacementOperators(MutationOperator):
    """
    Conditional Replacement (CRP) mutations.
    
    Replaces conditional expressions with alternatives:
    - True becomes False
    - False becomes True
    - Condition negations
    """
    
    operator_type = OperatorType.CRP
    description = "Replaces conditional expressions"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    REPLACEMENTS = {
        "True": "False",
        "False": "True",
        "true": "false",
        "false": "true",
        "if": "if",  # For condition inversion
    }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find conditional values that can be mutated."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith(("#", "//")):
                continue
            
            # Find boolean literals
            for original, replacement in [("True", "False"), ("False", "True"),
                                          ("true", "false"), ("false", "true")]:
                if original in line:
                    mutations.append(Mutation(
                        id="",
                        operator_type=OperatorType.CRP,
                        source_file=file_path,
                        line_number=i + 1,
                        original_code=original,
                        mutated_code=replacement,
                        target_node="boolean",
                    ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply conditional mutation."""
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


class SwitchCaseReplacement(MutationOperator):
    """
    Switch/Case Replacement mutations.
    
    Replaces case values in switch statements.
    """
    
    operator_type = OperatorType.CRP
    description = "Replaces switch case values"
    languages = ["javascript", "java", "c", "cpp", "go"]
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find case values for mutation."""
        mutations = []
        lines = source_code.split("\n")
        
        # Pattern to match case statements
        case_pattern = r'case\s+(\w+)\s*:'
        
        for i, line in enumerate(lines):
            matches = list(re.finditer(case_pattern, line))
            for match in reversed(list(matches)):
                case_value = match.group(1)
                mutations.append(Mutation(
                    id="",
                    operator_type=OperatorType.CRP,
                    source_file=file_path,
                    line_number=i + 1,
                    original_code=case_value,
                    mutated_code="DEFAULT_CASE",
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    target_node="switch_case",
                ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply switch case mutation."""
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
