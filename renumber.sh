#!/bin/bash
# Publishes ordinals as `num` metadata tokens, which the sidebars render via the
# "$num" row token. herdr reports these positions over the API but has no
# built-in row token for either one, so this is the bridge.
#
# Spaces and agents are published unconditionally. Nothing is displayed unless
# the user puts "$num" in that sidebar's `rows`, so `rows` is the on/off switch.
set -euo pipefail

herdr="${HERDR_BIN_PATH:-herdr}"
source_id=numbered-workspaces

# Only spaces whose token disagrees with their current number are written, which
# keeps the common case (nothing moved) to a single API call.
number_spaces() {
  "$herdr" workspace list |
    jq -r '
      .result.workspaces[]
      | select((.tokens.num // "") != (.number | tostring))
      | "\(.workspace_id)\t\(.number)"
    ' |
    while IFS=$'\t' read -r id number; do
      "$herdr" workspace report-metadata "$id" \
        --source "$source_id" --token "num=$number"
    done
}

# herdr prints the config path it actually resolved, honouring
# HERDR_CONFIG_PATH, so we never reimplement its path lookup.
agent_panel_sort() {
  local config
  config=$("$herdr" --help | sed -n 's/^Config: *//p')
  [ -r "$config" ] || return 0
  sed -n 's/^[[:space:]]*agent_panel_sort[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$config" | tail -1
}

# `focus_agent` indexes the agents sidebar, which is `agent list` order only
# under the default `spaces` sort — `priority` reorders the sidebar without
# reordering the API response. Under any other sort the position we can see is
# not the position the shortcut uses, so we clear rather than publish a number
# that points at the wrong agent.
#
# Pane tokens are write-only over the API, so unlike spaces there is nothing to
# diff against and every agent is rewritten on each run.
number_agents() {
  local sort panes id n=0
  sort=$(agent_panel_sort)
  panes=$("$herdr" agent list | jq -r '.result.agents[].pane_id')
  [ -n "$panes" ] || return 0

  while read -r id; do
    if [ "${sort:-spaces}" = spaces ]; then
      n=$((n + 1))
      "$herdr" pane report-metadata "$id" --source "$source_id" --token "num=$n"
    else
      "$herdr" pane report-metadata "$id" --source "$source_id" --clear-token num
    fi
  done <<<"$panes"
}

number_spaces
number_agents
