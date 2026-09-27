"""Canonical typed-token matching; optional packages never change decisions."""
from __future__ import annotations

import re

TOKEN = re.compile(r"<[A-Z][A-Z0-9_]*>|[^\s<>]+|[<>]")
FAMILY = {
    "<IPV4>": "<IP>", "<IPV6>": "<IP>", "<IP>": "<IP>",
    "<UUID>": "<ID>", "<HEX>": "<ID>", "<ID>": "<ID>",
}


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(TOKEN.findall(text))


def family(token: str) -> str:
    return FAMILY.get(token, token)


def score_tokens(a, b) -> int:
    """0..10000. Different literals or incompatible slot types cannot merge."""
    if len(a) != len(b):
        return 0
    if not a:
        return 10000
    total = 0
    for x, y in zip(a, b):
        if x == y:
            total += 10000
        elif family(x) == family(y):
            total += 9000
        else:
            return 0
    return total // len(a)


def merge_template(a, b) -> list[str]:
    if score_tokens(a, b) == 0:
        raise ValueError("incompatible templates")
    return [x if x == y else family(x) for x, y in zip(a, b)]


def compute_similarity(a: str, b: str) -> float:
    return score_tokens(tokenize(a), tokenize(b)) / 10000


def token_similarity(a: str, b: str) -> float:
    return compute_similarity(a, b)


def render_template(original: str, template) -> str:
    matches = list(TOKEN.finditer(original))
    if len(matches) != len(template):
        raise ValueError("template and representative have different token counts")
    result, pos = [], 0
    for match, token in zip(matches, template):
        result.extend((original[pos:match.start()], token))
        pos = match.end()
    result.append(original[pos:])
    return "".join(result)