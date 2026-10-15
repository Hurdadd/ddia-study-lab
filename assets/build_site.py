#!/usr/bin/env python3
"""Build a static allowlisted deployment, never copy workspace metadata."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'public'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
allowed={'.html','.css','.js','.json','.svg','.png','.webp','.jpg','.woff2','.txt'}
for source in [ROOT/'assets',ROOT/'final-project',ROOT/'docs',*sorted(ROOT.glob('ch[0-9]*'))]:
 for p in source.rglob('*'):
  if not p.is_file() or p.suffix not in allowed: continue
  if any(s.startswith('.') or s=='__pycache__' for s in p.relative_to(ROOT).parts): continue
  if p.name.endswith(('.browser-check.json','.finalize.json','.delivery.json','.finalize-summary.json')): continue
  q=OUT/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
public_docs=['docs/DEVELOPMENT.md','docs/HOSTING.md','docs/RECOVERY.md','docs/SOLUTION_FORMAT.md','docs/THIRD_PARTY_NOTICES.md']
public_docs += [f'final-project/adrs/ADR-{n:03}.md' for n in range(1,16)]
for name in public_docs:
 q=OUT/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,q)
for name in ['index.html','exercise-audit.html','README.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','GOVERNANCE.md','SUPPORT.md','AUTHORS.md','CHANGELOG.md','NOTICE','LICENSE','DCO']:
 shutil.copy2(ROOT/name,OUT/name)
assert not list(OUT.rglob('.env*'))
assert not (OUT/'PRODUCT.md').exists()
assert not (OUT/'HANDOFF_EXERCISE_SOLUTIONS_FA.md').exists()
assert not (OUT/'docs/DEPLOYMENT.md').exists()
assert not (OUT/'assets/solutions/_schema.md').exists()
assert not (OUT/'final-project/research').exists()
print(f'Built {len(list(OUT.rglob("*")))} static entries in public/')
