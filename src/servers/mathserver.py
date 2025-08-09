from mcp.server.fastmcp import FastMCP
import math

mcp=FastMCP("Math")

@mcp.tool()
def add(a:int,b:int)->int:
    """_summary_
    Add to numbers
    """
    return a+b

@mcp.tool()
def multiple(a:int,b:int)-> int:
    """Multiply two numbers"""
    return a*b


# Subtract two numbers
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

# Divide two numbers
@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b

# Raise a to the power of b
@mcp.tool()
def power(a: int, b: int) -> int:
    """Raise a to the power of b"""
    return a ** b

# Advanced math tool functions
@mcp.tool()
def sqrt(x: float) -> float:
    """Square root of x (x >= 0)."""
    if x < 0:
        raise ValueError("sqrt domain error: x must be >= 0.")
    return math.sqrt(x)

@mcp.tool()
def log(x: float, base: float = math.e) -> float:
    """Logarithm of x with the given base (x > 0, base > 0, base != 1)."""
    if x <= 0:
        raise ValueError("log domain error: x must be > 0.")
    if base <= 0 or base == 1:
        raise ValueError("log domain error: base must be > 0 and != 1.")
    return math.log(x, base)

@mcp.tool()
def exp(x: float) -> float:
    """e**x."""
    return math.exp(x)

@mcp.tool()
def gcd(a: int, b: int) -> int:
    """Greatest common divisor."""
    return math.gcd(a, b)

@mcp.tool()
def lcm(a: int, b: int) -> int:
    """Least common multiple."""
    if a == 0 or b == 0:
        return 0
    try:
        return math.lcm(a, b)  # type: ignore[attr-defined]
    except AttributeError:
        return abs(a * b) // math.gcd(a, b)

@mcp.tool()
def factorial(n: int) -> int:
    """n! for non-negative integer n."""
    if n < 0:
        raise ValueError("factorial domain error: n must be >= 0.")
    return math.factorial(n)

@mcp.tool()
def nCr(n: int, r: int) -> int:
    """Combination: n choose r."""
    if n < 0 or r < 0 or r > n:
        raise ValueError("nCr domain error: require n >= 0 and 0 <= r <= n.")
    try:
        return math.comb(n, r)  # type: ignore[attr-defined]
    except AttributeError:
        return factorial(n) // (factorial(r) * factorial(n - r))

@mcp.tool()
def nPr(n: int, r: int) -> int:
    """Permutation: n P r."""
    if n < 0 or r < 0 or r > n:
        raise ValueError("nPr domain error: require n >= 0 and 0 <= r <= n.")
    try:
        return math.perm(n, r)  # type: ignore[attr-defined]
    except AttributeError:
        return factorial(n) // factorial(n - r)

@mcp.tool()
def sin(x: float) -> float:
    """Sine of x (radians)."""
    return math.sin(x)

@mcp.tool()
def cos(x: float) -> float:
    """Cosine of x (radians)."""
    return math.cos(x)

@mcp.tool()
def tan(x: float) -> float:
    """Tangent of x (radians)."""
    return math.tan(x)

@mcp.tool()
def sin_deg(deg: float) -> float:
    """Sine of an angle in degrees."""
    return math.sin(math.radians(deg))

@mcp.tool()
def cos_deg(deg: float) -> float:
    """Cosine of an angle in degrees."""
    return math.cos(math.radians(deg))

@mcp.tool()
def tan_deg(deg: float) -> float:
    """Tangent of an angle in degrees."""
    return math.tan(math.radians(deg))

@mcp.tool()
def abs_val(x: float) -> float:
    """Absolute value of x."""
    return abs(x)

@mcp.tool()
def floor(x: float) -> int:
    """Floor of x."""
    return math.floor(x)

@mcp.tool()
def ceil(x: float) -> int:
    """Ceiling of x."""
    return math.ceil(x)

@mcp.tool()
def round_num(x: float, ndigits: int = 0) -> float:
    """Round x to `ndigits` decimal places (default 0)."""
    return round(x, ndigits)

#The transport="stdio" argument tells the server to:

#Use standard input/output (stdin and stdout) to receive and respond to tool function calls.

if __name__=="__main__":
    mcp.run(transport="stdio")