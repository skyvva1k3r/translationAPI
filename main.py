import os
import requests
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Numeric, VARCHAR, text, insert
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from deep_translator import (GoogleTranslator,
                             ChatGptTranslator,
                             MicrosoftTranslator,
                             PonsTranslator,
                             LingueeTranslator,
                             MyMemoryTranslator,
                             YandexTranslator,
                             PapagoTranslator,
                             DeeplTranslator,
                             QcriTranslator,
                             single_detection,
                             batch_detection)
load_dotenv()
password = os.getenv("password")

class Message(BaseModel):
    message: str


DATABASE_URL = f"postgresql://postgres:{password}@localhost:5432/translations_db"
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()

app = FastAPI()

@app.get('/')
async def root():
    return ({"message": "Translations API is running. Use /add"})

@app.post('/add')
async def translate_API(message : Message):
    return translate(message.message)

@app.get('/all')
async def show_API():
    return show()

def translate(message):
    message = message.capitalize()
    with engine.connect() as connection:
        sql = text("SELECT * FROM translations WHERE eng = :message")
        result = connection.execute(sql, {"message" :  message})
        rows = result.fetchall()
    if rows:
        return {"status" : "info", "message" :"Translation already exists.", "translation" : {"rus" : rows[0][1], "eng" : rows[0][2]}}
    if not rows:
        translate = GoogleTranslator(source='en', target='ru').translate(f"{message}")
        if translate == message:
            raise HTTPException(status_code=400, detail = "Translation failed. Wrong word given.")
        with engine.connect() as connection:
            sql = text("INSERT INTO public.translations(eng, rus) VALUES (:message, :translate);")
            result = connection.execute(sql, {"message": message, "translate" : translate})
            connection.commit()
    return {"status" : "success", "word_en" : message, "word_ru" : translate}

def show():
    with engine.connect() as connection:
        sql = text("SELECT * FROM translations")
        result = connection.execute(sql)
        rows = result.fetchall()
    if rows:
        for row in range(len(rows)):
            rows[row] = {"id" : rows[row][0], "rus" : rows[row][1], "eng" : rows[row][2]}
        return {"status" : "success", "translations" : rows}
    else:
        return {"status" : "success", "message" : "Nothing translated yet."}


print(translate("Hi"))


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)