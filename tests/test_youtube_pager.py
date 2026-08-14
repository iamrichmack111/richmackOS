import importlib.util
import io
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "youtube_summarize",
    ROOT / "youtube_summarize.py",
)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class PagerTests(unittest.TestCase):
    def test_auto_prefers_bat(self):
        with mock.patch.object(MOD.sys.stdout, "isatty", return_value=True), \
             mock.patch.object(MOD.shutil, "which", side_effect=lambda x: f"/usr/bin/{x}"), \
             mock.patch.object(MOD.subprocess, "run") as run:
            MOD.page_text("hello\n", pager="auto")
            cmd = run.call_args.args[0]
            self.assertEqual(cmd[0], "/usr/bin/bat")
            self.assertIn("--paging=always", cmd)
            self.assertEqual(run.call_args.kwargs["input"], "hello\n")

    def test_auto_falls_back_to_less_R(self):
        def which(name):
            return None if name == "bat" else "/usr/bin/less"

        with mock.patch.object(MOD.sys.stdout, "isatty", return_value=True), \
             mock.patch.object(MOD.shutil, "which", side_effect=which), \
             mock.patch.object(MOD.subprocess, "run") as run:
            MOD.page_text("hello\n", pager="auto")
            self.assertEqual(run.call_args.args[0], ["/usr/bin/less", "-R"])

    def test_redirected_output_does_not_spawn_pager(self):
        fake_stdout = io.StringIO()
        with mock.patch.object(MOD.sys, "stdout", fake_stdout), \
             mock.patch.object(MOD.subprocess, "run") as run:
            MOD.page_text("hello\n", pager="auto")
            run.assert_not_called()
            self.assertEqual(fake_stdout.getvalue(), "hello\n")


if __name__ == "__main__":
    unittest.main()
