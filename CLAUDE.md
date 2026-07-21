# Numbered Workspaces

## Who's who

- Claude is **BONECRUSHER 9000**
- Alfred is **CHEBUZILLA**

## What this is

A herdr plugin that mirrors each space's ordinal into a `num` metadata token so
`ui.sidebar.spaces` can render it via the `"$num"` row token. Published to
GitHub as `abrose/herdr-numbered-workspaces`, installable with
`herdr plugin install`.

## Why `min_herdr_version` is 0.7.4

Both halves of this plugin shipped in herdr v0.7.4, per its release notes:
"configurable row layouts for expanded Space and Agent sidebar entries,
including built-in display tokens, per-agent overrides, custom metadata tokens,
and pane/workspace metadata reporting through the CLI and socket API."

v0.6.3 added `pane.report_metadata`, which is pane-level and does not help —
this plugin needs the *workspace* variant. Do not lower the pin.

## Why agent numbering is conditional

`focus_agent(idx)` resolves through `crate::ui::agent_panel_entries()`, which is
a three-stage pipeline: collect (flat walk of workspaces → tabs → layout panes,
keeping agent panes), then `apply_agent_view()`, then render. The sidebar
renders that same list with `.enumerate()`, so sidebar row *i* is exactly what
`alt+(i+1)` focuses.

The socket API's `agent_list` calls `collect_agent_infos()`, which performs the
same walk but **never calls `apply_agent_view`**. So `agent list` order equals
sidebar order only when:

1. `ui.agent_panel_sort = "spaces"` (the default). `"priority"` re-sorts by
   attention and recency. Not readable over the API, but it *is* persisted to
   `config.toml` even when toggled by clicking the sidebar header — which is why
   the script reads the config file.
2. No `agent_view_override` is active. Set via `agent.view.set` by any caller;
   can filter agents out entirely. **Not detectable at all** — the query is
   never readable. This is the known limitation in the README.

`AgentInfo` has no ordinal field, while `WorkspaceInfo` is built with
`number: index + 1`. That asymmetry looks intentional. The real fix is upstream.

Pane metadata tokens are **write-only**: `tokens` appears on workspaces in
`api snapshot`, but `pane get`, `pane list`, and `agent list` all lack it. Hence
no diffing on the agent path, and no way to verify agent tokens except by
looking at the sidebar.

## Things that are easy to get wrong

- `herdr plugin link` does **not** run build commands and does **not** copy
  files. Re-run it after editing `herdr-plugin.toml`, and read the `warnings`
  field — a misspelled event name links successfully and silently never fires.
- Plugin stdout/stderr is captured, never printed.
  `herdr plugin log list --plugin numbered-workspaces` is the only place it
  surfaces.
- Commands are argv, not a shell. No globbing, no pipes, no `$VAR` expansion in
  the manifest.
- `install` over a linked plugin is refused. `herdr plugin unlink` first.
- The `"$num"` row token lives in the *user's* `config.toml`. No manifest field
  can put it there, which is why the README's config step is load-bearing.

## Dev loop

```bash
herdr plugin link "$PWD"
herdr plugin action invoke numbered-workspaces.renumber
herdr workspace list | jq '.result.workspaces[] | {label, number, tokens}'
herdr plugin log list --plugin numbered-workspaces --limit 5
```
