"""Report pipeline progress and obvious-case outcome counts.

Cross-checks the manifest against what's actually on disk for data/raw,
data/text, and data/parsed (existence, not just the manifest's own status
field, so this catches drift between the two), then applies
classify.classify_pair_rule() to every extracted command pair to report
the "obvious case" counts from doc/pipeline/05_classify_outcomes.md ahead
of the LLM/human-review tiers that don't exist yet.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field

from clubfloyd_mine import classify
from clubfloyd_mine import extract_pairs
from clubfloyd_mine import manifest as manifest_io
from clubfloyd_mine import paths
from clubfloyd_mine.models import ManifestRecord, ManifestStatus

# Label used for pairs classify_pair_rule left uncertain (returned None).
# Not an OutcomeBucket value, since "uncertain" means "not yet classified",
# not a real outcome -- see classify_pair_rule's docstring.
UNCERTAIN = "uncertain"


@dataclass
class AuditReport:
    year: int | None
    discovered: int = 0
    fetched: int = 0
    normalized: int = 0
    parsed: int = 0
    # Records the manifest itself marks ManifestStatus.ERROR -- e.g. a
    # source page confirmed gone (real 404), not merely "not fetched yet".
    # Excluded from `complete`'s expected count below: a permanently
    # unfetchable page must not make the whole corpus report FAIL forever.
    errored: int = 0
    extracted_commands: int = 0
    # Keyed by OutcomeBucket.value, plus UNCERTAIN for pairs
    # classify_pair_rule returned None for. A dict (not one field per
    # bucket) because classify_pair_rule's rule coverage grows over time
    # (see doc/classification/examples/*.md) and this must reflect whatever
    # buckets it actually produces without a matching audit.py edit every
    # time.
    rule_outcome_counts: dict[str, int] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        """True when every discovered record that isn't a known-errored
        source has made it all the way through fetch/normalize/extract-pairs
        with nothing dropped along the way.

        This is the gate for trusting the pipeline enough to build on top of
        it -- e.g. CLAUDE.md's "add tests before broad crawling" extends to
        "don't widen scope (more years) until the current scope is clean."
        A record the manifest marks ManifestStatus.ERROR (e.g. a confirmed
        404 -- see 20230603-i-am-prey) is expected to never fetch; it must
        not count against this forever.
        """
        expected = self.discovered - self.errored
        return self.discovered > 0 and expected == self.fetched == self.normalized == self.parsed


def build_report(records: list[ManifestRecord], *, root, year: int | None) -> AuditReport:
    report = AuditReport(year=year)
    counts: Counter[str] = Counter()
    for record in records:
        # Presence in the manifest at all counts as discovered, regardless
        # of how far its status has since advanced.
        report.discovered += 1
        if record.status is ManifestStatus.ERROR:
            report.errored += 1
        if paths.raw_html_path(record.year, record.id, root).exists():
            report.fetched += 1
        if paths.transcript_json_path(record.year, record.id, root).exists():
            report.normalized += 1
        if paths.command_pairs_path(record.year, record.id, root).exists():
            report.parsed += 1
        for pair in extract_pairs.load_command_pairs(record, root):
            report.extracted_commands += 1
            outcome = classify.classify_pair_rule(pair)
            counts[outcome.value if outcome is not None else UNCERTAIN] += 1
    report.rule_outcome_counts = dict(counts)
    return report


def _print_report(report: AuditReport) -> None:
    scope = f"year {report.year}" if report.year is not None else "all years"
    print(f"audit: {scope}")
    print(f"  discovered pages:    {report.discovered}")
    print(f"  errored pages:       {report.errored}")
    print(f"  fetched pages:       {report.fetched}")
    print(f"  normalized pages:    {report.normalized}")
    print(f"  parsed pages:        {report.parsed}")
    print(f"  extracted commands:  {report.extracted_commands}")
    # Uncertain first (the "how much is left" number), then every bucket
    # classify_pair_rule actually produced, busiest first.
    print(f"  uncertain commands:  {report.rule_outcome_counts.get(UNCERTAIN, 0)}")
    for bucket, count in sorted(report.rule_outcome_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if bucket == UNCERTAIN:
            continue
        print(f"  {bucket + ':':<21}{count}")
    print(f"  result:              {'PASS' if report.complete else 'FAIL'}")


def run(args: argparse.Namespace) -> None:
    manifest_file = paths.manifest_path(args.root)
    records = manifest_io.load_manifest(manifest_file)
    if not records:
        print(f"audit: no records in {manifest_file}; run discover first")
        return

    year = getattr(args, "year", None)
    selected = [r for r in records.values() if year is None or r.year == year]
    if not selected:
        scope = f"year {year}" if year is not None else "any year"
        print(f"audit: no records found for {scope}")
        return

    report = build_report(selected, root=args.root, year=year)
    _print_report(report)
    if not report.complete:
        raise SystemExit(1)
