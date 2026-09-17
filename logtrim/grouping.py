from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Iterable

from logtrim.models import Group
from logtrim.normalize import normalize_event_text, normalize_json_text


def _group_records(
    records: Iterable[str], normalizer: Callable[[str], str]
) -> list[Group]:
    grouped: OrderedDict[str, Group] = OrderedDict()
    for record in records:
        key = normalizer(record)
        if key not in grouped:
            grouped[key] = Group(
                pattern=key,
                sample=record,
                count=1,
                first_seen=record,
                last_seen=record,
            )
            continue

        group = grouped[key]
        group.count += 1
        group.last_seen = record

    return list(grouped.values())


def group_records(records: Iterable[str]) -> list[Group]:
    """Group free-form log records by normalized pattern."""

    return _group_records(records, normalize_event_text)


def group_json_records(records: Iterable[str]) -> list[Group]:
    """Group JSON log records using the stable JSON normalizer."""

    return _group_records(records, normalize_json_text)
