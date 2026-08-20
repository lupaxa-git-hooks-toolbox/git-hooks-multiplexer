# Examples

The only file you copy is `src/multiplexer`. There is no package install.

## Copy into several hook types

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

## Confirm commits to master

A subhook that prompts should open `/dev/tty` so Git's stdin stays free:

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

Save as `hooks/pre-commit/02-confirm_default_branch` and `chmod +x` it.

## Record a pre-push payload

```bash
#!/bin/sh
cat > /tmp/pre-push-stdin.txt
exit 0
```

Both this hook and a later `02-…` check receive the same ref lines.

## Ordered lint then test

```text
hooks/pre-commit/01-ruff
hooks/pre-commit/02-pytest
```

If `01-ruff` exits non-zero, `02-pytest` does not run.
