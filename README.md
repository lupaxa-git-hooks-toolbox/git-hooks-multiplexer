<p align="center">
    <a href="https://github.com/lupaxa-git-hooks-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/git-hooks-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Multiplexer</h1>

One self-contained script. Copy it into `.git/hooks` — no pip install, no
package. It runs every executable under `hooks/<hook-type>/` at the
repository root, in name order, and stops on the first failure.

The hook type is the name Git invoked (`pre-commit`, `commit-msg`,
`pre-push`, …), not the source file name. Most subhooks just run; a subhook
that needs a human should read `/dev/tty`.

## Install

Python 3.13 or newer on `PATH`. The only file you need is `src/multiplexer`.

[Setup Git Hooks](https://setup-git-hooks.thelupaxaproject.org/) (`setup-hooks`)
can install that file into `.git/hooks` automatically. Point
`hooks/multiplexer-config.yml` at this repository and run `setup-hooks`; the
CLI copies the script unless you skip that step. See that project's
[getting started](https://setup-git-hooks.thelupaxaproject.org/getting-started/)
guide.

To install by hand, copy `src/multiplexer` into `.git/hooks` under the hook
name you want:

```bash
cp src/multiplexer .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The same file can be copied (or symlinked) under every hook name you need.
Then add executables under `hooks/pre-commit/` in the project.

## Development

These steps are only for changing this repository.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make init
make check
```

## Documentation

The published guide is at
[git-hooks-multiplexer.thelupaxaproject.org](https://git-hooks-multiplexer.thelupaxaproject.org/).

Sources live in [`mkdocs/`](mkdocs/index.md). After `make init`:

```bash
make mkdocs-serve
```

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
