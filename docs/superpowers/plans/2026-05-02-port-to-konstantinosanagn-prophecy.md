# Port dual-venue work to konstantinosanagn/prophecy-pred-markets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the UI work and Kalshi integration from this clone (`tinosattavily/tavily-kalshi`, branch `prophecy-design-port`) onto `konstantinosanagn/prophecy-pred-markets` via a new branch + PR + Vercel preview verification, without disturbing the source remote or destructively replacing the target's `main`.

**Architecture:** Two-remote model on the existing clone at `~/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/`. `origin` (tinosattavily) stays the safety net; a new remote `port` (konstantinosanagn) receives a `port-from-dual-venue` branch. Vercel auto-deploys preview from that branch. User verifies, iterates, then merges PR only on explicit go.

**Tech Stack:** git (CLI), GitHub CLI (`gh`), Vercel (target deploy platform), optionally `vercel` CLI for env-var sync.

**Spec:** `docs/superpowers/specs/2026-05-02-port-to-konstantinosanagn-prophecy-design.md`

**Hard rules (do not violate without explicit per-occurrence user approval):**
- No `git push --force` to any remote.
- No deletes of branches/refs on either remote.
- No PR merge until preview verification passes and user says go.
- No env-var writes to Vercel without showing the diff to user first.
- Pause at every CHECKPOINT for user confirmation.

---

## Task 1: Pre-flight commit of dirty UI files

**Files:**
- Modify (commit, do not push): all 7 currently-dirty frontend files on `prophecy-design-port`.

**Working dir for all commands:** `/Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue`

- [ ] **Step 1.1: Confirm we're on the expected branch with the expected dirty set**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue status --short --branch
```

Expected: branch `## prophecy-design-port`, modifications listed for these 7 files (and possibly more `docs/superpowers/` files now committed):
```
 M frontend/app/globals.css
 M frontend/components/Dashboard.tsx
 M frontend/components/input/UrlInput.tsx
 M frontend/components/layout/AppShell.tsx
 M frontend/components/layout/ConfigPanelContent.tsx
 M frontend/components/layout/ConfigPanelHeader.tsx
 M frontend/components/layout/TopNav.tsx
```

If the dirty set differs, STOP and report to user.

- [ ] **Step 1.2: Stage exactly the 7 frontend files (not `docs/`)**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue add \
  frontend/app/globals.css \
  frontend/components/Dashboard.tsx \
  frontend/components/input/UrlInput.tsx \
  frontend/components/layout/AppShell.tsx \
  frontend/components/layout/ConfigPanelContent.tsx \
  frontend/components/layout/ConfigPanelHeader.tsx \
  frontend/components/layout/TopNav.tsx
```

- [ ] **Step 1.3: Verify staged set matches**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue diff --cached --name-only
```

Expected: exactly those 7 paths, nothing else.

- [ ] **Step 1.4: Commit (do NOT push to origin)**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue commit -m "$(cat <<'EOF'
fix(frontend): WIP UI polish on Dashboard, AppShell, ConfigPanel, TopNav, UrlInput, globals

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: one commit on `prophecy-design-port`, 7 files changed.

- [ ] **Step 1.5: Verify and DO NOT push**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue log --oneline -3
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue status --short --branch
```

Expected: new commit at HEAD, branch `prophecy-design-port` ahead of `origin/prophecy-design-port` by 2 commits (this WIP + the spec commit `1947fee`). NO `git push` to origin in this task.

---

## Task 2: Switch `gh` CLI active account to konstantinosanagn

**Files:** None (CLI state only).

- [ ] **Step 2.1: Confirm both accounts are still authenticated**

Run:
```bash
gh auth status 2>&1
```

Expected: both `tinosattavily` and `konstantinosanagn` shown as logged in.

- [ ] **Step 2.2: Switch active account**

Run:
```bash
gh auth switch -u konstantinosanagn
```

Expected: `✓ Switched active account for github.com to konstantinosanagn`.

- [ ] **Step 2.3: Verify**

Run:
```bash
gh auth status 2>&1 | grep -E 'Active account|Logged in'
gh api user --jq .login
```

Expected: konstantinosanagn shown as Active; `gh api user` returns `konstantinosanagn`.

---

## Task 3: Add `port` remote pointing at konstantinosanagn/prophecy-pred-markets

**Files:** `.git/config` (auto-modified by `git remote add`).

- [ ] **Step 3.1: Confirm `port` remote does not already exist**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue remote -v
```

