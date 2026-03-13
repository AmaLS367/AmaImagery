import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx

BASE_URL = os.getenv("AMAIMAGERY_API", "http://localhost:8000").rstrip("/")
OUTPUT_DIR = Path("outputs")
DEFAULT_TIMEOUT = 20.0
DEFAULT_POLL_TIMEOUT_SEC = 900
DEFAULT_POLL_INTERVAL_SEC = 3.0

PAYLOAD = {
    "prompt": (
        "masterpiece, best quality, 1girl, solo, school uniform, pleated skirt, thighhighs," 
        "ponytail, brown hair, blush, embarrassed, panties visible, white panties,"
        "rating:explicit, nsfw "
    ),
    "negative_prompt": (
        "lowres, worst quality, bad quality, bad anatomy, extra limbs, extra fingers, "
        "fused fingers, missing arms, disfigured, watermark, signature, text"
    ),
    "steps": 28,
    "guidance_scale": 7,
    "width": 1024,
    "height": 1024,
}


def _client() -> httpx.Client:
    return httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)


def generate(client: httpx.Client, payload: dict) -> str:
    response = client.post(f"{BASE_URL}/api/v1/images/generate", json=payload)
    response.raise_for_status()
    data = response.json()
    task_id = data["task_id"]
    print(f"Task ID: {task_id}")
    return task_id


def poll(client: httpx.Client, task_id: str, timeout_sec: int, interval_sec: float) -> dict:
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        response = client.get(f"{BASE_URL}/api/v1/images/status/{task_id}")
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        provider = data.get("provider_name")
        print(f"Status: {status} | Provider: {provider}")

        if status in {"completed", "failed", "canceled"}:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data

        time.sleep(interval_sec)

    raise TimeoutError(f"Timed out waiting for generation {task_id}")


def download_image(client: httpx.Client, status_payload: dict) -> Path | None:
    image_url = status_payload.get("image_url")
    if not image_url:
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = status_payload.get("image_filename") or f"{status_payload['task_id']}.png"
    target = OUTPUT_DIR / filename

    absolute_url = image_url if image_url.startswith("http") else urljoin(f"{BASE_URL}/", image_url.lstrip("/"))
    with client.stream("GET", absolute_url) as response:
        response.raise_for_status()
        with target.open("wb") as file_obj:
            for chunk in response.iter_bytes():
                file_obj.write(chunk)

    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit a generation request and wait for completion.")
    parser.add_argument("--prompt", default=PAYLOAD["prompt"], help="Main prompt")
    parser.add_argument("--negative-prompt", default=PAYLOAD["negative_prompt"], help="Negative prompt")
    parser.add_argument("--steps", type=int, default=PAYLOAD["steps"], help="Inference steps")
    parser.add_argument("--guidance-scale", type=float, default=PAYLOAD["guidance_scale"], help="CFG / guidance")
    parser.add_argument("--width", type=int, default=PAYLOAD["width"], help="Image width")
    parser.add_argument("--height", type=int, default=PAYLOAD["height"], help="Image height")
    parser.add_argument("--style", default="anime", choices=["anime", "realistic"], help="Generation style")
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_POLL_TIMEOUT_SEC, help="Polling timeout")
    parser.add_argument(
        "--interval-sec",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SEC,
        help="Polling interval in seconds",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = {
        "prompt": args.prompt,
        "negative_prompt": args.negative_prompt,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "width": args.width,
        "height": args.height,
        "style": args.style,
    }

    with _client() as client:
        task_id = generate(client, payload)
        result = poll(client, task_id, timeout_sec=args.timeout_sec, interval_sec=args.interval_sec)

        if result.get("status") != "completed":
            return 1

        path = download_image(client, result)
        if path is not None:
            print(f"Saved image to: {path}")
        else:
            print("Generation completed but no image_url was returned.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
