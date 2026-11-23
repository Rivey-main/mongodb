from pymongo import MongoClient
from pymongo.errors import OperationFailure
import time

client = MongoClient("mongodb://172.17.0.2:27017/?replicaSet=rs0")
db = client.lab
coll = db.accounts
coll.delete_many({})

# Инициализация: два счёта по 1000
coll.insert_many([
    {"_id": "A", "balance": 1000},
    {"_id": "B", "balance": 1000},
])

# --- Транзакция T1: начинает и "замирает" ---
s1 = client.start_session()
s1.start_transaction()
before = coll.find_one({"_id": "A"}, session=s1)
print(f"[T1] Видит A = {before['balance']}  (ожидаем 1000)")

# --- Пока T1 "спит", другая сессия меняет A ---
s2 = client.start_session()
coll.update_one({"_id": "A"}, {"$inc": {"balance": 500}}, session=s2)
print(f"[T2] Изменила A на +500 (вне транзакции, авто-коммит)")

# --- T1 снова читает A: должна видеть СТАРОЕ значение! ---
after = coll.find_one({"_id": "A"}, session=s1)
print(f"[T1] Повторно видит A = {after['balance']}  (ожидаем всё ещё 1000!)")

# --- А теперь T1 делает запись в A ---
try:
    coll.update_one({"_id": "A"}, {"$inc": {"balance": -200}}, session=s1)
    s1.commit_transaction()
    print("[T1] Коммит прошёл — но что стало с балансом?")
except OperationFailure as e:
    print(f"[T1] Конфликт при коммите: {e}")
    s1.abort_transaction()
finally:
    final = coll.find_one({"_id": "A"})
    print(f"[ФИНАЛ] A = {final['balance']}")