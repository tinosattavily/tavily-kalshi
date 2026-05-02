# Port `prophecy-pred-markets-dual-venue` work to `konstantinosanagn/prophecy-pred-markets`

**Date:** 2026-05-02
**Status:** Approved by user (sections 1–3 confirmed in brainstorming)
**Author:** Claude (with kwnstantinosanagn@gmail.com)

## Goal

Move the UI work and Kalshi integration from this clone (`tinosattavily/tavily-kalshi`, working dir `~/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/`) onto the user's deployed personal repo (`konstantinosanagn/prophecy-pred-markets`) safely, with frequent visual verification against the deployed Vercel preview, and without disturbing the source repo or destructively replacing the target's `main`.

## Non-goals

- Not retiring or rewriting `tinosattavily/tavily-kalshi` (the source remote stays intact as a safety net).
- Not force-pushing or directly mutating the target's `main` branch in this plan.
- Not refactoring the codebase during the port — files move as-is.
- Not opening cleanup PRs in the source repo.

## Source repo state (snapshot at 2026-05-02)

- Working dir: `~/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/`
- Origin: `https://github.com/tinosattavily/tavily-kalshi.git`
- Active branch: `prophecy-design-port`
- Recent commits (top of branch):
  - `26b21b7 feat(backend): populate sibling markets in Kalshi single-market responses`
  - `122ca84 fix(frontend): center URL input in viewport`
  - `cac6ed7 fix(frontend): bound sidebars to viewport height`
  - `9139d39 fix(frontend): defer ThemeToggle icon to client mount`
  - `e70babc fix(frontend): scope --font-sans/--font-mono to body`
- Uncommitted modifications (7 files), to be committed before port:
  - `frontend/app/globals.css`
  - `frontend/components/Dashboard.tsx`
  - `frontend/components/input/UrlInput.tsx`
  - `frontend/components/layout/AppShell.tsx`
  - `frontend/components/layout/ConfigPanelContent.tsx`
  - `frontend/components/layout/ConfigPanelHeader.tsx`
  - `frontend/components/layout/TopNav.tsx`
- Untracked: `docs/superpowers/` — internal brainstorming/spec docs, must NOT be pushed to the public deployed repo.

## Target repo state

- Repo: `https://github.com/konstantinosanagn/prophecy-pred-markets.git` (public)
- Branches: `main` at `e9d28ac…`, `master` at `a14a1c5…`, plus a `vercel/react-server-components-cve-…` branch and PR #1.
- Deploys to Vercel; per-branch preview URLs are auto-generated.
- Env vars: Kalshi-related secrets are believed to NOT be set in target's Vercel project (per user). Other vars (Tavily, MongoDB, etc.) status TBD.
- History overlap with source: target's `master` SHA `a14a1c5…` is present in the source repo locally — confirms the two share lineage. Target's `main` `e9d28ac…` is not present locally; target's main has commits we don't have (likely Vercel config).

## GitHub auth state

Both accounts already authenticated via `gh`:
- `tinosattavily` (active)
- `konstantinosanagn` (inactive — must be made active for `gh pr create` against the target)

`git push` uses git credentials (osxkeychain), separate from `gh` CLI active account. May need a per-URL credential helper or `GH_TOKEN` injection if the keychain pushes the wrong identity.

## Strategy: Branch + PR with two remotes

Operate from this same clone — no fresh checkout. Add `konstantinosanagn/prophecy-pred-markets` as a second remote, push your work as a new branch, let Vercel auto-deploy a preview from it, verify visually, iterate, then merge the PR only when you give the go.

**Why branch+PR (vs. mirror-replace or cherry-pick):**
- Preview URLs per branch make "check the deployed output frequently" trivial.
- Reversible at every step until the final merge.
- Keeps source remote untouched as a backup.
- We do NOT rebase onto target's `main` — the PR diff will be large, but Vercel deploys preview from branch HEAD's tree (i.e. your work as-is), so verification is unaffected by git-history shape. We worry about merge mechanics only at the very end.

## Step sequence with checkpoints

### Phase 1 — Pre-flight (in source clone, on `prophecy-design-port`)

1. Confirm `git status` is as expected; commit the 7 dirty files as one "WIP UI polish" commit on `prophecy-design-port`. **Do NOT push this commit to `origin` (tinosattavily) during this port** — `origin/prophecy-design-port` stays at the existing SHA so it remains a clean backup snapshot.
2. Commit this spec file (`docs/superpowers/specs/2026-05-02-port-to-konstantinosanagn-prophecy-design.md`) on `prophecy-design-port` for the record. (Other untracked items in `docs/superpowers/` may also be committed here.) These will be excluded from the port branch's tree at step 8.