Expected: only `origin` listed, no `port`. If `port` already exists, STOP and report — user may have a different config.

- [ ] **Step 3.2: Add the remote**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue remote add port https://github.com/konstantinosanagn/prophecy-pred-markets.git
```

- [ ] **Step 3.3: Verify**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue remote -v
```

Expected: both `origin` (tinosattavily/tavily-kalshi) and `port` (konstantinosanagn/prophecy-pred-markets) listed for fetch and push.

---

## Task 4: Fetch from `port` and inspect divergence (CHECKPOINT before pushing)

**Files:** Local refs only (no working-tree changes).

- [ ] **Step 4.1: Fetch all refs from `port`**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue fetch port
```

Expected: refs come down (`port/main`, `port/master`, `port/vercel/...`). No errors.

- [ ] **Step 4.2: Show what's on `port/main` we don't have**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue log --oneline port/main ^HEAD | head -50
```

Capture the output — this is the list of commits unique to target's main.

- [ ] **Step 4.3: Show what's on our HEAD that's not on `port/main`** (sample, not full list — could be hundreds)

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue rev-list --count HEAD ^port/main
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue log --oneline HEAD ^port/main | head -10
```

Capture the count and first 10 commits.

- [ ] **Step 4.4: Verify a common ancestor exists (sanity check)**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue merge-base HEAD port/main 2>&1 || echo "NO_COMMON_ANCESTOR"
```

If `NO_COMMON_ANCESTOR`, the histories are unrelated and merging will need `--allow-unrelated-histories`. Note this for Task 12.

- [ ] **Step 4.5: CHECKPOINT — report to user**

Compose a report including:
- Number of commits on our branch ahead of `port/main`
- Full list of commits on `port/main` not in our branch (from 4.2)
- Whether common ancestor exists (from 4.4)
- Recommended next step (push as new branch — no rewrite of either history)

**STOP and wait for user "go" before Task 5.**

---

## Task 5: Create `port-from-dual-venue` branch and remove `docs/superpowers/` from its tree

**Files:**
- Modify: `.gitignore` (append `docs/superpowers/`)
- Delete from tree (not from disk): everything under `docs/superpowers/`

- [ ] **Step 5.1: Create and check out the port branch**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue checkout -b port-from-dual-venue
```

Expected: switched to new branch `port-from-dual-venue` at the same SHA as `prophecy-design-port`.

- [ ] **Step 5.2: Verify the branch sits at the expected SHA**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue log --oneline -3
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue rev-parse HEAD prophecy-design-port
```

Expected: HEAD and `prophecy-design-port` point to the same SHA; top commit is the WIP UI polish commit from Task 1.

- [ ] **Step 5.3: Remove `docs/superpowers/` from tracking on this branch**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue rm -r docs/superpowers/
```

Expected: lists each tracked file under `docs/superpowers/` being removed.

- [ ] **Step 5.4: Append to `.gitignore`**

Use the Edit tool to add `docs/superpowers/` to `.gitignore`. First Read the file to see current contents, then append the line at the end with a comment.

Example final block at end of `.gitignore`:
```
# Internal brainstorming/spec docs — not for public deployed repo
docs/superpowers/
```

- [ ] **Step 5.5: Stage and commit**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue add .gitignore
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue status --short
```

Expected: `D docs/superpowers/...` (the rm -r staging) plus `M .gitignore`.

Then:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue commit -m "$(cat <<'EOF'
chore: exclude internal brainstorming docs from public repo

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5.6: Confirm files still exist on disk**

Run:
```bash
ls /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/docs/superpowers/specs/
```

Expected: spec file still listed. (Removal was from git tree only on this branch.)

- [ ] **Step 5.7: Confirm `prophecy-design-port` still has the docs**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue ls-tree -r prophecy-design-port -- docs/superpowers/ | head -5
```

Expected: tree entries shown — docs are still tracked on `prophecy-design-port`, only the port branch sheds them.

---

## Task 6: Push `port-from-dual-venue` to `port` remote

**Files:** Remote refs only.

- [ ] **Step 6.1: First push attempt**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue push -u port port-from-dual-venue
```

