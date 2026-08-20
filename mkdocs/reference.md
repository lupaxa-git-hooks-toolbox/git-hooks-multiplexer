# Reference

## Invocation

| Item        | Source                                         |
| :---------- | :--------------------------------------------- |
| Hook type   | Basename of `argv[0]` (the name Git invoked)   |
| Arguments   | `sys.argv[1:]`, forwarded to each subhook      |
| Stdin       | Read once; replayed to every subhook           |
| Working dir | Repository working tree (`git rev-parse`)      |
| Subhooks    | `hooks/<type>/*` that are executable files     |

Do not resolve the real path of the multiplexer when deciding the hook type.
A symlink named `pre-commit` must stay `pre-commit`.

## Supported hook names

The allowlist matches current [githooks(5)](https://git-scm.com/docs/githooks)
names, including `pre-merge-commit`, `pre-push`, `commit-msg`,
`prepare-commit-msg`, `pre-receive`, `update`, `post-rewrite`, and
`push-to-checkout`.

An unknown installed name exits 1 with `Unknown hook type`.

## Hooks that use stdin

These hooks receive a payload on stdin. The multiplexer replays it to every
subhook:

| Hook                     | Typical stdin                         |
| :----------------------- | :------------------------------------ |
| `pre-push`               | Local and remote ref lines            |
| `pre-receive`            | Old / new oid and ref name            |
| `post-receive`           | Same format as `pre-receive`          |
| `post-rewrite`           | Rewritten commit pairs                |
| `reference-transaction`  | Reference update lines                |

## Hooks that use arguments

| Hook                  | Typical arguments                      |
| :-------------------- | :------------------------------------- |
| `commit-msg`          | Path to the commit message file        |
| `prepare-commit-msg`  | Message file, source, optional SHA     |
| `pre-push`            | Remote name and URL                    |
| `update`              | Ref name, old oid, new oid             |
| `post-checkout`       | Previous HEAD, new HEAD, flag          |
| `post-merge`          | Squash flag                            |

## Exit codes

| Code        | Meaning                                      |
| :---------- | :------------------------------------------- |
| `0`         | All subhooks succeeded, or none were found   |
| Subhook `N` | First failing subhook's exit code            |
| `1`         | Unknown hook type or no Git working tree     |

## Hook file

The product is the single file `src/multiplexer`. It uses the Python standard
library only. There is no package to install or import.

Copy or symlink it into `.git/hooks` under the hook name you want. Python
3.13 or newer must be on `PATH`.
