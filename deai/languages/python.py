"""Python-specific style humanizer."""

from __future__ import annotations

import ast
import io
import random
import tokenize
from typing import Optional

from ..styles import StyleProfile

PYTHON_NAME_POOLS = {
    "index": ["i", "j", "k", "idx", "ii", "jj", "kk", "n", "nn", "pos", "counter"],
    "temp": ["tmp", "temp", "buf", "t", "tt", "x", "xx", "holder", "val", "v"],
    "bool": ["ok", "flag", "done", "found", "valid", "yes", "good", "ready", "success"],
    "list": [
        "items",
        "lst",
        "arr",
        "data",
        "stuff",
        "things",
        "vals",
        "rows",
        "records",
    ],
    "str": ["s", "text", "msg", "line", "word", "name_str", "txt", "content", "raw"],
    "result": ["res", "result", "ret", "out", "output", "ans", "r", "val", "value"],
    "obj": ["obj", "o", "item", "thing", "entity", "rec", "row", "record", "el"],
    "func": [
        "run",
        "go",
        "do_it",
        "process",
        "handle",
        "exec",
        "calc",
        "fetch",
        "get_data",
    ],
}


class _StyleTransformer(ast.NodeTransformer):
    def __init__(self, style: StyleProfile, rng):
        self.style = style
        self.rng = rng
        self.scopes: list[dict[str, str]] = [{}]

    def push_scope(self, arg_names: list[str]):
        mapping = {}
        for a in arg_names:
            mapping[a] = self._pick_unique(a)
        self.scopes.append(mapping)

    def pop_scope(self):
        self.scopes.pop()

    def _guess_pool(self, old: str) -> list[str]:
        if old in ("self", "cls"):
            return [old]
        old_l = old.lower()
        if len(old) <= 2 and old in "ijknmxyz":
            return PYTHON_NAME_POOLS["index"]
        if old_l.startswith(("is_", "has_", "should_", "can_", "use_", "need_")):
            return PYTHON_NAME_POOLS["bool"]
        if any(k in old_l for k in ("list", "arr", "items", "data", "values", "keys")):
            return PYTHON_NAME_POOLS["list"]
        if any(
            k in old_l
            for k in ("name", "text", "str", "msg", "title", "content", "path")
        ):
            return PYTHON_NAME_POOLS["str"]
        if any(
            k in old_l for k in ("result", "return", "output", "response", "answer")
        ):
            return PYTHON_NAME_POOLS["result"]
        if old_l.startswith(("get_", "fetch_", "load_", "calc_", "process_")):
            return PYTHON_NAME_POOLS["func"]
        return PYTHON_NAME_POOLS["obj"]

    def _pick_unique(self, old: str) -> str:
        pool = self._guess_pool(old)
        if len(pool) == 1 and pool[0] in ("self", "cls"):
            return pool[0]

        if self.style.naming_style == "short":
            pool = [p for p in pool if len(p) <= 3] or pool
        elif self.style.naming_style == "verbose":
            pool = [p for p in pool if len(p) >= 4] or pool

        used: set[str] = set()
        for s in self.scopes:
            used.update(s.values())

        name = self.rng.choice(pool)
        while name in used:
            name = name + str(self.rng.randint(1, 9))

        if self.style.name_prefixes and self.rng.random() < 0.15:
            name = self.rng.choice(self.style.name_prefixes) + name
        if self.style.name_suffixes and self.rng.random() < 0.10:
            name = name + self.rng.choice(self.style.name_suffixes)
        return name

    def _rename(self, name: str) -> str:
        for s in reversed(self.scopes):
            if name in s:
                return s[name]
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef):
        all_args = [
            a.arg for a in node.args.args + node.args.posonlyargs + node.args.kwonlyargs
        ]
        self.push_scope(all_args)
        if node.args.vararg:
            self.scopes[-1][node.args.vararg.arg] = self._pick_unique(
                node.args.vararg.arg
            )
        if node.args.kwarg:
            self.scopes[-1][node.args.kwarg.arg] = self._pick_unique(
                node.args.kwarg.arg
            )

        for a in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            a.arg = self._rename(a.arg)
        if node.args.vararg:
            node.args.vararg.arg = self._rename(node.args.vararg.arg)
        if node.args.kwarg:
            node.args.kwarg.arg = self._rename(node.args.kwarg.arg)

        # Strip type hints if style doesn't like them
        if not self.style.use_type_hints:
            for a in (
                node.args.args + node.args.posonlyargs + node.args.kwonlyargs
            ):
                a.annotation = None
            if node.args.vararg is not None:
                node.args.vararg.annotation = None
            if node.args.kwarg is not None:
                node.args.kwarg.annotation = None
            node.returns = None

        # Docstring handling
        if not self.style.use_docstrings and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:]

        self.generic_visit(node)

        if (
            not node.name.startswith("_")
            and self.rng.random() < self.style.private_prefix_rate
        ):
            node.name = "_" + node.name

        self.pop_scope()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            new_name = self._pick_unique(node.id)
            self.scopes[-1][node.id] = new_name
            node.id = new_name
        else:
            node.id = self._rename(node.id)
        return node

    def visit_Assign(self, node: ast.Assign):
        node.value = self.visit(node.value)

        if (
            self.rng.random() < self.style.temp_variable_rate
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            tmp_id = self.rng.choice(PYTHON_NAME_POOLS["temp"]) + str(
                self.rng.randint(1, 99)
            )
            tmp_assign = ast.Assign(
                targets=[ast.Name(id=tmp_id, ctx=ast.Store())], value=node.value
            )
            node.value = ast.Name(id=tmp_id, ctx=ast.Load())
            node.targets[0] = self.visit(node.targets[0])
            return [tmp_assign, node]

        for i, t in enumerate(node.targets):
            if isinstance(t, ast.Name):
                node.targets[i] = self.visit(t)
            else:
                self.visit(t)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not self.style.use_type_hints:
            # Convert x: int = 1  ->  x = 1
            if node.value is not None and isinstance(node.target, ast.Name):
                return ast.Assign(
                    targets=[ast.Name(id=node.target.id, ctx=ast.Store())],
                    value=node.value,
                )
        return self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        if self.rng.random() < self.style.redundant_compare_rate:
            if isinstance(node.test, ast.Name):
                node.test = ast.Compare(
                    left=node.test,
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value=True)],
                )
            elif isinstance(node.test, ast.Compare):
                for i, op in enumerate(node.test.ops):
                    if isinstance(op, ast.Is):
                        node.test.ops[i] = ast.Eq()
                    elif isinstance(op, ast.IsNot):
                        node.test.ops[i] = ast.NotEq()
        return node

    def visit_Expr(self, node: ast.Expr):
        self.generic_visit(node)
        # Strip module-level docstrings if style dislikes them
        if (
            not self.style.use_docstrings
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return None
        return node


def _human_comment(style: StyleProfile, rng) -> str:
    pool = []
    if style.todo_phrases:
        pool.extend(["# " + p for p in style.todo_phrases])
    if style.hack_phrases:
        pool.extend(["# " + p for p in style.hack_phrases])
    if style.confessions:
        pool.extend(["# " + p for p in style.confessions])
    if not pool:
        return "# todo"
    comment = rng.choice(pool)
    if rng.random() < style.typo_rate:
        comment = (
            comment.lower()
            .replace("this", "dis")
            .replace("sure", "shure")
            .replace("because", "bc")
        )
    return comment


def _add_comments(source: str, style: StyleProfile, rng) -> str:
    lines = source.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") and rng.random() < style.comment_density:
            indent = len(line) - len(line.lstrip())
            result.append(line)
            result.append(
                " " * (indent + style.indent_size) + _human_comment(style, rng)
            )
            continue
        result.append(line)
    return "\n".join(result)


def _randomize_quotes(source: str, style: StyleProfile, rng) -> str:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (IndentationError, Exception):
        return source

    new_tokens = []
    for tok in tokens:
        t_type, t_string, start, end, line = tok
        if t_type == tokenize.STRING and len(t_string) >= 2:
            if t_string.startswith(('"""', "'''")):
                new_tokens.append(tok)
                continue
            prefix = ""
            body = t_string
            if len(body) > 1 and body[0] not in "\"'" and body[1] in "\"'":
                prefix = body[0]
                body = body[1:]
            q = body[0]
            inner = body[1:-1]
            if q == '"' and "'" not in inner and rng.random() < 0.4:
                new_tokens.append(
                    (t_type, prefix + "'" + inner + "'", start, end, line)  # type: ignore[arg-type]
                )
            elif q == "'" and '"' not in inner and rng.random() < 0.4:
                new_tokens.append(
                    (t_type, prefix + '"' + inner + '"', start, end, line)  # type: ignore[arg-type]
                )
            else:
                new_tokens.append(tok)
        else:
            new_tokens.append(tok)

    try:
        return tokenize.untokenize(new_tokens)
    except ValueError:
        return source


def _messy_spacing(source: str, style: StyleProfile, rng) -> str:
    operators = (
        "==",
        "!=",
        "<=",
        ">=",
        "//",
        "**",
        "->",
        ":=",
        "=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
    )
    lines = []
    for raw_line in source.split("\n"):
        line_chars = []
        in_string = None
        i = 0
        while i < len(raw_line):
            ch = raw_line[i]
            if ch in "\"'":
                if raw_line.startswith('"""', i) or raw_line.startswith("'''", i):
                    if in_string is None:
                        in_string = raw_line[i : i + 3]
                    elif in_string == raw_line[i : i + 3]:
                        in_string = None
                    line_chars.append(raw_line[i : i + 3])
                    i += 3
                    continue
                if in_string is None:
                    in_string = ch
                elif in_string == ch and (i == 0 or raw_line[i - 1] != "\\"):
                    in_string = None
                line_chars.append(ch)
                i += 1
                continue

            if in_string is None:
                matched = False
                for op in operators:
                    if raw_line.startswith(op, i):
                        if rng.random() < 0.25:
                            style_choice = rng.choice(["both", "left", "right", "none"])
                            if style_choice == "both":
                                line_chars.append(" " + op + " ")
                            elif style_choice == "left":
                                line_chars.append(" " + op)
                            elif style_choice == "right":
                                line_chars.append(op + " ")
                            else:
                                line_chars.append(op)
                        else:
                            line_chars.append(op)
                        i += len(op)
                        matched = True
                        break
                if matched:
                    continue

            line_chars.append(ch)
            i += 1
        lines.append("".join(line_chars))
    return "\n".join(lines)


def _extra_newlines(source: str, style: StyleProfile, rng) -> str:
    lines = source.split("\n")
    result = []
    for line in lines:
        result.append(line)
        if line.strip() == "" and rng.random() < 0.15:
            result.append("")
    return "\n".join(result)


def humanize_python(
    source: str, style: StyleProfile, seed: Optional[int] = None
) -> str:
    rng = random.Random(seed)
    tree = ast.parse(source)
    transformer = _StyleTransformer(style, rng)
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    new_source = ast.unparse(tree)
    new_source = _add_comments(new_source, style, rng)
    new_source = _randomize_quotes(new_source, style, rng)
    new_source = _messy_spacing(new_source, style, rng)
    new_source = _extra_newlines(new_source, style, rng)
    return new_source
