import os
import requests
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Numeric, VARCHAR, text
from dotenv import load_dotenv
load_dotenv()
password = os.getenv("password")


DATABASE_URL = f"postgresql://postgres:{password}@localhost:5432/translations_db"
engine = create_engine(DATABASE_URL, echo=True)


def translate(message):
    with engine.connect() as connection:
        sql = text("SELECT * FROM translations WHERE rus = :message")
        result = connection.execute(sql, {"message" :  message})
        rows = result.fetchall()

    if rows:
        return "Already translated"
        #Сделать возврат корректный
    if not rows:
        translate = requests.get(f"https://api.mymemory.translated.net/get?q={message}&langpair=en|ru").json()["responseData"]["translatedText"]
        with engine.connect() as connection:
            sql = text("INSERT INTO translations (rus, eng) VALUES (:message, :translate)")
            result = connection.execute(sql, {"message": message, "translate" : translate})
            connection.commit()
        #Сделать возврат корректный



print(translate("Hello"))