Three possible outcomes — handle each:

**Outcome A (success):** New branch created on `konstantinosanagn/prophecy-pred-markets`, tracking set up. Proceed to Step 6.4.

**Outcome B (auth/permission failure 403):** osxkeychain is using `tinosattavily` credentials which lack write access to `konstantinosanagn/prophecy-pred-markets`. STOP and apply Step 6.2.

**Outcome C (network or other error):** STOP and report to user; do not retry blindly.

- [ ] **Step 6.2: (Only if 6.1 failed with 403) Configure per-URL credential**

Get the konstantinosanagn token from `gh`:
```bash
gh auth token --user konstantinosanagn
```

Then re-issue the push with the token in the URL **for this push only** (do not persist the token in `.git/config`):
```bash
TOKEN=$(gh auth token --user konstantinosanagn)
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue push https://konstantinosanagn:${TOKEN}@github.com/konstantinosanagn/prophecy-pred-markets.git port-from-dual-venue:port-from-dual-venue
```

After success, set upstream cleanly using the regular remote:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue branch --set-upstream-to=port/port-from-dual-venue port-from-dual-venue
```

- [ ] **Step 6.3: (Only if 6.2 still fails) Ask user to choose a credential strategy**

STOP. Report 403 and ask user whether to:
- (a) Set git's credential helper to use konstantinosanagn for this URL persistently, or
- (b) Use SSH remote URL instead of HTTPS, or
- (c) Investigate gh permission scopes.

- [ ] **Step 6.4: Verify branch exists on remote**

Run:
```bash
gh api repos/konstantinosanagn/prophecy-pred-markets/branches/port-from-dual-venue --jq '{name, commit: .commit.sha}'
```

Expected: returns `name: "port-from-dual-venue"` and a commit SHA matching local HEAD:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue rev-parse HEAD
```

---

## Task 7: Open PR against target's `main`

**Files:** None (GitHub state only).

- [ ] **Step 7.1: Create the PR via gh**

Run:
```bash
gh pr create \
  --repo konstantinosanagn/prophecy-pred-markets \
  --base main \
  --head konstantinosanagn:port-from-dual-venue \
  --title "Port: dual-venue UI + Kalshi integration from tavily-kalshi" \
  --body "$(cat <<'EOF'
## Summary

Ports the UI redesign and Kalshi integration work from the development repo `tinosattavily/tavily-kalshi` (branch `prophecy-design-port`) onto this deployed repo via a Vercel preview verification loop.

**Scope:** full repo (frontend + backend).

**Strategy:** push as a new branch, verify against the Vercel preview URL, iterate on fixes via additional commits, merge only after explicit verification.

**Note on diff size:** because this branch was developed independently of this repo's `main`, the diff against `main` is large. The Vercel preview reflects the actual end-state for verification.

## Verification plan

- [ ] Vercel preview deploys cleanly (build succeeds)
- [ ] Frontend loads at preview URL
- [ ] Polymarket URL → analysis flow works
- [ ] Kalshi URL → analysis flow works (requires Kalshi env vars on Vercel — see env-var sync sub-task)
- [ ] No regressions vs. current production at konstantinosanagn deploy URL

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: gh prints the PR URL (e.g. `https://github.com/konstantinosanagn/prophecy-pred-markets/pull/N`). Capture this URL.

- [ ] **Step 7.2: Verify PR exists and report URL to user**

Run:
```bash
gh pr view --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --json url,state,headRefName,baseRefName
```

Expected: `state: "OPEN"`, `headRefName: "port-from-dual-venue"`, `baseRefName: "main"`.

Report the PR URL to user.

---

## Task 8: Wait for Vercel preview deploy and CHECKPOINT visual verification

**Files:** None.

- [ ] **Step 8.1: Poll PR for Vercel status check (up to ~5 min)**

Run periodically:
```bash
gh pr view --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --json statusCheckRollup
```

Look for a Vercel check in `statusCheckRollup`. Possible states: `IN_PROGRESS`, `SUCCESS`, `FAILURE`.

If polling more than once in this session, prefer `ScheduleWakeup` with `delaySeconds: 270` rather than busy-loop sleep.

