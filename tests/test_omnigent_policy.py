import unittest
from scripts.omnigent_policies import bounded_tool_access
from scripts.omnigent_tools import read_local_artifact

class PolicyTests(unittest.TestCase):
    def test_synthetic_start_gate_and_required_lifecycle(self):
        for name in ('sys_agent_start', 'sys_session_send', 'sys_read_inbox', 'run_frozen_experiment'):
            self.assertEqual(bounded_tool_access({'type':'tool_call','data':{'name':name}})['result'],'ALLOW')
    def test_arbitrary_os_and_publication_denied(self):
        for name in ('sys_os_shell','exec_command','deploy','sys_call_async'):
            self.assertEqual(bounded_tool_access({'type':'tool_call','data':{'name':name}})['result'],'DENY')
    def test_async_cannot_escape_scope(self):
        self.assertEqual(bounded_tool_access({'type':'tool_call','data':{'name':'sys_call_async','arguments':{'tool':'sys_os_shell'}}})['result'],'DENY')
    def test_read_design_seal_without_general_file_access(self):
        result=read_local_artifact('research/designs/dng02-input-v1.sha256')
        self.assertEqual(result['status'],'ok')
        with self.assertRaises(ValueError): read_local_artifact('research/../.env')
