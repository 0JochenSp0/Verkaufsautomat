# Third-party skills

These skill folders are unmodified copies of other people's work. Their licenses apply.

| Folder | Source | License | Version / date |
|---|---|---|---|
| `find-skills/` | https://github.com/vercel-labs/skills (`skills/find-skills`) | MIT, © Vercel, Inc. | copied 2026-11-21 |
| `improve-codebase-architecture/` | https://github.com/mattpocock/skills (`skills/engineering/improve-codebase-architecture`) | MIT, © Matt Pocock | copied 2026-11-22 |
| `graphify/` | https://github.com/Graphify-Labs/graphify (written by `graphify install --project`) | Apache-2.0, © Graphify Labs | graphifyy 0.9.115 (`.graphify_version`) |

Full license texts: in each source repository (`LICENSE`). To update a skill, copy it again from its source, or for graphify run `graphify install --project` after upgrading the package.

Note: `find-skills` calls `npx skills`. That CLI needs Node ≥ 22 and fails on this Pi's Node 20. The fallback is the search API `https://skills.sh/api/search?q=…`.
