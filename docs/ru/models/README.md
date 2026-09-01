# Models

AmaImagery — code-only repository. Он не распространяет веса моделей, датасеты и Hugging Face cache. В отслеживаемом `models/` остаются только лёгкие конфигурации для опциональных локальных runtime-ов.

## Настройка provider-а

- **ComfyUI:** запустите ComfyUI отдельно, получите checkpoints на условиях их источника и задайте `COMFYUI_BASE_URL`.
- **Diffusers:** укажите в `MODEL_ID` Hugging Face model identifier либо локальный путь вне Git. В `.env.example` по умолчанию указан `runwayml/stable-diffusion-v1-5`.

Для первой онлайн-загрузки Diffusers установите `NO_NETWORK=false`; если upstream-модель требует подтверждения доступа, задайте `HF_TOKEN`. После загрузки модели в cache или по локальному пути установите `NO_NETWORK=true` для offline-режима.

`VAE_ID`, `IP_ADAPTER_DIR` и `IP_IMAGE_ENCODER_PATH` опциональны и должны указывать на assets, которые оператор получил самостоятельно.

## Compliance

Лицензия модели не становится лицензией приложения. Перед скачиванием, использованием, распространением или предоставлением модели проверьте её upstream-лицензию и [NOTICE](../../../NOTICE.txt).

## Связанные разделы

- [Backend Providers](../backend/providers.md)
- [Docker](../docker/README.md)
- [Reference](../reference/README.md)
