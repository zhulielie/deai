"""Python-specific style humanizer."""

from __future__ import annotations

import ast
import io
import random
import string
import tokenize
from typing import Optional

from ..styles import StyleProfile

# Names chosen to game detect-ai's scoring:
# - Mix in HUMAN_SHORT_NAMES (trigger short_ratio > 0.2  -15pts)
# - Avoid DEAI_NAME_POOLS (avoid deai_pool +30pts)
# - CamelCase injection breaks snake_case_ratio <= 0.95 (avoid +15pts)
_SHORTS = ["a", "b", "c", "p", "q", "r", "t", "y", "cnt", "ans"]
PYTHON_NAME_POOLS = {
    "index": ["a", "b", "c", "p", "q", "r", "t", "y", "cnt", "m", "w", "spot", "loc", "offs"],
    "temp": ["cnt", "ans", "a", "b", "c", "p", "q", "r", "t", "y", "cell", "box", "slot", "pad"],
    "bool": ["on", "off", "up", "down", "hit", "miss", "pass", "fail", "set", "flip"] + _SHORTS,
    "list": [
        "group", "bunch", "pack", "batch", "pile",
        "heap", "stack", "seq", "chain", "cluster",
    ] + _SHORTS,
    "str": ["blob", "chars", "tag", "label", "key", "token", "word", "phrase", "string"] + _SHORTS,
    "result": ["gain", "fruit", "payoff", "score", "mark", "grade", "note", "tally", "sum"] + _SHORTS,
    "obj": ["unit", "piece", "part", "bit", "chunk", "block", "segment", "member", "atom"] + _SHORTS,
    "func": [
        "work", "task", "job", "act", "move",
        "step", "call", "invoke", "apply", "drive",
    ] + _SHORTS,
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
        if len(old) <= 2:
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
        # Default to temp pool (has more short names) instead of obj pool
        return PYTHON_NAME_POOLS["temp"]

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
            name = name + self.rng.choice(string.ascii_lowercase)

        if self.style.name_prefixes and self.rng.random() < 0.15:
            name = self.rng.choice(self.style.name_prefixes) + name
        if self.style.name_suffixes and self.rng.random() < 0.10:
            name = name + self.rng.choice(self.style.name_suffixes)
        # Break snake_case uniformity to dodge detect-ai's perfect_snake_case bonus
        if self.rng.random() < 0.12:
            name = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
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

    def _build_listcomp_loop(self, node: ast.ListComp) -> tuple[str, list[ast.AST]]:
        """Expand a listcomp into tmp=[] + nested for loops + appends."""
        tmp_id = self.rng.choice(PYTHON_NAME_POOLS["temp"]) + self.rng.choice(
            string.ascii_lowercase
        )
        used: set[str] = set()
        for s in self.scopes:
            used.update(s.values())
        while tmp_id in used:
            tmp_id = tmp_id + self.rng.choice(string.ascii_lowercase)

        init = ast.Assign(
            targets=[ast.Name(id=tmp_id, ctx=ast.Store())],
            value=ast.List(elts=[], ctx=ast.Load()),
        )

        def _nest(generators, elt):
            if not generators:
                return ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=tmp_id, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[elt],
                        keywords=[],
                    )
                )
            g = generators[0]
            body = _nest(generators[1:], elt)
            for if_cond in reversed(g.ifs):
                body = ast.If(test=if_cond, body=[body], orelse=[])
            return ast.For(
                target=g.target,
                iter=g.iter,
                body=[body],
                orelse=[],
            )

        loop = _nest(node.generators, node.elt)
        return tmp_id, [init, loop]

    def visit_Assign(self, node: ast.Assign):
        # Expand list comprehension in assignment to for+append
        if isinstance(node.value, ast.ListComp):
            tmp_id, pre = self._build_listcomp_loop(node.value)
            node.value = ast.Name(id=tmp_id, ctx=ast.Load())
            # visit targets after so the temp name is in scope
            for i, t in enumerate(node.targets):
                if isinstance(t, ast.Name):
                    node.targets[i] = self.visit(t)
                else:
                    self.visit(t)
            return pre + [node]

        node.value = self.visit(node.value)

        if (
            self.rng.random() < self.style.temp_variable_rate
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            tmp_id = self.rng.choice(PYTHON_NAME_POOLS["temp"]) + self.rng.choice(
                string.ascii_lowercase
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

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        for i, op in enumerate(node.ops):
            if isinstance(op, ast.Is):
                if (
                    i < len(node.comparators)
                    and isinstance(node.comparators[i], ast.Constant)
                    and node.comparators[i].value is None
                ):
                    node.ops[i] = ast.Eq()
            elif isinstance(op, ast.IsNot):
                if (
                    i < len(node.comparators)
                    and isinstance(node.comparators[i], ast.Constant)
                    and node.comparators[i].value is None
                ):
                    node.ops[i] = ast.NotEq()
        return node

    def _is_walrus_expr(self, node: ast.AST) -> bool:
        """Check if node contains a NamedExpr anywhere."""
        for child in ast.walk(node):
            if isinstance(child, ast.NamedExpr):
                return True
        return False

    def _extract_walrus(self, node: ast.AST):
        """Extract walrus assignments from an expression, return (new_expr, assignments)."""
        assignments: list[ast.Assign] = []

        class _WalrusExtractor(ast.NodeTransformer):
            def __init__(self, outer):
                self.outer = outer

            def visit_NamedExpr(self, node: ast.NamedExpr):
                new_target = self.outer.visit(node.target)
                new_value = self.outer.visit(node.value)
                assignments.append(
                    ast.Assign(targets=[new_target], value=new_value)
                )
                return ast.Name(id=new_target.id, ctx=ast.Load())

        extractor = _WalrusExtractor(self)
        new_node = extractor.visit(node)
        return new_node, assignments

    def visit_If(self, node: ast.If):
        if self._is_walrus_expr(node.test):
            node.test, walrus_assignments = self._extract_walrus(node.test)
            self.generic_visit(node)
            # Redundant compare
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
            return walrus_assignments + [node]

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

    def visit_JoinedStr(self, node: ast.JoinedStr):
        """Convert f-string to .format() call."""
        format_parts: list[str] = []
        args: list[ast.expr] = []

        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                # Escape literal braces for .format()
                s = val.value.replace("{", "{{").replace("}", "}}")
                format_parts.append(s)
            elif isinstance(val, ast.FormattedValue):
                val.value = self.visit(val.value)
                if val.format_spec and val.format_spec.values:
                    spec_parts: list[str] = []
                    for s in val.format_spec.values:
                        if isinstance(s, ast.Constant) and isinstance(s.value, str):
                            spec_parts.append(s.value)
                        elif isinstance(s, ast.FormattedValue):
                            spec_parts.append("{}")
                            s.value = self.visit(s.value)
                            args.append(s.value)
                    spec = "".join(spec_parts)
                    format_parts.append("{{:{}}}".format(spec))
                else:
                    format_parts.append("{}")
                args.append(val.value)

        format_str = "".join(format_parts)
        return ast.Call(
            func=ast.Attribute(
                value=ast.Constant(value=format_str),
                attr="format",
                ctx=ast.Load(),
            ),
            args=args,
            keywords=[],
        )

    def visit_ListComp(self, node: ast.ListComp):
        """Convert list comprehension to list() with generator expression."""
        # For expression-level listcomps that aren't in an Assign,
        # wrap in list(genexpr) to avoid AI fingerprint
        self.generic_visit(node)
        gen = ast.GeneratorExp(elt=node.elt, generators=node.generators)
        return ast.Call(
            func=ast.Name(id="list", ctx=ast.Load()),
            args=[gen],
            keywords=[],
        )

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
    # Adversarial fallback: guarantee a detect-ai human marker
    _MARKERS = [
        "todo", "fixme", "hack", "xxx", "bug", "broken", "temp", "temporary",
        "workaround", "kludge", "shit", "fuck", "damn", "crap", "wtf", "ugh",
        "later", "revisit", "dont forget", "sleep", "3am", "cursed", "pray",
        "works on my machine",
    ]
    if not any(m in comment.lower() for m in _MARKERS):
        comment = "# " + rng.choice(["TODO", "FIXME", "HACK", "damn"])
    return comment


def _add_comments(source: str, style: StyleProfile, rng) -> str:
    if not source.strip():
        return source
    lines = source.split("\n")
    result = []
    injected = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") and rng.random() < style.comment_density:
            indent = len(line) - len(line.lstrip())
            result.append(line)
            result.append(
                " " * (indent + style.indent_size) + _human_comment(style, rng)
            )
            injected += 1
            continue
        result.append(line)
    # Guarantee at least one human marker comment if none were injected
    if injected == 0 and lines:
        # Find a good line (after an import or before a def) to inject
        for i, line in enumerate(result):
            if line.strip().startswith("def "):
                indent = len(line) - len(line.lstrip())
                result.insert(i, " " * (indent + style.indent_size) + _human_comment(style, rng))
                injected += 1
                break
        if injected == 0:
            # fallback: append at end
            result.append(_human_comment(style, rng))
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
            if q == '"' and "'" not in inner and rng.random() < 0.65:
                new_tokens.append(
                    (t_type, prefix + "'" + inner + "'", start, end, line)  # type: ignore[arg-type]
                )
            elif q == "'" and '"' not in inner and rng.random() < 0.65:
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
                        if rng.random() < 0.35:
                            # Bias toward none/tight to create inconsistency vs spaced ops
                            style_choice = rng.choice(["none", "none", "both", "left"])
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


def _trailing_whitespace(source: str, style: StyleProfile, rng) -> str:
    lines = source.split("\n")
    result = []
    for line in lines:
        result.append(line)
        if line.strip() and rng.random() < 0.28:
            result[-1] = line + " " * rng.randint(1, 4)
    return "\n".join(result)


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
    new_source = _trailing_whitespace(new_source, style, rng)
    new_source = _extra_newlines(new_source, style, rng)
    return new_source
