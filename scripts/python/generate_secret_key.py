import argparse
import base64
import os
import secrets
import sys
from pathlib import Path

DJANGO_ALLOWED = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"


def gen_urlsafe(nbytes: int) -> str:
    # ~4/3 * nbytes characters, URL-safe only
    return secrets.token_urlsafe(nbytes)


def gen_hex(nbytes: int) -> str:
    # Exactly 2*nbytes characters [0-9a-f]
    return secrets.token_hex(nbytes)


def gen_base64(nbytes: int) -> str:
    # URL-safe Base64 without padding
    return base64.urlsafe_b64encode(os.urandom(nbytes)).rstrip(b"=").decode("ascii")


def gen_django(length: int = 50) -> str:
    # Compatible with Django SECRET_KEY format
    return "".join(secrets.choice(DJANGO_ALLOWED) for _ in range(length))


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--format", choices=["urlsafe", "hex", "base64", "django"], default="urlsafe")
    p.add_argument("--bytes", type=int, default=64, help="Raw buffer size in bytes for urlsafe/hex/base64")
    p.add_argument("--length", type=int, default=50, help="String length for --format=django")
    p.add_argument("--env-var", type=str, default="", help="Environment variable name to write to file")
    p.add_argument("--out", type=Path, default=None, help="Path to .env file; if provided, appends ENV=VALUE")
    p.add_argument("--help", action="store_true")
    args = p.parse_args()

    if args.help:
        print(
            "Examples:\n"
            "  python generate_secret_key.py                      # URL-safe ~86 chars\n"
            "  python generate_secret_key.py --format=hex         # 128 hex chars\n"
            "  python generate_secret_key.py --format=base64      # URL-safe Base64\n"
            "  python generate_secret_key.py --format=django      # 50 chars (Django style)\n"
            "  python generate_secret_key.py --env-var=SECRET_KEY --out=.env\n",
            file=sys.stderr,
        )
        return 0

    if args.format == "urlsafe":
        key = gen_urlsafe(args.bytes)
    elif args.format == "hex":
        key = gen_hex(args.bytes)
    elif args.format == "base64":
        key = gen_base64(args.bytes)
    else:
        key = gen_django(args.length)

    print(key)

    if args.out and args.env_var:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        line = f"{args.env_var}={key}\n"
        if args.out.exists() and args.out.stat().st_size > 0:
            with args.out.open("rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    line = "\n" + line
        with args.out.open("a", encoding="utf-8") as f:
            f.write(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
