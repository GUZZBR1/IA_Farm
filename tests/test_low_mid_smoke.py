from __future__ import annotations

import unittest

from run_low_mid_smoke import REQUIRED_MARKERS, _missing_markers


class LowMidSmokeTests(unittest.TestCase):
    def test_current_portuguese_cli_markers_are_required(self):
        output = "[SISTEMA] IA_FARM_MOCK=1\nDemonstração concluída\nEncerrando a simulação."

        self.assertEqual(_missing_markers(output), [])
        self.assertIn("Demonstração concluída", REQUIRED_MARKERS)

    def test_missing_cli_marker_fails_with_precise_diagnostic(self):
        output = "IA_FARM_MOCK=1\nEncerrando a simulação"

        self.assertEqual(_missing_markers(output), ["Demonstração concluída"])


if __name__ == "__main__":
    unittest.main()
