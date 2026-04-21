"""Base classes for mutation operators."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import ast

from ..core.mutation import Mutation, OperatorType


@dataclass
class OperatorConfig:
    """Configuration for mutation operators."""
    enabled: bool = True
    probability: float = 1.0  # Probability of applying this operator
    max_per_file: Optional[int] = None  # Max mutations per file
    exclude_patterns: List[str] = []  # Patterns to exclude
    include_patterns: List[str] = []  # Patterns to include


class MutationOperator(ABC):
    """
    Abstract base class for mutation operators.
    
    Each operator implements specific mutation logic for a
    particular type of code transformation.
    """
    
    operator_type: OperatorType = OperatorType.AOR
    description: str = ""
    languages: List[str] = []
    
    def __init__(self, config: Optional[OperatorConfig] = None):
        self.config = config or OperatorConfig()
    
    @abstractmethod
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """
        Find all possible mutation locations in source code.
        
        Args:
            source_code: The source code to analyze
            file_path: Path to the source file
            language: Programming language
            
        Returns:
            List of Mutation objects
        """
        pass
    
    @abstractmethod
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """
        Apply a mutation to source code.
        
        Args:
            source_code: Original source code
            mutation: Mutation to apply
            
        Returns:
            Mutated source code
        """
        pass
    
    def should_mutate(
        self,
        node: ast.AST,
        context: Dict[str, Any],
    ) -> bool:
        """
        Determine if a node should be mutated.
        
        Override this to add custom filtering logic.
        """
        # Check probability
        if self.config.probability < 1.0:
            import random
            if random.random() > self.config.probability:
                return False
        
        return True
    
    def get_replacement(
        self,
        original: str,
        node: ast.AST,
    ) -> str:
        """
        Get replacement code for a mutation.
        
        Override in subclasses to implement specific replacements.
        """
        return original
    
    def validate_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> bool:
        """
        Validate that a mutation is syntactically correct.
        
        Args:
            source_code: Original source code
            mutation: Mutation to validate
            
        Returns:
            True if mutation is valid
        """
        try:
            mutated = self.apply_mutation(source_code, mutation)
            # Try to parse the mutated code
            if mutation.target_node == "python":
                ast.parse(mutated)
            return True
        except Exception:
            return False


class CompositeOperator(MutationOperator):
    """
    Combines multiple operators into one.
    
    Useful for applying multiple mutations at once or
    creating operator pipelines.
    """
    
    def __init__(self, operators: List[MutationOperator], config: Optional[OperatorConfig] = None):
        super().__init__(config)
        self.operators = operators
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find mutations from all sub-operators."""
        all_mutations = []
        for op in self.operators:
            mutations = op.find_mutations(source_code, file_path, language)
            all_mutations.extend(mutations)
        return all_mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply mutation using the appropriate sub-operator."""
        for op in self.operators:
            if op.operator_type == mutation.operator_type:
                return op.apply_mutation(source_code, mutation)
        return source_code


class SelectiveOperator(MutationOperator):
    """
    Operator that only mutates specific patterns.
    
    Allows fine-grained control over what gets mutated
    based on pattern matching.
    """
    
    def __init__(
        self,
        patterns: List[str],
        replacements: List[str],
        config: Optional[OperatorConfig] = None,
    ):
        super().__init__(config)
        self.patterns = patterns
        self.replacements = replacements
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find pattern matches for mutation."""
        import re
        mutations = []
        lines = source_code.split("\n")
        
        for i, line in enumerate(lines):
            for j, pattern in enumerate(self.patterns):
                matches = list(re.finditer(re.escape(pattern), line))
                for match in matches:
                    mutations.append(Mutation(
                        id="",
                        operator_type=self.operator_type,
                        source_file=file_path,
                        line_number=i + 1,
                        original_code=pattern,
                        mutated_code=self.replacements[j] if j < len(self.replacements) else pattern,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=line.strip(),
                    ))
        
        return mutations
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply pattern-based mutation."""
        lines = source_code.split("\n")
        line_idx = mutation.line_number - 1
        
        if 0 <= line_idx < len(lines):
            lines[line_idx] = lines[line_idx].replace(
                mutation.original_code,
                mutation.mutated_code,
                1,
            )
        
        return "\n".join(lines)


class ConditionalOperator(MutationOperator):
    """
    Operator with conditional mutation logic.
    
    Only applies mutations when certain conditions are met.
    """
    
    def __init__(
        self,
        condition_fn: callable,
        delegate: MutationOperator,
        config: Optional[OperatorConfig] = None,
    ):
        super().__init__(config)
        self.condition_fn = condition_fn
        self.delegate = delegate
    
    def find_mutations(
        self,
        source_code: str,
        file_path: str,
        language: str,
    ) -> List[Mutation]:
        """Find mutations where condition is met."""
        all_mutations = self.delegate.find_mutations(source_code, file_path, language)
        return [
            m for m in all_mutations
            if self.condition_fn(m)
        ]
    
    def apply_mutation(
        self,
        source_code: str,
        mutation: Mutation,
    ) -> str:
        """Apply mutation through delegate."""
        return self.delegate.apply_mutation(source_code, mutation)
