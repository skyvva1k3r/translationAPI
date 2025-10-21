import os
import requests
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Numeric, VARCHAR, text, insert
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse  
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
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt
import jose

load_dotenv()
password = os.getenv("password")

class Message(BaseModel):
    message: str

class Regis(BaseModel):
    email : str
    password : str
    

DATABASE_URL = f"postgresql://postgres:{password}@localhost:5432/translations_db"
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def root():
    return FileResponse('index(AI gen.).html')

@app.post('/add')
async def translate_API(message : Message):
    return translate(message.message)

@app.get('/all')
async def show_API():
    return show()

@app.post('/reg')
async def registration(user : Regis):
    with engine.connect() as connection:
        sql = text("SELECT * FROM users WHERE email = :login")
        result = connection.execute(sql, {"login" : user.email })
        rows = result.fetchall()
    if rows:
        return {"status" : "info", "message" : "Account with this email already exists.", "debug" : result}
    else:
        h = bcrypt.hash(user.password)
        with engine.connect() as connection:
            sql = text("INSERT INTO public.users(email, password) VALUES (:email, :password);")
            result = connection.execute(sql, {"email": user.email, "password" : h})
            connection.commit()
        return {"status" : "success", "message" : "Account successfully created."}


def translate(message):
    message = message.capitalize()
    with engine.connect() as connection:
        sql = text("SELECT * FROM translations WHERE eng = :message")
        result = connection.execute(sql, {"message" :  message})
        rows = result.fetchall()
    if rows:
        return {"status" : "info", "message" :"Translation already exists.", "translation" : {"rus" : rows[0][1], "eng" : rows[0][2]}}
    if not rows:
        translate = []
        translate.append((GoogleTranslator(source='en', target='ru').translate(f"{message}")).capitalize())
        translate.append((MyMemoryTranslator(source='en-GB', target='ru-RU').translate(f"{message}")).capitalize())
        translate.append((PonsTranslator(source='en', target='ru').translate(f"{message}")).capitalize())
        translate = set(translate)
        translate = ", ".join(translate)
        if translate == message:
            raise HTTPException(status_code=400, detail = "Translation failed. Wrong word given.")
        with engine.connect() as connection:
            sql = text("INSERT INTO public.translations(rus, eng) VALUES (:translate, :message);")
            result = connection.execute(sql, {"translate": translate, "message" : message})
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