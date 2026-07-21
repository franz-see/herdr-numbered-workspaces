# Numbered Workspaces

Puts a number in front of every space — and every agent — in herdr's sidebars.

```
SPACES                         AGENTS
1  ● feat-APP-5421-hexagonize   1  ● claude   feat-APP-5421
2  ● dotfiles-chezmoi           2  ● claude   dotfiles-chezmoi
3  ● agora-docs                 3  ● claude   agora-docs
```

Most useful alongside herdr's indexed jump bindings, `switch_workspace` and
`focus_agent`: those keys take you straight to entry *n*, but nothing in the
sidebar tells you which entry is which number. This plugin closes that loop.
See [Pairs with indexed switching](#pairs-with-indexed-switching).

## How it works

herdr knows both positions internally but exposes no built-in sidebar row token
for either, so the plugin mirrors them back in as `num` metadata tokens, which
the sidebars *can* render via the `"$num"` row token.

**Spaces** are straightforward: `herdr workspace list` reports each space's
ordinal as `number`. Only the spaces whose token disagrees with their current
number are written, so the steady state — nothing moved — costs a single API
call.

**Agents** are ordered by a flat walk of every workspace, then every tab, then
every pane in layout order, keeping the panes herdr recognises as agents. That
is the order `herdr agent list` returns, and the order the agents sidebar
displays. Pane metadata tokens are write-only over the API, so unlike spaces
there is nothing to diff against and every agent is rewritten on each run.

Positions shift for a lot of reasons, so the plugin hooks every event that can
move one — workspace, tab, and pane creation, closure, and reordering, plus
`pane.agent_detected` for when a plain pane becomes an agent. It also hooks
`workspace.focused`: metadata tokens live in memory and do not survive a server
restart, and focus is the first event after reattaching, so it doubles as the
recovery hook.

## Requirements

- herdr 0.7.4 or newer — workspace metadata reporting and configurable
  sidebar row tokens both landed in that release
- `bash` and [`jq`](https://jqlang.github.io/jq/) on `PATH`
- Linux or macOS

## Install

```bash
herdr plugin install abrose/herdr-numbered-workspaces --yes
```

Then add the `"$num"` token to whichever sidebars you want numbered, in
`~/.config/herdr/config.toml`:

```toml
[ui.sidebar.spaces]
rows = [
  ["$num", "state_icon", "workspace"],
  ["branch", "git_status"],
]

[ui.sidebar.agents]
rows = [
  ["$num", "state_icon", "workspace", "tab"],
  ["agent"],
]
```

Reload the config and populate the tokens for what you already have open:

```bash
herdr server reload-config
herdr plugin action invoke numbered-workspaces.renumber
```

**The config step is not optional.** Nothing in a herdr manifest can edit your
`config.toml`, so without `"$num"` in `rows` the plugin runs correctly and you
see no difference.

If you use `[ui.sidebar.agents.rows_by_agent]` to override the layout for a
specific agent, add `"$num"` there too — an override **replaces** `rows` rather
than extending it.

## Pairs with indexed switching

The numbers earn their keep once you can actually jump to them. herdr ships both
indexed bindings **unbound**; they are optional and you opt in:

```toml
[keys]
prefix = "ctrl+a"
switch_workspace = "prefix+shift+1..9"
focus_agent = "prefix+alt+1..9"
```

Now `prefix+shift+3` jumps to the third space and `prefix+alt+3` to the third
agent, and the sidebar shows you which ones those are before you press. Without
the bindings the numbers are decoration; without the plugin the bindings are a
guessing game. They are two halves of the same feature.

Both ranges cap at 9, so only the first nine entries are reachable this way.
The plugin still numbers past 9, since the position is worth knowing even where
no shortcut reaches.

## Agent numbering and `agent_panel_sort`

`focus_agent` indexes the agents **sidebar**, which is the `herdr agent list`
order only under the default `agent_panel_sort = "spaces"`. Setting:

```toml
[ui]
agent_panel_sort = "priority"
```

reorders the sidebar by attention and recency **without** reordering the API
response — so the position the plugin can observe is no longer the position the
shortcut uses.

Rather than publish a number that points at the wrong agent, the plugin detects
this and **clears** the agent tokens instead. Under `priority` sort you get no
agent numbers at all. Space numbers are unaffected.

Note that clicking the sidebar's sort header toggles this setting at runtime and
writes it back to `config.toml`, so it can change without you editing anything.

**Known limitation:** herdr also lets any plugin or CLI caller impose an agent
view via `agent.view.set`, which can re-sort *and filter* the agents sidebar.
That override is not readable over the socket API, so the plugin cannot detect
it. While such a view is active, agent numbers may be wrong. Space numbers
remain correct.

The underlying fix would be an ordinal field on herdr's `AgentInfo`, the way
`WorkspaceInfo` already carries `number`.

## Configuration

None. The `rows` you configure *are* the switch: a `num` token renders only in a
sidebar whose `rows` include `"$num"`, so numbering spaces but not agents is
just a matter of leaving `"$num"` out of `[ui.sidebar.agents]`.

The token name is fixed at `num`.

## Uninstall

```bash
herdr plugin uninstall numbered-workspaces
```

Remove `"$num"` from your sidebar `rows` as well. Any tokens already published
stay until the next server restart, since they are only held in memory.

## Troubleshooting

Plugin output is captured rather than printed, so this is where errors surface:

```bash
herdr plugin log list --plugin numbered-workspaces --limit 5
```

To confirm space tokens are being published:

```bash
herdr workspace list | jq '.result.workspaces[] | {label, number, tokens}'
```

Agent tokens cannot be read back — the API exposes no `tokens` field on panes —
so the sidebar itself is the only way to check them.

If a token matches but the sidebar shows nothing, the `"$num"` row token is
missing from that sidebar's `rows`.

## License

MIT
