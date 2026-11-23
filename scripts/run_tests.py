"""Run the sub-question checks (tests/q*_*/check_*.py) in parallel and report timings.

Every check is read-only (graph and source), so they can run side by side. Output of each check is kept and printed only for failures, so
the log is short. A timing table lists the slowest checks. Any nonzero exit, error or timeout is a failure.

Usage: uv run python scripts/run_tests.py [-j N] [-k PATTERN] [--slowest N] [--timings FILE]
  -j N         workers (default JOBS env, else 4; 1 = serial)
  -k PATTERN   run only checks whose path contains PATTERN (for example q17 or q9_), repeatable
  --failed     rerun only the checks that failed last time (read from .test-last-failed)
"""

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILED = ROOT / ".test-last-failed"


def run(path: Path) -> tuple[Path, int, float, str]:
    t = time.monotonic()
    p = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    return path, p.returncode, time.monotonic() - t, p.stdout + p.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=int(os.environ.get("JOBS", "4")))
    ap.add_argument("-k", action="append", default=[])
    ap.add_argument("--failed", action="store_true")
    ap.add_argument("--slowest", type=int, default=8)
    a = ap.parse_args()
    files = sorted(ROOT.glob("tests/q*_*/check_*.py"))
    if a.failed and FAILED.exists():
        keep = set(FAILED.read_text().split())
        files = [f for f in files if str(f.relative_to(ROOT)) in keep]
    if a.k:
        files = [f for f in files if any(k in str(f) for k in a.k)]
    if not files:
        print("no checks selected")
        return 1
    t0 = time.monotonic()
    done: list[tuple[Path, int, float, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, a.j)) as ex:
        for fut in as_completed([ex.submit(run, f) for f in files]):
            r = fut.result()
            done.append(r)
            print(f"{'ok  ' if r[1] == 0 else 'FAIL'} {r[2]:6.1f}s  {r[0].relative_to(ROOT)}", flush=True)
    bad = [r for r in done if r[1] != 0]
    for path, _rc, _t, out in sorted(bad):
        print(f"\n== {path.relative_to(ROOT)}\n{out}")
    FAILED.write_text("\n".join(str(r[0].relative_to(ROOT)) for r in bad))
    print(f"\nslowest: " + ", ".join(f"{r[0].parent.name} {r[2]:.0f}s" for r in sorted(done, key=lambda r: -r[2])[: a.slowest]))
    print(f"{len(done) - len(bad)}/{len(done)} check files passed in {time.monotonic() - t0:.0f}s (sum of checks {sum(r[2] for r in done):.0f}s, {a.j} workers)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
