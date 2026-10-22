# FutureSkill theme review

These are source-extracted design previews, not a replacement for the FastAPI app.
The six real HTML pages and reskilling dependencies are copied into `_source`.
`Current` keeps original page styles. The other entries inject `_future.css`;
all share `_SourcePreview` and `_shell.css`.

Every entry can navigate between assessment, reskilling, trends, uncertainty, SDG
and the development screen inventory. The last is a review tool, not a learner
module. Its sample links make assessment results and reskilling states accessible.

The preview boundary supplies anonymous, isolated backend fixtures. Reskilling
save/upload actions fail explicitly rather than pretending to save. Personal
assessment scoring is disabled; the inventory's S05 link shows labeled canned
sample results. Uncertainty calculations use the same illustrative arithmetic as
the original Python module, and are not validated employment forecasts.
SDG exploration retains all 17 goals and only the reviewed goal 4/8 links.
Unknown careers do not acquire fabricated relationships.

Changing appearance does not reload the inner document, so an open drawer and
entered values survive. Preview theme storage is in memory, isolated from the
working website. Local SDG artwork and real attributed photographs are copied
unaltered; see `public/images/futureskill/sdg/SOURCES.md`.

To refresh source snapshots and anonymous fixtures, from workspace root:

    python artifacts/mockup-sandbox-preview/scripts/extract-futureskill.py

Do not refresh after beginning source-snapshot-specific modifications without
checking the diff. Theme styles and shared preview-engine files are not overwritten.
Graduate an approved theme into the existing FastAPI pages; do not replace the
app's framework or copy preview API stubs into production.
