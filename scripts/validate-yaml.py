#!/usr/bin/env python3
"""Validate basic YAML files if PyYAML is available; otherwise do a lightweight syntax sanity check."""
from pathlib import Path
import sys

paths = [Path('.github/labels.yml'), Path('portfolio/domains.yaml')]
try:
    import yaml  # type: ignore
except Exception:
    for p in paths:
        text = p.read_text(encoding='utf-8')
        if '\t' in text:
            raise SystemExit(f'{p}: tabs are not allowed in YAML')
        if not text.strip():
            raise SystemExit(f'{p}: empty file')
        print(f'{p}: basic check ok')
    sys.exit(0)

for p in paths:
    with p.open(encoding='utf-8') as f:
        yaml.safe_load(f)
    print(f'{p}: YAML ok')
