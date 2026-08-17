"""
CP8 Evidence Graph Schema
Content-addressed, canonical, immutable.
Every node carries SHA-256 identity of its canonical form.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Optional, Dict, List
from pathlib import Path


class NodeType(Enum):
    ARTIFACT = auto()
    MEASUREMENT = auto()
    REPRESENTATION = auto()
    DECODING = auto()
    REPLICATION = auto()
    INTERPRETATION = auto()
    ORIGIN_HYPOTHESIS = auto()
    CHALLENGE = auto()
    REVISION = auto()
    CLAIM = auto()
    BRANCH = auto()
    SYNTHESIS = auto()
    PROMOTION_DECISION = auto()
    RECEIPT = auto()
    RUN = auto()


class PromotionVerdict(Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class FiveFieldClaim:
    """
    OBSERVED / CONTEXT / INFERENCE / TEST / CONCLUSION
    Frozen and hashable for content-addressing.
    """
    OBSERVED: str
    CONTEXT: str
    INFERENCE: str
    TEST: str
    CONCLUSION: str

    def canonical(self) -> str:
        """Deterministic serialization for content-addressing."""
        obj = {
            "OBSERVED": self.OBSERVED,
            "CONTEXT": self.CONTEXT,
            "INFERENCE": self.INFERENCE,
            "TEST": self.TEST,
            "CONCLUSION": self.CONCLUSION,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    """
    Base node for the evidence graph.
    Content-addressed via SHA-256 of canonical JSON.
    """
    node_type: NodeType
    run_id: str
    stage: Optional[str] = None
    claim: Optional[FiveFieldClaim] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)  # SHA-256 hashes of parent nodes
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: Optional[str] = None
    branch_id: Optional[str] = None

    def canonical(self) -> str:
        """Deterministic serialization. Field order is enforced."""
        obj = {
            "node_type": self.node_type.name,
            "run_id": self.run_id,
            "stage": self.stage,
            "claim": self.claim.canonical() if self.claim else None,
            "payload": self._normalize_payload(self.payload),
            "parents": sorted(self.parents),
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "branch_id": self.branch_id,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sort keys for deterministic hashing."""
        if isinstance(payload, dict):
            return {k: EvidenceNode._normalize_payload(v) for k, v in sorted(payload.items())}
        elif isinstance(payload, list):
            return [EvidenceNode._normalize_payload(i) for i in payload]
        return payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.sha256(),
            "node_type": self.node_type.name,
            "run_id": self.run_id,
            "stage": self.stage,
            "claim": asdict(self.claim) if self.claim else None,
            "payload": self.payload,
            "parents": self.parents,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "branch_id": self.branch_id,
            "canonical": self.canonical(),
        }


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """
    Signed decision record from the Promotion Gate.
    No Receipt = No Promotion. Enforced by the gate, not by policy.
    """
    run_id: str
    verdict: PromotionVerdict
    target_node_hash: str
    gate_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gate_keeper: str = "CP8_KERNEL"  # Or human Reality Veto key
    signature: Optional[str] = None  # HMAC or Ed25519 in production
    reason: str = ""

    def canonical(self) -> str:
        obj = {
            "run_id": self.run_id,
            "verdict": self.verdict.value,
            "target_node_hash": self.target_node_hash,
            "gate_timestamp": self.gate_timestamp,
            "gate_keeper": self.gate_keeper,
            "reason": self.reason,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()


@dataclass
class CP8RunRecord:
    """
    Complete record of a CP8 execution.
    Immutable after closure.
    """
    run_id: str
    preregistered_at: str
    anchor_claim: FiveFieldClaim
    stages_completed: List[str] = field(default_factory=list)
    branch_ids: List[str] = field(default_factory=list)
    evidence_nodes: List[str] = field(default_factory=list)  # hashes
    synthesis_hash: Optional[str] = None
    promotion_hash: Optional[str] = None
    closed_at: Optional[str] = None
    status: str = "OPEN"  # OPEN | STAGES_COMPLETE | SYNTHESIZED | PROMOTED | CLOSED

    def merkle_root(self) -> str:
        """Compute Merkle root over all evidence node hashes."""
        hashes = sorted(self.evidence_nodes)
        if not hashes:
            return hashlib.sha256(b"").hexdigest()
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            hashes = next_level
        return hashes[0]
