# Multiplexer

One self-contained script. Copy `src/multiplexer` into `.git/hooks` — no pip
install, no package. It runs every executable under `hooks/<hook-type>/` at
the root of a Git repository.

The same file can be installed as `pre-commit`, `commit-msg`, `pre-push`,
`pre-merge-commit`, or any other supported hook. The hook type is the name Git
invoked, not the name of the source file.

## What it does

- Discovers executable subhooks in `hooks/<type>/` and runs them in name order
- Forwards Git's command-line arguments to each subhook
- Replays Git's stdin so every subhook sees the same payload
- Inherits the terminal so optional prompts appear; other hooks just run
- Stops on the first non-zero exit code

## Next steps

- [Getting started](getting-started.md) — copy the script, or let [Setup Git Hooks](https://setup-git-hooks.thelupaxaproject.org/) install it
- [Usage](usage.md) — layout, prompts, and fail-fast behaviour
- [Reference](reference.md) — hook names, arguments, and stdin
- [Examples](examples.md) — copy-paste install and subhook recipes
