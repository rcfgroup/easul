from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine
import datetime as dt

class JourneyBase(SQLModel):
    timestamp: dt.datetime
    reference: str
    source: str
    label: str
    complete: bool

class Journey(JourneyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class JourneyCreate(JourneyBase):
    pass

class JourneyRead(JourneyBase):
    id: int

engine = create_engine("sqlite:///database.db")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

