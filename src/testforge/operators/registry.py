"""
Operator registry for managing mutation operators.
"""

from typing import Dict, List, Type, Optional, Callable, Any
from pathlib import Path
import ast

from ..core.mutation import OperatorType


class OperatorRegistry:
    """
    Registry for mutation operators.
    
    Provides registration, lookup, and management of mutation operators
    across different programming languages and operator types.
    """
    
    _instance: Optional["OperatorRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._operators: Dict[OperatorType, Dict[str, Type]] = {}
        self._language_operators: Dict[str, List[OperatorType]] = {}
        self._operator_factories: Dict[str, Callable] = {}
        self._initialized = True
        
        # Register default operators
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default mutation operators."""
        # Import and register default operators
        from .arithmetic import ArithmeticOperators
        from .logical import LogicalOperators
        from .relational import RelationalOperators
        from .statement import StatementOperators
        
        # Register by type
        self._operators[OperatorType.AOR] = {
            "ArithmeticOperators": ArithmeticOperators,
        }
        self._operators[OperatorType.LOR] = {
            "LogicalOperators": LogicalOperators,
        }
        self._operators[OperatorType.ROR] = {
            "RelationalOperators": RelationalOperators,
        }
        
        # Language mappings
        self._language_operators["python"] = [
            OperatorType.AOR,
            OperatorType.LOR,
            OperatorType.ROR,
            OperatorType.ASR,
            OperatorType.RVR,
            OperatorType.UOD,
            OperatorType.SOD,
        ]
        self._language_operators["javascript"] = [
            OperatorType.AOR,
            OperatorType.LOR,
            OperatorType.ROR,
            OperatorType.ASR,
            OperatorType.SOD,
        ]
        self._language_operators["java"] = [
            OperatorType.AOR,
            OperatorType.LOR,
            OperatorType.ROR,
            OperatorType.ASR,
            OperatorType.NVR,
            OperatorType.ECR,
        ]
    
    def register(
        self,
        operator_type: OperatorType,
        language: str,
        operator_class: Type,
    ) -> None:
        """Register a mutation operator."""
        if operator_type not in self._operators:
            self._operators[operator_type] = {}
        
        self._operators[operator_type][language] = operator_class
        
        if language not in self._language_operators:
            self._language_operators[language] = []
        if operator_type not in self._language_operators[language]:
            self._language_operators[language].append(operator_type)
    
    def register_factory(
        self,
        name: str,
        factory: Callable,
    ) -> None:
        """Register an operator factory function."""
        self._operator_factories[name] = factory
    
    def get_operator(
        self,
        operator_type: OperatorType,
        language: str,
    ) -> Optional[Type]:
        """Get an operator class by type and language."""
        if operator_type not in self._operators:
            return None
        return self._operators[operator_type].get(language)
    
    def get_operators_for_language(self, language: str) -> List[OperatorType]:
        """Get all operator types available for a language."""
        return self._language_operators.get(language, [])
    
    def get_all_operators(self) -> Dict[OperatorType, Dict[str, Type]]:
        """Get all registered operators."""
        return self._operators.copy()
    
    def create_operator(
        self,
        operator_type: OperatorType,
        language: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """Create an operator instance by type and language."""
        operator_class = self.get_operator(operator_type, language)
        if operator_class:
            return operator_class(config or {})
        
        # Try factory
        factory = self._operator_factories.get(operator_type.value)
        if factory:
            return factory(config)
        
        return None
    
    def list_operators(self) -> List[Dict[str, Any]]:
        """List all registered operators."""
        result = []
        for op_type, languages in self._operators.items():
            result.append({
                "type": op_type.value,
                "languages": list(languages.keys()),
            })
        return result


# Global registry instance
_registry: Optional[OperatorRegistry] = None


def get_registry() -> OperatorRegistry:
    """Get the global operator registry."""
    global _registry
    if _registry is None:
        _registry = OperatorRegistry()
    return _registry


def register_operator(
    operator_type: OperatorType,
    language: str,
) -> Callable:
    """Decorator to register a mutation operator."""
    def decorator(cls: Type) -> Type:
        registry = get_registry()
        registry.register(operator_type, language, cls)
        return cls
    return decorator


# Convenience functions
def get_available_operators(language: str) -> List[str]:
    """Get list of available operator names for a language."""
    registry = get_registry()
    return [op.value for op in registry.get_operators_for_language(language)]


def is_operator_available(operator_type: OperatorType, language: str) -> bool:
    """Check if an operator is available for a language."""
    registry = get_registry()
    return registry.get_operator(operator_type, language) is not None
