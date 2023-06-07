from fastapi import FastAPI
from sqlmodel import Session, select
from easul.server import models


app = FastAPI()

@app.on_event("startup")
def on_startup():
    models.create_db_and_tables()

@app.post("/journeys/")
def create_journey(journey:models.JourneyCreate):
    with Session(models.engine) as session:
        db_journey = models.Journey.from_orm(journey)
        session.add(db_journey)
        session.commit()
        session.refresh(db_journey)
        return db_journey

@app.get("/journeys/")
def read_journey():
    with Session(models.engine) as session:
        journeys = session.exec(select(models.Journey)).all()
        return journeys
