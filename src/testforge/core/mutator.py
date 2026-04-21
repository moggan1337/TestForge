"""
Code mutator - applies mutation operators to source code.
"""

import ast
import re
import tempfile
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, field

from .mutation import Mutation, OperatorType


class MutationStrategy(Enum):
    """Strategy for selecting mutations to apply."""
    ALL = "all"  # Apply all possible mutations
    COVERAGE_GUIDED = "coverage_guided"  # Only mutations in covered code
    RANDOM = "random"  # Random subset of mutations
    PRIORITIZED = "prioritized"  # High-value mutations first
    SMART = "smart"  # Intelligent selection based on code analysis


class Mutator:
    """
    Applies mutation operators to source code.
    
    Supports multiple programming languages and provides configurable
    mutation strategies for efficient mutation testing.
    """
    
    def __init__(
        self,
        source_file: Path,
        operators: Optional[List[OperatorType]] = None,
        strategy: MutationStrategy = MutationStrategy.ALL,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        max_mutations_per_file: Optional[int] = None,
    ):
        self.source_file = Path(source_file)
        self.operators = operators or list(OperatorType)
        self.strategy = strategy
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
        self.max_mutations_per_file = max_mutations_per_file
        self._language = self._detect_language()
        self._source_code = ""
        self._ast_root: Optional[ast.AST] = None
    
    def _detect_language(self) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
        }
        return ext_map.get(self.source_file.suffix.lower(), "unknown")
    
    def load_source(self) -> str:
        """Load source code from file."""
        with open(self.source_file, "r", encoding="utf-8") as f:
            self._source_code = f.read()
        
        if self._language == "python":
            try:
                self._ast_root = ast.parse(self._source_code)
            except SyntaxError:
                self._ast_root = None
        
        return self._source_code
    
    def should_exclude(self, line: str, line_num: int) -> bool:
        """Check if line should be excluded from mutation."""
        # Check for mutation skip comments
        skip_patterns = [
            r"#\s*no-mutate",
            r"//\s*no-mutate",
            r"/\*\s*no-mutate",
            r"#\s*pragma:\s*no-mutate",
            r"//\s*pragma:\s*no-mutate",
        ]
        for pattern in skip_patterns:
            if re.search(pattern, line):
                return True
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def generate_mutations(self) -> List[Mutation]:
        """Generate all possible mutations for the source file."""
        if not self._source_code:
            self.load_source()
        
        mutations = []
        
        if self._language == "python":
            mutations.extend(self._generate_python_mutations())
        elif self._language in ("javascript", "typescript"):
            mutations.extend(self._generate_js_mutations())
        elif self._language == "java":
            mutations.extend(self._generate_java_mutations())
        else:
            # Generic line-based mutations for unsupported languages
            mutations.extend(self._generate_generic_mutations())
        
        # Apply limit if set
        if self.max_mutations_per_file and len(mutations) > self.max_mutations_per_file:
            if self.strategy == MutationStrategy.RANDOM:
                import random
                return random.sample(mutations, self.max_mutations_per_file)
            mutations = mutations[: self.max_mutations_per_file]
        
        return mutations
    
    def _generate_python_mutations(self) -> List[Mutation]:
        """Generate mutations for Python source code."""
        mutations = []
        
        if not self._ast_root:
            return self._generate_generic_mutations()
        
        lines = self._source_code.split("\n")
        
        for node in ast.walk(self._ast_root):
            # Arithmetic Operator Replacement (AOR)
            if OperatorType.AOR in self.operators:
                mutations.extend(self._mutate_arithmetic_operators(node, lines))
            
            # Logical Operator Replacement (LOR)
            if OperatorType.LOR in self.operators:
                mutations.extend(self._mutate_logical_operators(node, lines))
            
            # Relational Operator Replacement (ROR)
            if OperatorType.ROR in self.operators:
                mutations.extend(self._mutate_relational_operators(node, lines))
            
            # Assignment Operator Replacement (ASR)
            if OperatorType.ASR in self.operators:
                mutations.extend(self._mutate_assignment_operators(node, lines))
            
            # Return Value Replacement (RVR)
            if OperatorType.RVR in self.operators:
                mutations.extend(self._mutate_return_values(node, lines))
            
            # Unary Operator Deletion (UOD)
            if OperatorType.UOD in self.operators:
                mutations.extend(self._mutate_unary_operators(node, lines))
        
        return mutations
    
    def _mutate_arithmetic_operators(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for arithmetic operators."""
        mutations = []
        
        # Define arithmetic replacements
        replacements = {
            ast.Add: [ast.Sub, ast.Mult, ast.Div],
            ast.Sub: [ast.Add, ast.Mult, ast.Div],
            ast.Mult: [ast.Add, ast.Sub, ast.Div],
            ast.Div: [ast.Mult, ast.Add, ast.Sub],
            ast.FloorDiv: [ast.Div, ast.Mult],
            ast.Mod: [ast.Mult, ast.Add, ast.Sub],
            ast.Pow: [ast.Mult],
        }
        
        for child in ast.walk(node):
            if isinstance(child, tuple([*replacements.keys()])):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        op_symbols = {"+": "-", "-": "+", "*": "/", "/": "*", "//": "/", "%": "*", "**": "*"}
                        for op_type, alternatives in replacements.items():
                            if isinstance(child, op_type):
                                original = self._get_op_symbol(child, lines[line_num], child.col_offset)
                                for alt_op in alternatives:
                                    mutated = self._get_alt_symbol(alt_op, original)
                                    if mutated:
                                        mutations.append(Mutation(
                                            id="",
                                            operator_type=OperatorType.AOR,
                                            source_file=self.source_file,
                                            line_number=line_num + 1,
                                            original_code=original,
                                            mutated_code=mutated,
                                            start_pos=child.col_offset,
                                            end_pos=child.col_offset + len(original),
                                            target_node=type(child).__name__,
                                        ))
        return mutations
    
    def _mutate_logical_operators(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for logical operators."""
        mutations = []
        
        replacements = {
            ast.And: ast.Or,
            ast.Or: ast.And,
        }
        
        for child in ast.walk(node):
            if isinstance(child, tuple(replacements.keys())):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        original = "and" if isinstance(child, ast.And) else "or"
                        mutated = "or" if isinstance(child, ast.And) else "and"
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.LOR,
                            source_file=self.source_file,
                            line_number=line_num + 1,
                            original_code=original,
                            mutated_code=mutated,
                            start_pos=child.col_offset,
                            end_pos=child.col_offset + len(original),
                            target_node=type(child).__name__,
                        ))
        
        # Also handle boolean literals in comparisons
        for child in ast.walk(node):
            if isinstance(child, ast.UnaryOp) and isinstance(child.op, ast.Not):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        mutations.append(Mutation(
                            id="",
                            operator_type=OperatorType.UOD,
                            source_file=self.source_file,
                            line_number=line_num + 1,
                            original_code="not ",
                            mutated_code="",
                            start_pos=child.col_offset,
                            end_pos=child.col_offset + 4,
                            target_node="UnaryOp",
                        ))
        
        return mutations
    
    def _mutate_relational_operators(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for relational operators."""
        mutations = []
        
        replacements = {
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
        
        for child in ast.walk(node):
            if isinstance(child, tuple([*replacements.keys()])):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        op_type = type(child.op)
                        if op_type in replacements:
                            original = self._get_rel_op_symbol(child, lines[line_num])
                            for alt in replacements[op_type]:
                                mutated = self._get_rel_op_symbol_type(alt, original)
                                if mutated:
                                    mutations.append(Mutation(
                                        id="",
                                        operator_type=OperatorType.ROR,
                                        source_file=self.source_file,
                                        line_number=line_num + 1,
                                        original_code=original,
                                        mutated_code=mutated,
                                        start_pos=child.col_offset,
                                        end_pos=child.col_offset + len(original),
                                        target_node="Compare",
                                    ))
        return mutations
    
    def _mutate_assignment_operators(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for assignment operators."""
        mutations = []
        
        replacements = {
            "+=": "-=",
            "-=": "+=",
            "*=": "/=",
            "/=": "*=",
            "%=": "*=",
        }
        
        for child in ast.walk(node):
            if isinstance(child, ast.AugAssign):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        op_map = {ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=", 
                                  ast.Div: "/=", ast.FloorDiv: "/=", ast.Mod: "%=", ast.Pow: "**="}
                        op_type = type(child.op)
                        if op_type in op_map:
                            original = op_map[op_type]
                            for alt, replacement in replacements.items():
                                if original == alt:
                                    mutations.append(Mutation(
                                        id="",
                                        operator_type=OperatorType.ASR,
                                        source_file=self.source_file,
                                        line_number=line_num + 1,
                                        original_code=original,
                                        mutated_code=replacement,
                                        start_pos=child.col_offset,
                                        end_pos=child.col_offset + len(original),
                                        target_node="AugAssign",
                                    ))
        return mutations
    
    def _mutate_return_values(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for return values."""
        mutations = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        value_str = ast.unparse(child.value) if hasattr(ast, 'unparse') else ""
                        if value_str and value_str != "None":
                            # Replace with False/True swap for boolean returns
                            if value_str in ("True", "False"):
                                mutated = "False" if value_str == "True" else "True"
                                mutations.append(Mutation(
                                    id="",
                                    operator_type=OperatorType.RVR,
                                    source_file=self.source_file,
                                    line_number=line_num + 1,
                                    original_code=value_str,
                                    mutated_code=mutated,
                                    start_pos=child.col_offset,
                                    end_pos=child.col_offset + len(value_str),
                                    target_node="Return",
                                ))
        return mutations
    
    def _mutate_unary_operators(
        self, node: ast.AST, lines: List[str]
    ) -> List[Mutation]:
        """Find and create mutations for unary operators."""
        mutations = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.UnaryOp):
                line_num = child.lineno - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if not self.should_exclude(line, line_num):
                        if isinstance(child.op, ast.USub):
                            # Check if this is negation
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.UOD,
                                source_file=self.source_file,
                                line_number=line_num + 1,
                                original_code="-",
                                mutated_code="+",
                                start_pos=child.col_offset,
                                end_pos=child.col_offset + 1,
                                target_node="UnaryOp",
                            ))
        return mutations
    
    def _generate_generic_mutations(self) -> List[Mutation]:
        """Generate mutations using regex for generic language support."""
        mutations = []
        lines = self._source_code.split("\n")
        
        for line_num, line in enumerate(lines):
            if self.should_exclude(line, line_num):
                continue
            
            # Arithmetic operators
            if OperatorType.AOR in self.operators:
                for original, alternatives in [("+", ["-", "*", "/"]), 
                                                ("-", ["+", "*", "/"]),
                                                ("*", ["+", "-", "/"]),
                                                ("/", ["*", "+", "-"])]:
                    if original in line:
                        for alt in alternatives:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.AOR,
                                source_file=self.source_file,
                                line_number=line_num + 1,
                                original_code=original,
                                mutated_code=alt,
                                target_node="generic",
                            ))
            
            # Logical operators
            if OperatorType.LOR in self.operators:
                for original, alternatives in [("&&", ["||"]), ("||", ["&&"]),
                                                ("and", ["or"]), ("or", ["and"])]:
                    if original in line:
                        for alt in alternatives:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.LOR,
                                source_file=self.source_file,
                                line_number=line_num + 1,
                                original_code=original,
                                mutated_code=alt,
                                target_node="generic",
                            ))
            
            # Relational operators
            if OperatorType.ROR in self.operators:
                for original, alternatives in [("<=", [">", "!=", "<"]),
                                                (">=", ["<", "!=", ">"]),
                                                ("==", ["!=", "<", ">"]),
                                                ("!=", ["==", "<", ">"])]:
                    if original in line:
                        for alt in alternatives:
                            mutations.append(Mutation(
                                id="",
                                operator_type=OperatorType.ROR,
                                source_file=self.source_file,
                                line_number=line_num + 1,
                                original_code=original,
                                mutated_code=alt,
                                target_node="generic",
                            ))
        
        return mutations
    
    def _generate_js_mutations(self) -> List[Mutation]:
        """Generate mutations for JavaScript/TypeScript."""
        return self._generate_generic_mutations()
    
    def _generate_java_mutations(self) -> List[Mutation]:
        """Generate mutations for Java."""
        return self._generate_generic_mutations()
    
    def _get_op_symbol(self, node: ast.AST, line: str, col_offset: int) -> str:
        """Get the symbol for an operator node."""
        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
            ast.And: "and", ast.Or: "or",
        }
        op_type = type(node.op)
        return op_map.get(op_type, "")
    
    def _get_alt_symbol(self, alt_op_type: ast.AST, original: str) -> str:
        """Get alternative symbol for an operator type."""
        op_map = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
            ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
            ast.And: "and", ast.Or: "or",
        }
        return op_map.get(alt_op_type, original)
    
    def _get_rel_op_symbol(self, node: ast.Compare, line: str) -> str:
        """Get relational operator symbol from Compare node."""
        ops = {
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "is", ast.IsNot: "is not",
            ast.In: "in", ast.NotIn: "not in",
        }
        if node.ops:
            op = node.ops[0]
            return ops.get(type(op), "")
        return ""
    
    def _get_rel_op_symbol_type(self, op_type: type, original: str) -> str:
        """Get symbol for relational operator type."""
        ops = {
            ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=", ast.Is: "is", ast.IsNot: "is not",
            ast.In: "in", ast.NotIn: "not in",
        }
        return ops.get(op_type, original)
    
    def apply_mutation(self, mutation: Mutation) -> str:
        """Apply a single mutation to the source code."""
        lines = self._source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            # Replace the original code with mutated code
            mutated_line = line.replace(mutation.original_code, mutation.mutated_code, 1)
            lines[line_idx] = mutated_line
        
        return "\n".join(lines)
    
    def apply_mutations(self, mutations: List[Mutation]) -> Dict[Mutation, str]:
        """Apply multiple mutations, returning original -> mutated mapping."""
        results = {}
        for mutation in mutations:
            mutated_code = self.apply_mutation(mutation)
            results[mutation] = mutated_code
        return results
    
    def save_mutated_file(self, mutation: Mutation, output_path: Path) -> None:
        """Save a mutated version of the file."""
        mutated_code = self.apply_mutation(mutation)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(mutated_code)


class CoverageGuidedMutator(Mutator):
    """
    Coverage-guided mutation generator.
    
    Only generates mutations for code paths that are covered by tests,
    significantly reducing the number of mutations to evaluate.
    """
    
    def __init__(
        self,
        source_file: Path,
        coverage_data: Dict[str, Set[int]],
        operators: Optional[List[OperatorType]] = None,
        strategy: MutationStrategy = MutationStrategy.COVERAGE_GUIDED,
    ):
        super().__init__(source_file, operators, strategy)
        self.coverage_data = coverage_data
    
    def generate_mutations(self) -> List[Mutation]:
        """Generate only covered mutations."""
        all_mutations = super().generate_mutations()
        covered_mutations = []
        
        covered_lines = self.coverage_data.get(str(self.source_file), set())
        
        for mutation in all_mutations:
            if mutation.line_number in covered_lines:
                covered_mutations.append(mutation)
        
        return covered_mutations


class SmartMutator(Mutator):
    """
    Smart mutation generator that prioritizes high-value mutations.
    
    Applies heuristics to select mutations that are most likely to
    reveal test weaknesses.
    """
    
    def generate_mutations(self) -> List[Mutation]:
        """Generate prioritized mutations."""
        all_mutations = super().generate_mutations()
        
        # Score each mutation
        scored_mutations = []
        for mutation in all_mutations:
            score = self._score_mutation(mutation)
            scored_mutations.append((score, mutation))
        
        # Sort by score (higher is better)
        scored_mutations.sort(key=lambda x: x[0], reverse=True)
        
        # Apply limit if set
        if self.max_mutations_per_file:
            return [m for _, m in scored_mutations[: self.max_mutations_per_file]]
        
        return [m for _, m in scored_mutations]
    
    def _score_mutation(self, mutation: Mutation) -> float:
        """Score a mutation based on various heuristics."""
        score = 0.0
        
        # Operator-based scoring
        high_value_operators = {
            OperatorType.ROR: 2.0,  # Relational often catches logic errors
            OperatorType.LOR: 2.0,  # Logical errors are serious
            OperatorType.AOR: 1.0,  # Arithmetic is common
            OperatorType.RVR: 1.5,  # Return values are critical
        }
        score += high_value_operators.get(mutation.operator_type, 0.5)
        
        # Length-based scoring (longer original code = more impactful)
        if len(mutation.original_code) > 2:
            score += 0.5
        
        # Context-based scoring
        context_keywords = ["if", "while", "for", "return", "assert", "validate"]
        if any(kw in mutation.context.lower() for kw in context_keywords):
            score += 1.0
        
        return score
