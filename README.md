# Numbered Workspaces

Puts a number in front of every space in herdr's left-hand spaces sidebar.

```
1  ● feat-APP-5421-hexagonize-market-research-agent
2  ● dotfiles-chezmoi
3  ● agora-docs
```

Most useful alongside herdr's indexed `switch_workspace` binding: that key jumps
you straight to space *n*, but nothing in the sidebar tells you which space is
which number. This plugin closes that loop. See
[Pairs with indexed switching](#pairs-with-indexed-switching).

## How it works

`herdr workspace list` already reports each space's ordinal as `number`, but
herdr has no built-in sidebar row token for it. The plugin mirrors that ordinal
back into herdr as a `num` metadata token, which the sidebar *can* render via
the `"$num"` row token.

Ordinals shift whenever a space is created, closed, or moved, so the plugin
hooks those three events and rewrites the tokens. It also hooks
`workspace.focused`: metadata tokens live in memory and do not survive a server
restart, and focus is the first event after reattaching, so it doubles as the
recovery hook.

Each run writes only the spaces whose token disagrees with their current
number, so the steady state — nothing moved — costs a single API call.

## Requirements

- herdr 0.7.4 or newer — workspace metadata reporting and configurable
  sidebar row tokens both landed in that release
- `bash` and [`jq`](https://jqlang.github.io/jq/) on `PATH`
- Linux or macOS

## Install

```bash
herdr plugin install abrose/herdr-numbered-workspaces --yes
```

Then add the `"$num"` token to your spaces sidebar in
`~/.config/herdr/config.toml`:

```toml
[ui.sidebar.spaces]
rows = [
  ["$num", "state_icon", "workspace"],
  ["branch", "git_status"],
]
```

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

Now `prefix+shift+3` jumps to the third space, and the sidebar shows you which
one that is before you press it. Without the binding the numbers are decoration;
without the plugin the binding is a guessing game. They are two halves of the
same feature.

The range caps at 9, so only the first nine spaces are reachable this way.

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

If `tokens.num` matches `number` but the sidebar shows nothing, the `"$num"`
row token is missing from your config.

## License

MIT
