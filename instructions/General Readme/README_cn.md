# genai — 项目指南（中文）

## 概览

这是一个端到端的图像生成项目（含 NSFW 用例）。
- 后端：Python + FastAPI，监听 8000 端口。
- 前端：React + TypeScript + Vite，开发时监听 5173。

本指南包含运行说明、架构、日志、生成流程和排障方法。

---

## 本地快速启动

前置：Python 3.11+、Node.js 18+

PowerShell 命令：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

提示：前端使用 Vite proxy，将 `/generate` 转发到后端，因此前端应使用相对路径 `/generate`。

---

## 生成流程

1. 用户在 `Generate.tsx` 点击生成。
2. 前端构建 payload 并推入 `RequestQueue` 队列。
3. `generateJSON` 发起 `fetch('/generate')`。
4. Vite 将请求代理到 `http://localhost:8000/generate`。
5. 后端执行模型推理并返回 `path` 等信息。
6. 前端通过 `/file?path=...` 显示图片。

---

## 排错要点

- 若点击按钮没有发出请求：打开浏览器 DevTools，查看 Console（应有 `Button clicked`）和 Network（应有 `/generate`）。
- 若后端可通过 curl 访问但前端没发请求：检查 `vite.config.ts` 的 proxy、`api.ts` 使用的路径、以及 `RequestQueue` 行为。

---

如需我把指南转为 PDF、添加架构图或扩展到 CI/CD 部署说明，我可以继续完善。
