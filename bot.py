import config

import asyncio
import asyncpg


from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, BoundFilter, IDFilter


from middlewares.db import DbMiddleware
from models.states import AccessUser

import logging

from handlers import registration
from handlers import commands
from handlers import admin

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


logger = logging.getLogger(__name__)


async def create_pool():
    pool = await asyncpg.create_pool(host=config.db_host, 
    port=config.db_port, user=config.db_user, password=config.db_pass,
    database=config.db_type)
    return pool


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    logger.error("Starting bot")
    
     
    bot = Bot(token=config.admin_token)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
   
    
    dp.filters_factory.bind(AccessUser)
    registration.register_registration_handlers(dp)
    commands.register_registration_handlers(dp)
    admin.register_registration_handlers(dp)
    
    # get pool connect to db (asyncpg)
    pool = await create_pool()
    # forward pool to middleware
    dp.middleware.setup(DbMiddleware(pool))
    # forward pool to bot
    bot["conn"] = pool



    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
