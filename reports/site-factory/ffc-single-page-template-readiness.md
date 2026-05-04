# FFC Single Page Template site-factory readiness

- **cbmagent issue:** [#34](https://github.com/cbmagent/cbmagent-brain/issues/34)
- **Upstream repo inspected:** [FreeForCharity/FFC-IN-FFC_Single_Page_Template](https://github.com/FreeForCharity/FFC-IN-FFC_Single_Page_Template)
- **Inspection time:** 2026-05-04T13:58:09Z
- **Inspection mode:** read-only upstream clone plus validation commands; no production DNS/cloud/provider writes.

## Executive recommendation

Use this template as the **preferred human-assisted base** for cbmagent portfolio net-new nonprofit sites after a short hardening pass. It is already a good static GitHub Pages candidate: the site builds with `output: 'export'`, has GitHub Pages base-path support, includes CI/deploy workflows, and has unusually complete non-technical replacement documentation.

Do **not** treat it as a fully automated site-factory source yet. Factory automation would currently need to patch many hardcoded organization, metadata, domain, brand, and integration values scattered across source and docs. A small machine-readable site profile layer should be added upstream before using it for repeatable bulk generation.

## Dependency, build, and export strategy

### Stack observed

- Next.js App Router with TypeScript.
- Static export via `next.config.ts`:
  - `output: 'export'`
  - `images.unoptimized: true`
  - `basePath` and `assetPrefix` from `NEXT_PUBLIC_BASE_PATH`.
- GitHub Pages deployment via `.github/workflows/deploy.yml` and `actions/deploy-pages`.
- CI via `.github/workflows/ci.yml`:
  - `npm ci`
  - Prettier format check
  - ESLint
  - Jest
  - Playwright Chromium install
  - static build
  - E2E tests
- Asset-path helper: `src/lib/assetPath.ts` prefixes static assets with `NEXT_PUBLIC_BASE_PATH` for GitHub Pages subpath deployments.

### Content and route shape

- 114 TypeScript/TSX files under `src/components`.
- Static app routes found:
  - `/`
  - `/cookie-policy`
  - `/donation-policy`
  - `/free-for-charity-donation-policy`
  - `/privacy-policy`
  - `/security-acknowledgements`
  - `/terms-of-service`
  - `/vulnerability-disclosure-policy`
- Public assets found:
  - 76 files under `public/Images`
  - 19 files under `public/Svgs`
  - 3 files under `public/videos`
- Tests found:
  - 4 Jest test files in `__tests__`
  - 10 Playwright specs in `tests`

### Validation run

Validated from a fresh shallow clone of the upstream repo.

| Command | Result | Notes |
|---|---:|---|
| `npm ci` | PASS | Installed 1050 packages; npm reported 14 advisories. |
| `npm run format:check` | PASS | All matched files use Prettier style. |
| `npm run lint` | PASS with warnings | 7 warnings; no ESLint errors. Warnings are mainly static-export `<img>` usage plus one React immutability warning in testimonials navigation setup. |
| `npm test -- --runInBand` | PASS | 4 test suites, 26 tests passed. |
| `npm run build` | PASS | Next.js static export succeeded and generated 12 static pages/items including robots and sitemap. |
| `npm audit --omit=dev` | FAIL | 2 production advisories: Next.js high-severity DoS advisory and PostCSS moderate advisory. |

## Strengths for cbmagent portfolio use

1. **Static hosting fit:** The template is already designed for GitHub Pages and static export, matching the portfolio migration direction.
2. **Base-path support:** `NEXT_PUBLIC_BASE_PATH`, `assetPrefix`, and `assetPath()` make it viable for both `owner.github.io/repo/` and custom-domain deployments.
3. **Non-technical onboarding docs:** `TEMPLATE_USAGE.md` and `CONTENT_REPLACEMENT_GUIDE.md` are strong enough to support assisted setup by operators or nonprofit stakeholders.
4. **Quality gates are present:** CI, tests, linting, CodeQL, Dependabot, Lighthouse, link checking, and deployment smoke checks are represented in the repo.
5. **Policy-page baseline:** The existing legal/policy page structure provides a useful default for nonprofit sites that need transparent privacy/security/donation language.
6. **Upstream giveback alignment:** The repo is already maintained as an FFC template, so improvements can be contributed upstream rather than forked privately.

## Gaps before cbmagent factory adoption

### Must fix before default factory use

1. **Clear production dependency advisories.** `npm audit --omit=dev` currently reports production dependency advisories in `next` and `postcss`. Even if the current static export remains operational, downstream generated repos would inherit audit noise immediately.
2. **Introduce machine-readable site profile/config.** Factory automation needs one durable place for site name, domain, metadata, social links, brand colors, donation/application URLs, and integration IDs. Today these values are spread across source, docs, public `CNAME`, metadata, and components.
3. **Separate FFC-specific content from reusable defaults.** The current template is deeply branded as Free For Charity. That is fine for a source template, but cbmagent needs an explicit replacement map for source files and not only human-facing prose.

### Should fix for smoother scale-out

1. **Metadata should become data-driven.** `src/app/layout.tsx` hardcodes `metadataBase`, title, description, keywords, OpenGraph, Twitter handle, icons, manifest, and preconnects.
2. **Domain/CNAME should be generated from profile data.** `public/CNAME` is site-specific and should not silently carry into all generated sites.
3. **Third-party integrations need explicit enable/disable controls.** GTM, Zeffy, GuideStar, Microsoft Forms, SociableKit/Facebook Events, and social links are valuable but should be opt-in per generated site.
4. **Lint warning budget should be intentional.** The `<img>` warnings are acceptable for static export, but the React immutability warning should be reviewed upstream.
5. **Version documentation drift should be cleaned up.** README references Next.js 16.0.7 while the package install resolved/build reported Next.js 16.2.1.

## Upstream issues opened

Opened these upstream issues to make the inspection actionable for Free For Charity reuse:

1. [FreeForCharity/FFC-IN-FFC_Single_Page_Template#195: Add machine-readable site profile for factory-generated nonprofit sites](https://github.com/FreeForCharity/FFC-IN-FFC_Single_Page_Template/issues/195)
2. [FreeForCharity/FFC-IN-FFC_Single_Page_Template#196: Clear production npm audit advisories before template reuse](https://github.com/FreeForCharity/FFC-IN-FFC_Single_Page_Template/issues/196)

## Recommended cbmagent next steps

1. Track upstream issue #195 as the blocker for fully automated generation from this template.
2. Track upstream issue #196 as the security/noise blocker before making this the default factory base.
3. For near-term one-off sites, allow human-assisted use of the template with a per-site GitHub issue that records the filled content replacement guide.
4. After upstream #195 lands, build a cbmagent dry-run generator that produces a patch from a site profile without pushing or changing DNS.
5. Keep DNS, custom domain, and production Pages settings gated through GitHub Issues/Actions and human approvals.

## Decision

**Status:** Conditionally ready.

The template is suitable for immediate manual or assisted pilot use. It is not yet suitable as a fully autonomous bulk site factory base until the dependency advisories are cleared and a machine-readable site profile/config pattern exists.
