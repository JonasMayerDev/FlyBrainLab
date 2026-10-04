"""Process-only credential and bounded free-tier configuration checks."""
import contextlib
import io
import os
import unittest
from unittest.mock import patch

from scripts import with_credentials


class CredentialsHelperTests(unittest.TestCase):
    def run_helper(self, options, settings):
        output = io.StringIO()
        calls = []

        def child(command, *, cwd, env):
            calls.append((command, dict(env)))
            return 0

        with patch.dict(os.environ, settings, clear=True), \
             patch("sys.argv", ["with_credentials.py", *options, "--", "fixture-command"]), \
             patch.object(with_credentials.subprocess, "call", side_effect=child), \
             patch("sys.stdin.isatty", return_value=False), \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = with_credentials.main()
        return result, calls, output.getvalue()

    def test_mcp_uses_only_environment_and_caps_confirmed_free_attempts(self):
        result, calls, output = self.run_helper(["--brightdata-mcp"], {
            "BRIGHTDATA_API_KEY": "UNIT_TEST_KEY_NEVER_REAL",
            "BRIGHTDATA_FREE_REQUEST_ALLOWANCE": "5000",
            "BRIGHTDATA_MAX_REQUESTS": "10",
        })
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        command, settings = calls[0]
        self.assertEqual(command, ["fixture-command"])
        self.assertEqual(settings["BRIGHTDATA_TRANSPORT"], "mcp")
        self.assertEqual(settings["BRIGHTDATA_MAX_REQUESTS"], "2")
        self.assertEqual(settings["BRIGHTDATA_MAX_COST_USD"], "0")
        self.assertEqual(settings["BRIGHTDATA_ESTIMATED_REQUEST_COST_USD"], "0")
        self.assertNotIn("BRIGHTDATA_SERP_ZONE", settings)
        self.assertNotIn("UNIT_TEST_KEY_NEVER_REAL", output)

    def test_single_remaining_free_request_is_respected(self):
        result, calls, _ = self.run_helper(["--brightdata-mcp"], {
            "BRIGHTDATA_API_KEY": "UNIT_TEST_KEY_NEVER_REAL",
            "BRIGHTDATA_FREE_REQUEST_ALLOWANCE": "1",
        })
        self.assertEqual(result, 0)
        self.assertEqual(calls[0][1]["BRIGHTDATA_MAX_REQUESTS"], "1")

    def test_missing_or_invalid_free_confirmation_does_not_launch(self):
        for value in (None, "0", "-1", "invalid"):
            with self.subTest(value=value):
                settings = {"BRIGHTDATA_API_KEY": "UNIT_TEST_KEY_NEVER_REAL"}
                if value is not None:
                    settings["BRIGHTDATA_FREE_REQUEST_ALLOWANCE"] = value
                result, calls, output = self.run_helper(["--brightdata-mcp"], settings)
                self.assertEqual(result, 2)
                self.assertEqual(calls, [])
                self.assertNotIn("UNIT_TEST_KEY_NEVER_REAL", output)

    def test_missing_key_does_not_launch_noninteractive_process(self):
        result, calls, _ = self.run_helper(["--brightdata-mcp"], {
            "BRIGHTDATA_FREE_REQUEST_ALLOWANCE": "5000",
        })
        self.assertEqual(result, 2)
        self.assertEqual(calls, [])

    def test_rest_and_mcp_options_are_mutually_exclusive(self):
        for rest_option in ("--brightdata", "--unlocker"):
            with self.subTest(rest_option=rest_option), self.assertRaises(SystemExit) as error:
                self.run_helper(["--brightdata-mcp", rest_option], {})
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
