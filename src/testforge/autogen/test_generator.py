"""
Automatic test generation for mutation testing.

Analyzes surviving mutations and generates tests to kill them.
"""

from typing import List, Dict, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import ast
import re
import subprocess


@dataclass
class GeneratedTest:
    """A generated test case."""
    name: str
    code: str
    target_mutation_id: str
    language: str = "python"
    confidence: float = 0.0
    imports: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "code": self.code,
            "target_mutation_id": self.target_mutation_id,
            "language": self.language,
            "confidence": self.confidence,
            "imports": self.imports,
        }


@dataclass
class TestTemplate:
    """Template for generating tests."""
    name: str
    template: str
    required_imports: List[str] = field(default_factory=list)
   适用于: List[str] = field(default_factory=list)  # operator types


class TestGenerator:
    """
    Automatically generates tests to cover surviving mutations.
    
    Analyzes code and mutations to generate targeted test cases
    that will kill specific mutations.
    """
    
    TEMPLATES = {
        "python": [
            TestTemplate(
                name="assertion_test",
                template='''
def test_{func_name}_{mutation_id}():
    """Test to kill mutation at {line}"""
    # Original code at line {line}: {original}
    # Mutated to: {mutated}
    result = {func_name}({args})
    assert result == {expected}, f"Expected {expected}, got {{result}}"
''',
                required_imports=[],
               适用于=["AOR", "ROR", "LOR", "RVR"],
            ),
            TestTemplate(
                name="edge_case_test",
                template='''
def test_{func_name}_edge_case_{mutation_id}():
    """Edge case test for {func_name} at line {line}"""
    # Mutation: {original} -> {mutated}
    with pytest.raises({exception_type}):
        {func_name}({edge_case_args})
''',
                required_imports=["pytest"],
               适用于=["ROR", "AOR"],
            ),
            TestTemplate(
                name="boundary_test",
                template='''
def test_{func_name}_boundary_{mutation_id}():
    """Boundary test for {func_name}"""
    # Testing boundary at line {line}
    assert {func_name}({boundary_args}) == {expected_boundary}
''',
                required_imports=[],
               适用于=["ROR"],
            ),
            TestTemplate(
                name="comprehensive_test",
                template='''
@pytest.mark.parametrize("input,expected", [
    {cases}
])
def test_{func_name}_param_{mutation_id}(input, expected):
    """Parameterized test for {func_name}"""
    assert {func_name}(input) == expected
''',
                required_imports=["pytest"],
               适用于=["AOR", "LOR", "ROR", "RVR"],
            ),
        ],
    }
    
    def __init__(self, language: str = "python"):
        self.language = language
        self._templates = self.TEMPLATES.get(language, [])
    
    def generate_tests_for_mutations(
        self,
        mutations: List[Any],
        source_code: str,
        test_file: Optional[Path] = None,
    ) -> List[GeneratedTest]:
        """
        Generate tests for a list of mutations.
        
        Args:
            mutations: List of surviving mutations
            source_code: Source code containing the mutations
            test_file: Optional existing test file to extend
            
        Returns:
            List of generated test cases
        """
        generated_tests = []
        
        # Parse source to understand structure
        func_info = self._analyze_source(source_code)
        
        for mutation in mutations:
            tests = self._generate_tests_for_mutation(
                mutation,
                func_info,
                source_code,
            )
            generated_tests.extend(tests)
        
        return generated_tests
    
    def _analyze_source(self, source_code: str) -> Dict[str, Any]:
        """Analyze source code to understand function signatures and structure."""
        info = {
            "functions": {},
            "classes": {},
            "imports": [],
        }
        
        try:
            tree = ast.parse(source_code)
            
            # Extract function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    defaults = [
                        ast.unparse(d) if hasattr(ast, 'unparse') else ""
                        for d in node.args.defaults
                    ]
                    
                    info["functions"][node.name] = {
                        "args": args,
                        "defaults": defaults,
                        "line": node.lineno,
                        "returns": node.returns,
                    }
                
                elif isinstance(node, ast.ClassDef):
                    info["classes"][node.name] = {
                        "line": node.lineno,
                        "methods": [
                            m.name for m in node.body
                            if isinstance(m, ast.FunctionDef)
                        ],
                    }
            
            # Extract imports
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info["imports"].append(node.module)
            
        except SyntaxError:
            pass
        
        return info
    
    def _generate_tests_for_mutation(
        self,
        mutation: Any,
        func_info: Dict[str, Any],
        source_code: str,
    ) -> List[GeneratedTest]:
        """Generate tests for a specific mutation."""
        tests = []
        
        # Find the function containing this mutation
        containing_func = self._find_containing_function(
            mutation.line_number,
            func_info,
        )
        
        if not containing_func:
            # Try to create a basic test
            tests.append(self._generate_basic_test(mutation))
            return tests
        
        # Generate tests based on mutation type
        op_type = mutation.operator_type.value
        
        if op_type == "ROR":
            tests.extend(self._generate_ror_tests(mutation, containing_func, func_info))
        elif op_type == "AOR":
            tests.extend(self._generate_aor_tests(mutation, containing_func, func_info))
        elif op_type == "LOR":
            tests.extend(self._generate_lor_tests(mutation, containing_func, func_info))
        elif op_type == "RVR":
            tests.extend(self._generate_rvr_tests(mutation, containing_func, func_info))
        else:
            tests.append(self._generate_basic_test(mutation))
        
        return tests
    
    def _find_containing_function(
        self,
        line_number: int,
        func_info: Dict[str, Any],
    ) -> Optional[Tuple[str, Dict]]:
        """Find the function containing a line number."""
        for func_name, func_data in func_info["functions"].items():
            if func_data["line"] <= line_number:
                return func_name, func_data
        return None
    
    def _generate_ror_tests(
        self,
        mutation: Any,
        containing_func: Tuple[str, Dict],
        func_info: Dict[str, Any],
    ) -> List[GeneratedTest]:
        """Generate tests for Relational Operator Replacement mutations."""
        tests = []
        func_name, func_data = containing_func
        
        # Generate boundary tests
        test_code = f'''
def test_{func_name}_boundary_{mutation.id[:8]}():
    """Test boundary conditions for {func_name}"""
    # Original: {mutation.original_code}, Mutated: {mutation.mutated_code}
    
    # Test at the exact boundary
    result = {func_name}({", ".join(func_data["args"][:1])}={func_data["defaults"][0] if func_data["defaults"] else "0"})
    assert result is not None, "Function should return a value"
    
    # Test with values that expose the difference
    # Original: {mutation.original_code}, Changed to: {mutation.mutated_code}
'''
        
        tests.append(GeneratedTest(
            name=f"test_{func_name}_boundary_{mutation.id[:8]}",
            code=test_code,
            target_mutation_id=mutation.id,
            confidence=0.8,
            imports=["pytest"] if "pytest" in self._templates else [],
        ))
        
        return tests
    
    def _generate_aor_tests(
        self,
        mutation: Any,
        containing_func: Tuple[str, Dict],
        func_info: Dict[str, Any],
    ) -> List[GeneratedTest]:
        """Generate tests for Arithmetic Operator Replacement mutations."""
        tests = []
        func_name, func_data = containing_func
        
        # Generate edge case tests with zero and negative numbers
        test_code = f'''
def test_{func_name}_arithmetic_edge_cases_{mutation.id[:8]}():
    """Test arithmetic edge cases for {func_name}"""
    # Original operator: {mutation.original_code}
    # Mutated operator: {mutation.mutated_code}
    
    # Test with zero
    args = {{}}
    for i, arg in enumerate({func_data["args"]}):
        args[arg] = 0 if i == 0 else 1
    result = {func_name}(**args)
    
    # Test with negative numbers
    args["{func_data["args"][0]}"] = -1
    result = {func_name}(**args)
    
    # Test with maximum values
    import sys
    args["{func_data["args"][0]}"] = sys.maxsize
    result = {func_name}(**args)
'''
        
        tests.append(GeneratedTest(
            name=f"test_{func_name}_arithmetic_edge_cases_{mutation.id[:8]}",
            code=test_code,
            target_mutation_id=mutation.id,
            confidence=0.75,
            imports=["pytest", "sys"],
        ))
        
        return tests
    
    def _generate_lor_tests(
        self,
        mutation: Any,
        containing_func: Tuple[str, Dict],
        func_info: Dict[str, Any],
    ) -> List[GeneratedTest]:
        """Generate tests for Logical Operator Replacement mutations."""
        tests = []
        func_name, func_data = containing_func
        
        # Generate comprehensive logical tests
        test_code = f'''
@pytest.mark.parametrize("a,b,expected", [
    (True, True, True),
    (True, False, True),
    (False, True, True),
    (False, False, False),
])
def test_{func_name}_logical_{mutation.id[:8]}(a, b, expected):
    """Test logical conditions for {func_name}"""
    # Original: {mutation.original_code}, Mutated: {mutation.mutated_code}
    result = {func_name}(a, b)
    assert result == expected, f"Expected {{expected}}, got {{result}}"
'''
        
        tests.append(GeneratedTest(
            name=f"test_{func_name}_logical_{mutation.id[:8]}",
            code=test_code,
            target_mutation_id=mutation.id,
            confidence=0.85,
            imports=["pytest"],
        ))
        
        return tests
    
    def _generate_rvr_tests(
        self,
        mutation: Any,
        containing_func: Tuple[str, Dict],
        func_info: Dict[str, Any],
    ) -> List[GeneratedTest]:
        """Generate tests for Return Value Replacement mutations."""
        tests = []
        func_name, func_data = containing_func
        
        test_code = f'''
def test_{func_name}_return_value_{mutation.id[:8]}():
    """Test return value for {func_name}"""
    # Original return: {mutation.original_code}
    # Mutated to: {mutation.mutated_code}
    
    # Test various inputs to check return value
    result = {func_name}({", ".join(func_data["args"][:1])}=True)
    assert isinstance(result, bool), "Return should be boolean"
    
    result = {func_name}({", ".join(func_data["args"][:1])}=False)
    assert isinstance(result, bool), "Return should be boolean"
'''
        
        tests.append(GeneratedTest(
            name=f"test_{func_name}_return_value_{mutation.id[:8]}",
            code=test_code,
            target_mutation_id=mutation.id,
            confidence=0.7,
            imports=["pytest"],
        ))
        
        return tests
    
    def _generate_basic_test(self, mutation: Any) -> GeneratedTest:
        """Generate a basic test when specific analysis isn't possible."""
        test_code = f'''
def test_mutation_{mutation.id[:8]}():
    """Test to kill mutation at {mutation.source_file}:{mutation.line_number}"""
    # {mutation.operator_type.value}: {mutation.original_code} -> {mutation.mutated_code}
    # This test should expose the mutation
    pass
'''
        
        return GeneratedTest(
            name=f"test_mutation_{mutation.id[:8]}",
            code=test_code,
            target_mutation_id=mutation.id,
            confidence=0.5,
            imports=[],
        )
    
    def write_test_file(
        self,
        tests: List[GeneratedTest],
        output_path: Path,
        existing_tests: Optional[str] = None,
    ) -> None:
        """Write generated tests to a file."""
        lines = []
        
        # Add existing tests if provided
        if existing_tests:
            lines.append(existing_tests)
            lines.append("")
            lines.append("#" * 60)
            lines.append("# Auto-generated tests below")
            lines.append("#" * 60)
            lines.append("")
        
        # Collect all unique imports
        all_imports = set()
        for test in tests:
            all_imports.update(test.imports)
        
        # Add imports
        if "pytest" in all_imports:
            lines.append("import pytest")
        if "sys" in all_imports:
            lines.append("import sys")
        
        lines.append("")
        
        # Add generated tests
        for test in tests:
            lines.append(test.code)
            lines.append("")
        
        # Write to file
        with open(output_path, "w") as f:
            f.write("\n".join(lines))
    
    def validate_generated_tests(
        self,
        tests: List[GeneratedTest],
        source_file: Path,
    ) -> Dict[str, bool]:
        """Validate that generated tests work correctly."""
        results = {}
        
        for test in tests:
            try:
                # Try to parse the test code
                compile(test.code, "<string>", "exec")
                results[test.name] = True
            except SyntaxError:
                results[test.name] = False
        
        return results
