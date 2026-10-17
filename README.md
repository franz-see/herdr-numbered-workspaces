# Numbered Workspaces

Puts an expanded-sidebar navigation number in front of every space in herdr's
left-hand spaces sidebar, including grouped worktrees.

```
1  ● feat-search
2  ● dotfiles
3  ● example-docs
```

Most useful alongside herdr's indexed `switch_workspace` binding: that key jumps
you straight to space *n*, but nothing in the sidebar tells you which space is
which number. This plugin closes that loop. See
[Pairs with indexed switching](#pairs-with-indexed-switching).

## How it works

`herdr workspace list` reports `number` in flat storage order. Navigation uses
sidebar order instead: linked worktrees appear beneath their repository's main
workspace, even when other workspaces separate them in the API list.

The plugin reconstructs Herdr's **expanded** sidebar order using
`worktree.repo_key` and `worktree.is_linked_worktree`:

- At the first member of a repository group, emit the main workspace first,
  followed by its other members in their original API order.
- Group only repositories with at least two members and a main workspace.
- Keep ungrouped workspaces in their original order and emit each workspace once.

It publishes the resulting one-based positions as `num` metadata, rendered by
the `"$num"` row token. For example, `[main, btop, linked-worktree]` becomes
`[main, linked-worktree, btop]`: the worktree gets **2**, not its API number **3**.

The plugin hooks `workspace.created`, `workspace.closed`, `workspace.moved`, and
`workspace.focused` to refresh the numbers. Focus also repopulates metadata after
a server restart. Only changed tokens are written, so steady state costs one API
call.

### Limitation: collapsed worktree groups

**Keep worktree groups expanded when using these numbers as shortcuts.** The
inspected Herdr 0.8.2 workspace API does not expose group collapse state or the
actual visible navigation ordinal. Collapsing a group can change shortcut
positions without changing the plugin's expanded-order numbers. A plugin-only
implementation cannot guarantee correct numbers in that state. This limitation
concerns repository groups, not the sidebar visibility toggle.

## Requirements

- herdr 0.7.4 or newer — workspace metadata reporting and configurable
  sidebar row tokens both landed in that release
- `bash` and [`jq`](https://jqlang.github.io/jq/) on `PATH`
- Linux or macOS

## Install

For a local checkout:

```bash
herdr plugin link /path/to/herdr-numbered-workspaces
```

Once the changes are released upstream, install from GitHub:

```bash
herdr plugin install abrose/herdr-numbered-workspaces
```

If this plugin ID is already locally linked, use `plugin link` to point it at
your checkout rather than attempting a GitHub install over the local link.

Then add the `"$num"` token to your spaces sidebar in
`~/.config/herdr/config.toml`:

```toml
[ui.sidebar.spaces]
rows = [
  ["$num", "state_icon", "workspace"],
  ["branch", "git_status"],
]
```

Declaring `rows` replaces the default layout, so repeat the built-in tokens you
want to keep.

Reload the config and populate the tokens for the spaces you already have open:

```bash
herdr server reload-config
herdr plugin action invoke numbered-workspaces.renumber
```

**The config step is not optional.** Nothing in a herdr manifest can edit your
`config.toml`, so without `"$num"` in `rows` the plugin runs correctly and you
see no difference.

## Pairs with indexed switching

The numbers earn their keep once you can actually jump to them. herdr ships
`switch_workspace` **unbound** — it is an optional indexed binding you opt into:

```toml
[keys]
prefix = "ctrl+a"
switch_workspace = "prefix+shift+1..9"
```

With worktree groups expanded, `prefix+shift+3` jumps to the third sidebar
workspace. The same numbering applies to `prefix`, then `w`, then `3` using the
default workspace navigation binding; no custom indexed binding is required for
that route.

The range caps at 9, so only the first nine spaces are reachable this way. The
plugin still numbers past 9, since the position is worth knowing even where no
shortcut reaches.

## Scope

Spaces only. herdr has a matching `focus_agent` indexed binding for the agents
sidebar, but agent ordering cannot be read reliably over the socket API — see
[CLAUDE.md](CLAUDE.md) for the details. Numbering agents would mean publishing
numbers that are silently wrong whenever `ui.agent_panel_sort` is `"priority"`
or another plugin has set an agent view, so this plugin does not attempt it.

## Configuration

None. The token name is fixed at `num`.

## Uninstall

```bash
herdr plugin uninstall numbered-workspaces
```

Remove `"$num"` from `ui.sidebar.spaces.rows` as well. Any tokens already
published stay until the next server restart, since they are only held in
memory.

## Troubleshooting

Plugin output is captured rather than printed, so this is where errors surface:

```bash
herdr plugin log list --plugin numbered-workspaces --limit 5
```

To confirm the tokens are actually being published:

```bash
herdr workspace list | jq '.result.workspaces[] | {label, number, tokens}'
```

`tokens.num` should match the workspace's position in the **expanded sidebar**,
not necessarily the API's `number`. A mismatch between those two fields is
expected when worktrees are grouped. If metadata is present but the sidebar
shows no numbers, check that `"$num"` is in your row configuration. If navigation
lands elsewhere, expand all worktree groups and invoke the renumber action again.

## Tests

Development tests require Python 3 as well as the runtime Bash and jq dependencies:

```bash
python3 -B -m unittest discover -s tests -v
bash -n renumber.sh
```

Tests execute the actual script against a fake Herdr CLI; they do not read or
modify a live session. They cover non-contiguous worktrees, multiple repositories,
parent/child ordering, unchanged tokens, CLI failures, and direct execution on
NixOS. The script resolves Bash through `PATH`, so `/bin/bash` is not required.

## License

MIT
