# Image Generator

## Legal and licensing

This repository ships model weights and documentation that depend on upstream components.

- Stable Diffusion v1.5 — CreativeML Open RAIL-M
- DreamShaper v6 — CreativeML Open RAIL-M
- VAE sd-vae-ft-mse — MIT

Full texts and records are provided under models/AmaFusion_V1/LICENSES/
- OpenRAIL-M.txt — full text of CreativeML Open RAIL-M
- Upstream_DreamShaper_LICENSE.txt — upstream model record and links
- VAE_LICENSE.txt — full MIT text

Use-based restrictions
When distributing weights or providing model access as a service, include a clear notice of the CreativeML Open RAIL-M restrictions and link the full license text. Keep OpenRAIL-M.txt and this repository’s MODEL_CARD.md together with the weights.

Datasets
See models/AmaFusion_V1/DATA_SOURCES.md for the list of datasets actually used for training, their license terms, required attribution strings, and evidence files. Prefer CC0 and CC BY datasets.

Provenance and attributions
See ATTRIBUTIONS.md for the consolidated provenance chain and links.

### Files map

- models/AmaFusion_V1/LICENSES/OpenRAIL-M.txt    full OpenRAIL-M text
- models/AmaFusion_V1/LICENSES/Upstream_DreamShaper_LICENSE.txt    upstream record and links
- models/AmaFusion_V1/LICENSES/VAE_LICENSE.txt   full MIT text for sd-vae-ft-mse
- models/AmaFusion_V1/DATA_SOURCES.md            dataset ledger
- models/AmaFusion_V1/MODEL_CARD.md              model card with legal section
- ATTRIBUTIONS.md                                 consolidated upstream references
- NOTICE.txt                                      high-level notice about third-party licenses

## Install
```bash
py -3.11 -m venv .venv && . .venv\Scripts\Activate.ps1 (.\.venv\Scripts\Activate.ps1)
python -m pip install --upgrade pip wheel setuptools
pip install --index-url https://download.pytorch.org/whl/cu121 ^
  torch==2.2.2+cu121 torchvision==0.17.2+cu121 torchaudio==2.2.2+cu121
(powershell: pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.2.2+cu121 torchvision==0.17.2+cu121 torchaudio==2.2.2+cu121)

pip install xformers==0.0.25.post1
pip install "diffusers==0.29.2"
pip install -r requirements.txt
```

## Run
```bash
python run.py
```
