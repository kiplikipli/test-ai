import asyncio

import httpx

from config import settings


class ToolClientError(RuntimeError):
    pass


async def call_tool(endpoint: str, payload: dict) -> dict:
    if 'legal_entity_id' not in payload:
        raise ToolClientError('Missing required legal_entity_id for tool call.')

    url = f"{settings.n8n_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    attempts = 2
    last_error: Exception | None = None

    for _ in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            await asyncio.sleep(0.25)

    raise ToolClientError(f'Tool call failed for {endpoint}: {last_error}')
