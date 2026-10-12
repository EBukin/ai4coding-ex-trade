# A2 research: learner tooling

Date: 2026-10-11. Plan: `.docs/plans/0018-agentic-exercise-1-build.md`, step A2.

## 1. Timeline (local history) in Positron without Git

**Yes, it works.** Local history is a core VS Code workbench feature, independent of Git, and Positron inherits it.

- VS Code added local file history to the Timeline view in 1.66. Each save adds an entry; entries can be compared and restored. Setting `workbench.localHistory.enabled` (default `true`), plus `maxFileSize`, `maxFileEntries` (50), `exclude`, `mergeWindow`. Source: <https://code.visualstudio.com/updates/v1_66>
- UI path, VS Code: Explorer view (`Ctrl+Shift+E`), expand the **Timeline** section at the bottom. It shows events for the file active in the editor: Git commits and local file saves. Source: <https://code.visualstudio.com/docs/sourcecontrol/history>
- UI path, Positron: same. Explorer > Timeline. Positron docs have no page on it, and no Positron GitHub issue reports it missing (`gh search issues --repo posit-dev/positron "local history"` / `"timeline"`: nothing relevant).
- Local evidence: this machine runs Positron 2026.08.0 (Code OSS 1.124.0, `product.json`). `%APPDATA%\Positron\User\History\` holds 912 file histories, including `entries.json` with `"source":"Chat Edit: ..."` entries. Assistant edits are recorded too.
- Caveats for the page: only edits made inside the IDE are tracked. One entry per save (merged within 10 s). Learner must open a file first, then expand Timeline. Filter icon in Timeline toggles "Local History" vs "Git History".

## 2. Which assistants read `AGENTS.md`

| Assistant | Reads `AGENTS.md`? | Notes |
|---|---|---|
| Posit Assistant (Positron 2026.07+) | **Yes**, only `AGENTS.md` | Project memory = `AGENTS.md` in project root; user memory `~/.posit/assistant/AGENTS.md`. Project wins on conflict. Loaded only in trusted workspaces. Supports `@file.md` imports, relative, cannot escape folder. Source: <https://assistant.posit.co/docs/features/memory/> |
| Old Positron Assistant (deprecated) | yes | Read `agents.md`, `claude.md`, `positron.md`, `llms.txt` etc. Replaced by Posit Assistant in 2026.07. Source: <https://positron.posit.co/assistant-chat-instructions.html> |
| Copilot Chat, VS Code (agent mode) | **Yes**, root `AGENTS.md` | `chat.useAgentsMdFile` turns it on/off; on by default since 1.104. Nested files: `chat.useNestedAgentsMdFiles`, off by default. `chat.useClaudeMdFile` also lets the local agent read `CLAUDE.md`. Sources: <https://code.visualstudio.com/docs/agent-customization/custom-instructions.md>, <https://code.visualstudio.com/updates/v1_104> |
| Claude Code | **Yes, since v2.1.277**, but only when no `CLAUDE.md`/`CLAUDE.local.md` exists in cwd or above | Default setting `claude-md-or-agents-md`. If a `CLAUDE.md` exists, `AGENTS.md` is skipped unless imported or setting `claude-md-and-agents-md`. `@AGENTS.md` import in `CLAUDE.md` works and never double-loads. On Windows prefer the import over a symlink. Source: <https://code.claude.com/docs/en/memory> (sections "AGENTS.md", "Share one file with other coding tools") |

**Recommendation for `farm-trade-support/`:** ship `AGENTS.md` only (works in all three). Optionally add a one-line `CLAUDE.md` containing `@AGENTS.md` for older Claude Code versions. Do not put a second, divergent `CLAUDE.md`.

## 3. Stata `sem` and `estat teffects`

Tested in StataNow 19 on simulated data (see 4). Syntax accepted:

```stata
sem (lny <- lns lnf) (lnf <- lns), nolog
estat teffects
```

- `estat teffects` reports three tables: **Direct**, **Indirect**, **Total** effects, each with coefficient, OIM std. err., z, p, CI. Paths with no indirect route show `0 (no path)`.
- Options: `compact` (omit no-path rows), `standardized` (adds a "Std. coef." column), `nolabel`, `nodirect`, `noindirect`, `nototal`, plus display options. Manual: <https://www.stata.com/manuals/semestatteffects.pdf>
- Stored results (verified by `return list`): `r(direct)`, `r(indirect)`, `r(total)` (1 x 3, columns `lny:lnf lny:lns lnf:lns`), `r(V_direct)`, `r(V_indirect)`, `r(V_total)` (3 x 3), `r(nobs)`, scalar `r(N_groups)`.
- Extraction for `putexcel`:

```stata
qui estat teffects
matrix b_d = r(direct)
matrix b_i = r(indirect)
matrix b_t = r(total)
matrix V_i = r(V_indirect)
scalar se_i = sqrt(V_i[2,2])          // lny:lns
matrix E = b_d[1,"lny:lns"], b_i[1,"lny:lns"], b_t[1,"lny:lns"]
putexcel set "outputs/tables/sem_effects.xlsx", replace
putexcel A1 = matrix(E), names
```

Gotcha: index by name (`[1,"lny:lns"]`) or position 2; `r()` is overwritten by the next r-class command, so copy matrices first.

## 4. Data-generating process

Proposed DGP (no fixed effects, 30 countries x 20 years = 600 obs, fixed seed):

```
cs_i      ~ N(0, 1)                                  country size
lns_it    = 5 + 1.0*cs_i + 0.02*(year-2010) + N(0, 0.30)   subsidy, ln USD million
lnf_it    = 9.5 + 0.60*lns_it + N(0, 0.30)           fertiliser, ln tonnes
lny_it    = 1.0 + 0.10*lns_it + 0.40*lnf_it + N(0, 0.08)   output, ln USD million
```

True effects: direct 0.10, indirect 0.6 x 0.4 = 0.24, total 0.34.

Test result (seed 20260311): direct 0.093 (SE 0.007), indirect 0.240, total 0.333. All within ±0.03.

Noise matters:

- First try with `sd(e1)=0.15`, `sd(e2)=0.10` gave direct 0.082 (SE 0.016). `lnf` was almost collinear with `lns`, so the direct effect was imprecise.
- Rule of thumb: SE(direct) ≈ sd(e2) / (sqrt(N) x sd(lns) x sqrt(1-R²)), where R² = R² of lnf on lns. Keep `sd(e1)` ≥ 0.3 and `sd(e2)` ≤ 0.08 to get SE ≈ 0.007, so ±0.03 is about 4 SE.
- B2 should assert |estimate - truth| < 0.03 for all three on the chosen seed.

Magnitudes (level means in test): subsidy 261 USD million (range 9 to 2,486), fertiliser 340,000 t (41,000 to 1.6 million), output 730 USD million (230 to 1,970). Plausible for mid-size countries. Output looks low next to fertiliser for large countries; raise the `lny` intercept (for example 3.0 gives mean output ~5,400 USD million) if B1 wants agricultural value added on a realistic scale. Changing intercepts does not change the elasticities.

## Open issues

- No official Positron page documents Timeline; evidence is VS Code docs plus the local Positron 2026.08 install. A human should still click Explorer > Timeline once in Positron with a non-Git folder before launch.
- Claude Code reads `AGENTS.md` only from v2.1.277 and only without a `CLAUDE.md`; learners on older versions need the `@AGENTS.md` import.
- The Stata REST server failed with `Failed to create worker process` on a new `--session-id`; the default session worked.
