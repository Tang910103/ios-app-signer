#!/usr/bin/env python3
"""Test App Store Connect external TestFlight group automation without upload."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASE = "https://api.appstoreconnect.apple.com/v1"


class ASCError(RuntimeError):
    pass


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def run_openssl_sign(message: bytes, key_path: Path) -> bytes:
    process = subprocess.run(
        ["/usr/bin/openssl", "dgst", "-sha256", "-sign", str(key_path)],
        input=message,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise ASCError(
            "OpenSSL 签名失败:\n" + process.stderr.decode("utf-8", errors="replace").strip()
        )
    return process.stdout


def make_jwt(key_id: str, issuer_id: str, private_key: Path) -> str:
    now = int(time.time())
    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    payload = {"iss": issuer_id, "aud": "appstoreconnect-v1", "iat": now, "exp": now + 1200}
    signing_input = f"{b64url(json.dumps(header, separators=(',', ':')).encode())}.{b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = run_openssl_sign(signing_input.encode("utf-8"), private_key)
    return f"{signing_input}.{b64url(signature)}"


def format_asc_errors(payload: dict[str, Any] | None) -> str:
    if not payload:
        return "未知错误"
    errors = payload.get("errors")
    if not isinstance(errors, list) or not errors:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    lines: list[str] = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        parts = [item.get("code"), item.get("title"), item.get("detail")]
        text = " | ".join(str(part) for part in parts if part)
        if text:
            lines.append(text)
    return "\n".join(lines) if lines else json.dumps(payload, ensure_ascii=False, indent=2)


def request_json(
    token: str,
    method: str,
    path: str,
    query: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{API_BASE}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        payload = None
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                payload = None
        raise ASCError(f"{method} {path} 失败 (HTTP {exc.code})\n{format_asc_errors(payload)}") from exc
    except urllib.error.URLError as exc:
        raise ASCError(f"{method} {path} 网络错误: {exc.reason}") from exc

    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def fetch_all(token: str, path: str, query: dict[str, str] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url = f"{API_BASE}{path}"
    next_query = query or {}

    while next_url:
        if next_query:
            url = next_url + "?" + urllib.parse.urlencode(next_query, doseq=True)
        else:
            url = next_url

        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            payload = None
            if raw:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except Exception:
                    payload = None
            raise ASCError(f"GET {path} 失败 (HTTP {exc.code})\n{format_asc_errors(payload)}") from exc

        items.extend(payload.get("data", []))
        links = payload.get("links") or {}
        next_href = links.get("next")
        if next_href:
            parsed = urllib.parse.urlparse(next_href)
            next_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            next_query = dict(urllib.parse.parse_qsl(parsed.query))
        else:
            next_url = ""
            next_query = {}

    return items


def find_app(token: str, bundle_id: str | None, app_id: str | None) -> dict[str, Any]:
    if app_id:
        payload = request_json(token, "GET", f"/apps/{app_id}")
        return payload["data"]
    if not bundle_id:
        raise ASCError("请提供 --bundle-id 或 --app-id")
    apps = fetch_all(token, "/apps", {"filter[bundleId]": bundle_id})
    if not apps:
        raise ASCError(f"未找到 bundle id 为 {bundle_id} 的 App")
    return apps[0]


def list_beta_groups(token: str, app_id: str) -> list[dict[str, Any]]:
    return fetch_all(token, f"/apps/{app_id}/betaGroups", {"limit": "200"})


def attrs(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("attributes") or {}


def ensure_internal_group(groups: list[dict[str, Any]]) -> None:
    for group in groups:
        if attrs(group).get("isInternalGroup") is True:
            return
    raise ASCError("App Store Connect 中还没有 Internal Testing 组，Apple 不允许直接创建 External Testing 组。")


def ensure_external_group(token: str, app_id: str, group_name: str, groups: list[dict[str, Any]]) -> tuple[dict[str, Any], bool]:
    for group in groups:
        a = attrs(group)
        if a.get("isInternalGroup") is True:
            continue
        if a.get("name") == group_name:
            return group, False

    payload = {
        "data": {
            "type": "betaGroups",
            "attributes": {
                "name": group_name,
                "isInternalGroup": False,
                "publicLinkEnabled": False,
            },
            "relationships": {
                "app": {
                    "data": {
                        "type": "apps",
                        "id": app_id,
                    }
                }
            },
        }
    }
    created = request_json(token, "POST", "/betaGroups", body=payload)
    return created["data"], True


def ensure_public_link(token: str, group: dict[str, Any], limit: int | None) -> tuple[dict[str, Any], bool]:
    current = attrs(group)
    if current.get("publicLink"):
        return group, False

    attributes: dict[str, Any] = {"publicLinkEnabled": True}
    if limit is not None:
        attributes["publicLinkLimitEnabled"] = True
        attributes["publicLinkLimit"] = limit

    payload = {
        "data": {
            "id": group["id"],
            "type": "betaGroups",
            "attributes": attributes,
        }
    }
    updated = request_json(token, "PATCH", f"/betaGroups/{group['id']}", body=payload)
    return updated["data"], True


def find_build(
    token: str,
    app_id: str,
    version: str | None,
    build_number: str | None,
    build_id: str | None,
) -> dict[str, Any]:
    if build_id:
        payload = request_json(token, "GET", f"/builds/{build_id}")
        return payload["data"]

    query: dict[str, str] = {"filter[app]": app_id, "limit": "200"}
    if version:
        query["filter[preReleaseVersion.version]"] = version

    builds = fetch_all(token, "/builds", query)
    valid_builds: list[dict[str, Any]] = []
    for build in builds:
        a = attrs(build)
        if a.get("processingState") != "VALID":
            continue
        if build_number and a.get("version") != build_number:
            continue
        valid_builds.append(build)

    if not valid_builds:
        wanted = f"version={version or '*'}, build={build_number or '*'}"
        raise ASCError(f"没有找到可挂组的 VALID build: {wanted}")

    valid_builds.sort(key=lambda item: (attrs(item).get("uploadedDate") or "", attrs(item).get("version") or ""))
    return valid_builds[-1]


def attach_build(token: str, group_id: str, build_id: str) -> None:
    payload = {
        "data": [
            {
                "type": "builds",
                "id": build_id,
            }
        ]
    }
    request_json(token, "POST", f"/betaGroups/{group_id}/relationships/builds", body=payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="单独测试 TestFlight 外部分组和挂组流程")
    parser.add_argument("--api-key-id", required=True, help="App Store Connect API Key ID")
    parser.add_argument("--issuer-id", required=True, help="App Store Connect Issuer ID")
    parser.add_argument("--private-key", required=True, help="AuthKey_<KEYID>.p8 文件路径")
    parser.add_argument("--bundle-id", help="App 的 bundle id")
    parser.add_argument("--app-id", help="App Store Connect app id，可替代 bundle id")
    parser.add_argument("--external-group", required=True, help="目标外部测试组名称")
    parser.add_argument("--public-link-limit", type=int, help="公开链接人数上限")
    parser.add_argument("--build-version", help="营销版本号，例如 2.3.1")
    parser.add_argument("--build-number", help="构建号，例如 231")
    parser.add_argument("--build-id", help="直接指定 ASC build id")
    parser.add_argument(
        "--skip-attach-build",
        action="store_true",
        help="只测试创建/查询外部测试组和公开链接，不挂 build",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = make_jwt(args.api_key_id, args.issuer_id, Path(args.private_key))

    app = find_app(token, args.bundle_id, args.app_id)
    app_id = app["id"]
    app_name = attrs(app).get("name", "")
    bundle_id = attrs(app).get("bundleId", args.bundle_id or "")
    print(f"App: {app_name} ({bundle_id})")
    print(f"App ID: {app_id}")

    groups = list_beta_groups(token, app_id)
    ensure_internal_group(groups)
    group, was_created = ensure_external_group(token, app_id, args.external_group, groups)
    print(f"External Group: {attrs(group).get('name')} ({group['id']})")
    print("Group Action:", "created" if was_created else "reused")

    group, link_enabled = ensure_public_link(token, group, args.public_link_limit)
    group_attrs = attrs(group)
    print("Public Link Action:", "enabled" if link_enabled else "reused")
    print("Public Link:", group_attrs.get("publicLink") or "<none>")

    if args.skip_attach_build:
        print("Build Attach: skipped")
        return 0

    build = find_build(token, app_id, args.build_version, args.build_number, args.build_id)
    build_attrs = attrs(build)
    print(
        "Selected Build:",
        f"id={build['id']}, buildNumber={build_attrs.get('version')}, processingState={build_attrs.get('processingState')}",
    )
    attach_build(token, group["id"], build["id"])
    print("Build Attach: success")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ASCError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
