# Source Lineage Standard

Every derived site or workflow should record its source lineage.

## Required Fields

Use these fields in portfolio registries or repo READMEs when applicable:

```yaml
source_lineage:
  primary_template: FreeForCharity/FFC-IN-FFC_Single_Page_Template
  secondary_template: FreeForCharity/FFC-IN-Footer_Only_Template
  operations_reference: FreeForCharity/FFC-Cloudflare-Automation
  advanced_reference: clarkemoyer/technologyadoptionbarriers.org
  attribution_required: true
  upstream_giveback_tracking: true
```

## README Acknowledgement

Derived repos should include an acknowledgement section unless there is a project-specific reason not to.

## Upstream Candidate Trigger

Create an upstream-candidate issue when a downstream change is:

- reusable by other nonprofits,
- a template bug fix,
- an accessibility improvement,
- a GitHub Pages/static export improvement,
- a workflow/issue-form improvement,
- a provider/agent operations improvement,
- a documentation/runbook improvement that reduces nonprofit setup burden.
