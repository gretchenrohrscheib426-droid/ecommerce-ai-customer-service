import json
import os
import subprocess
import sys
import unittest


class BootstrapTest(unittest.TestCase):
    def test_import_never_loads_model_or_connectors(self):
        code = "import sys,ecommerce_graph_agent.cli; assert not ({'torch','transformers','neo4j','pymysql'} & set(sys.modules))"
        subprocess.run([sys.executable, "-c", code], check=True)

    def test_doctor_does_not_expose_key(self):
        env = dict(os.environ, DEEPSEEK_API_KEY="unit-test-not-a-real-secret")
        run = subprocess.run(
            [sys.executable, "-m", "ecommerce_graph_agent", "doctor"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn(env["DEEPSEEK_API_KEY"], run.stdout)
        payload = json.loads(run.stdout)
        self.assertTrue(payload["deepseek_key_present"])
        self.assertFalse(payload["online_enabled"])


if __name__ == "__main__":
    unittest.main()
