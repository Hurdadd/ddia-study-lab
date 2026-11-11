# Hosting

The production educational website is public at https://ddia-study-lab.vercel.app/.
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


## Web Analytics (page views only)

Issue: https://github.com/Hurdadd/ddia-study-lab/issues/10

The static export generator (`assets/build_site.py`) adds a first-party
Vercel Web Analytics script to full HTML pages in `public/`. This does not
enable collection on its own: the owner must enable **Web Analytics** in the
Vercel dashboard for project `own-the-stack` (team `hurdad`) **before
the next production deployment**.

The site collects standard cookieless, anonymized pageviews only. The
analytics provider can report page URL, referrer, approximate country, device
type and browser. No custom events, exercise answers, account identifiers,
or local browser storage contents are sent by project code. Review the
public-facing privacy notice before activating collection.

On the current Hobby plan, Vercel includes 50,000 Web Analytics events
per month across the team and pauses collection instead of charging for
additional analytics events. Analytics scripts also consume ordinary
network requests. Do not enable Web Analytics Plus or upgrade the plan
for this feature.

Activation and verification:

1. In Vercel, open project `own-the-stack` → **Analytics** → **Enable**.
2. From the current GitHub `main` checkout, run
   `python3 assets/build_site.py` and
   `python3 assets/check_publication.py --export`.
3. Confirm `public/index.html`, `public/studio/index.html`, and a chapter
   page contain exactly one `/_vercel/insights/script.js` reference.
4. Deploy this build to the existing `own-the-stack` production project
   (the last deployment came from Vercel CLI; a GitHub push alone does
   **not** redeploy it). Run `vercel --prod` from the linked project
   checkout using the team's authorized Vercel account.
5. Open https://ddia-study-lab.vercel.app/ as a real browser visitor.
   Verify the analytics script loads and a view request succeeds, then
   check Analytics in the project dashboard. Historical traffic before
   activation cannot be recovered.

Revert the analytics injection in `assets/build_site.py` and redeploy
if collection must be disabled; also disable Web Analytics in Vercel.
