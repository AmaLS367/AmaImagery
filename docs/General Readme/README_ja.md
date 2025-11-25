# genai — プロジェクトガイド (日本語)

## 概要

このリポジトリは NSFW 画像生成のフルスタックプロジェクトです。
- バックエンド: Python + FastAPI（デフォルト: ポート8000）
- フロントエンド: React + TypeScript + Vite（dev: ポート5173）

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

開発ではフロントエンドで相対パス `/generate` を使って Vite のプロキシを利用してください。

---

（詳細は `README_en.md` を参照してください。）
