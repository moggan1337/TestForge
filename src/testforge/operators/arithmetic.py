"""Arithmetic mutation operators."""

from typing import List, Dict, Optional, Any, Tuple
import ast
import re

from .base import MutationOperator, OperatorConfig
from ..core.mutation import Mutation, OperatorType


class ArithmeticOperators(MutationOperator):
    """
    Arithmetic Operator Replacement (AOR) mutations.
    
    Replaces arithmetic operators with alternative operators:
    - Addition with subtraction, multiplication, division
    - Subtraction with addition, multiplication, division
    - Multiplication with addition, subtraction, division
    - Division with multiplication, addition, subtraction
    """
    
    operator_type = OperatorType.AOR
    description = "Replaces arithmetic operators with alternatives"
    languages = ["python", "javascript", "java", "go", "c", "cpp"]
    
    # Replacement mappings
    REPLACEMENTS = {
        "+": ["-", "*", "/"],
        "-": ["+", "*", "/"],
        "*": ["/", "+", "-"],
        "/": ["*", "+", "-"],
        "//": ["/", "*"],
        "%": ["*", "+", "-"],
        "**": ["*", "+", "-"],
    }
    
    def __init__(self, config: Optional[OperatorConfig] = None):
        super().__init__(config)
        self._binary_ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "**",
        }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find arithmetic operators that can be mutated."""
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
            if isinstance(node, ast.BinOp):
                op_symbol = self._binary_ops.get(type(node.op))
                if op_symbol and op_symbol in self.REPLACEMENTS:
                    line_num = node.lineno - 1
                    if 0 <= line_num < len(lines):
                        line = lines[line_num]
                        
                        for replacement in self.REPLACEMENTS[op_symbol]:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.AOR,
                                source_file=file_path,
                                line_number=line_num + 1,
                                original_code=op_symbol,
                                mutated_code=replacement,
                                start_pos=node.col_offset,
                                end_pos=node.col_offset + len(op_symbol),
                                target_node="BinOp",
                            ))
            
            elif isinstance(node, ast.AugAssign):
                # Augmented assignments like +=, -=
                op_map = {
                    ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=",
                    ast.Div: "/=", ast.FloorDiv: "//=", ast.Mod: "%=", ast.Pow: "**=",
                }
                op_symbol = op_map.get(type(node.op))
                if op_symbol:
                    line_num = node.lineno - 1
                    if 0 <= line_num < len(lines):
                        line = lines[line_num]
                        # Get base operator
                        base_op = op_symbol[0]
                        if base_op in self.REPLACEMENTS:
                            for replacement in self.REPLACEMENTS[base_op]:
                                mutations.append(Mutation(
                                    id="",
                                    operator_type=OperatorType.ASR,
                                    source_file=file_path,
                                    line_number=line_num + 1,
                                    original_code=op_symbol,
                                    mutated_code=replacement + "=",
                                    start_pos=node.col_offset,
                                    end_pos=node.col_offset + len(op_symbol),
                                    target_node="AugAssign",
                                ))
        
        return mutations
    
    def _find_generic_mutations(
        self,
        source_code: str,
        file_path: str,
    ) -> List[Mutation]:
        """Find arithmetic mutations using regex."""
        mutations = []
        lines = source_code.split("\n")
        
        # Pattern for arithmetic operators (not in strings or comments)
        pattern = r'(?<![/*\w])(\+\+|--|\+=|-=|\*=|\/=|%=|\\=|\+|-|\*|\/|%)(?![/*\w])'
        
        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith(("#", "//")):
                continue
            
            matches = list(re.finditer(pattern, line))
            for match in matches:
                op = match.group(1)
                if op in self.REPLACEMENTS:
                    for replacement in self.REPLACEMENTS[op]:
                        if op in ["++", "--"]:
                            # Handle increment/decrement
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.AOR,
                                source_file=file_path,
                                line_number=i + 1,
                                original_code=op,
                                mutated_code=replacement + replacement,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                target_node="generic",
                            ))
                        else:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.AOR,
                                source_file=file_path,
                                line_number=i + 1,
                                original_code=op,
                                mutated_code=replacement,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                target_node="generic",
                            ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply the arithmetic mutation."""
        lines = source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            # Only replace if the original is there
            if mutation.original_code in line:
                # Replace first occurrence
                lines[line_idx] = line.replace(
                    mutation.original_code,
                    mutation.mutated_code,
                    1,
                )
        
        return "\n".join(lines)
    
    def get_replacement(
        self,
        original: str,
        node: ast.AST,
    ) -> str:
        """Get replacement arithmetic operator."""
        if original in self.REPLACEMENTS:
            alternatives = self.REPLACEMENTS[original]
            return alternatives[0] if alternatives else original
        return original


class BitwiseOperators(MutationOperator):
    """
    Bitwise Operator Replacement mutations.
    
    Replaces bitwise operators with alternatives.
    """
    
    operator_type = OperatorType.AOR
    description = "Replaces bitwise operators"
    languages = ["python", "c", "cpp", "java", "go"]
    
    REPLACEMENTS = {
        "&": ["|", "^", "~"],
        "|": ["&", "^", "~"],
        "^": ["&", "|", "~"],
        "~": ["&", "|", "^"],
        "<<": [">>", ">>>"],
        ">>": ["<<", "<<<"],
    }
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find bitwise operators for mutation."""
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            for op, replacements in self.REPLACEMENTS.items():
                if op in line:
                    for replacement in replacements:
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.AOR,
                            source_file=file_path,
                            line_number=i + 1,
                            original_code=op,
                            mutated_code=replacement,
                            target_node="bitwise",
                        ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply bitwise mutation."""
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
