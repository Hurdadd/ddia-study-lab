# Security policy

The supported release is the current `main` branch of the educational website.
The proposed AI platform has no running API, database, worker or model service.

Never submit API keys, access tokens, real tenant data or private interview material.
For a vulnerability, use GitHub’s **Report a vulnerability** feature if available.
Otherwise create an issue titled “Request a private security contact” with no exploit,
secret or personal data; the maintainer will arrange a private channel.
Do not disclose details publicly before a coordinated fix is available.

The maintainer is hurdad ashouri (@Hurdadd). This volunteer project has no guaranteed
security-response SLA; acknowledgement and remediation depend on availability.

For the private deployment, verify Vercel Authentication protects every route and
asset, including deployment-specific URLs. Never commit environment files, platform
credentials, bypass links or `.vercel` authentication state. Report an unintended
public deployment immediately through the private repository’s issue channel.
