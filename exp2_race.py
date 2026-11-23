from pymongo import MongoClient
from pymongo.errors import OperationFailure
from concurrent.futures import ThreadPoolExecutor
import threading

client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
db = client.lab
coll = db.counter
coll.delete_many({})
coll.insert_one({"_id": "x", "value": 0})

barrier = threading.Barrier(2)  # обе транзакции ждут друг друга

def worker(name, increment):
    session = client.start_session()
    try:
        session.start_transaction()
        doc = coll.find_one({"_id": "x"}, session=session)
        barrier.wait()  # обе прочитали одно и то же значение
        new_val = doc["value"] + increment
        coll.update_one({"_id": "x", "value": doc["value"]},
                        {"$set": {"value": new_val}}, session=session)
        session.commit_transaction()
        print(f"[{name}]  Коммит, value = {new_val}")
    except OperationFailure as e:
        print(f"[{name}]  Конфликт: {e}")
        session.abort_transaction()

with ThreadPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(worker, "T1", 10)
    f2 = ex.submit(worker, "T2", 20)
    f1.result(); f2.result()

print(f"[ФИНАЛ] counter = {coll.find_one({'_id': 'x'})['value']}")
print("Ожидание: ровно одно обновление применилось (10 ИЛИ 20), второе — конфликт")