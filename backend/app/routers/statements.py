from urllib.parse import quote
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_session

from app.services import statements

router = APIRouter(prefix='/api/statements', tags=['statements'])

@router.get('')
def list_statements(session: Annotated[Session, Depends(get_session)],
                    offset: Annotated[int, Query(ge=0)] = 0,
                    limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return statements.list_statements(session=session, offset=offset, limit=limit)


@router.get('/{statement_id}')
def read_statement(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    return statements.read_statement(statement_id=statement_id, session=session)


@router.get('/{statement_id}/summary')
def statement_summary(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    return statements.statement_summary(statement_id=statement_id, session=session)


@router.get('/{statement_id}/file')
def download_statement(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    statement = statements.download_statement(statement_id=statement_id, session=session)
    return Response(content=statement.csv_contents, media_type='text/csv', headers={
        'Content-Disposition': f"attachment; filename*=UTF-8''{quote(statement.filename, safe='')}",
        'X-Content-Type-Options': 'nosniff',
    })
