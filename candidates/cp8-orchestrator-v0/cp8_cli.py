#!/usr/bin/env python3
"""
CP8 Command Line Interface
/cp8 investigate "Crabwood encoding"
"""

import argparse
import sys
from pathlib import Path

from cp8_orchestrator import CP8Orchestrator


def main():
    parser = argparse.ArgumentParser(description="CP8 Kernel Orchestrator")
    parser.add_argument("--data-dir", default="/opt/asin-hhc-bridge/cp8_data", help="Storage path")
    subparsers = parser.add_subparsers(dest="command")

    # investigate
    investigate_parser = subparsers.add_parser("investigate", help="Start a CP8 investigation")
    investigate_parser.add_argument("anchor", help="The hypothesis or artifact to investigate")
    investigate_parser.add_argument("--branches", nargs="+", help="Custom branch IDs")

    # promote
    promote_parser = subparsers.add_parser("promote", help="Apply Reality Veto at Promotion Gate")
    promote_parser.add_argument("run_id", help="Run ID to promote")
    promote_parser.add_argument("verdict", choices=["PASS", "HOLD", "FAIL"], help="Promotion verdict")
    promote_parser.add_argument("--reason", default="No reason provided", help="Decision rationale")
    promote_parser.add_argument("--keeper", default="HUMAN_VETO", help="Gate keeper identity")

    # status
    status_parser = subparsers.add_parser("status", help="Check run status")
    status_parser.add_argument("run_id", help="Run ID to query")

    # node
    node_parser = subparsers.add_parser("node", help="Retrieve evidence node by hash")
    node_parser.add_argument("hash", help="Content hash of the node")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    orch = CP8Orchestrator(Path(args.data_dir))

    if args.command == "investigate":
        run_id = orch.investigate(args.anchor, branches=args.branches)
        print(f"\nRUN_ID={run_id}")

    elif args.command == "promote":
        decision = orch.promote(args.run_id, args.verdict, args.reason, args.keeper)
        print(f"\nDECISION_HASH={decision.sha256()}")

    elif args.command == "status":
        run = orch.get_run(args.run_id)
        if run:
            import json
            print(json.dumps(run, indent=2))
        else:
            print(f"Run {args.run_id} not found", file=sys.stderr)
            sys.exit(1)

    elif args.command == "node":
        node = orch.get_node(args.hash)
        if node:
            import json
            print(json.dumps(node, indent=2))
        else:
            print(f"Node {args.hash} not found", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
