# NSFW Image Generator

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

## Online:
```bash
cp .env.online .env
python run.py
```

## Offline:
```bash
cp .env.offline .env
# распаковать архив models/ в /app/models
python run.py
```
