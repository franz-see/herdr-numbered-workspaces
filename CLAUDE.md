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
