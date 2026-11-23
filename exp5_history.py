from pymongo import MongoClient
import time

client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
db = client.lab
coll = db.history_test
coll.delete_many({})
coll.insert_one({"_id": "hot", "v": 0})

# Открываем долгую транзакцию-читателя
long_reader = client.start_session()
long_reader.start_transaction()
_ = coll.find_one({"_id": "hot"}, session=long_reader)
print("[Reader] Открыт долгий снапшот")

# Генерируем много версий документа
for i in range(1000):
    coll.update_one({"_id": "hot"}, {"$inc": {"v": 1}})

# Смотрим метрики WiredTiger
stats = db.command("serverStatus")["wiredTiger"]
cache = stats["cache"]
print(f"В кэше: {cache['bytes currently in the cache']/1e6:.1f} MB")
print(f"History Store 'dirty': {cache.get('tracked dirty bytes in the cache', 0)/1e6:.1f} MB")

long_reader.abort_transaction()  # освобождаем снапшот
time.sleep(2)
print("[Reader] Снапшот закрыт — WT может очистить историю")