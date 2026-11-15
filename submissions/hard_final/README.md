# Final Hard controller — upload verified artifacts here

This directory is reserved for the **exact submitted agent**, not the early prototype on `main`.

## Required files

- `agent.py`
- `hard_v2_model.py`
- `params.json`
- `dashboard.html` (auxiliary visualization bundled by the team; not the Tukey application)

The source archive supplied by the team is `hard_final_submission.zip`, SHA-256:

`63fc916796cbcc18906972867c854b568a6e1ed40b2dfaafd9dacfdd2a9081a4`

The ZIP passed the official local checker in the team's verification. The team reported **23.32 public Hard points** for the final line of development. A public score is not a private ranking prediction.

**Why files are not yet in this directory:** the full final ZIP lives in the team's local `artifacts/` directory, which is ignored by Git. To make this repository self-contained, the team must unpack those four files here and commit them before the presentation. Do not replace them with an older experimental version.

On PowerShell, from the repository root:

```powershell
New-Item -ItemType Directory -Force submissions/hard_final | Out-Null
Expand-Archive -LiteralPath "C:\\path\\to\\hard_final_submission.zip" -DestinationPath "submissions/hard_final" -Force
git add submissions/hard_final
git commit -m "feat: include final Hard submission source"
git push origin main
```

The code in the folder should reproduce the uploaded ZIP content. Do not add test-hidden data, PIN, raw restricted datasets or secrets.

[Project overview](../../README.md) · [Evaluation methodology](../../docs/FINAL_TECHNICAL.md)
