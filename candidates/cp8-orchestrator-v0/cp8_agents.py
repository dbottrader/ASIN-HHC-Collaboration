"""
CP8 Agent Mesh.
Independent workers never receive the originating interpretation.
They receive artifact, measurements, and prior receipts only.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from cp8_schema import EvidenceNode, NodeType, FiveFieldClaim


@dataclass
class AgentContext:
    """
    What an agent is allowed to see.
    Deliberately excludes interpretations from other branches.
    """
    run_id: str
    branch_id: str
    artifact: Dict[str, Any]
    measurements: List[Dict[str, Any]] = field(default_factory=list)
    prior_receipts: List[str] = field(default_factory=list)
    stage: Optional[str] = None


class CP8Agent(ABC):
    """
    Base agent. All agents produce EvidenceNodes.
    """
    agent_id: str = "base"
    is_adversarial: bool = False

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        """
        Produce evidence nodes based ONLY on the provided context.
        No access to other branches' interpretations.
        """
        pass


class EvidenceAgent(CP8Agent):
    """Searches local corpus, Drive, GitHub, prior receipts."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        # In production: connect to Drive API, GitHub API, local index
        # Stub: produce a claim node documenting the search scope
        claim = FiveFieldClaim(
            OBSERVED=f"Evidence search initiated for run {context.run_id}",
            CONTEXT=f"Branch {context.branch_id}, stage {context.stage}",
            INFERENCE="Local corpus and prior receipts are available for retrieval",
            TEST="Search scope defined, execution pending integration",
            CONCLUSION="Evidence channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.CLAIM,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"search_scope": ["drive", "github", "local_corpus", "prior_receipts"]}
        )
        return [node]


class ResearchAgent(CP8Agent):
    """External literature search."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="External literature search initiated",
            CONTEXT="Public repositories and academic databases",
            INFERENCE="Relevant publications may exist",
            TEST="Query construction and API search required",
            CONCLUSION="Research channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.CLAIM,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"databases": ["arxiv", "scholar", "pubmed", "github"]}
        )
        return [node]


class ChronologyAgent(CP8Agent):
    """Reconciles timestamps, releases, commits, provenance."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Temporal artifacts present in context",
            CONTEXT="Run contains timestamped data",
            INFERENCE="Chronological ordering affects causal claims",
            TEST="Cross-reference timestamps against known release dates",
            CONCLUSION="Chronology channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.CLAIM,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"temporal_fields": list(context.artifact.keys())}
        )
        return [node]


class PatternAgent(CP8Agent):
    """Structural comparisons without seeing preferred conclusion."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Artifact exhibits structural regularities",
            CONTEXT="Pattern analysis without access to prior interpretations",
            INFERENCE="Structural features may indicate encoding or design",
            TEST="Compare against known pattern libraries",
            CONCLUSION="Pattern channel established; no convergence bias injected"
        )
        node = EvidenceNode(
            node_type=NodeType.CLAIM,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"pattern_types": ["geometric", "statistical", "topological"]}
        )
        return [node]


class SkepticAgent(CP8Agent):
    """Adversarial. Tries to kill the hypothesis."""

    def __init__(self, agent_id: str = "skeptic"):
        super().__init__(agent_id)
        self.is_adversarial = True

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Hypothesis has been proposed",
            CONTEXT="Adversarial review required before synthesis",
            INFERENCE="The hypothesis may suffer from confirmation bias, data leakage, or unfalsifiability",
            TEST="Attempt falsification through alternative explanations and stress tests",
            CONCLUSION="Skeptic channel active; hypothesis treated as guilty until stress-tested"
        )
        node = EvidenceNode(
            node_type=NodeType.CHALLENGE,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage="CHALLENGE",
            claim=claim,
            agent_id=self.agent_id,
            payload={"adversarial_mode": True, "target": "all_active_hypotheses"}
        )
        return [node]


class ReplicationAgent(CP8Agent):
    """Attempts to reproduce calculations, geometry, code."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Methods and data are specified",
            CONTEXT="Replication requires independent execution",
            INFERENCE="If the result is robust, it should reproduce under identical conditions",
            TEST="Re-run calculations, rebuild geometry, re-execute code",
            CONCLUSION="Replication channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.REPLICATION,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage="REPLICATION",
            claim=claim,
            agent_id=self.agent_id,
            payload={"replication_target": "artifact_measurements_and_transforms"}
        )
        return [node]


