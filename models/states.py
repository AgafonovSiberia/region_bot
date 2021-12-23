from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types
from middlewares.db import DbMiddleware

from models import engine
import admin_config

from db.db_engine import DB_engine


class Admin(StatesGroup):
    send_message_to_users=State()

class Registration(StatesGroup):
    get_name = State()
    get_sgo_login = State()
    get_sgo_pass = State()
    get_new_name = State()

class Diary(StatesGroup):
    get_diary =  State()
    get_homework = State()


class AccessUser(BoundFilter):
    key = 'is_reg'
    def __init__(self, is_reg):
        self.is_reg = is_reg
    async def check(self, message:types.Message):
        status = await engine.get_status(message)
        if message.chat.id==admin_config.id_admin:
            return 'admin'==self.is_reg
        elif  status:
            return 'auth_user'==self.is_reg
        elif not(status):
            return 'new_user'==self.is_reg
        

