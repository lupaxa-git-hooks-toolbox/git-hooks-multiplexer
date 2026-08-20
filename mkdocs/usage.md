# Usage

## Repository layout

Install the multiplexer under the Git hook name. Commit subhooks with the
project:

```text
.git/hooks/pre-commit          copy of multiplexer (not committed)
.git/hooks/pre-merge-commit    same file, different name (optional)

hooks/
└── pre-commit/
    ├── 01-python_coding_standard
    ├── 02-confirm_default_branch
    └── 03-link_check_readme
```

`.git/hooks` is local to each clone. Teammates and CI need the same copy, or
they can run [Setup Git Hooks](https://setup-git-hooks.thelupaxaproject.org/)
(`setup-hooks`) to install the multiplexer. Prefix names with `01-`, `02-`, …
when order matters.
Hidden files are skipped. Only regular files with the executable bit set run.

## Interactive and non-interactive subhooks

Most subhooks just run and exit. A subhook that needs a human (for example a
yes/no confirm before committing to `master`) should read the keyboard from
`/dev/tty`, not stdin. Git may already be using stdin for a payload.

The multiplexer inherits stdout and stderr so those optional prompts appear
immediately. Hooks that do not prompt are unchanged.

## Arguments and stdin

Git's hook arguments are passed through to every subhook. Stdin is read once
and replayed to each child, so a second `pre-push` check still sees the refs.

## Fail-fast

If a subhook exits non-zero, remaining subhooks do not run. The multiplexer
exits with that same code so Git aborts the operation.

## Missing configuration

If `hooks/<type>/` does not exist, or it contains no executables, the
multiplexer exits 0 without printing. Install the hook early; add subhooks
when you need them.
