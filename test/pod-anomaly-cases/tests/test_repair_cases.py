import importlib.util
import subprocess
import sys
import unittest
from unittest.mock import patch

from .helpers import ROOT

sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('repair_cases', ROOT / 'scripts/repair_cases.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.pop(0)


class RepairSuiteTests(unittest.TestCase):
    def test_clean_is_limited_to_four_selected_namespaces(self):
        with patch.object(module, 'command', return_value='test-context'), patch.object(module, 'clean') as clean:
            module.main(['clean'])
        self.assertEqual([call.args[0]['namespace'] for call in clean.call_args_list],
                         ['aiops-case-04', 'aiops-case-06', 'aiops-case-09', 'aiops-case-11'])

    def test_invalid_manifest_stops_before_any_cleanup_or_deploy(self):
        with patch.object(module, 'command', side_effect=subprocess.CalledProcessError(1, 'kubectl')), \
             patch.object(module, 'clean') as clean, patch.object(module, 'deploy') as deploy:
            with self.assertRaises(subprocess.CalledProcessError):
                module.reset(module.selected_cases(), 10)
        clean.assert_not_called()
        deploy.assert_not_called()

    def test_timeout_is_not_reported_as_success(self):
        with patch.object(module, 'resolve_workload_pods', return_value=[]), patch.object(module, 'status'), \
             patch.object(module.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaisesRegex(RuntimeError, 'c04, c06, c09, c11'):
                module.wait_for_faults(module.selected_cases(), 10)
