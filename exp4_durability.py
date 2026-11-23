from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
import time

client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0")
coll = client.lab.durability
coll.delete_many({})

# --- Коммит без journal ---
s = client.start_session()
s.start_transaction(write_concern=WriteConcern(w=1, j=False))
coll.insert_one({"_id": "no_journal", "ts": time.time()}, session=s)
s.commit_transaction()
print("Закоммичено без j=true — в журнале может ещё не быть")

# --- Коммит с journal ---
s = client.start_session()
s.start_transaction(write_concern=WriteConcern(w=1, j=True))
coll.insert_one({"_id": "with_journal", "ts": time.time()}, session=s)
s.commit_transaction()
print("Закоммичено с j=true — гарантированно в WAL")

# --- Разница видна только при краше. Покажем статус journal ---
stats = client.admin.command("serverStatus")
print("\nWiredTiger WAL stats:")
for k, v in stats["wiredTiger"]["log"].items():
    if "bytes" in k or "records" in k:
        print(f"  {k}: {v}")