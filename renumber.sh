#!/usr/bin/env bash
# Publishes expanded-sidebar positions as `num` metadata for the "$num" row token.
# The API's `number` is flat storage order, not grouped worktree navigation order.
# Mirror Herdr's expanded grouping: emit each repository's parent, then its linked
# worktrees, at the first member's position. Collapse state is not exposed by the
# API, so these numbers are only navigation hints when groups are expanded.
# Only changed tokens are written; the steady state costs a single API call.
set -euo pipefail

herdr="${HERDR_BIN_PATH:-herdr}"

"$herdr" workspace list |
  jq -r '
    .result.workspaces as $workspaces
    | (reduce $workspaces[] as $ws ({};
        if $ws.worktree == null then .
        else .[$ws.worktree.repo_key] += [$ws]
        end
      )) as $groups
    | reduce $workspaces[] as $ws ({seen: {}, ordered: []};
        $ws.worktree.repo_key as $key
        | (if $key == null then [] else $groups[$key] end) as $members
        | ($members | map(select(.worktree.is_linked_worktree == false))) as $parents
        | if ($members | length) >= 2 and ($parents | length) > 0 then
            if .seen[$key] then .
            else
              .seen[$key] = true
              | .ordered += ([$parents[0]] + [
                  $members[] | select(.workspace_id != $parents[0].workspace_id)
                ])
            end
          else .ordered += [$ws]
          end
      )
    | .ordered | to_entries[]
    | .value as $ws
    | (.key + 1 | tostring) as $number
    | select(($ws.tokens.num // "") != $number)
    | "\($ws.workspace_id)\t\($number)"
  ' |
  while IFS=$'\t' read -r id number; do
    "$herdr" workspace report-metadata "$id" \
      --source numbered-workspaces --token "num=$number"
  done
