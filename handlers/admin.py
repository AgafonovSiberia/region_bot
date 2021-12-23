from keyboards import keyboard
from datetime import timedelta
import datetime
import config
from models.states import Admin
from handlers import registration
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher import FSMContext

from db.db_engine import DB_engine


from models import stickers, engine, sgo_api



async def main_to_admin (message, state: FSMContext):
    await message.bot.send_sticker(chat_id=message.chat.id, sticker=stickers.god_mode)
    await message.answer('God mode activated! Hello my admin\U0001F618', reply_markup=keyboard.keyboard_to_admin)


async def write_message_to_users(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    await call.message.answer('Введи сообщение и отправьте его мне.\nПосле этого я разошлю его всем зарегистрированным пользователям.')
    await Admin.send_message_to_users.set()

    
async def send_message_to_users(message, state: FSMContext):
    users_list_id = await engine.get_list_id_users(message)

    for user_id in users_list_id:
        try:
            await message.bot.send_message(chat_id=user_id[0], text=message.text, parse_mode='HTML')
        except Exception as error:
            print(error)


def register_registration_handlers(dp: Dispatcher):
    dp.register_message_handler(main_to_admin, commands="start", state="*", is_reg='admin')
    dp.register_callback_query_handler(write_message_to_users, lambda call: call.data=='send_message_to_users',  state="*")
    dp.register_message_handler(send_message_to_users, state=Admin.send_message_to_users)
