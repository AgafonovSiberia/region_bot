from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from db.db_engine import DB_engine


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]
    def __init__(self, pool):
        super().__init__()
        self.pool = pool

    async def pre_process(self, obj, data, *args):
        db = await self.pool.acquire()
        data["db"] = db
        data['db_engine'] = DB_engine(db)
     
    async def post_process(self, obj, data, *args):
        del data['db_engine']
        db = data.get("db")
        if db:
            await db.close()