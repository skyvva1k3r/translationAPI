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
        temp = "{" + message + "}"
        sql = text("SELECT * FROM translations WHERE rus = :temp")
        result = connection.execute(sql, {"message": message})
        rows = result.fetchall()

    if rows:
        return "Already translated"
    if not rows:
        translate = requests.get(f"https://api.mymemory.translated.net/get?q={message}&langpair=en|ru").json()
        with engine.connect() as connection:
            sql = text("INSERT INTO translations ()")

print(translate("Hello"))