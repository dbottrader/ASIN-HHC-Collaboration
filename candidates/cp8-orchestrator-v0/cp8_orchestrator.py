"""
CP8 Orchestrator
Converts sloppy human input into parallel, stage-guarded, branch-isolated execution.
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from cp8_schema import (
    EvidenceNode, NodeType, FiveFieldClaim, PromotionDecision,
    PromotionVerdict, CP8RunRecord
)
from cp8_storage import CP8Storage
from cp8_kernel import CP8Job, CP8Stage, CP8KernelError
from cp8_agents import (
    AgentContext, EvidenceAgent, ResearchAgent, ChronologyAgent,
    PatternAgent, SkepticAgent, ReplicationAgent, PriorArtAgent,
    BuilderAgent, ArchivistAgent, ACESynthesisAgent
)


class CP8Orchestrator:
    """
    Main entry point.
    /cp8 investigate "Crabwood encoding" -> RUN ID, branches, evidence graph, promotion record.
    """

    def __init__(self, storage_base: Path):
        self.storage = CP8Storage(storage_base)
        self.agents = {
            "evidence": EvidenceAgent("evidence"),
            "research": ResearchAgent("research"),
            "chronology": ChronologyAgent("chronology"),
            "pattern": PatternAgent("pattern"),
            "skeptic": SkepticAgent("skeptic"),
            "replication": ReplicationAgent("replication"),
            "prior_art": PriorArtAgent("prior_art"),
            "builder": BuilderAgent("builder"),
            "archivist": ArchivistAgent("archivist"),
        }
        self.synthesis_agent = ACESynthesisAgent("ace_synthesis")

    def investigate(self, anchor: str, branches: Optional[List[str]] = None) -> str:
        """
        Entry point. Creates a preregistered run, executes branches, synthesizes,
        and stops at the Promotion Gate for human Reality Veto.
        """
        run_id = self._generate_run_id()
        print(f"[CP8] RUN {run_id} preregistered")
        print(f"[CP8] Anchor: {anchor}")

        # 1. Preregister the job in the kernel
        job = CP8Job(run_id=run_id, anchor=anchor)
        job.transition_to(CP8Stage.ARTIFACT.name, {"anchor": anchor})

        # 2. Define branches (default parallel investigation tracks)
        if branches is None:
            branches = [
                "conventional_explanation",
                "encoding_hypothesis", 
                "historical_symbol_comparison",
                "information_theory_analysis",
                "contamination_prior_art_analysis"
            ]

        # 3. Execute branches in isolation
        branch_reports = []
        all_nodes = []

        for branch_id in branches:
            print(f"[CP8] Branch {branch_id} starting...")
            nodes = self._execute_branch(job, branch_id, anchor)
            all_nodes.extend(nodes)
            
            # Collect report for synthesis (no interpretations exposed)
            report = {
                "branch_id": branch_id,
                "findings": [n.sha256() for n in nodes if n.claim],
                "node_count": len(nodes),
                "agent_ids": list(set(n.agent_id for n in nodes if n.agent_id))
            }
            branch_reports.append(report)
            print(f"[CP8] Branch {branch_id} closed. {len(nodes)} nodes.")

        # 4. Force kernel through remaining stages
        for stage in CP8Stage.ordered_names()[1:]:  # Skip ARTIFACT, already done
            if stage == CP8Stage.SYNTHESIS.name:
                continue  # Handled separately
            job.transition_to(stage, {"status": "auto_advance"})

        # 5. ACE Synthesis (only after branches close)
        print("[CP8] Synthesizing closed branch reports...")
        synthesis_node = self.synthesis_agent.synthesize(run_id, branch_reports)
        all_nodes.append(synthesis_node)
        job.transition_to("SYNTHESIS", {"synthesis_hash": synthesis_node.sha256()})

        # 6. Store all evidence nodes
        for node in all_nodes:
            self.storage.store(node.sha256(), node.to_dict(), namespace="objects")

        # 7. Archivist commits the run
        archivist = self.agents["archivist"]
        archivist_nodes = archivist.execute(AgentContext(
            run_id=run_id,
            branch_id="meta",
            artifact={"nodes_committed": len(all_nodes)},
            stage="ARCHIVE"
        ))
        for node in archivist_nodes:
            self.storage.store(node.sha256(), node.to_dict(), namespace="objects")

        # 8. Build run record
        run_record = CP8RunRecord(
            run_id=run_id,
            preregistered_at=job.preregistered_at,
            anchor_claim=FiveFieldClaim(
                OBSERVED=anchor,
                CONTEXT="Preregistered investigation anchor",
                INFERENCE="Systematic multi-branch analysis required",
                TEST="Execute CP8 kernel stages across isolated branches",
                CONCLUSION="Investigation pipeline complete, awaiting promotion"
            ),
            stages_completed=job.stages_completed,
            branch_ids=branches,
            evidence_nodes=[n.sha256() for n in all_nodes],
            synthesis_hash=synthesis_node.sha256(),
            status="STAGES_COMPLETE"
        )

        # 9. STOP at Promotion Gate. No Receipt = No Promotion.
        # The gate creates a HOLD decision by default.
        # Human (or authorized veto key) must call promote() to change this.
        gate_decision = PromotionDecision(
            run_id=run_id,
            verdict=PromotionVerdict.HOLD,
            target_node_hash=synthesis_node.sha256(),
            reason="Awaiting Reality Veto. Human judgment required before promotion.",
            gate_keeper="CP8_KERNEL"
        )

        self.storage.store(gate_decision.sha256(), {
            "hash": gate_decision.sha256(),
            "run_id": gate_decision.run_id,
            "verdict": gate_decision.verdict.value,
            "target_node_hash": gate_decision.target_node_hash,
            "gate_timestamp": gate_decision.gate_timestamp,
            "gate_keeper": gate_decision.gate_keeper,
            "reason": gate_decision.reason,
            "canonical": gate_decision.canonical()
        }, namespace="objects")

        run_record.promotion_hash = gate_decision.sha256()
        run_record.status = "SYNTHESIZED"

        # 10. Persist run record
        self.storage.store_run(run_id, {
            "run_id": run_record.run_id,
            "preregistered_at": run_record.preregistered_at,
            "anchor_claim": run_record.anchor_claim.canonical(),
            "stages_completed": run_record.stages_completed,
            "branch_ids": run_record.branch_ids,
            "evidence_nodes": run_record.evidence_nodes,
            "synthesis_hash": run_record.synthesis_hash,
            "promotion_hash": run_record.promotion_hash,
            "merkle_root": run_record.merkle_root(),
            "status": run_record.status,
        })

        print(f"[CP8] RUN {run_id} complete. Status: {run_record.status}")
        print(f"[CP8] Evidence nodes: {len(all_nodes)}")
        print(f"[CP8] Merkle root: {run_record.merkle_root()}")
        print(f"[CP8] Promotion Gate: {gate_decision.verdict.value}")
        print(f"[CP8] Use promote('{run_id}', verdict, reason) to apply Reality Veto.")

        return run_id

    def _execute_branch(self, job: CP8Job, branch_id: str, anchor: str) -> List[EvidenceNode]:
        """
        Execute specialist agents on a branch.
        Agents receive ONLY artifact + measurements + prior receipts.
        No interpretation from other branches.
        """
        nodes = []
        
        # Build artifact context
        artifact = {"anchor": anchor, "branch": branch_id}
        
        # Execute non-adversarial agents in parallel (simulated sequentially here)
        for agent_name in ["evidence", "research", "chronology", "pattern", "prior_art"]:
            agent = self.agents[agent_name]
            context = AgentContext(
                run_id=job.run_id,
                branch_id=branch_id,
                artifact=artifact,
                stage=job.current_stage
            )
            result = agent.execute(context)
            nodes.extend(result)

        # Execute adversarial agent
        skeptic = self.agents["skeptic"]
        context = AgentContext(
            run_id=job.run_id,
            branch_id=branch_id,
            artifact=artifact,
            stage="CHALLENGE"
        )
        nodes.extend(skeptic.execute(context))

        # Replication attempt
        replicator = self.agents["replication"]
        context = AgentContext(
            run_id=job.run_id,
            branch_id=branch_id,
            artifact=artifact,
            stage="REPLICATION"
        )
        nodes.extend(replicator.execute(context))

        # Builder (only if branch produces something actionable - stubbed here)
        builder = self.agents["builder"]
        context = AgentContext(
            run_id=job.run_id,
            branch_id=branch_id,
            artifact=artifact,
            stage="ARTIFACT"
        )
        nodes.extend(builder.execute(context))

        return nodes

    def promote(self, run_id: str, verdict: str, reason: str, gate_keeper: str = "HUMAN_VETO") -> PromotionDecision:
        """
        Reality Veto / Promotion Gate.
        Human (or authorized key) decides PASS, HOLD, or FAIL.
        Creates a signed decision record.
        """
        # Load existing run
        run_data = self.storage.retrieve_run(run_id)
        if not run_data:
            raise ValueError(f"Run {run_id} not found")

        if run_data.get("status") not in ["STAGES_COMPLETE", "SYNTHESIZED"]:
            raise PermissionError(f"Cannot promote run with status {run_data.get('status')}")

        # Validate verdict
        try:
            promotion_verdict = PromotionVerdict(verdict.upper())
        except ValueError:
            raise ValueError(f"Invalid verdict: {verdict}. Use PASS, HOLD, or FAIL.")

        target_hash = run_data.get("synthesis_hash")
        if not target_hash:
            raise ValueError("No synthesis hash found for promotion")

        decision = PromotionDecision(
            run_id=run_id,
            verdict=promotion_verdict,
            target_node_hash=target_hash,
            reason=reason,
            gate_keeper=gate_keeper
        )

        # Store decision
        self.storage.store(decision.sha256(), {
            "hash": decision.sha256(),
            "run_id": decision.run_id,
            "verdict": decision.verdict.value,
            "target_node_hash": decision.target_node_hash,
            "gate_timestamp": decision.gate_timestamp,
            "gate_keeper": decision.gate_keeper,
            "reason": decision.reason,
            "canonical": decision.canonical()
        }, namespace="objects")

        # Update run record
        run_data["promotion_hash"] = decision.sha256()
        run_data["status"] = "PROMOTED" if promotion_verdict == PromotionVerdict.PASS else "CLOSED"
        run_data["promotion_verdict"] = promotion_verdict.value
        run_data["promotion_reason"] = reason
        run_data["promotion_gate_keeper"] = gate_keeper
        run_data["promotion_timestamp"] = datetime.now(timezone.utc).isoformat()

        self.storage.store_run(run_id, run_data)

        print(f"[CP8] Promotion Gate decision for {run_id}: {promotion_verdict.value}")
        print(f"[CP8] Gate keeper: {gate_keeper}")
        print(f"[CP8] Reason: {reason}")

        return decision

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.storage.retrieve_run(run_id)

    def get_node(self, content_hash: str) -> Optional[Dict[str, Any]]:
        return self.storage.retrieve(content_hash, namespace="objects")

    def _generate_run_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        uid = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:8]
        return f"CP8-{timestamp}-{uid}"
