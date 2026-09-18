"""Creation of one evaluation run directory.

Every artefact this tool writes goes under evaluation/runs/<timestamp>/, which
../GOALS.md requires so that input/ and output/ are never touched. Phase 04
owns the rest of the run lifecycle; this module only creates a fresh directory
and refuses to reuse one that already exists.
"""

from datetime import datetime, timezone
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parent / "runs"
RUN_SUBDIRECTORIES = ("hr", "lr", "bicubic")
TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def create_run_directory(root: Path | None = None, moment: datetime | None = None) -> Path:
    """Create <root>/<UTC timestamp>/ with the run's subdirectories.

    Raises FileExistsError rather than writing into an existing directory: a
    previous run's record must never be overwritten.
    """
    root = RUNS_ROOT if root is None else root
    moment = datetime.now(timezone.utc) if moment is None else moment
    run = root / moment.strftime(TIMESTAMP_FORMAT)
    run.mkdir(parents=True, exist_ok=False)
    for name in RUN_SUBDIRECTORIES:
        (run / name).mkdir()
    return run
