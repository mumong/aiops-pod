"""Exercise real c06 bootstrap behavior, independent of Kubernetes status labels."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from .helpers import ROOT, render


class StartupConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs = list(yaml.safe_load_all(render('cases/crashloop-runtime')))
        cls.deployment = next(d for d in docs if d['kind'] == 'Deployment' and d['metadata']['name'] == 'workload')
        cls.source = next(d for d in docs if d['metadata']['name'] == 'workload-startup')['data']['bootstrap.py']

    def run_bootstrap(self, env):
        with patch.dict(os.environ, env, clear=True), patch('runpy.run_path') as start:
            exec(compile(self.source, 'bootstrap.py', 'exec'), {})
            start.assert_called_once_with('/opt/aiops/server.py', run_name='__main__')
            return os.environ['HTTP_PORT']

    def test_rendered_wrong_variable_exits_before_service_starts(self):
        app = self.deployment['spec']['template']['spec']['containers'][0]
        env = {v['name']: v['value'] for v in app['env'] if 'value' in v}
        with patch('builtins.print') as log, self.assertRaises(SystemExit) as result:
            self.run_bootstrap(env)
        self.assertEqual(result.exception.code, 2)
        self.assertIn('APP_CONFIG_PATH is required', log.call_args.args[0])

    def test_correct_name_loads_real_config_and_controls_port(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'app.json'
            config.write_text(json.dumps({'http_port': 18080}))
            self.assertEqual(self.run_bootstrap({'APP_CONFIG_PATH': str(config)}), '18080')

    def test_renaming_variable_does_not_bypass_missing_or_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'app.json'
            for content in (None, '{invalid', '{}', '{"http_port": 0}'):
                if content is not None:
                    config.write_text(content)
                with self.subTest(content=content), self.assertRaises(SystemExit) as result:
                    self.run_bootstrap({'APP_CONFIG_PATH': str(config)})
                self.assertEqual(result.exception.code, 2)
