# Hosting

The production educational website is public at https://own-the-stack.vercel.app/.
The GitHub repository is public. The site is a static export, with no AI
backend, production tenant data, or model credentials.

Build: `python3 assets/build_site.py`. Output: `public/`.
The export copies only approved documentation and website assets; local notes,
raw tool reports, credentials and review captures are excluded.

Vercel Standard Protection keeps preview/generated deployment URLs protected
while the production alias is public. Confirm the intended project and team,
then verify anonymous access to the production home, capstone, scripts and diagrams.
For Git-based deployment, the commit author must have the required Vercel access.
Manual source-file deployments use the project owner's authenticated account.
Keep source/log visibility private and do not publish bypass credentials.
