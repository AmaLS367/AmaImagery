# ATTRIBUTIONS

This file documents the provenance and licensing of the model assets shipped in this repository.
Scope here is the model layer only. Project-level code and its licenses are handled separately in the repository root.

## Summary

- Base lineage: Stable Diffusion v1.5 -> DreamShaper v6 -> AmaFusion_V1
- License context: CreativeML Open RAIL-M applies to the base and upstream derivative. MIT applies to the selected VAE.
- You must preserve all upstream notices when distributing weights or providing model access as a service.

## Upstream models

1) Stable Diffusion v1.5
Link: https://huggingface.co/runwayml/stable-diffusion-v1-5
License: CreativeML Open RAIL-M
Local copy of full text: models/AmaFusion_V1/LICENSES/OpenRAIL-M.txt

2) DreamShaper v6
Link: https://huggingface.co/Lykon/dreamshaper-6
License shown on model card: CreativeML Open RAIL-M
Upstream record: models/AmaFusion_V1/LICENSES/Upstream_DreamShaper_LICENSE.txt
Full text of the license is the same OpenRAIL-M located at models/AmaFusion_V1/LICENSES/OpenRAIL-M.txt

## VAE

VAE: sd-vae-ft-mse (original)
Link: https://huggingface.co/stabilityai/sd-vae-ft-mse-original
License: MIT
Local license file: models/AmaFusion_V1/LICENSES/VAE_LICENSE.txt

## Training data sources

The derivative model AmaFusion_V1 was fine-tuned on external datasets. Each dataset must have a license compatible with commercial redistribution of a derivative model or a written permission. Keep the table below in sync with the actual data used.

Rules of inclusion
- Allowed: CC0, CC BY, custom permissions that allow commercial training and redistribution of derivative models
- Avoid: CC BY-SA and CC NC for commercial full IP transfer scenarios
- For CC BY include author and source. Keep proofs of license pages at download time in models/AmaFusion_V1/EVIDENCE/

Template entries

| Dataset name | Link | License | Attribution text to include | Notes |
| --- | --- | --- | --- | --- |
| [REPLACE_NAME] | [URL] | CC0 | Not required |  |
| [REPLACE_NAME] | [URL] | CC BY 4.0 | © Author Name. Licensed under CC BY 4.0. | Include author as specified by dataset |
| Manga109-s | https://huggingface.co/datasets/ykonya/Manga109-s | As stated on dataset card for commercial use | As required on card | Use only the s subset that permits commercial use |
| [Remove if present] EasyPortrait | https://huggingface.co/datasets/gofixyourself/EasyPortrait | CC BY-SA 4.0 | ShareAlike may impose downstream sharing conditions | Do not include if you plan full IP transfer without SA obligations unless you obtain explicit permission that waives SA for training use |

Provide the final, exact list in models/AmaFusion_V1/DATA_SOURCES.md

## Notices and use restrictions

- CreativeML Open RAIL-M imposes use-based restrictions. When you distribute weights or provide access via API you must include a clear notice of these restrictions and a link to the full license text.
- Keep OpenRAIL-M.txt together with the model weights and MODEL_CARD.md
- The buyer of AmaFusion_V1 accepts ongoing compliance with the upstream licenses

## Third party code dependencies

This section refers only to model tooling that may accompany weights, not to your application code.
Generate automatic license inventories and keep them under version control:

- Python: pip-licenses --format=markdown --with-authors --with-urls > THIRD_PARTY_LICENSES_PY.md
- Node: npx license-checker --production --summary > THIRD_PARTY_LICENSES_WEB.txt

Store these in compliance/ or repository root. These files do not replace this ATTRIBUTIONS document.

## Provenance chain

Stable Diffusion v1.5 -> DreamShaper v6 -> AmaFusion_V1
- Base and upstream are under CreativeML Open RAIL-M
- AmaFusion_V1 inherits the obligation to preserve license notices and use-based restrictions
- VAE sd-vae-ft-mse is under MIT and can be redistributed with its MIT text

## File map

- models/AmaFusion_V1/LICENSES/OpenRAIL-M.txt full text of CreativeML Open RAIL-M
- models/AmaFusion_V1/LICENSES/Upstream_DreamShaper_LICENSE.txt upstream record and links
- models/AmaFusion_V1/LICENSES/VAE_LICENSE.txt full MIT text for sd-vae-ft-mse
- models/AmaFusion_V1/DATA_SOURCES.md concrete dataset list and licenses
- models/AmaFusion_V1/EVIDENCE/ optional screenshots or PDFs of dataset license pages on the download date
- models/AmaFusion_V1/MODEL_CARD.md must explicitly reference OpenRAIL-M and summarize use restrictions

## Contact

Maintainer: Ama
Compliance contact: <email or URL>
Last verified: <YYYY-MM-DD>
