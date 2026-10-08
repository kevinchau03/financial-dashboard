import csv
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
from app.database import get_session
from app.services.csv_import import read_csv, clean_data, load_csv
from app.services.analytics import get_total_income, get_total_spent, get_time_range

router = APIRouter(tags=['uploads'])

@router.post("/api/upload_csv")
async def upload_csv(file: UploadFile, session: Annotated[Session, Depends(get_session)], format: Annotated[Literal['csv', 'td'], Form()] = 'csv'):
    try:
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(400, 'Please upload a CSV file.')
        contents = await file.read(5 * 1024 * 1024 + 1)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(413, 'CSV files must be no larger than 5 MB.')
        try:
            extracted = read_csv(contents, format=format)
            cleaned = clean_data(extracted)
            data = load_csv(cleaned, session, filename=file.filename, contents=contents)
        except UnicodeDecodeError:
            raise HTTPException(400, 'Please save your CSV with UTF-8 encoding.')
        except (csv.Error, ValueError) as error:
            raise HTTPException(400, str(error))
        if format == 'td':
            statement_id = data['statement_id']
            start_date, end_date = get_time_range(session, statement_id)
            data['stats'] = {
                'total_income': str(get_total_income(session, statement_id)),
                'total_spent': str(get_total_spent(session, statement_id)),
                'start_date': start_date,
                'end_date': end_date,
            }
        return {'filename': file.filename, **data, 'row_count': len(data['rows'])}
    finally:
        await file.close()
