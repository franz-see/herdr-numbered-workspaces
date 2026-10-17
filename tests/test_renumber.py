"""Black-box tests: execute the real plugin against a fake Herdr CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def workspace(identifier, number, *, repo=None, linked=False, num=None):
    return {
        "workspace_id": identifier,
        "number": number,
        "tokens": {} if num is None else {"num": num},
        "worktree": None if repo is None else {
            "repo_key": repo,
            "is_linked_worktree": linked,
        },
    }


class RenumberTests(unittest.TestCase):
    def run_plugin(self, workspaces, *, direct=False, failure="", expected_status=0):
        with tempfile.TemporaryDirectory(prefix="numbered workspaces test ") as tmp:
            directory = Path(tmp)
            response = directory / "response.json"
            calls = directory / "calls.jsonl"
            executable = directory / "fake herdr"
            response.write_text(json.dumps({"result": {"workspaces": workspaces}}))
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "with open(os.environ['TEST_CALLS'], 'a') as log:\n"
                "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                "if sys.argv[1:] == ['workspace', 'list']:\n"
                "    if os.environ['TEST_FAILURE'] == 'list': sys.exit(7)\n"
                "    print(Path(os.environ['TEST_RESPONSE']).read_text())\n"
                "elif sys.argv[1:3] == ['workspace', 'report-metadata']:\n"
                "    if os.environ['TEST_FAILURE'] == 'report': sys.exit(7)\n"
                "else:\n"
                "    sys.exit('unexpected command')\n"
            )
            executable.chmod(0o755)
            env = {
                **os.environ,
                "HERDR_BIN_PATH": str(executable),
                "TEST_RESPONSE": str(response),
                "TEST_CALLS": str(calls),
                "TEST_FAILURE": failure,
            }
            command = [str(ROOT / "renumber.sh")]
            if not direct:
                command.insert(0, "bash")
            result = subprocess.run(
                command,
                cwd=directory,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, expected_status, result.stderr)
            return [json.loads(line) for line in calls.read_text().splitlines()]

    def assert_numbers(self, workspaces, expected):
        calls = self.run_plugin(workspaces)
        self.assertEqual(calls[0], ["workspace", "list"])
        self.assertEqual(
            calls[1:],
            [
                ["workspace", "report-metadata", identifier,
                 "--source", "numbered-workspaces", "--token", f"num={number}"]
                for identifier, number in expected
            ],
        )

    def test_non_contiguous_worktrees_follow_their_parent(self):
        # The reported failure: flat workspace 7 is sidebar entry 2.
        spaces = [workspace("main", 1, repo="example-repo")]
        spaces += [workspace(f"other-{i}", i) for i in range(2, 7)]
        spaces += [workspace("worktree", 7, repo="example-repo", linked=True)]
        self.assert_numbers(
            spaces,
            [("main", 1), ("worktree", 2)]
            + [(f"other-{i}", i + 1) for i in range(2, 7)],
        )

    def test_flat_workspaces_keep_their_order(self):
        self.assert_numbers(
            [workspace("one", 1), workspace("two", 2)],
            [("one", 1), ("two", 2)],
        )

    def test_parent_moves_before_children_at_first_group_member(self):
        self.assert_numbers(
            [workspace("before", 1),
             workspace("child", 2, repo="repo", linked=True),
             workspace("between", 3),
             workspace("parent", 4, repo="repo")],
            [("before", 1), ("parent", 2), ("child", 3), ("between", 4)],
        )

    def test_interleaved_repositories_preserve_group_and_child_order(self):
        self.assert_numbers(
            [workspace("a-main", 1, repo="a"),
             workspace("b-child", 2, repo="b", linked=True),
             workspace("plain", 3),
             workspace("a-child-1", 4, repo="a", linked=True),
             workspace("b-main", 5, repo="b"),
             workspace("a-child-2", 6, repo="a", linked=True)],
            [("a-main", 1), ("a-child-1", 2), ("a-child-2", 3),
             ("b-main", 4), ("b-child", 5), ("plain", 6)],
        )

    def test_linked_worktrees_without_a_parent_stay_flat(self):
        self.assert_numbers(
            [workspace("child-1", 1, repo="repo", linked=True),
             workspace("plain", 2),
             workspace("child-2", 3, repo="repo", linked=True)],
            [("child-1", 1), ("plain", 2), ("child-2", 3)],
        )

    def test_single_repository_member_stays_flat(self):
        self.assert_numbers(
            [workspace("plain", 1), workspace("main", 2, repo="repo")],
            [("plain", 1), ("main", 2)],
        )

    def test_missing_worktree_and_tokens_are_supported(self):
        self.assert_numbers([{"workspace_id": "old", "number": 1}], [("old", 1)])

    def test_matching_grouped_tokens_need_only_one_list_call(self):
        self.assert_numbers(
            [workspace("main", 1, repo="repo", num="1"),
             workspace("plain", 2, num="3"),
             workspace("child", 3, repo="repo", linked=True, num="2")],
            [],
        )

    def test_only_changed_grouped_tokens_are_published(self):
        self.assert_numbers(
            [workspace("main", 1, repo="repo", num="1"),
             workspace("plain", 2, num="2"),
             workspace("child", 3, repo="repo", linked=True, num="3")],
            [("child", 2), ("plain", 3)],
        )

    def test_numbers_continue_past_nine(self):
        self.assert_numbers(
            [workspace(f"w{i}", i) for i in range(1, 13)],
            [(f"w{i}", i) for i in range(1, 13)],
        )

    def test_repository_keys_and_workspace_ids_are_not_shell_code(self):
        identifier = "worktree with spaces; $(exit 99)"
        repo = "repo.with/[brackets] and spaces"
        self.assert_numbers(
            [workspace("main", 1, repo=repo),
             workspace("other", 2),
             workspace(identifier, 3, repo=repo, linked=True)],
            [("main", 1), (identifier, 2), ("other", 3)],
        )

    def test_empty_session_only_lists_workspaces(self):
        self.assert_numbers([], [])

    def test_list_failure_is_propagated_without_metadata_writes(self):
        calls = self.run_plugin([], failure="list", expected_status=7)
        self.assertEqual(calls, [["workspace", "list"]])

    def test_metadata_failure_stops_the_run(self):
        calls = self.run_plugin(
            [workspace("first", 1), workspace("second", 2)],
            failure="report", expected_status=7,
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][2], "first")

    def test_manifest_entrypoint_runs_directly_on_nixos(self):
        self.assertEqual(self.run_plugin([], direct=True), [["workspace", "list"]])


if __name__ == "__main__":
    unittest.main()
