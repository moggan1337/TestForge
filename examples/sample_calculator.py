"""
Sample calculator module for demonstrating TestForge mutation testing.
"""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def is_positive(n: int) -> bool:
    """Check if a number is positive."""
    return n > 0


def is_negative(n: int) -> bool:
    """Check if a number is negative."""
    return n < 0


def compare(a: int, b: int) -> int:
    """Compare two numbers."""
    if a > b:
        return 1
    elif a < b:
        return -1
    else:
        return 0


def max_of_three(a: int, b: int, c: int) -> int:
    """Return the maximum of three numbers."""
    if a >= b and a >= c:
        return a
    elif b >= a and b >= c:
        return b
    else:
        return c


def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp a value between min and max."""
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    else:
        return value


def absolute_value(n: int) -> int:
    """Return the absolute value."""
    if n < 0:
        return -n
    return n
