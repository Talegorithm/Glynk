from glynk.storage.postgres import PostgresStore
from glynk.config import AppConfig

config = AppConfig.from_env()
db = PostgresStore(config.storage)
db._execute("DELETE FROM reading_progress WHERE unit_id = %s", ("f280a35784ab37e4",))
db._execute("DELETE FROM reading_sessions WHERE unit_id = %s", ("f280a35784ab37e4",))
db._execute("DELETE FROM anchors WHERE target_unit = %s", ("f280a35784ab37e4",))
db.delete_unit("f280a35784ab37e4")
print("Deleted unit f280a35784ab37e4")

