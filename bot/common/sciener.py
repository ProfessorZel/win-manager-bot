import hashlib
import time

import httpx

from common.config import settings

_access_token: str | None = None
_lock_id: int | None = None


async def _authenticate():
    global _access_token
    md5_pass = hashlib.md5(settings.sciener_password.encode()).hexdigest()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.sciener_api_url}/oauth2/token",
            data={
                "clientId": settings.sciener_client_id,
                "clientSecret": settings.sciener_client_secret,
                "username": settings.sciener_username,
                "password": md5_pass,
            },
        )
        data = resp.json()
        if "access_token" not in data:
            raise Exception(f"Sciener auth failed: {data}")
        _access_token = data["access_token"]


async def _fetch_lock_id():
    global _lock_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.sciener_api_url}/v3/key/list",
            params={
                "clientId": settings.sciener_client_id,
                "accessToken": _access_token,
                "pageNo": 1,
                "pageSize": 100,
                "date": int(time.time() * 1000),
            },
        )
        data = resp.json()
        keys = data.get("list", [])
        if not keys:
            raise Exception("Sciener: замки не найдены")
        _lock_id = keys[0]["lockId"]


async def ensure_auth():
    if not _access_token:
        await _authenticate()
    if not _lock_id:
        await _fetch_lock_id()


async def add_keyboard_password(name: str, pwd: str) -> dict:
    await ensure_auth()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.sciener_api_url}/v3/keyboardPwd/add",
            data={
                "clientId": settings.sciener_client_id,
                "accessToken": _access_token,
                "lockId": _lock_id,
                "keyboardPwdType": 2,
                "keyboardPwd": pwd,
                "keyboardPwdName": name,
                "date": int(time.time() * 1000),
            },
        )
        return resp.json()
