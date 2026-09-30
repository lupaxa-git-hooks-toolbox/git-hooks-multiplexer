<p align="center">
    <a href="https://github.com/lupaxa-git-hooks-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/git-hooks-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Git Hooks Multiplexer</h1>

One self-contained script. Copy it into `.git/hooks` — no pip install, no
package. It runs every executable under `hooks/<hook-type>/` at the
repository root, in name order, and stops on the first failure.

The hook type is the name Git invoked (`pre-commit`, `commit-msg`,
`pre-push`, …), not the source file name. A symlink named `pre-commit`
stays `pre-commit`; the real path is not used. Most subhooks just run; a
subhook that needs a human should read `/dev/tty`.

## Install

Python 3.13 or newer on `PATH`. The only file you need is `src/multiplexer`.

[Setup Git Hooks](https://github.com/lupaxa-git-hooks-toolbox/setup-git-hooks)
(`setup-hooks`) can install that file into `.git/hooks` automatically. Point
`hooks/multiplexer-config.yml` at this repository and run `setup-hooks`; the
CLI copies the script unless you skip that step. See that project's
[README](https://github.com/lupaxa-git-hooks-toolbox/setup-git-hooks#readme).

To install by hand, copy `src/multiplexer` into `.git/hooks` under the hook
name you want:

```bash
cp src/multiplexer .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The same file can be copied (or symlinked) under any supported hook name.
The installed name is the hook type.

```bash
ln -s /path/to/git-hooks-multiplexer/src/multiplexer .git/hooks/pre-commit
```

`.git/hooks` is local to each clone. Teammates and CI need the same copy, or
they can run `setup-hooks`.

## Subhooks

Create executables under `hooks/<type>/` at the **repository root** (not
inside `.git/hooks`):

```bash
mkdir -p hooks/pre-commit
# add 01-lint, 02-confirm_default_branch, …
chmod +x hooks/pre-commit/*
```

Git runs `.git/hooks/pre-commit`, which runs those files in alphabetic
order. Prefix names with `01-`, `02-`, … when order matters. Hidden files
are skipped. Only regular files with the executable bit set run.

If `hooks/<type>/` is missing or has no executables, the multiplexer exits 0
and Git continues.

## Behaviour

- Git's hook arguments are forwarded to every subhook.
- Stdin is read once and replayed to each child, so a second `pre-push` check still sees the same refs.
- stdout and stderr stay on the terminal so optional prompts appear.
- A non-zero subhook abort stops the rest; the multiplexer exits with that code.
- Exit `0` means every subhook succeeded, or none were found; exit `1` means an unknown hook type or no Git working tree.

A subhook that prompts (for example a yes/no confirm before committing to
`master`) should read `/dev/tty`, not stdin. Git may already be using stdin
for a payload.

## Supported Hook Names

The allowlist matches current [githooks(5)](https://git-scm.com/docs/githooks)
names:

`applypatch-msg`, `commit-msg`, `fsmonitor-watchman`, `p4-changelist`,
`p4-post-changelist`, `p4-pre-submit`, `p4-prepare-changelist`,
`post-applypatch`, `post-checkout`, `post-commit`, `post-index-change`,
`post-merge`, `post-receive`, `post-rewrite`, `post-update`,
`pre-applypatch`, `pre-auto-gc`, `pre-commit`, `pre-merge-commit`,
`pre-push`, `pre-rebase`, `pre-receive`, `prepare-commit-msg`,
`proc-receive`, `push-to-checkout`, `reference-transaction`,
`sendemail-validate`, `update`

An unknown installed name exits 1 with `Unknown hook type`.

## Examples

### Copy into Several Hook Types

```bash
MUX=/path/to/git-hooks-multiplexer/src/multiplexer
cp "$MUX" .git/hooks/pre-commit
cp "$MUX" .git/hooks/pre-merge-commit
cp "$MUX" .git/hooks/commit-msg
cp "$MUX" .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-merge-commit \
  .git/hooks/commit-msg .git/hooks/pre-push
```

A symlink to the same file works the same way if you prefer one copy on disk.

### Confirm Commits to Master

A subhook that prompts should open `/dev/tty` so Git's stdin stays free.
Save as `hooks/pre-commit/02-confirm_default_branch` and `chmod +x` it:

```bash
#!/usr/bin/env bash
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "${branch}" == "master" ]] || exit 0

exec < /dev/tty
read -r -p "Are you sure you want to commit to ${branch}? [Yes/No] " response
case "${response}" in
  [yY]|[yY][eE][sS]) exit 0 ;;
  *) exit 1 ;;
esac
```

### Ordered Lint Then Test

```text
hooks/pre-commit/01-ruff
hooks/pre-commit/02-pytest
```

If `01-ruff` exits non-zero, `02-pytest` does not run. A silent lint that
forwards the tool's exit code:

```bash
#!/bin/sh
exec ruff check .
```

### Record a Pre-Push Payload

Stdin is replayed to every subhook. Both this file and a later `02-…` check
see the same ref lines. Save as `hooks/pre-push/01-record` and `chmod +x` it:

```bash
#!/bin/sh
cat > /tmp/pre-push-stdin.txt
exit 0
```

### Forward Commit-Msg Arguments

Git's arguments are passed through. A `commit-msg` subhook receives the
path to the message file as `$1`:

```bash
#!/bin/sh
exec grep -qE '^[A-Z]' "$1"
```

Save as `hooks/commit-msg/01-capitalised_subject` and `chmod +x` it. Install
the multiplexer as `.git/hooks/commit-msg` first.

## Development

These steps are only for changing this repository.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make init
make check
```

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
