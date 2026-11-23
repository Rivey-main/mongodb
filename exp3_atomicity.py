from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
db = client.lab
coll = db.accounts
coll.delete_many({})
coll.insert_many([
    {"_id": "A", "balance": 1000},
    {"_id": "B", "balance": 1000},
])

session = client.start_session()
session.start_transaction()
try:
    # Списываем с A
    coll.update_one({"_id": "A", "balance": {"$gte": 500}},
                    {"$inc": {"balance": -500}}, session=session)
    print("[T] A списан на 500")

    # Проверяем "внутри транзакции" — что видит сама транзакция?
    print("[T] внутри: A =", coll.find_one({"_id": "A"}, session=session)["balance"])

    # Искусственная ошибка — эмулируем сбой бизнес-логики
    raise RuntimeError("Бизнес-ошибка: перевод отклонён банком-корреспондентом!")

except RuntimeError as e:
    print(f"[T] Откат: {e}")
    session.abort_transaction()

# Проверяем снаружи
print("[ВНЕ] A =", coll.find_one({"_id": "A"})["balance"], " (ожидаем 1000)")
print("[ВНЕ] B =", coll.find_one({"_id": "B"})["balance"], " (ожидаем 1000)")