- [ ] **Step 8.2: Get the preview URL from PR comments or check details**

Run:
```bash
gh pr view --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --json comments
```

Vercel typically posts a comment with the preview URL. Alternative: check the Vercel dashboard.

- [ ] **Step 8.3: If build FAILED — diagnose**

Pull the Vercel deployment logs (via Vercel CLI if installed, otherwise via dashboard) and report root cause to user. Common causes:
- Missing env var → likely (proceed to Task 9 ahead of schedule)
- Build error from new code → fix in a commit on `port-from-dual-venue`
- Vercel project config mismatch (e.g. wrong root directory, wrong framework preset) → escalate to user

- [ ] **Step 8.4: CHECKPOINT — user visual verification**

Send to user:
- The preview URL
- The current production URL (`konstantinosanagn/prophecy-pred-markets` deploy)
- Verification protocol from spec (load app → paste market URL → run analysis → view report; specifically exercise Kalshi paths)

**STOP and wait for user report on what works / breaks before Task 9 or further commits.**

---

## Task 9: Inventory required env vars

**Files:** None (read-only inspection of source repo).

- [ ] **Step 9.1: Find env var references in backend**

Run:
```bash
grep -rEn 'os\.(getenv|environ)' /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/backend/ 2>/dev/null | head -50
```

Capture all distinct env var names referenced.

- [ ] **Step 9.2: Find env var references in frontend**

Run:
```bash
grep -rEn 'process\.env\.[A-Z_]+' /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue/frontend/ 2>/dev/null | head -50
```

Capture all distinct env var names referenced.

- [ ] **Step 9.3: Check for `.env.example` or similar**

Run:
```bash
find /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue -maxdepth 3 -name '.env*' -not -path '*/node_modules/*' 2>/dev/null
```

Read any `.env.example` files found.

- [ ] **Step 9.4: Compile required-vars list grouped by category**

Produce a markdown table to share with user:

| Var name | Used in (FE/BE) | Likely value source | On target Vercel? |
|---|---|---|---|
| KALSHI_API_KEY | BE | konstantinosanagn account | unknown |
| ... | ... | ... | ... |

Save this list inline in the PR description as a comment update OR as a chat message to user — pick whichever the user prefers.

---

## Task 10: Sync missing env vars to target's Vercel project (CHECKPOINT)

**Files:** None.

- [ ] **Step 10.1: Detect Vercel CLI availability**

Run:
```bash
which vercel || echo "VERCEL_CLI_NOT_FOUND"
vercel --version 2>&1 || true
```

Branch:
- **Path A (CLI installed):** continue to 10.2.
- **Path B (CLI missing):** SKIP to 10.6 (manual handoff).

- [ ] **Step 10.2: (Path A) Check Vercel auth status**

Run:
```bash
vercel whoami 2>&1 || echo "VERCEL_NOT_AUTHED"
```

If not authed, report to user; ask them to run `vercel login` in `! vercel login` form or skip to 10.6.

- [ ] **Step 10.3: (Path A) List env vars on target project**

User must first `cd` the working dir to a directory linked to the konstantinosanagn Vercel project, OR we can pass `--scope`. Simplest:
```bash
cd /tmp && mkdir -p vercel-port-check && cd vercel-port-check
vercel link --yes --project prophecy-pred-markets --scope <user_vercel_org_or_username>
vercel env ls production 2>&1
vercel env ls preview 2>&1
```

If `--scope` value unknown, STOP and ask user.

Capture the list of var names already on target.

- [ ] **Step 10.4: (Path A) Diff against required list from Task 9**

Compute: `required ∩ on_target` (already present), `required − on_target` (missing). Report missing list to user.

- [ ] **Step 10.5: (Path A) CHECKPOINT — show diff, get per-var approval, write**

Show user the missing-vars list. For each, ask whether to copy the value from the source clone's local `.env` (or wherever they have it) into Vercel via `vercel env add`. Do NOT write any var without explicit approval per var.

For each approved:
```bash
echo "<value>" | vercel env add <NAME> production preview
```

