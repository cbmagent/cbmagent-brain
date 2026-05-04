# cbmagent Portfolio Status Dashboard

> **Generated:** 2026-05-04T05:29Z  
> **Source:** `portfolio/domains.yaml` · `reports/pages-readiness/` · `reports/repo-inventory/`  
> **Issue:** [#27 Create portfolio status dashboard markdown](https://github.com/cbmagent/cbmagent-brain/issues/27)

---

## Summary

| Metric | Value |
|---|---|
| Total domains | 15 |
| Canonical sites | 10 |
| Redirect-only aliases | 5 |
| ✅ Pages-ready (DNS → GH Pages + HTTPS 200) | 2 |
| 🔴 WordPress (migration needed) | 3 |
| ⚫ Unreachable / no DNS | 4 |
| ❓ Needs audit | 3 |
| ↩️ Redirector aliases | 3 |
| Repo mapped | 2 of 10 canonical |
| Open agent-ready issues | 10 |
| Human-needed blockers | 4 |

---

## Domain Registry

| Domain | Role | Priority | Hosting Target | Current State | Repo | Pages Status | Next Issue |
|---|---|---|---|---|---|---|---|
| [clarkemoyer.com](https://clarkemoyer.com) | canonical | p0 | github-pages | wordpress → next.js | [clarkemoyer/clarkemoyer.com](https://github.com/clarkemoyer/clarkemoyer.com) | ✅ DNS→Pages, HTTPS 200 | [#24 Per-site migration](https://github.com/cbmagent/cbmagent-brain/issues/24) |
| [clarkmoyer.com](https://clarkmoyer.com) | redirect-only | p2 | cloudflare-redirect | — | — | ↩️ alias | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [technologyadoptionbarriers.org](https://technologyadoptionbarriers.org) | canonical | p0 | github-pages | live-production-reference | [clarkemoyer/technologyadoptionbarriers.org](https://github.com/clarkemoyer/technologyadoptionbarriers.org) | ✅ DNS→Pages, HTTPS 200 | [#23 EPIC: TABS workflow extraction](https://github.com/cbmagent/cbmagent-brain/issues/23) |
| [moyermanagement.com](https://moyermanagement.com) | canonical | p1 | github-pages | 🔴 WordPress | TBD | 🔴 WordPress | [#39 WordPress inventory](https://github.com/cbmagent/cbmagent-brain/issues/39) |
| [physicalinvestor.com](https://physicalinvestor.com) | canonical | p1 | github-pages | audit-needed | TBD | ❓ Needs audit | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [completequarters.com](https://completequarters.com) | canonical | p2 | github-pages | audit-needed | TBD | ⚫ No DNS | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [completequarters.org](https://completequarters.org) | redirect-only | p3 | cloudflare-redirect | — | — | ↩️ alias | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [moyermanagement.org](https://moyermanagement.org) | redirect-only | p3 | cloudflare-redirect | — | — | ↩️ alias | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [moyermanagementsystems.com](https://moyermanagementsystems.com) | canonical-or-related | p2 | github-pages | audit-needed | TBD | ⚫ No DNS | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [aprilmoyer.com](https://aprilmoyer.com) | canonical | p2 | github-pages | audit-needed | TBD | ⚫ No DNS | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [aprilunlimited.com](https://aprilunlimited.com) | canonical | p2 | github-pages | 🔴 WordPress | TBD | 🔴 WordPress | [#39 WordPress inventory](https://github.com/cbmagent/cbmagent-brain/issues/39) |
| [focus-on-free.com](https://focus-on-free.com) | canonical-or-related | p2 | github-pages-or-redirect | 🔴 WordPress | TBD | 🔴 WordPress | [#39 WordPress inventory](https://github.com/cbmagent/cbmagent-brain/issues/39) |
| [focusonfree.org](https://focusonfree.org) | canonical-or-related | p2 | github-pages-or-redirect | audit-needed | TBD | ❓ Needs audit | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [focusonfree.us](https://focusonfree.us) | canonical-or-related | p3 | github-pages-or-redirect | audit-needed | TBD | ❓ Needs audit | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |
| [darkclouds.us](https://darkclouds.us) | canonical | p3 | github-pages | audit-needed | TBD | ⚫ No DNS | [#36 Per-domain issues](https://github.com/cbmagent/cbmagent-brain/issues/36) |

---

## Migration Status by Priority Tier

### P0 — Critical / In-Flight

| Site | State | Next Action |
|---|---|---|
| clarkemoyer.com | Next.js migration in progress; DNS → Pages live | Monitor PR/CI in [cbmagent/clarkemoyer.com](https://github.com/cbmagent/clarkemoyer.com) |
| technologyadoptionbarriers.org | Live reference; extract patterns → FFC giveback | [#23](https://github.com/cbmagent/cbmagent-brain/issues/23) TABS workflow extraction |

### P1 — High / Blocked on Audit

| Site | State | Blocker |
|---|---|---|
| moyermanagement.com | WordPress live — migration needed | Repo TBD; awaiting #36 per-domain issue |
| physicalinvestor.com | DNS resolves; platform unknown | Audit needed; awaiting #36 |

### P2 — Medium / Needs Investigation

| Site | State |
|---|---|
| completequarters.com | No DNS; dormant or parked |
| aprilmoyer.com | No DNS; dormant or parked |
| aprilunlimited.com | WordPress live — migration needed |
| focus-on-free.com | WordPress live — migration needed |
| moyermanagementsystems.com | No DNS; dormant or parked |
| focusonfree.org | DNS resolves; platform TBD |

### P3 — Low / Parked or Redirectors

- `clarkmoyer.com` — Cloudflare redirect alias  
- `completequarters.org` — Cloudflare redirect alias  
- `moyermanagement.org` — Cloudflare redirect alias  
- `focusonfree.us` — DNS resolves; audit pending  
- `darkclouds.us` — No DNS; dormant  

---

## Repo Mapping Status

| Domain | Declared Repo | Discovery Status | Best Match |
|---|---|---|---|
| clarkemoyer.com | `cbmagent/clarkemoyer.com` (not accessible) | mapped via discovery | [clarkemoyer/clarkemoyer.com](https://github.com/clarkemoyer/clarkemoyer.com) |
| technologyadoptionbarriers.org | `clarkemoyer/technologyadoptionbarriers.org` | ✅ exact match | — |
| All others | TBD | missing-or-unknown | See [#15](https://github.com/cbmagent/cbmagent-brain/issues/15) |

---

## Open Epics Tracker

| # | Epic | Priority | Status |
|---|---|---|---|
| [#14](https://github.com/cbmagent/cbmagent-brain/issues/14) | Portfolio domain inventory & DNS/HTTP audit automation | critical | open |
| [#15](https://github.com/cbmagent/cbmagent-brain/issues/15) | GitHub repository discovery & site repo mapping | critical | open |
| [#16](https://github.com/cbmagent/cbmagent-brain/issues/16) | GitHub Pages site factory for net-new/coming-soon sites | high | open |
| [#17](https://github.com/cbmagent/cbmagent-brain/issues/17) | WordPress → GitHub Pages migration factory | high | open |
| [#18](https://github.com/cbmagent/cbmagent-brain/issues/18) | Cloudflare read-only & production write-gated workflows | critical | open |
| [#19](https://github.com/cbmagent/cbmagent-brain/issues/19) | Microsoft & Google read-only/work-gated automation | high | open |
| [#20](https://github.com/cbmagent/cbmagent-brain/issues/20) | Provider usage, quota, routing & fallback reporting | critical | open |
| [#21](https://github.com/cbmagent/cbmagent-brain/issues/21) | VS Code operator console & local repo workspace | high | open |
| [#22](https://github.com/cbmagent/cbmagent-brain/issues/22) | Free For Charity upstream giveback loop | critical | open |
| [#23](https://github.com/cbmagent/cbmagent-brain/issues/23) | technologyadoptionbarriers.org workflow extraction | high | open |
| [#24](https://github.com/cbmagent/cbmagent-brain/issues/24) | Per-site migration program | high | open |

---

## Human-Needed Blockers

These require Clarke/admin action before agent automation can proceed:

| # | Title | Scope |
|---|---|---|
| [#29](https://github.com/cbmagent/cbmagent-brain/issues/29) | Cloudflare read-only token setup | DNS/HTTP audit automation |
| [#30](https://github.com/cbmagent/cbmagent-brain/issues/30) | Cloudflare production DNS write token | Protected write environment |
| [#31](https://github.com/cbmagent/cbmagent-brain/issues/31) | Microsoft read-only domain app | MS Graph / Entra read access |
| [#32](https://github.com/cbmagent/cbmagent-brain/issues/32) | Google read-only credentials | Search Console / Analytics |

---

## Next Agent Tasks (Prioritized)

1. [#36](https://github.com/cbmagent/cbmagent-brain/issues/36) — **Create per-domain issue set from domains.yaml** (priority:high)
2. [#33](https://github.com/cbmagent/cbmagent-brain/issues/33) — Backport environment model to FFC Cloudflare Automation (priority:high)
3. [#34](https://github.com/cbmagent/cbmagent-brain/issues/34) — Inspect FFC Single Page Template for site factory readiness (priority:high)
4. [#41](https://github.com/cbmagent/cbmagent-brain/issues/41) — Create Hermes provider/model verification workflow (priority:high)
5. [#40](https://github.com/cbmagent/cbmagent-brain/issues/40) — Create OpenClaw health and cooldown monitor (priority:high)

---

## Recently Merged PRs

| PR | Description |
|---|---|
| [#48](https://github.com/cbmagent/cbmagent-brain/pull/48) | CI: validate brain repo artifacts |
| [#47](https://github.com/cbmagent/cbmagent-brain/pull/47) | feat: GitHub repo discovery report |
| [#46](https://github.com/cbmagent/cbmagent-brain/pull/46) | docs: autonomous roadmap and operating loop |
| [#12](https://github.com/cbmagent/cbmagent-brain/pull/12) | docs: nonprofit giveback alignment tracker |
| [#11](https://github.com/cbmagent/cbmagent-brain/pull/11) | docs: read-only/write-gated environment rollout |

---

*This dashboard is generated from YAML/report inputs and updated by the autonomous agent cron loop.*  
*Source: [`portfolio/domains.yaml`](../portfolio/domains.yaml) · [`reports/pages-readiness/pages-readiness-latest.md`](../reports/pages-readiness/pages-readiness-latest.md) · [`reports/repo-inventory/latest.md`](../reports/repo-inventory/latest.md)*  
*Generator script: `scripts/build-dashboard.py` (planned — see [#27](https://github.com/cbmagent/cbmagent-brain/issues/27))*
