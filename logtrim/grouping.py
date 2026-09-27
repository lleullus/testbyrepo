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
from .models import Cluster, Config, LogPattern, NormalizedEvent, ResourceLimit
from .patterns import Normalizer
from .similarity import family, merge_template, render_template, score_tokens, tokenize
from .families import FamilyRecord, reduce_records
from .variability import generalized_pattern, signature as variability_signature


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
        self.adaptive_cache = OrderedDict()
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
                CREATE TABLE exact(
                    key TEXT PRIMARY KEY,cid INTEGER NOT NULL,n INTEGER NOT NULL,
                    baseline INTEGER NOT NULL,current INTEGER NOT NULL) WITHOUT ROWID;
                CREATE TABLE nodes(key BLOB,cid INTEGER,PRIMARY KEY(key,cid)) WITHOUT ROWID;
                CREATE TABLE variants(
                    cid INTEGER NOT NULL, signature TEXT NOT NULL,
                    n INTEGER NOT NULL, baseline INTEGER NOT NULL, current INTEGER NOT NULL,
                    PRIMARY KEY(cid,signature)) WITHOUT ROWID;
                CREATE TABLE family_states(
                    cid INTEGER NOT NULL,state TEXT NOT NULL,n INTEGER NOT NULL,
                    baseline INTEGER NOT NULL,current INTEGER NOT NULL,
                    PRIMARY KEY(cid,state)) WITHOUT ROWID;
                CREATE TABLE adaptive_values(
                    parser TEXT NOT NULL,skeleton TEXT NOT NULL,location TEXT NOT NULL,
                    lexical_type TEXT NOT NULL,value TEXT NOT NULL,weight INTEGER NOT NULL,
                    PRIMARY KEY(parser,skeleton,location,lexical_type,value)) WITHOUT ROWID;
                CREATE TABLE adaptive_promoted(
                    parser TEXT NOT NULL,skeleton TEXT NOT NULL,location TEXT NOT NULL,
                    lexical_type TEXT NOT NULL,distinct_count INTEGER NOT NULL,
                    occurrence_count INTEGER NOT NULL,entropy REAL NOT NULL,
                    dominant_ratio REAL NOT NULL,
                    PRIMARY KEY(parser,skeleton,location,lexical_type)) WITHOUT ROWID;
                CREATE TABLE adaptive_map(
                    cid INTEGER PRIMARY KEY,group_key TEXT NOT NULL,canonical INTEGER);
                CREATE INDEX adaptive_group ON adaptive_map(group_key,cid);
                CREATE INDEX variant_ranking ON variants(cid,n DESC,signature);
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
        self.stats["cache_peak"] = max(self.stats["cache_peak"], len(self.cache))


    def _adapt_pattern(self, parser: str, pattern: str) -> str:
        cache_key = (parser, pattern)
        cached = self.adaptive_cache.get(cache_key)
        if cached is not None:
            self.adaptive_cache.move_to_end(cache_key)
            return cached
        skeleton, _ = variability_signature(parser, pattern)
        promoted = {(location, lexical_type) for location, lexical_type in self.db.execute(
            "SELECT location,lexical_type FROM adaptive_promoted WHERE parser=? AND skeleton=?",
            (parser, skeleton))}
        generalized = generalized_pattern(parser, pattern, promoted) if promoted else pattern
        self.adaptive_cache[cache_key] = generalized
        if len(self.adaptive_cache) > self.config.cache_size:
            self.adaptive_cache.popitem(last=False)
        self.stats["adaptive_cache_peak"] = max(self.stats["adaptive_cache_peak"],
                                                len(self.adaptive_cache))
        return generalized

    def _learn_adaptive_positions(self):
        self.db.execute("DELETE FROM adaptive_values")
        self.db.execute("DELETE FROM adaptive_promoted")
        for key, weight in self.db.execute("SELECT key,n FROM exact"):
            parser, pattern = json.loads(key)
            skeleton, candidates = variability_signature(parser, pattern)
            self.db.executemany(
                "INSERT INTO adaptive_values VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(parser,skeleton,location,lexical_type,value) "
                "DO UPDATE SET weight=weight+excluded.weight",
                ((parser, skeleton, item.location, item.lexical_type, item.value, weight)
                 for item in candidates))
        positions = self.db.execute(
            "SELECT parser,skeleton,location,lexical_type,SUM(weight),COUNT(*),MAX(weight) "
            "FROM adaptive_values GROUP BY parser,skeleton,location,lexical_type "
            "HAVING COUNT(*)>=3 AND SUM(weight)>=3")
        promoted = 0
        for parser, skeleton, location, lexical_type, total, distinct, maximum in positions:
            entropy = 0.0
            for (weight,) in self.db.execute(
                    "SELECT weight FROM adaptive_values WHERE parser=? AND skeleton=? "
                    "AND location=? AND lexical_type=?", (parser, skeleton, location, lexical_type)):
                probability = weight / total
                entropy -= probability * math.log2(probability)
            dominant = maximum / total
            if entropy < 1.0 or dominant > 0.8:
                continue
            self.db.execute("INSERT INTO adaptive_promoted VALUES (?,?,?,?,?,?,?,?)",
                            (parser, skeleton, location, lexical_type, distinct,
                             total, entropy, dominant))
            promoted += 1
        self.stats["adaptive.signatures"] = self.db.execute("SELECT COUNT(*) FROM exact").fetchone()[0]
        self.stats["adaptive.values"] = self.db.execute("SELECT COUNT(*) FROM adaptive_values").fetchone()[0]
        self.stats["adaptive.promoted_positions"] = promoted

    def _merge_adaptive_clusters(self):
        self.db.execute("DELETE FROM adaptive_map")
        for cid, body in self.db.execute("SELECT id,body FROM clusters ORDER BY id"):
            cluster = Cluster(**json.loads(body))
            generalized = self._adapt_pattern(cluster.parser, cluster.pattern)
            group_key = json.dumps([cluster.parser, cluster.anchors, generalized],
                                   ensure_ascii=True, separators=(",", ":"))
            self.db.execute("INSERT INTO adaptive_map VALUES (?,?,?)", (cid, group_key, cid))
        self.db.execute("UPDATE adaptive_map SET canonical=(SELECT MIN(cid) FROM adaptive_map m2 "
                         "WHERE m2.group_key=adaptive_map.group_key)")
        old_count = self.db.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
        new_count = self.db.execute("SELECT COUNT(DISTINCT canonical) FROM adaptive_map").fetchone()[0]
        self.stats["adaptive.merged_clusters"] = old_count - new_count
        self.db.execute("DROP TABLE IF EXISTS clusters_new")
        self.db.execute("CREATE TABLE clusters_new(id INTEGER PRIMARY KEY,n INTEGER,body TEXT)")
        self.db.execute("DROP TABLE IF EXISTS variants_new")
        self.db.execute("CREATE TABLE variants_new(cid INTEGER NOT NULL,signature TEXT NOT NULL,"
                         "n INTEGER NOT NULL,baseline INTEGER NOT NULL,current INTEGER NOT NULL,"
                         "PRIMARY KEY(cid,signature)) WITHOUT ROWID")
        self.db.execute("DROP TABLE IF EXISTS family_states_new")
        self.db.execute("CREATE TABLE family_states_new(cid INTEGER NOT NULL,state TEXT NOT NULL,"
                         "n INTEGER NOT NULL,baseline INTEGER NOT NULL,current INTEGER NOT NULL,"
                         "PRIMARY KEY(cid,state)) WITHOUT ROWID")
        groups = self.db.execute(
            "SELECT group_key,MIN(cid) FROM adaptive_map GROUP BY group_key ORDER BY MIN(cid)")
        for group_key, canonical in groups:
            member_rows = self.db.execute(
                "SELECT c.id,c.body FROM clusters c JOIN adaptive_map m ON m.cid=c.id "
                "WHERE m.group_key=? ORDER BY c.id", (group_key,))
            merged = None
            generalized = json.loads(group_key)[2]
            template = tokenize(generalized)
            for _, body in member_rows:
                cluster = Cluster(**json.loads(body))
                if merged is None:
                    merged = Cluster(cluster.id, generalized, list(template), list(template),
                                     cluster.parser, list(cluster.anchors),
                                     representative=cluster.representative or cluster.pattern)
                merged.count += cluster.count
                merged.baseline += cluster.baseline
                merged.current += cluster.current
                merged.sample = merged.sample or cluster.sample
                if cluster.first_seen:
                    merged.first_seen = min(merged.first_seen or cluster.first_seen,
                                             cluster.first_seen)
                if cluster.last_seen:
                    merged.last_seen = max(merged.last_seen or cluster.last_seen,
                                           cluster.last_seen)
                for name, slot in cluster.slots.items():
                    target = merged.slots.get(name)
                    if target is None:
                        merged.slots[name] = dict(slot)
                    else:
                        old_count, new_count = target["count"], slot["count"]
                        total_count = old_count + new_count
                        target["mean"] = (target["mean"] * old_count + slot["mean"] * new_count) / total_count
                        target["count"] = total_count
                        target["min"] = min(target["min"], slot["min"])
                        target["max"] = max(target["max"], slot["max"])
            if merged is None:
                continue
            merged.id = canonical
            self.db.execute("INSERT INTO clusters_new VALUES (?,?,?)",
                            (canonical, merged.count, json.dumps(asdict(merged),
                                                                 ensure_ascii=True, allow_nan=False)))
            self.db.execute(
                "INSERT INTO variants_new SELECT ?,signature,SUM(n),SUM(baseline),SUM(current) "
                "FROM variants v JOIN adaptive_map m ON m.cid=v.cid "
                "WHERE m.group_key=? GROUP BY signature", (canonical, group_key))
            self.db.execute(
                "INSERT INTO family_states_new SELECT ?,state,SUM(n),SUM(baseline),SUM(current) "
                "FROM family_states f JOIN adaptive_map m ON m.cid=f.cid "
                "WHERE m.group_key=? GROUP BY state", (canonical, group_key))
            for exact_key, count, baseline, current in self.db.execute(
                    "SELECT e.key,e.n,e.baseline,e.current FROM exact e "
                    "JOIN adaptive_map m ON m.cid=e.cid WHERE m.group_key=?", (group_key,)):
                parser, raw_pattern = json.loads(exact_key)
                if self._adapt_pattern(parser, raw_pattern) == raw_pattern:
                    continue
                self.db.execute(
                    "INSERT INTO variants_new VALUES (?,?,?,?,?) "
                    "ON CONFLICT(cid,signature) DO UPDATE SET "
                    "n=n+excluded.n,baseline=baseline+excluded.baseline,current=current+excluded.current",
                    (canonical, raw_pattern, count, baseline, current))
        self.db.execute("UPDATE exact SET cid=(SELECT canonical FROM adaptive_map "
                         "WHERE adaptive_map.cid=exact.cid)")
        self.db.execute("DELETE FROM clusters")
        self.db.execute("INSERT INTO clusters SELECT id,n,body FROM clusters_new")
        self.db.execute("DELETE FROM variants")
        self.db.execute("INSERT INTO variants SELECT cid,signature,n,baseline,current FROM variants_new")
        self.db.execute("DELETE FROM family_states")
        self.db.execute("INSERT INTO family_states SELECT cid,state,n,baseline,current "
                         "FROM family_states_new")
        self.db.execute("DELETE FROM nodes")
        for cid, body in self.db.execute("SELECT id,body FROM clusters"):
            cluster = Cluster(**json.loads(body))
            event = NormalizedEvent(cluster.pattern, tuple(cluster.leader),
                                    tuple(cluster.anchors), cluster.parser, None)
            self.index.add(event, cid)
        self.db.execute("DROP TABLE clusters_new")
        self.db.execute("DROP TABLE variants_new")
        self.db.execute("DROP TABLE family_states_new")
        self.db.execute("DELETE FROM adaptive_map")
        self.cache.clear()
        self.adaptive_cache.clear()
        self.stats["clusters"] = self.db.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
        self.stats["exact_patterns"] = self.db.execute("SELECT COUNT(*) FROM exact").fetchone()[0]

    def _apply_adaptive_inference(self):
        self._learn_adaptive_positions()
        self.adaptive_cache.clear()
        self._merge_adaptive_clusters()

    def ingest(self, lines, phase: str = "main"):
        if phase not in {"main", "baseline", "current"}:
            raise ValueError("invalid analysis phase")
        if phase == "baseline" and self.current_started:
            raise ValueError("baseline must precede current input")
        if phase == "current":
            self.current_started = True
        for record in reduce_records(assemble(lines, self.config, self.stats),
                                     self.config, self.stats):
            start = time.perf_counter_ns()
            if isinstance(record, FamilyRecord):
                event = NormalizedEvent(record.pattern, tokenize(record.pattern), (),
                                        record.parser, None, (), record.text)
                key = json.dumps([record.parser, record.pattern], ensure_ascii=True)
                physical_lines = record.physical_lines
            else:
                event = self.normalizer.normalize(record.text)
                key = event.key()
                physical_lines = record.physical_lines
            raw_pattern = event.pattern
            raw_key = key
            if isinstance(record, FamilyRecord):
                row = self.db.execute("SELECT cid FROM exact WHERE key=?", (raw_key,)).fetchone()
                cid = row[0] if row else None
            else:
                cid = self.cache.get(raw_key)
                if cid is None:
                    row = self.db.execute("SELECT cid FROM exact WHERE key=?", (raw_key,)).fetchone()
                    cid = row[0] if row else None
            known_exact = cid is not None
            new_exact = not known_exact
            adaptive_event = False
            if not known_exact:
                adapted = self._adapt_pattern(event.parser, raw_pattern)
                adaptive_event = adapted != raw_pattern
                if adaptive_event:
                    event = NormalizedEvent(adapted, tokenize(adapted), event.anchors, event.parser,
                                            event.timestamp, event.captures, event.semantic_pattern)
            self.stats["normalize_ns"] += time.perf_counter_ns() - start
            if cid is None and not isinstance(record, FamilyRecord):
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
                                  event.parser, list(event.anchors), representative=raw_pattern)
                self.index.add(event, cid)
                self.stats["clusters"] += 1
            else:
                cluster = self.get(cid)
                # Baseline templates stay frozen; leaders never change in any mode.
                if not known_exact and not (phase == "current" and cluster.baseline):
                    cluster.template = merge_template(cluster.template, event.tokens)
            sample = None
            if self.config.sample_mode != "none":
                sample = (record.text if self.config.sample_mode == "raw"
                          else (event.semantic_pattern or event.pattern))
                sample = sample[:self.config.sample_chars]
            cluster.observe(event, phase, sample)
            if isinstance(record, FamilyRecord) and record.family_state is not None:
                self.db.execute(
                    "INSERT INTO family_states VALUES (?,?,?,?,?) "
                    "ON CONFLICT(cid,state) DO UPDATE SET "
                    "n=n+1,baseline=baseline+excluded.baseline,current=current+excluded.current",
                    (cid, record.family_state, 1, int(phase == "baseline"), int(phase == "current")))
            variant = event.semantic_pattern
            if not adaptive_event and variant is not None and variant != event.pattern:
                self.db.execute(
                    "INSERT INTO variants VALUES (?,?,?,?,?) "
                    "ON CONFLICT(cid,signature) DO UPDATE SET "
                    "n=n+1,baseline=baseline+excluded.baseline,current=current+excluded.current",
                    (cid, variant, 1, int(phase == "baseline"), int(phase == "current")))
            self.db.execute("INSERT OR REPLACE INTO clusters VALUES (?,?,?)",
                            (cid, cluster.count, json.dumps(asdict(cluster), ensure_ascii=True,
                                                           allow_nan=False)))
            if new_exact:
                self.db.execute("INSERT INTO exact VALUES (?,?,?,?,?)",
                                (raw_key, cid, 1, int(phase == "baseline"), int(phase == "current")))
                self.stats["exact_patterns"] += 1
            else:
                self.db.execute("UPDATE exact SET n=n+1,baseline=baseline+?,current=current+? "
                                "WHERE key=?",
                                (int(phase == "baseline"), int(phase == "current"), raw_key))
            self._remember(key, cid)
            self.stats["events"] += 1
            self.stats["event_physical_lines"] += record.physical_lines
            self.stats["timestamp_missing"] += event.timestamp is None
            self.phase_events[phase] += 1
            if self.stats["events"] % 1000 == 0:
                self.db.commit()
        self.db.commit()
        self._apply_adaptive_inference()
        self.db.commit()
        return self

    def summary(self) -> dict:
        # Verify once per report, not on every mini-batch ingest.
        total = self.db.execute("SELECT COALESCE(SUM(n),0) FROM clusters").fetchone()[0]
        if total != self.stats["events"]:
            raise RuntimeError("count conservation invariant failed")
        events, count = self.stats["events"], self.stats["clusters"]
        physical = self.stats["physical_lines"]
        coarse = self.stats["exact_patterns"]
        return {
            "schema_version": "4.0", "variant_schema_version": "1.0",
            "tool_version": __version__,
            "backend": "stdlib-typed-leader", "storage": "temporary-sqlite",
            "config_digest": self.config.digest(self.normalizer.rule_specs),
            "config": asdict(self.config), "original_count": physical,
            "logical_events": events, "exact_patterns": coarse, "coarse_patterns": coarse,
            "trimmed_count": count, "threshold": self.config.threshold,
            "compression_ratio": 100 * (1 - count / events) if events else 0.0,
            "coarse_compression_ratio": 100 * (1 - coarse / events) if events else 0.0,
            "physical_compression_ratio": 100 * (1 - count / physical) if physical else 0.0,
            "compression_stages": {
                "physical_lines": physical,
                "logical_events": events,
                "coarse_patterns": coarse,
                "final_patterns": count,
            },
            "phase_events": dict(self.phase_events), "counts_exact": True,
            "candidate_search": "bounded-approximate", "input_order_sensitive": True,
            "elapsed_ns": time.perf_counter_ns() - self.started,
            "diagnostics": dict(self.stats),
        }

    def rows(self):
        for body, cid in self.db.execute("SELECT body,id FROM clusters ORDER BY n DESC,id"):
            cluster = Cluster(**json.loads(body))
            row = asdict(cluster)
            row.pop("leader")
            row["variants"] = {
                signature: {"count": count, "baseline": baseline, "current": current}
                for signature, count, baseline, current in self.db.execute(
                    "SELECT signature,n,baseline,current FROM variants "
                    "WHERE cid=? ORDER BY n DESC,signature LIMIT ?",
                    (cid, self.config.max_variants))
            }
            overflow = self.db.execute(
                "SELECT COALESCE(SUM(n),0) FROM variants WHERE cid=? "
                "AND signature NOT IN (SELECT signature FROM variants WHERE cid=? "
                "ORDER BY n DESC,signature LIMIT ?)",
                (cid, cid, self.config.max_variants)).fetchone()[0]
            row["variant_other_count"] = overflow
            row["variant_unique_count"] = self.db.execute(
                "SELECT COUNT(*) FROM variants WHERE cid=?", (cid,)).fetchone()[0]
            row["family_states"] = {
                state: {"count": count, "baseline": baseline, "current": current}
                for state, count, baseline, current in self.db.execute(
                    "SELECT state,n,baseline,current FROM family_states "
                    "WHERE cid=? ORDER BY state", (cid,))
            }
            representative = cluster.representative or cluster.pattern
            row.pop("representative", None)
            row["representative"] = representative
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