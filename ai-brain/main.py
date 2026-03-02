import json
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.mastermind import process_message
from agents.sql_generator import generate_employee_sql
from config import settings
from models.meeting_state import MeetingState
from services.redis_service import RedisService

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format='%(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
redis_service = RedisService()


class AIProcessRequest(BaseModel):
    sessionId: str
    message: str
    userEmail: str
    legalEntityId: int


class AIProcessResponse(BaseModel):
    sessionId: str
    response: str
    status: str


class SQLGenerateRequest(BaseModel):
    ddl: str
    request: str
    legalEntityId: int


class SQLGenerateResponse(BaseModel):
    sql: str


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@app.post('/ai/process', response_model=AIProcessResponse)
async def ai_process(request: AIProcessRequest) -> AIProcessResponse:
    state = await redis_service.load_state(request.sessionId)
    if state is None:
        state = MeetingState(
            session_id=request.sessionId,
            legal_entity_id=request.legalEntityId,
            requester_email=request.userEmail,
        )

    response_text = ''
    try:
        state, response_text = await process_message(state, request.message)
    finally:
        logger.info(
            json.dumps(
                {
                    'session_id': request.sessionId,
                    'legal_entity_id': request.legalEntityId,
                    'requester_email': request.userEmail,
                    'status': state.status,
                }
            )
        )

    if state.status == 'completed':
        await redis_service.delete_state(state.session_id)
    else:
        await redis_service.save_state(state)

    return AIProcessResponse(sessionId=request.sessionId, response=response_text, status=state.status)


@app.post('/ai/sql/generate', response_model=SQLGenerateResponse)
async def ai_sql_generate(request: SQLGenerateRequest) -> SQLGenerateResponse:
    try:
        sql = await generate_employee_sql(
            ddl=request.ddl,
            user_request=request.request,
            legal_entity_id=request.legalEntityId,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        json.dumps(
            {
                'event': 'sql_generation',
                'legal_entity_id': request.legalEntityId,
                'request': request.request,
                'sql': sql,
            }
        )
    )
    return SQLGenerateResponse(sql=sql)
