"""Read the pinned BOR release (CSV files in a zip kept outside the repo) and verify it.

The release is identified in data/sources.yaml (`bor_layers`): zip name, sha256, run id and snapshot id.
Nothing here writes to a database. Loaders and checks share this reader; expected answers in tests are
derived separately from the same files.

    release = BorRelease()          # path from BOR_RELEASE_ZIP or the default below
    release.verify_zip()            # zip sha256 equals data/sources.yaml
    release.manifest                # manifest.json as a dict
    for row in release.rows("groups"): ...        # dicts of strings
    release.verify_member("groups")               # sha256 of the member equals manifest.output_checksums
"""

import csv
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = "~/Learning/Sabbatical/beneficial-ownership-resolution/dist"


def _sha256(stream) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


class BorRelease:
    def __init__(self, path: str | os.PathLike | None = None):
        self.source = yaml.safe_load((ROOT / "data/sources.yaml").read_text())
        self.source = self.source.get("sources", self.source)["bor_layers"]
        default = Path(DEFAULT_DIR).expanduser() / self.source["file"]
        self.path = Path(path or os.environ.get(self.source["path_env"]) or default).expanduser()
        self._zip = zipfile.ZipFile(self.path)
        self._prefix = self.source["file"].removesuffix(".zip") + "/"

    @property
    def manifest(self) -> dict:
        return json.loads(self._zip.read(self._prefix + "manifest.json"))

    def verify_zip(self) -> bool:
        with open(self.path, "rb") as f:
            return _sha256(f) == self.source["sha256"]

    def verify_identity(self) -> list[str]:
        """Problems comparing the manifest with data/sources.yaml (empty list means none)."""
        m, problems = self.manifest, []
        for key in ("run_id", "snapshot_id", "schema_version"):
            if str(m.get(key)) != str(self.source[key]):
                problems.append(f"{key}: manifest {m.get(key)!r} vs sources.yaml {self.source[key]!r}")
        return problems

    def verify_member(self, table: str) -> bool:
        with self._zip.open(self._prefix + f"{table}.csv") as f:
            return _sha256(f) == self.manifest["output_checksums"][f"{table}.csv"]

    def rows(self, table: str, **equals: str):
        """Stream the rows of one table as dicts of strings, keeping rows where every column equals its value."""
        with self._zip.open(self._prefix + f"{table}.csv") as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                if all(row[k] == v for k, v in equals.items()):
                    yield row
