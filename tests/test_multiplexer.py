#!/usr/bin/env python3
"""Integration tests for src/multiplexer install and dispatch."""

import contextlib
import errno
import importlib.util
import os
import pty
import select
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unittest
import unittest.mock
from importlib.machinery import SourceFileLoader


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(REPO_ROOT, "src", "multiplexer")


def _load_script():
    loader = SourceFileLoader("multiplexer_hook", SCRIPT)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _read_until(fd, needle, timeout=2.0):
    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], deadline - time.monotonic())
        if not ready:
            break
        try:
            chunk = os.read(fd, 1024)
        except OSError as exc:
            if exc.errno == errno.EIO:
                break
            raise
        if not chunk:
            break
        buf += chunk
        if needle in buf:
            return buf
    raise AssertionError("timed out waiting for %r, got %r" % (needle, buf))


def _reap_pty_child(pid, fd, timeout=2.0):
    """Drain PTY master *fd* until *pid* exits.

    Linux raises EIO once the slave closes. That is the child exiting, not a
    hang — keep going and reap it.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                os.read(fd, 1024)
            except OSError as exc:
                if exc.errno != errno.EIO:
                    raise
        waited = os.waitpid(pid, os.WNOHANG)
        if waited != (0, 0):
            return waited[1]
    waited = os.waitpid(pid, os.WNOHANG)
    if waited != (0, 0):
        return waited[1]
    raise AssertionError("interactive hook did not exit after tty reply")


class ReapPtyChildTests(unittest.TestCase):
    def test_linux_eio_means_child_exited(self):
        pid = 4242
        fd = 7
        with (
            unittest.mock.patch("test_multiplexer.select.select", return_value=([fd], [], [])),
            unittest.mock.patch(
                "test_multiplexer.os.read",
                side_effect=OSError(errno.EIO, "Input/output error"),
            ),
            unittest.mock.patch("test_multiplexer.os.waitpid", return_value=(pid, 0)) as waitpid,
        ):
            status = _reap_pty_child(pid, fd, timeout=1.0)
        self.assertEqual(status, 0)
        waitpid.assert_called()


def _run(args, cwd, env=None, input_bytes=None):
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class HookTypeTests(unittest.TestCase):
    def test_uses_invoked_name_not_source_file(self):
        mux = _load_script()
        self.assertEqual(
            mux.hook_type_from_invocation("/repo/.git/hooks/pre-commit"),
            "pre-commit",
        )
        self.assertEqual(
            mux.hook_type_from_invocation("/opt/toolbox/src/multiplexer"),
            "multiplexer",
        )
        self.assertEqual(
            mux.check_hook_type(argv0="/repo/.git/hooks/commit-msg"),
            "commit-msg",
        )


class MultiplexerRepoTests(unittest.TestCase):
    def setUp(self):
        work_tmp = os.path.join(REPO_ROOT, ".test-tmp")
        os.makedirs(work_tmp, exist_ok=True)
        self.repo = tempfile.mkdtemp(prefix="mux-", dir=work_tmp)
        self.addCleanup(shutil.rmtree, self.repo)
        init = _run(["git", "init"], cwd=self.repo)
        self.assertEqual(init.returncode, 0, init.stderr.decode("utf-8", "replace"))
        _run(["git", "config", "user.email", "mux@example.test"], cwd=self.repo)
        _run(["git", "config", "user.name", "Mux Tester"], cwd=self.repo)
        os.makedirs(os.path.join(self.repo, ".git", "hooks"), exist_ok=True)
        self.record_dir = os.path.join(self.repo, ".hook-records")
        os.mkdir(self.record_dir)
        self.env = os.environ.copy()
        self.env["RECORD_DIR"] = self.record_dir

    def _hooks_dir(self, hook_type):
        path = os.path.join(self.repo, "hooks", hook_type)
        os.makedirs(path, exist_ok=True)
        return path

    def _write_recorder(self, hook_type, name):
        path = os.path.join(self._hooks_dir(hook_type), name)
        with open(path, "w") as handle:
            handle.write(
                "#!/bin/sh\n"
                'out="${RECORD_DIR}/$(basename "$0")"\n'
                'printf \'%s\\n\' "$*" > "$out.argv"\n'
                'cat > "$out.stdin"\n'
            )
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def _write_tty_prompt(self, hook_type, name):
        path = os.path.join(self._hooks_dir(hook_type), name)
        with open(path, "w") as handle:
            handle.write(
                "#!/bin/sh\n"
                "printf 'Are you sure? [Yes/No] ' >&2\n"
                "exec < /dev/tty\n"
                "read -r response\n"
                'printf \'%s\\n\' "$response" > "${RECORD_DIR}/$(basename "$0").answer"\n'
                "case $response in\n"
                "  [yY]|[yY][eE][sS]) exit 0 ;;\n"
                "  *) exit 1 ;;\n"
                "esac\n"
            )
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def _write_exiter(self, hook_type, name, code):
        path = os.path.join(self._hooks_dir(hook_type), name)
        with open(path, "w") as handle:
            handle.write("#!/bin/sh\nexit %d\n" % code)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def _install_copy(self, hook_name):
        dest = os.path.join(self.repo, ".git", "hooks", hook_name)
        shutil.copy(SCRIPT, dest)
        os.chmod(dest, os.stat(dest).st_mode | stat.S_IEXEC)
        return dest

    def _install_symlink(self, hook_name):
        dest = os.path.join(self.repo, ".git", "hooks", hook_name)
        os.symlink(os.path.abspath(SCRIPT), dest)
        return dest

    def _invoke(self, hook_path, args=None, stdin=b""):
        return _run(
            [hook_path] + list(args or []),
            cwd=self.repo,
            env=self.env,
            input_bytes=stdin,
        )

    def test_copy_named_pre_commit_runs_subhooks(self):
        self._write_recorder("pre-commit", "01-record")
        hook = self._install_copy("pre-commit")
        result = self._invoke(hook)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        argv_path = os.path.join(self.record_dir, "01-record.argv")
        self.assertTrue(os.path.isfile(argv_path), result.stderr.decode("utf-8", "replace"))

    def test_symlink_named_pre_commit_runs_subhooks(self):
        self._write_recorder("pre-commit", "01-record")
        hook = self._install_symlink("pre-commit")
        result = self._invoke(hook)
        self.assertEqual(
            result.returncode,
            0,
            "symlink install failed:\nstdout=%s\nstderr=%s"
            % (result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")),
        )
        argv_path = os.path.join(self.record_dir, "01-record.argv")
        self.assertTrue(os.path.isfile(argv_path), result.stderr.decode("utf-8", "replace"))

    def test_symlink_forwards_hook_arguments(self):
        self._write_recorder("commit-msg", "01-record")
        hook = self._install_symlink("commit-msg")
        result = self._invoke(hook, args=[".git/COMMIT_EDITMSG"])
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        with open(os.path.join(self.record_dir, "01-record.argv")) as handle:
            self.assertEqual(handle.read().rstrip("\n"), ".git/COMMIT_EDITMSG")

    def test_symlink_replays_stdin_to_each_subhook(self):
        self._write_recorder("pre-push", "01-one")
        self._write_recorder("pre-push", "02-two")
        hook = self._install_symlink("pre-push")
        payload = b"refs/heads/master abc refs/heads/master def\n"
        result = self._invoke(hook, args=["origin", "git@example.test:repo.git"], stdin=payload)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        for name in ("01-one", "02-two"):
            with open(os.path.join(self.record_dir, name + ".stdin"), "rb") as handle:
                self.assertEqual(handle.read(), payload)
            with open(os.path.join(self.record_dir, name + ".argv")) as handle:
                self.assertEqual(handle.read().rstrip("\n"), "origin git@example.test:repo.git")

    def test_failed_subhook_aborts_with_its_exit_code(self):
        self._write_exiter("pre-commit", "01-fail", 7)
        self._write_recorder("pre-commit", "02-later")
        hook = self._install_copy("pre-commit")
        result = self._invoke(hook)
        self.assertEqual(result.returncode, 7)
        self.assertFalse(os.path.isfile(os.path.join(self.record_dir, "02-later.argv")))

    def test_symlink_pre_merge_commit_is_accepted(self):
        self._write_recorder("pre-merge-commit", "01-record")
        hook = self._install_symlink("pre-merge-commit")
        result = self._invoke(hook)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertTrue(os.path.isfile(os.path.join(self.record_dir, "01-record.argv")))

    def test_interactive_hook_shows_prompt_before_tty_reply(self):
        self._write_tty_prompt("pre-commit", "01-ask")
        hook = self._install_copy("pre-commit")

        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.repo)
            os.execve(hook, [hook], self.env)
            os._exit(127)

        status = None
        try:
            _read_until(fd, b"Are you sure?")
            os.write(fd, b"yes\r")
            status = _reap_pty_child(pid, fd)
        except Exception:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            raise
        finally:
            os.close(fd)

        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 0)
        with open(os.path.join(self.record_dir, "01-ask.answer")) as handle:
            self.assertEqual(handle.read().strip(), "yes")


if __name__ == "__main__":
    unittest.main()
