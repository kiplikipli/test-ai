import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import settings


class SQLGenerationResult(BaseModel):
    sql: str


_llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    temperature=0,
)

_prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (
                'Generate exactly one safe MySQL SELECT statement. '
                'Never generate INSERT/UPDATE/DELETE/DDL. '
                'Always include `legal_entity_id = {{LEGAL_ENTITY_ID}}` in WHERE clause. '
                'Use only columns/tables from provided DDL. '
                'Add LIMIT 50 if not present. '
                'Return only SQL text.'
            ),
        ),
        (
            'human',
            'DDL:\n{ddl}\n\nUser request:\n{user_request}\n\nlegal_entity_id: {legal_entity_id}',
        ),
    ]
)


def _validate_generated_sql(sql: str) -> str:
    compact = re.sub(r'\s+', ' ', sql.strip())
    lowered = compact.lower()

    if not lowered.startswith('select '):
        raise ValueError('Only SELECT SQL is allowed.')
    if ';' in compact[:-1]:
        raise ValueError('Only one SQL statement is allowed.')
    if ' legal_entity_id ' not in f' {lowered} ':
        raise ValueError('SQL must include legal_entity_id filter.')
    banned = [' insert ', ' update ', ' delete ', ' drop ', ' alter ', ' truncate ', ' create ']
    if any(token in f' {lowered} ' for token in banned):
        raise ValueError('Unsafe SQL detected.')
    if ' limit ' not in f' {lowered} ':
        compact = f'{compact.rstrip(";")} LIMIT 50'
    return compact.rstrip(';')


async def generate_employee_sql(ddl: str, user_request: str, legal_entity_id: int) -> str:
    structured = _llm.with_structured_output(SQLGenerationResult)
    chain = _prompt | structured
    result = await chain.ainvoke(
        {
            'ddl': ddl,
            'user_request': user_request,
            'legal_entity_id': legal_entity_id,
        }
    )
    sql = result.sql.replace('{{LEGAL_ENTITY_ID}}', str(legal_entity_id))
    return _validate_generated_sql(sql)
