# Режимы онлайн/оффлайн — кратко

## Размещение

* Кэш проекта: `models\.cache\huggingface\hub`
* Локальные модели:
  * чекпоинт SD: `models\*.safetensors` 
  * VAE (оффлайн): `models\vae\sd-vae-ft-mse\`

## Переменные окружения (обязательны для процесса)

* Переключатели режима:

  * **Оффлайн**:
    `NO_NETWORK=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 DIFFUSERS_OFFLINE=1`
  * **Онлайн**:
    `NO_NETWORK=0 HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 DIFFUSERS_OFFLINE=0`
* Пути кэша HF:

  * `HF_HOME=\models\.cache\huggingface`
  * `HUGGINGFACE_HUB_CACHE=\models\.cache\huggingface\hub`
  * `TRANSFORMERS_CACHE=\models\.cache\huggingface\hub`
* VAE:

  * оффлайн: `VAE_ID=models/vae/sd-vae-ft-mse`
  * онлайн:  `VAE_ID=stabilityai/sd-vae-ft-mse` (можно и локальный путь)

## Разовый прогрев кэша (онлайн)

PowerShell:

```powershell
$env:NO_NETWORK="0"; $env:HF_HUB_OFFLINE="0"; $env:TRANSFORMERS_OFFLINE="0"; $env:DIFFUSERS_OFFLINE="0"
$env:HF_HOME="$PWD\models\.cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE="$PWD\models\.cache\huggingface\hub"
$env:TRANSFORMERS_CACHE="$PWD\models\.cache\huggingface\hub"
python .\scripts\python\warm_cache.py
```

Результат: в кэше появятся snapshots для `runwayml/stable-diffusion-v1-5`, CLIP и VAE. После этого оффлайн не обращается к сети.

## Запуск: оффлайн

```powershell
$env:NO_NETWORK="1"; $env:HF_HUB_OFFLINE="1"; $env:TRANSFORMERS_OFFLINE="1"; $env:DIFFUSERS_OFFLINE="1"
$env:HF_HOME="$PWD\models\.cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE="$PWD\models\.cache\huggingface\hub"
$env:TRANSFORMERS_CACHE="$PWD\models\.cache\huggingface\hub"
$env:VAE_ID="models/vae/sd-vae-ft-mse"
python .\run.py
```

## Запуск: онлайн

```powershell
$env:NO_NETWORK="0"; $env:HF_HUB_OFFLINE="0"; $env:TRANSFORMERS_OFFLINE="0"; $env:DIFFUSERS_OFFLINE="0"
$env:HF_HOME="$PWD\models\.cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE="$PWD\models\.cache\huggingface\hub"
$env:TRANSFORMERS_CACHE="$PWD\models\.cache\huggingface\hub"
$env:VAE_ID="stabilityai/sd-vae-ft-mse"   # либо локальный путь
python .\run.py
```

## Поведение пайплайна (важно)

* **Оффлайн**: `config` для `from_single_file` берётся из локального snapshot `runwayml/stable-diffusion-v1-5`; VAE — из `models/vae/sd-vae-ft-mse`; `local_files_only=True`.
* **Онлайн**: `config="runwayml/stable-diffusion-v1-5"`; VAE — по `VAE_ID` (repo id или локальный путь); `local_files_only=False`.
* IP-Adapter в оффлайне отключается (нет онлайновых зависимостей) — без падений.

## Роут `/file` (чтобы изображения открывались)

* В `main.py` в lifespan-прослойке должно быть: `app.state.redis_client = redis_client`.
* В `routes/files.py` Redis трогаем **только** когда `FILE_SINGLE_USE=1`. При `FILE_SINGLE_USE=0` никакого запроса к Redis нет.

## Диагностика по логам

* `mode.offline` / `mode.online` — активный режим пайплайна.
* HF ошибки:

  * `LocalEntryNotFoundError` в оффлайне — нет нужного snapshot в `models\.cache\...` → прогреть кэш онлайн.
  * `Invalid config` — в `from_single_file(config=...)` передан не repo id и не путь к локальному diffusers-репо → проверить `config`.
* `/file`:

  * `file.signature_invalid` — сломанная подпись ссылки.
  * `file.link_expired` — срок истёк.
  * `file.redis_missing` — включён `FILE_SINGLE_USE=1`, но `app.state.redis_client` не выставлен.
  * `file.not_found` / `file.unsupported_type` — несуществующий путь или запрещённый тип.

## Замечание по Windows

Предупреждение про symlink в кэше HF — штатно. Если бесит, добавь
`HF_HUB_DISABLE_SYMLINKS_WARNING=1`.

## Версии 

torch==2.2.2+cu121
torchvision==0.17.2+cu121
torchaudio==2.2.2+cu121
xformers==0.0.25.post1
diffusers==0.29.2
transformers==4.57.0
huggingface-hub==0.35.3
tokenizers==0.22.1
safetensors==0.6.2
accelerate==1.10.1
pillow==11.3.0
numpy==1.26.4

