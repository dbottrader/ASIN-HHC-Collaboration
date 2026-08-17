"""
Content-addressed storage with atomic writes,
snapshot rotation, and path traversal guardrails.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional
import fcntl


class CP8Storage:
    """
    Immutable content-addressed store.
    Objects are written once, read many.
    """

    def __init__(self, base_path: Path, max_snapshots: int = 10):
        self.base_path = Path(base_path).resolve()
        self.objects_path = self.base_path / "objects"
        self.runs_path = self.base_path / "runs"
        self.snapshots_path = self.base_path / "snapshots"
        self.max_snapshots = max_snapshots

        self.objects_path.mkdir(parents=True, exist_ok=True)
        self.runs_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_path.mkdir(parents=True, exist_ok=True)

    def _guard_path(self, rel_path: str) -> Path:
        """Prevent path traversal. Only allow relative paths within base."""
        target = (self.base_path / rel_path).resolve()
        if not str(target).startswith(str(self.base_path)):
            raise PermissionError(f"Path traversal blocked: {rel_path}")
        return target

    def store(self, content_hash: str, data: dict, namespace: str = "objects") -> Path:
        """
        Atomic write with fsync.
        Returns the stored path.
        """
        # Shard by first 2 chars of hash to avoid directory explosion
        shard = content_hash[:2]
        dir_path = self.base_path / namespace / shard
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{content_hash}.json"
        if file_path.exists():
            return file_path  # Idempotent

        # Write to temp, then atomic rename
        fd, temp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, sort_keys=True, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, file_path)
        except Exception:
            os.unlink(temp_path)
            raise

        return file_path

    def retrieve(self, content_hash: str, namespace: str = "objects") -> Optional[dict]:
        shard = content_hash[:2]
        file_path = self.base_path / namespace / shard / f"{content_hash}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def store_run(self, run_id: str, record: dict) -> Path:
        """Store a run record by its run ID (not content-addressed, versioned)."""
        safe_id = run_id.replace("/", "_").replace("..", "_")
        file_path = self.runs_path / f"{safe_id}.json"
        
        # Atomic write
        fd, temp_path = tempfile.mkstemp(dir=str(self.runs_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(record, f, sort_keys=True, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, file_path)
        except Exception:
            os.unlink(temp_path)
            raise

        self._rotate_snapshots(safe_id, record)
        return file_path

    def retrieve_run(self, run_id: str) -> Optional[dict]:
        safe_id = run_id.replace("/", "_").replace("..", "_")
        file_path = self.runs_path / f"{safe_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _rotate_snapshots(self, run_id: str, record: dict):
        """Keep last N versions of run records for audit."""
        snapshot_dir = self.snapshots_path / run_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = record.get("preregistered_at", "unknown").replace(":", "-")
        snap_path = snapshot_dir / f"{timestamp}.json"
        
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(record, f, sort_keys=True, indent=2, ensure_ascii=False)

        # Cleanup old snapshots
        snaps = sorted(snapshot_dir.glob("*.json"))
        while len(snaps) > self.max_snapshots:
            snaps[0].unlink()
            snaps = snaps[1:]

    def exists(self, content_hash: str, namespace: str = "objects") -> bool:
        shard = content_hash[:2]
        return (self.base_path / namespace / shard / f"{content_hash}.json").exists()
