"""Logical sub-setting utilities with a tiny expression parser."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List

from core.dataset import DataSet

Token = tuple[str, Any]

OPERATORS: Dict[str, tuple[int, Callable[[Any, Any], Any]]] = {
    "^": (4, lambda a, b: a ** b),
    "*": (3, lambda a, b: a * b),
    "/": (3, lambda a, b: a / b),
    "+": (2, lambda a, b: a + b),
    "-": (2, lambda a, b: a - b),
    ">": (1, lambda a, b: a > b),
    ">=": (1, lambda a, b: a >= b),
    "<": (1, lambda a, b: a < b),
    "<=": (1, lambda a, b: a <= b),
    "==": (1, lambda a, b: a == b),
    "!=": (1, lambda a, b: a != b),
    "&": (0, lambda a, b: bool(a) and bool(b)),
    "|": (0, lambda a, b: bool(a) or bool(b)),
}

UNARY_OPERATORS: Dict[str, Callable[[Any], Any]] = {
    "neg": lambda a: -a,
    "not": lambda a: not bool(a),
}

FUNCTIONS: Dict[str, Callable[[float], float]] = {
    "log": math.log,
    "exp": math.exp,
    "sqrt": math.sqrt,
}


def tokenize(expr: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            start = i
            while i < len(expr) and (expr[i].isalnum() or expr[i] == "_"):
                i += 1
            ident = expr[start:i]
            lowered = ident.lower()
            if lowered in ("and", "or", "not"):
                mapping = {"and": "&", "or": "|", "not": "not"}
                tokens.append(("OP", mapping[ident.lower()]))
            elif lowered in FUNCTIONS:
                tokens.append(("FUNC", lowered))
            else:
                tokens.append(("VAR", ident))
            continue
        if ch.isdigit() or (ch == "." and i + 1 < len(expr) and expr[i + 1].isdigit()):
            start = i
            i += 1
            while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
                i += 1
            tokens.append(("NUM", float(expr[start:i])))
            continue
        if ch in "'\"":
            quote = ch
            i += 1
            start = i
            while i < len(expr) and expr[i] != quote:
                i += 1
            if i >= len(expr):
                raise ValueError("unterminated string literal")
            tokens.append(("STR", expr[start:i]))
            i += 1
            continue
        # multi-char operators
        if expr.startswith("<=", i) or expr.startswith(">=", i) or expr.startswith("==", i) or expr.startswith("!=", i):
            tokens.append(("OP", expr[i : i + 2]))
            i += 2
            continue
        if ch in OPERATORS or ch in "()":
            if ch == "-":
                # look behind to determine unary
                if not tokens or tokens[-1][0] == "OP" and tokens[-1][1] != ")":
                    tokens.append(("OP", "neg"))
                    i += 1
                    continue
            tokens.append(("OP", ch))
            i += 1
            continue
        raise ValueError(f"unexpected character '{ch}' in expression")
    return tokens


def to_postfix(tokens: List[Token]) -> List[Token]:
    output: List[Token] = []
    stack: List[Token] = []
    for token in tokens:
        kind, value = token
        if kind in {"NUM", "STR", "VAR"}:
            output.append(token)
        elif kind == "OP" and value == "neg":
            stack.append(token)
        elif kind == "OP" and value == "not":
            stack.append(token)
        elif kind == "FUNC":
            stack.append(token)
        elif kind == "OP" and value == "(":
            stack.append(token)
        elif kind == "OP" and value == ")":
            while stack and stack[-1][1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("mismatched parentheses")
            stack.pop()
            if stack and stack[-1][0] == "FUNC":
                output.append(stack.pop())
        else:
            prec = OPERATORS[value][0]
            while stack and stack[-1][0] == "OP" and stack[-1][1] not in {"(", "neg", "not"}:
                top = stack[-1]
                top_prec = OPERATORS[top[1]][0]
                if top_prec >= prec:
                    output.append(stack.pop())
                else:
                    break
            stack.append(token)
    while stack:
        op = stack.pop()
        if op[1] in {"(", ")"}:
            raise ValueError("mismatched parentheses")
        output.append(op)
    return output


def evaluate_postfix(dataset: DataSet, row: int, postfix: List[Token]) -> Any:
    stack: List[Any] = []
    for kind, value in postfix:
        if kind == "NUM":
            stack.append(value)
        elif kind == "STR":
            stack.append(value)
        elif kind == "VAR":
            stack.append(dataset[value][row])
        elif kind == "FUNC":
            arg = stack.pop()
            stack.append(FUNCTIONS[value](float(arg)))
        elif kind == "OP" and value in OPERATORS:
            b = stack.pop()
            a = stack.pop()
            stack.append(OPERATORS[value][1](a, b))
        elif kind == "OP" and value in {"neg", "not"}:
            a = stack.pop()
            func = UNARY_OPERATORS[value]
            stack.append(func(a))
        else:
            raise ValueError(f"unsupported token {kind}:{value}")
    if len(stack) != 1:
        raise ValueError("invalid expression")
    return stack[0]


def filter_rows(dataset: DataSet, expr: str) -> List[int]:
    tokens = tokenize(expr)
    postfix = to_postfix(tokens)
    matched: List[int] = []
    for row in range(dataset.n_obs):
        if evaluate_postfix(dataset, row, postfix):
            matched.append(row)
    return matched


def evaluate_expression(dataset: DataSet, expr: str) -> List[Any]:
    tokens = tokenize(expr)
    postfix = to_postfix(tokens)
    return [evaluate_postfix(dataset, row, postfix) for row in range(dataset.n_obs)]


__all__ = ["filter_rows", "evaluate_expression", "tokenize", "to_postfix", "evaluate_postfix"]
