# Getting started

## Requirements

- Python 3.13 or newer on `PATH` (the script starts with `#!/usr/bin/env python3`)
- A Git working tree (client-side hooks)

The multiplexer is one file. There is nothing to pip install and no package
to import.

## Install as a Git hook

[Setup Git Hooks](https://setup-git-hooks.thelupaxaproject.org/) (`setup-hooks`)
can install this multiplexer into `.git/hooks` for you. Point
`hooks/multiplexer-config.yml` at this repository and run `setup-hooks`; the
CLI copies the script unless you skip that step. See that project's
[getting started](https://setup-git-hooks.thelupaxaproject.org/getting-started/)
guide.

To install by hand, copy `src/multiplexer` into `.git/hooks` under the hook
name you want:

```bash
cp /path/to/git-hooks-multiplexer/src/multiplexer .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The same file can be copied (or symlinked) as `pre-merge-commit`,
`commit-msg`, `pre-push`, and any other supported hook. The installed name is
the hook type.

```bash
cp /path/to/git-hooks-multiplexer/src/multiplexer .git/hooks/pre-merge-commit
cp /path/to/git-hooks-multiplexer/src/multiplexer .git/hooks/commit-msg
chmod +x .git/hooks/pre-merge-commit .git/hooks/commit-msg
```

A symlink is also fine if you keep a clone of this repo on disk:

```bash
ln -s /path/to/git-hooks-multiplexer/src/multiplexer .git/hooks/pre-commit
```

## Add subhooks

Create executables under `hooks/<type>/` at the **repository root** (not
inside `.git/hooks`):

```bash
mkdir -p hooks/pre-commit
# add 01-lint, 02-confirm_default_branch, …
chmod +x hooks/pre-commit/*
```

Git then runs `.git/hooks/pre-commit`, which runs those files in alphabetic
order.

## First check

```bash
.git/hooks/pre-commit
```

If `hooks/pre-commit/` is missing or empty, the multiplexer exits 0 and Git
continues.

## Developing this repository

The steps below are only for changing the multiplexer itself. The hook is the
single file `src/multiplexer`.

```bash
git clone https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer.git
cd git-hooks-multiplexer
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make init
make check
```
