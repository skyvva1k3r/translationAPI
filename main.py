import os
import requests
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Numeric, VARCHAR, text, insert
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
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
import bcrypt
from jose import jwt
from typing import Optional
load_dotenv()
password = os.getenv("password")
secret = os.getenv("secret")

class Message(BaseModel):
    message: str

class User(BaseModel):
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
async def translate_API(message : Message, authorization : str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    return translate(message.message, token)

@app.get('/all')
async def show_API(authorization : str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    return show(token)

@app.post('/del')
async def delete_API(message : Message, authorization : str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    return delete(message.message, token)

@app.post('/reg')
async def registration(user : User):
    with engine.connect() as connection:
        sql = text("SELECT * FROM users WHERE email = :login")
        result = connection.execute(sql, {"login" : user.email })
        rows = result.fetchall()
    if rows:
        return {"status" : "info", "message" : "Account with this email already exists."}
    else:
        h = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        with engine.connect() as connection:
            h = h.decode('utf-8')
            sql = text("INSERT INTO public.users(email, password) VALUES (:email, :password);")
            result = connection.execute(sql, {"email": user.email, "password" : h})
            connection.commit()
        return {"status" : "success", "message" : "Account successfully created."}

@app.post('/auth')
async def auth(user : User):
    with engine.connect() as connection:
        sql = text("SELECT * FROM users WHERE email = :login")
        result = connection.execute(sql, {"login" : user.email })
        rows = result.fetchall()
    if rows:
        password = str(rows[0][1]).encode('utf-8')
        if bcrypt.checkpw(user.password.encode('utf-8'), password):
            token = jwt.encode({"user_id" : rows[0][2]}, secret, algorithm="HS256")
            return {"status" : "success", "message" : "Authorized.", "token" : token}
        else:
            return {"status" : "info", "message" : "Wrong password."}
    else:
        return {"status" : "info", "message" : "Account with this email doesn't exist."}

def delete(message, token):
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    user_id = decoded["user_id"]
    with engine.connect() as connection:
        sql = text("DELETE FROM translations WHERE eng = :message AND user_id = :user_id")
        result = connection.execute(sql, {"message" : message, "user_id" : user_id})
        connection.commit()
    return {"status" : "success", "message" : "Translation deleted."}

def translate(message, token):
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    user_id = decoded["user_id"]
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
        try:
            translate.append((PonsTranslator(source='en', target='ru').translate(f"{message}")).capitalize())
        except AttributeError:
            pass
        translate = set(translate)
        translate = ", ".join(translate)
        if translate == message:
            raise HTTPException(status_code=400, detail = "Translation failed. Wrong word given.")
        with engine.connect() as connection:
            sql = text("INSERT INTO public.translations(rus, eng, user_id) VALUES (:translate, :message, :user_id);")
            result = connection.execute(sql, {"translate": translate, "message" : message, "user_id" : user_id})
            connection.commit()
    return {"status" : "success", "word_en" : message, "word_ru" : translate}

def show(token):
    with engine.connect() as connection:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = decoded["user_id"]
        sql = text("SELECT * FROM translations WHERE user_id = :user_id")
        result = connection.execute(sql, {"user_id": user_id})
        rows = result.fetchall()
    if rows:
        for row in range(len(rows)):
            rows[row] = {"id" : rows[row][0], "rus" : rows[row][1], "eng" : rows[row][2]}
        return {"status" : "success", "translations" : rows}
    else:
        return {"status" : "success", "message" : "Nothing translated yet."}