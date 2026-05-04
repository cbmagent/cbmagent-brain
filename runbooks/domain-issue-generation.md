# Domain issue generation

Use `scripts/create-domain-issues.py` to fan out `portfolio/domains.yaml` into one durable GitHub Issue per domain.

## Dry run

```bash
python3 scripts/create-domain-issues.py --json
```

The dry run prints the issues that would be created and the existing issues that already match by stable marker or title.

## Apply

```bash
python3 scripts/create-domain-issues.py --apply --json
```

The script creates missing issues only. Each generated issue includes a hidden marker in this form:

```html
<!-- domain-issue: example.com -->
```

That marker is what makes reruns safe across open and closed issues.

## Issue types

- `canonical-site`, `canonical-or-related-site`, and other non-redirect roles get a migration/repo/GitHub Pages checklist.
- `redirect-only` roles get a Cloudflare redirect checklist.

## Safety

The script only creates GitHub Issues. It does not change DNS, Cloudflare rules, GitHub Pages settings, provider settings, or repository settings. Any production DNS/provider write remains gated through protected GitHub Actions environments or human approval.