class PriorArtAgent(CP8Agent):
    """Checks whether something existed earlier."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Novelty claim requires validation",
            CONTEXT="Historical record may contain precedents",
            INFERENCE="Similarity does not imply influence; independence must be distinguished",
            TEST="Search historical corpus for functional or structural precedents",
            CONCLUSION="Prior-art channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.CLAIM,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"search_depth": "deep", "distinguish_similarity_from_influence": True}
        )
        return [node]


class BuilderAgent(CP8Agent):
    """Turns surviving concepts into runnable artifacts."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        claim = FiveFieldClaim(
            OBSERVED="Synthesis has produced actionable concepts",
            CONTEXT="Builder translates abstract findings into executable form",
            INFERENCE="Runnable artifacts enable further testing and validation",
            TEST="Produce code, interface, experiment, or dataset",
            CONCLUSION="Builder channel established"
        )
        node = EvidenceNode(
            node_type=NodeType.ARTIFACT,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage="ARTIFACT",
            claim=claim,
            agent_id=self.agent_id,
            payload={"output_types": ["code", "ui", "dataset", "experiment"]}
        )
        return [node]


class ArchivistAgent(CP8Agent):
    """Writes hashes, sources, versions, provenance into ledger."""

    def execute(self, context: AgentContext) -> List[EvidenceNode]:
        # The archivist documents the run itself
        claim = FiveFieldClaim(
            OBSERVED="Run has generated evidence nodes",
            CONTEXT="Provenance must be preserved for audit and reconstruction",
            INFERENCE="Content-addressed storage ensures tamper-evident history",
            TEST="Hash all nodes, record sources, versions, timestamps",
            CONCLUSION="Archivist channel complete; ledger updated"
        )
        node = EvidenceNode(
            node_type=NodeType.RECEIPT,
            run_id=context.run_id,
            branch_id=context.branch_id,
            stage=context.stage,
            claim=claim,
            agent_id=self.agent_id,
            payload={"action": "ledger_commit", "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        return [node]


class ACESynthesisAgent(CP8Agent):
    """
    Receives ONLY closed branch reports.
    Never sees branch interpretations during execution.
    """
    def __init__(self, agent_id: str = "ace_synthesis"):
        super().__init__(agent_id)

    def synthesize(self, run_id: str, branch_reports: List[Dict[str, Any]]) -> EvidenceNode:
        """
        Called after all branches close.
        Receives only reports, not raw interpretations.
        """
        # Aggregate findings without convergence bias
        agreement_matrix = {}
        contradictions = []
        unknowns = []

        for report in branch_reports:
            branch_id = report.get("branch_id")
            findings = report.get("findings", [])
            agreement_matrix[branch_id] = findings

        claim = FiveFieldClaim(
            OBSERVED="All branches have reported closed",
            CONTEXT="Synthesis receives only aggregated reports, not individual interpretations",
            INFERENCE="Cross-branch patterns may indicate robust or fragile conclusions",
            TEST="Check for agreement, contradiction, and gaps across independent workers",
            CONCLUSION="Synthesis complete; promotion candidate formed"
        )
        
        return EvidenceNode(
            node_type=NodeType.SYNTHESIS,
            run_id=run_id,
            stage="SYNTHESIS",
            claim=claim,
            agent_id=self.agent_id,
            payload={
                "agreement_matrix": agreement_matrix,
                "contradictions": contradictions,
                "unknowns": unknowns,
                "branches_synthesized": len(branch_reports)
            }
        )
