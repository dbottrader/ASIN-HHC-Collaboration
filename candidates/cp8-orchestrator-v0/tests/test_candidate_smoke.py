import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


CANDIDATE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CANDIDATE_ROOT))

from cp8_agents import ACESynthesisAgent
from cp8_orchestrator import CP8Orchestrator


class CandidateSmokeTest(unittest.TestCase):
    def test_investigate_reports_missing_synthesis_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ACESynthesisAgent, "__abstractmethods__", frozenset()):
                orchestrator = CP8Orchestrator(Path(temp_dir) / "cp8-data")

                with self.assertRaisesRegex(AttributeError, "SYNTHESIS"):
                    orchestrator.investigate("smoke", branches=["isolated-smoke"])


if __name__ == "__main__":
    unittest.main()
