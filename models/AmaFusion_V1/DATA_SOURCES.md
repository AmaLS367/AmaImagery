# DATA_SOURCES

This file lists every dataset used to fine-tune the model **AmaFusion_V1**.  
It is part of the model-layer compliance package and must stay together with the model weights.

> Goal: enable a clean commercial transfer (full IP transfer) while honoring upstream licenses.

## Inclusion policy

- Prefer **CC0** and **CC BY** datasets, or custom permissions that allow commercial training and redistribution of derivative models.
- Avoid **CC BY-SA** and **CC BY-NC** for commercial full IP transfer scenarios.
- For **CC BY**, include the author’s name and required attribution text verbatim.
- Keep proof of license terms at download time (screenshots or PDFs) in `models/AmaFusion_V1/EVIDENCE/`.

## Dataset ledger

Fill one row per dataset actually used for training. For any dataset considered but **not used**, mark Status as `Excluded` and explain why.

| Dataset | URL | License | Allowed use summary | Required attribution text | Evidence (path) | Status |
|---|---|---|---|---|---|---|
| Manga109-s | https://huggingface.co/datasets/ykonya/Manga109-s | As stated on dataset card permitting commercial use | Commercial use permitted for this subset; use only the **s** subset | As required on the dataset card | EVIDENCE/manga109-s_license.png | Included |
| EasyPortrait | https://huggingface.co/datasets/gofixyourself/EasyPortrait | CC BY-SA 4.0 | ShareAlike may impose downstream sharing obligations incompatible with full IP transfer | As required by CC BY-SA 4.0; see CC page | EVIDENCE/easyportrait_card.png | **Excluded** |
| [REPLACE_NAME] | [URL] | CC0 | Free to use for any purpose without attribution | Not required | EVIDENCE/[file].png | Included |
| [REPLACE_NAME] | [URL] | CC BY 4.0 | Commercial training allowed with attribution | © [Author]. Licensed under CC BY 4.0 | EVIDENCE/[file].png | Included |
| [REPLACE_NAME] | [URL] | Custom permission | As per written permission | Use text per permission letter | EVIDENCE/[file].pdf | Included |
| [REPLACE_NAME] | [URL] | [License] | [Summary] | [Attribution text] | EVIDENCE/[file].png | Pending |

> For each **Included** dataset under CC BY, copy the exact attribution string required by the dataset author into the “Required attribution text” column.

## Private / proprietary data

If you use any private datasets (e.g., collected with consent or provided by a client):
- Place the permission letter or consent statement in `EVIDENCE/` (redact personal data if needed).
- Add a ledger row with `License = Private/With Consent` and summarize the permitted uses.

## Excluded sources log (defensive)

List any candidate sources you evaluated and **did not** use, with short reasons (license, quality, duplicates, privacy concerns). This helps during audits.

- EasyPortrait — Excluded due to CC BY-SA 4.0 and ShareAlike obligations.
- [Add others you considered and dropped]

## Versioning

- Update this file **before** each training run.
- Tag the repository/release with a matching commit that includes this file.
- Keep the evidence files immutable (use dated filenames).

## Contacts

Maintainer: Ama
Compliance contact: <email or URL>  
Last updated: <YYYY-MM-DD>
