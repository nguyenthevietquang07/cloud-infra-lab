import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kubernetes_manifest_check.py"


spec = importlib.util.spec_from_file_location("kubernetes_manifest_check", SCRIPT)
kubernetes_manifest_check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(kubernetes_manifest_check)


class KubernetesManifestTests(unittest.TestCase):
    def test_manifest_has_expected_runtime_controls(self):
        report = kubernetes_manifest_check.inspect_manifest()

        self.assertTrue(report["passed"], report)
        self.assertIn("Deployment", report["kinds"])
        self.assertIn("Service", report["kinds"])
        self.assertTrue(report["checks"]["has_health_probes"])
        self.assertTrue(report["checks"]["has_resource_bounds"])


if __name__ == "__main__":
    unittest.main()
