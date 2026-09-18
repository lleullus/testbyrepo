"""Disk-backed exact aggregation and bounded, leader-constrained clustering."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import tempfile
import time
from collections import Counter, OrderedDict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import __version__
from .io_utils import assemble
from .models import Cluster, Config, LogPattern, ResourceLimit
from .patterns import Normalizer
from .similarity import family, merge_template, render_template, score_tokens


class DrainIndex:
    """Fixed-depth typed paths, relaxed prefixes and token-count fallback.

    This is Drain-inspired, not an implementation of the Drain paper.
    Each indexed lookup reads at most its quota; no all-pairs scan occurs.
    """
    def __init__(self, db, config):
        self.db, self.config = db, config

    def keys(self, event):
        base = [event.parser, event.anchors, len(event.tokens)]
        route = [family(t) for t in event.tokens[:self.config.depth]]
        result = []
        for suffix in (route, route[:1], []):
            key = hashlib.sha256(json.dumps(base + [suffix], ensure_ascii=True).encode()).digest()
            if key not in result:
                result.append(key)
        return result

    def add(self, event, cid):
        self.db.executemany("INSERT OR IGNORE INTO nodes VALUES (?,?)",
                            ((key, cid) for key in self.keys(event)))

    def query(self, event):
        keys, found = self.keys(event), set()
        budget = self.config.max_candidates
        for i, key in enumerate(keys):
            quota = (budget + len(keys) - i - 1) // (len(keys) - i)
            rows = self.db.execute("SELECT cid FROM nodes WHERE key=? ORDER BY cid LIMIT ?",
                                   (key, quota))
            for (cid,) in rows:
                found.add(cid)
            budget -= quota
        return sorted(found)


class Analyzer:
    def __init__(self, config: Config | None = None, rules: list[dict] | None = None,
                 work_dir: str | None = None):
        self.config = config or Config()
        self.stats = Counter()
        self.normalizer = Normalizer(self.config, rules, self.stats)
        self.cache = OrderedDict()
        self._tmp = tempfile.TemporaryDirectory(prefix="logtrim-", dir=work_dir)
        self.db = None
        try:
            self.db = sqlite3.connect(str(Path(self._tmp.name) / "state.sqlite"))
            self.db.execute(f"PRAGMA cache_size=-{int(self.config.sqlite_cache_kib)}")
            self.db.execute("PRAGMA temp_store=FILE")
            self.db.execute("PRAGMA mmap_size=0")
            self.db.executescript("""
                CREATE TABLE clusters(id INTEGER PRIMARY KEY, n INTEGER, body TEXT);
                CREATE INDEX ranking ON clusters(n DESC,id);
                CREATE TABLE exact(key TEXT PRIMARY KEY,cid INTEGER) WITHOUT ROWID;
                CREATE TABLE nodes(key BLOB,cid INTEGER,PRIMARY KEY(key,cid)) WITHOUT ROWID;
            """)
            self.index = DrainIndex(self.db, self.config)
        except BaseException:
            self.close()
            raise
        self.started = time.perf_counter_ns()
        self.phase_events = Counter()
        self.current_started = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
        self.cache.clear()
        self._tmp.cleanup()

    def get(self, cid: int) -> Cluster:
        row = self.db.execute("SELECT body FROM clusters WHERE id=?", (cid,)).fetchone()
        if row is None:
            raise KeyError(cid)
        return Cluster(**json.loads(row[0]))

    def _remember(self, key, cid):
        self.cache[key] = cid
        self.cache.move_to_end(key)
        if len(self.cache) > self.config.cache_size:
            self.cache.popitem(last=False)

    def ingest(self, lines, phase: str = "main"):
        if phase not in {"main", "baseline", "current"}:
            raise ValueError("invalid analysis phase")
        if phase == "baseline" and self.current_started:
            raise ValueError("baseline must precede current input")
        if phase == "current":
            self.current_started = True
        for record in assemble(lines, self.config, self.stats):
            start = time.perf_counter_ns()
            event = self.normalizer.normalize(record.text)
            self.stats["normalize_ns"] += time.perf_counter_ns() - start
            key, new_exact = event.key(), False
            cid = self.cache.get(key)
            if cid is None:
                row = self.db.execute("SELECT cid FROM exact WHERE key=?", (key,)).fetchone()
                cid = row[0] if row else None
            if cid is None:
                new_exact = True
                start = time.perf_counter_ns()
                ranked = []
                for candidate in self.index.query(event):
                    cluster = self.get(candidate)
                    self.stats["comparisons"] += 1
                    if cluster.parser != event.parser or cluster.anchors != list(event.anchors):
                        continue
                    score = min(score_tokens(cluster.leader, event.tokens),
                                score_tokens(cluster.template, event.tokens))
                    if score:
                        ranked.append((score, candidate))
                ranked.sort(key=lambda x: (-x[0], x[1]))
                minimum = math.ceil(self.config.threshold * 10000)
                margin = math.ceil(self.config.min_margin * 10000)
                if ranked and ranked[0][0] >= minimum:
                    second = ranked[1][0] if len(ranked) > 1 else 0
                    if ranked[0][0] - second >= margin:
                        cid = ranked[0][1]
                    else:
                        self.stats["ambiguous_events"] += 1
                self.stats["lookup_ns"] += time.perf_counter_ns() - start
            if cid is None:
                if self.config.max_clusters and self.stats["clusters"] >= self.config.max_clusters:
                    raise ResourceLimit("max_clusters reached")
                cid = self.stats["clusters"] + 1
                cluster = Cluster(cid, event.pattern, list(event.tokens), list(event.tokens),
                                  event.parser, list(event.anchors))
                self.index.add(event, cid)
                self.stats["clusters"] += 1
            else:
                cluster = self.get(cid)
                # Baseline templates stay frozen; leaders never change in any mode.
                if not (phase == "current" and cluster.baseline):
                    cluster.template = merge_template(cluster.template, event.tokens)
            sample = None
            if self.config.sample_mode != "none":
                sample = record.text if self.config.sample_mode == "raw" else event.pattern
                sample = sample[:self.config.sample_chars]
            cluster.observe(event, phase, sample)
            self.db.execute("INSERT OR REPLACE INTO clusters VALUES (?,?,?)",
                            (cid, cluster.count, json.dumps(asdict(cluster), ensure_ascii=True,
                                                           allow_nan=False)))
            if new_exact:
                self.db.execute("INSERT INTO exact VALUES (?,?)", (key, cid))
                self.stats["exact_patterns"] += 1
            self._remember(key, cid)
            self.stats["events"] += 1
            self.stats["event_physical_lines"] += record.physical_lines
            self.stats["timestamp_missing"] += event.timestamp is None
            self.phase_events[phase] += 1
            if self.stats["events"] % 1000 == 0:
                self.db.commit()
        self.db.commit()
        return self

    def summary(self) -> dict:
        # Verify once per report, not on every mini-batch ingest.
        total = self.db.execute("SELECT COALESCE(SUM(n),0) FROM clusters").fetchone()[0]
        if total != self.stats["events"]:
            raise RuntimeError("count conservation invariant failed")
        events, count = self.stats["events"], self.stats["clusters"]
        return {
            "schema_version": "3.0", "tool_version": __version__,
            "backend": "stdlib-typed-leader", "storage": "temporary-sqlite",
            "config_digest": self.config.digest(self.normalizer.rule_specs),
            "config": asdict(self.config), "original_count": self.stats["physical_lines"],
            "logical_events": events, "exact_patterns": self.stats["exact_patterns"],
            "trimmed_count": count, "threshold": self.config.threshold,
            "compression_ratio": 100 * (1 - count / events) if events else 0.0,
            "phase_events": dict(self.phase_events), "counts_exact": True,
            "candidate_search": "bounded-approximate", "input_order_sensitive": True,
            "elapsed_ns": time.perf_counter_ns() - self.started,
            "diagnostics": dict(self.stats),
        }

    def rows(self):
        for (body,) in self.db.execute("SELECT body FROM clusters ORDER BY n DESC,id"):
            cluster = Cluster(**json.loads(body))
            row = asdict(cluster)
            row.pop("leader")
            row["representative"] = cluster.pattern
            row["pattern"] = render_template(cluster.pattern, cluster.template)
            row["rarity"] = -math.log2(cluster.count / max(1, self.stats["events"]))
            yield row


def group_logs(lines, threshold: float = 0.85):
    """Compatibility iterator; aggregation finishes before the first result."""
    with Analyzer(Config(threshold=threshold)) as analyzer:
        analyzer.ingest(lines)
        for row in analyzer.rows():
            yield LogPattern(row["pattern"], row["count"], row["sample"],
                             datetime.fromisoformat(row["first_seen"]) if row["first_seen"] else None,
                             datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None)