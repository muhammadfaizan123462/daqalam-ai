#!/usr/bin/env python3
"""Qwen (Alibaba DashScope, OpenAI-compatible) helper.

Calls https://dashscope-intl.aliyuncs.com/compatible-mode/v1 using the
registered custom.qwen credential. The key itself is never in this file:
dynamic_credentials.py places a surrogate in the Authorization header and
Muse swaps in the real credential on an approved request to the registered
host.

Usage:
  qwen.py list-models
  qwen.py generate --model qwen-plus --prompt "Hello"
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
ALLOWED_HOSTS = ["dashscope-intl.aliyuncs.com"]
CONNECTOR = "custom.qwen"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def _open(request: urllib.request.Request, data: bytes | None = None):
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, data=data, timeout=60) as response:
        return read_json_response(response)


def list_models() -> dict:
    request = urllib.request.Request(f"{BASE_URL}/models")
    add_surrogate_to_request(request, CONNECTOR, allowed_hosts=ALLOWED_HOSTS)
    return _open(request)


def generate(model: str, prompt: str) -> dict:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
    ).encode()
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    add_surrogate_to_request(request, CONNECTOR, allowed_hosts=ALLOWED_HOSTS)
    return _open(request, data=payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qwen DashScope helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-models")
    gen = sub.add_parser("generate")
    gen.add_argument("--model", default="qwen-plus")
    gen.add_argument("--prompt", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list-models":
            print(json.dumps(list_models(), indent=2))
        else:
            result = generate(args.model, args.prompt)
            content = result["choices"][0]["message"]["content"]
            print(content)
    except Exception as exc:  # noqa: BLE001 - report the failure plainly
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
