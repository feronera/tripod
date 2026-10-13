"""Test added at review for change 011 (approved by the PO while tests/test_gate4_artifacts.py stays locked): a
Decision line with words after the decision, as agents write it, still counts."""
from tests import test_gate4_artifacts as g4
from tests import test_pod_scripts as scripts


class DecisionWordsTests(g4.Gate4Tests):
    def test_reject_with_more_words_refuses_gate4(self):
        c = self.ready(acceptance="# Acceptance\n\n## Decision\nDecision: reject (proposed; SuperBiz to confirm)\n")
        res = self.approve(c, 4, scripts.DEV, expect_ok=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("  - acceptance.md decides reject", res.stderr)


for _name in [n for n in dir(g4.Gate4Tests) if n.startswith("test_")]:
    setattr(DecisionWordsTests, _name, None)
