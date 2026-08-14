from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .repository import read_text


@dataclass
class FunctionComplexity:
    file: str
    name: str
    line: int
    end_line: int
    lines: int
    complexity: int


@dataclass
class ComplexityResult:
    files: int = 0
    functions: int = 0
    classes: int = 0
    branches: int = 0
    syntax_errors: int = 0
    long_functions: int = 0
    total_complexity: int = 0
    average_complexity: float = 0.0
    maximum_complexity: int = 0
    hotspots: list[FunctionComplexity] = field(
        default_factory=list
    )


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.classes = 0
        self.functions: list[FunctionComplexity] = []

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:
        self.classes += 1
        self.generic_visit(node)

    def _analyze_function(
        self,
        node: ast.AST,
    ) -> None:
        complexity = 1

        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Try,
                    ast.IfExp,
                    ast.Match,
                ),
            ):
                complexity += 1

            elif isinstance(
                child,
                ast.BoolOp,
            ):
                complexity += max(
                    1,
                    len(child.values) - 1,
                )

            elif isinstance(
                child,
                ast.comprehension,
            ):
                complexity += (
                    1
                    + len(child.ifs)
                )

        start = getattr(
            node,
            "lineno",
            0,
        )

        end = getattr(
            node,
            "end_lineno",
            start,
        )

        self.functions.append(
            FunctionComplexity(
                file=self.filename,
                name=getattr(
                    node,
                    "name",
                    "<anonymous>",
                ),
                line=start,
                end_line=end,
                lines=max(
                    1,
                    end - start + 1,
                ),
                complexity=complexity,
            )
        )

        self.generic_visit(node)

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        self._analyze_function(node)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self._analyze_function(node)


def analyze_python(
    files: list[Path],
) -> ComplexityResult:
    result = ComplexityResult()

    functions: list[FunctionComplexity] = []

    for path in files:
        result.files += 1

        try:
            tree = ast.parse(
                read_text(path),
                filename=str(path),
            )
        except SyntaxError:
            result.syntax_errors += 1
            continue

        analyzer = FunctionAnalyzer(
            str(path)
        )

        analyzer.visit(tree)

        result.classes += analyzer.classes

        functions.extend(
            analyzer.functions
        )

    result.functions = len(
        functions
    )

    result.total_complexity = sum(
        item.complexity
        for item in functions
    )

    result.branches = max(
        0,
        result.total_complexity
        - result.functions,
    )

    result.long_functions = sum(
        1
        for item in functions
        if item.lines >= 80
    )

    if functions:
        result.average_complexity = round(
            result.total_complexity
            / len(functions),
            2,
        )

        result.maximum_complexity = max(
            item.complexity
            for item in functions
        )

    result.hotspots = sorted(
        functions,
        key=lambda item: (
            item.complexity,
            item.lines,
        ),
        reverse=True,
    )[:20]

    return result
