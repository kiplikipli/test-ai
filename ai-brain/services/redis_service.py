import json

from redis.asyncio import Redis

from config import settings
from models.meeting_state import MeetingState


class RedisService:
    def __init__(self) -> None:
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)

    @staticmethod
    def _key(session_id: str) -> str:
        return f'meeting_session:{session_id}'

    async def load_state(self, session_id: str) -> MeetingState | None:
        data = await self.client.get(self._key(session_id))
        if not data:
            return None
        return MeetingState.model_validate(json.loads(data))

    async def save_state(self, state: MeetingState) -> None:
        payload = state.model_dump(mode='json')
        await self.client.set(self._key(state.session_id), json.dumps(payload), ex=settings.redis_ttl_seconds)

    async def delete_state(self, session_id: str) -> None:
        await self.client.delete(self._key(session_id))