After all writes, trigger a redeploy of the PR:
```bash
gh pr comment --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --body "redeploy"
```
(Or push an empty commit on the branch if comment-trigger isn't wired.)

- [ ] **Step 10.6: (Path B) Manual handoff**

Produce a copy-pasteable list of missing env vars and post to user:
> "Vercel CLI not available locally. Please add these env vars in Vercel UI for project `prophecy-pred-markets`, scope production+preview:
> - `KALSHI_API_KEY` = (your Kalshi API key)
> - `KALSHI_EMAIL` = (your Kalshi account email)
> - ...
> Once added, comment `redeploy` on the PR (or push any commit to `port-from-dual-venue`) to trigger a fresh preview build, then I'll re-verify."

**STOP and wait for user confirmation before re-verifying.**

---

## Task 11: Iteration loop until user says "ship it"

**Files:** Whatever needs fixing on `port-from-dual-venue`.

- [ ] **Step 11.1: Receive issue from user (preview URL test result)**

User reports a specific bug or visual delta from the preview.

- [ ] **Step 11.2: Reproduce locally if possible**

Run the affected flow in the local dev server (`cd frontend && npm run dev`, plus backend if needed), confirm bug.

- [ ] **Step 11.3: Fix on `port-from-dual-venue`**

Make minimal change addressing the report. Commit:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue add <files>
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue commit -m "fix(<scope>): <terse>"
```

- [ ] **Step 11.4: Push and wait for new preview**

Run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue push port port-from-dual-venue
```

Then poll preview status as in Task 8.

- [ ] **Step 11.5: CHECKPOINT — re-verify**

Send updated preview URL to user. Loop back to 11.1 if more issues, else proceed to Task 12.

---

## Task 12: Final merge (CHECKPOINT, only on explicit user "ship it")

**Files:** Remote `main` ref on target.

- [ ] **Step 12.1: Confirm explicit user go**

Do NOT proceed without an unambiguous "merge it" / "ship it" / "yes merge" from user. If unclear, STOP and ask.

- [ ] **Step 12.2: Recommend merge method based on diff shape**

Re-run:
```bash
git -C /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets-dual-venue log --oneline port/main ^port-from-dual-venue
```

If `port/main` has commits we don't have (e.g. Vercel config), recommend:
- Cherry-pick those commits onto `port-from-dual-venue` first (single new commit on our branch), push, then merge as a regular merge-commit.

If `port/main` is fully an ancestor (rare), recommend fast-forward or squash-merge.

If unrelated histories (no merge-base — flagged at Step 4.4), recommend merge-commit with `--allow-unrelated-histories` performed via `gh` PR merge UI is not directly supported — STOP and discuss strategy with user.

Present recommendation to user, await pick.

- [ ] **Step 12.3: Execute merge**

For squash-merge:
```bash
gh pr merge --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --squash --delete-branch=false
```

For merge-commit:
```bash
gh pr merge --repo konstantinosanagn/prophecy-pred-markets <PR_NUMBER> --merge --delete-branch=false
```

(`--delete-branch=false` keeps `port-from-dual-venue` around as a safety net even after merge.)

- [ ] **Step 12.4: Verify production deploy**

Wait for Vercel production deploy on `main` to finish (poll same way as Task 8). Smoke-test the live production URL end-to-end (Polymarket flow + Kalshi flow).

- [ ] **Step 12.5: Final report to user**

Report:
- PR merged at <SHA>
- Production deploy: success / link
- Any follow-ups needed (e.g. cleanup of `port-from-dual-venue` branch later, removal of obsolete branches on target, etc.)

---

## Self-review notes

**Spec coverage:** All 6 phases of the spec map to tasks (Phase 1 → Task 1, Phase 2 → Tasks 2–3, Phase 3 → Tasks 4–7, Phase 4 → Tasks 9–10, Phase 5 → Task 11, Phase 6 → Task 12). Task 8 (preview verification checkpoint) is split out for clarity.

**Hard rules from spec:** All 4 hard rules (no force push, no deletes, no merge without go, no env writes without diff approval) are enforced inline at Tasks 6, 10, 12.

**CHECKPOINTS where user must intervene:**
- Step 4.5 (review divergence before any push)
- Step 8.4 (visual verification of first preview)
- Step 10.5 / 10.6 (env var diff approval)
- Step 11.5 (iteration loop)
- Step 12.1 (final merge go)
- Step 12.2 (merge method choice)