### Phase 2 — Remote setup

3. `gh auth switch -u konstantinosanagn` — makes `gh` CLI use konstantinosanagn for PR creation and Vercel-related calls.
4. `git remote add port https://github.com/konstantinosanagn/prophecy-pred-markets.git`
5. `git fetch port` — pulls down target's refs.
6. **CHECKPOINT** — report to user: what's on `port/main` that we don't have, and how far our `prophecy-design-port` is ahead. User confirms before any push.

### Phase 3 — Push & open PR

7. `git checkout -b port-from-dual-venue` (from current `prophecy-design-port` HEAD).
8. On the port branch only: `git rm -r docs/superpowers/` (removes from tree), append `docs/superpowers/` to `.gitignore`, then commit "chore: exclude internal brainstorming docs from public repo". Files remain on disk and on `prophecy-design-port` — only the port branch sheds them.
9. `git push -u port port-from-dual-venue` — first push may surface a credential mismatch (see Risks).
10. `gh pr create --repo konstantinosanagn/prophecy-pred-markets --base main --head konstantinosanagn:port-from-dual-venue --title "Port: dual-venue UI + Kalshi integration" --body <…>`
11. **CHECKPOINT** — wait for Vercel preview URL to appear on the PR (status check or comment). User opens it, eyeballs against current production, reports any breakage.

### Phase 4 — Env vars (best-effort)

12. Inventory required env vars by reading source `backend/` and `frontend/` for `os.environ`/`process.env`/`NEXT_PUBLIC_*` references; produce a list grouped by `(known-set-on-target | likely-missing | unknown)`.
13. If `vercel` CLI is installed and authenticated for both projects: `vercel env pull` from source project, diff against target, propose missing additions to user.
14. **CHECKPOINT** — show diff to user; either Claude pushes the missing vars (with explicit per-var approval) or hands the list off for user to set in Vercel UI.
15. Trigger a redeploy on the PR after env vars are in place; re-verify the preview URL exercises Kalshi paths.

### Phase 5 — Iteration

16. Any fixes → commit on `port-from-dual-venue` → push → preview redeploys → re-verify. Repeat until user says "ship it."

### Phase 6 — Merge (only on explicit user go)

17. Merge PR. Method (squash vs merge-commit vs rebase) decided when we get there — depends on what the diff looks like and how the user wants the history to read on the target.
18. Verify production deploy on target succeeds; smoke-test the live URL.

## Risk mitigation

**Hard rules — do not violate without explicit user approval each time:**
- No `git push --force` to any remote.
- No deletes of branches/refs on either remote.
- No PR merge until preview verification passes and user says go.
- No env-var writes to Vercel without showing the diff to the user first.

**Safety nets:**
- `origin/prophecy-design-port` on `tinosattavily/tavily-kalshi` is untouched — full source-of-truth backup.
- Target's `main` is preserved on the remote regardless of what we push to a new branch.
- The PR can be closed without merging at zero cost.

**Known snag spots:**

| Risk | Detection | Response |
|---|---|---|
| Wrong git identity at push (keychain pushes as tinosattavily) | 403 or wrong author on first push attempt | Set `credential.helper` per URL or use `GH_TOKEN` from konstantinosanagn token; ask user before retrying |
| Vercel preview build fails (missing env, build error from new code) | PR status check turns red | Read build logs; fix in a commit on the branch if obvious, escalate to user otherwise |
| Backend changes don't deploy on Vercel (project may be FE-only with backend hosted elsewhere) | Backend routes 404 in preview | Stop, flag to user; backend port becomes a separate decision |
| Target's `main` has a Vercel config file we lack and the build needs it | Build error referencing missing `vercel.json` etc. | Cherry-pick that single config commit from `port/main` onto our branch |
| Unrelated-histories merge at step 17 | GitHub PR shows "no common history" or merge button greyed | Decide between (a) merge-commit allowing unrelated histories, (b) squash-merge, with user input |

## Verification protocol per checkpoint

At each preview push:
1. Open the Vercel preview URL.
2. Compare against current `konstantinosanagn/prophecy-pred-markets` production URL side-by-side.
3. Run through golden-path UX: load app, paste a market URL, run analysis, view report.
4. Specifically exercise Kalshi paths (Kalshi market URL → analysis output).
5. Report blockers / cosmetic deltas before continuing.

## Open questions left for implementation

- Exact PR body / title wording.
- Which env-var sync mechanism (`vercel` CLI vs MCP server vs manual handoff) — decide based on what's installed/authenticated when we get to phase 4.
- Final merge strategy at step 17 — pick when we see the actual diff.
