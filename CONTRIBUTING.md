# Contributing

Thank you for helping improve Own the Stack, maintained by hurdad ashouri.
The repository is currently private; access and public release are separate decisions.

1. Open an issue describing the reader’s problem, expected behavior and scope.
2. For an architectural change, propose or supersede an ADR before changing claims.
3. Branch from `main`; keep the patch focused and preserve Persian/English parity.
4. Run the checks in README. For UI changes, inspect light/dark, RTL/LTR, phone and
   desktop, keyboard focus, and reduced motion. Include relevant captures in the PR;
   do not commit machine-specific screenshots or local tool caches.
5. Submit a PR describing the problem, resulting behavior, validation and limitations.

## Content and design rules

- Follow `assets/ddia.css`: cream/cocoa, Nunito/Vazirmatn, flat pastels and readable
  ruled teaching surfaces. Extend incumbent components before adding new ones.
- Keep the workshop in sequence: product → needs → estimates → decisions → diagrams
  → implementation plan. No implied completion or fake benchmark/success claims.
- Every significant number needs a source or a labeled assumption, units, formula,
  workload and validation method. RPO/RTO must specify the failure domain.
- Distinguish official engineering practice from official hiring exercises and
  unverified candidate reports. Do not reproduce private or paywalled question banks.
- Do not edit frozen generated diagram HTML without regenerating its evidence receipt.
- Do not add live model/API calls, analytics or new dependencies without an issue
  explaining the purpose, maintenance cost and data handling.

## Rights and sign-off

Submit only work you have the right to contribute. Preserve third-party notices.
Do not submit book scans, substantial copyrighted excerpts, secrets or personal data.
Original contributions are licensed under AGPL-3.0-only unless a clearly identified
third-party component has its own compatible terms. No copyright assignment or CLA
is required. Sign your commits with `git commit -s` to certify the [DCO](DCO).

The maintainer reviews changes before merge. See GOVERNANCE and CODE_OF_CONDUCT.
