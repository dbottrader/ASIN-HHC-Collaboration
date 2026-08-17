"""
CP8 Kernel: Fixed stage pipeline.
No job is allowed to skip or reorder stages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum, auto


class CP8Stage(Enum):
    """
    Fixed and ordered. No job may skip or reorder.
    """
    ARTIFACT = auto()
    MEASUREMENT = auto()
    REPRESENTATION = auto()
    DECODING = auto()
    REPLICATION = auto()
    INTERPRETATION = auto()
    ORIGIN_HYPOTHESIS = auto()
    CHALLENGE = auto()
    REVISION = auto()

    @classmethod
    def ordered_names(cls) -> List[str]:
        return [s.name for s in cls]

    @classmethod
    def index_of(cls, stage_name: str) -> int:
        return cls.ordered_names().index(stage_name)


class CP8KernelError(Exception):
    pass


class StageSkipError(CP8KernelError):
    """Raised when a stage is skipped."""
    pass


class StageReorderError(CP8KernelError):
    """Raised when stages are attempted out of order."""
    pass


@dataclass
class CP8Job:
    """
    A job within the CP8 kernel.
    Preregistered, stage-guarded, immutable history.
    """
    run_id: str
    anchor: str  # The initial hypothesis/artifact description
    preregistered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stages_completed: List[str] = field(default_factory=list)
    current_stage: Optional[str] = None
    stage_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    is_closed: bool = False

    def transition_to(self, stage_name: str, data: Optional[Dict[str, Any]] = None):
        """
        Enforce fixed ordering. No skips. No reordering.
        """
        if stage_name not in CP8Stage.ordered_names():
            raise CP8KernelError(f"Unknown stage: {stage_name}")

        if self.is_closed:
            raise CP8KernelError("Job is closed. No further transitions.")

        if not self.stages_completed:
            # First stage must be ARTIFACT
            if stage_name != CP8Stage.ARTIFACT.name:
                raise StageReorderError(f"First stage must be ARTIFACT, got {stage_name}")

        else:
            last_stage = self.stages_completed[-1]
            last_idx = CP8Stage.index_of(last_stage)
            target_idx = CP8Stage.index_of(stage_name)

            if target_idx <= last_idx:
                raise StageReorderError(
                    f"Cannot move to {stage_name} (idx {target_idx}) from {last_stage} (idx {last_idx})"
                )
            if target_idx != last_idx + 1:
                raise StageSkipError(
                    f"Cannot skip from {last_stage} to {stage_name}. Must pass through intermediate stages."
                )

        self.stages_completed.append(stage_name)
        self.current_stage = stage_name
        if data:
            self.stage_data[stage_name] = data

    def close(self):
        self.is_closed = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "anchor": self.anchor,
            "preregistered_at": self.preregistered_at,
            "stages_completed": self.stages_completed,
            "current_stage": self.current_stage,
            "stage_data": self.stage_data,
            "is_closed": self.is_closed,
        }
