from keyboards import keyboard
from models import stickers, states, sgo_api

from handlers.commands import main 

from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher import FSMContext

from db.db_engine import DB_engine


from models.states import AccessUser


async def main_new_user(message, state: FSMContext):
    print('Пришёл новый пользователь')
    await message.answer_sticker(stickers.st_new_user)
    await message.answer('''Кажется, мы ещё не знакомы!\n
Чтобы получить доступ к моему функционалу тебе необходимо зарегистрироваться и предоставить мне свои данные от "Сетевого города"''')
    await message.answer('Как я могу к тебе обращаться?')
    await states.Registration.get_name.set()


async def get_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if len(data.keys())==0: 
        await state.update_data(name_user=message.text)
    await message.answer('Мне нужны твои данные авторизации для <b>Сетевого Города</b>: логин и пароль, которые ты вводишь на region.zabedu.ru\n\n\n\U0001F464 введи свой <b>ЛОГИН</b>: ', parse_mode="HTML")
    await states.Registration.get_sgo_login.set()


async def get_sgo_login(message: types.Message, state: FSMContext):
    await state.update_data(sgo_login=message.text)
    await message.answer_sticker(sticker=stickers.st_incognito)
    await message.answer('Не бойся, я никому не расскажу твой пароль, но сохраню себе в секретную базу данных в зашифрованном виде.\n\n\U0001F510 введи <b>ПАРОЛЬ</b>: ', parse_mode="HTML")
    await states.Registration.get_sgo_pass.set()
   

async def get_sgo_pass(message: types.Message, state: FSMContext, db_engine:DB_engine):
    '''Достаём данные введённые пользователем из state.data 
    и грузим в базу данных'''
    await state.update_data(sgo_pass=message.text)
  
    data = await state.get_data() 
    test_connect = await sgo_api.test_connect(data["sgo_login"], data["sgo_pass"])

    if test_connect==True:
        '''если авторизация прошла успешно, то 
        - пишем данные в базу данных
        - отсылаем ему main-меню
        - сбрасываем state'''
        params = message.chat.id, data['name_user'], data['sgo_login'], data['sgo_pass']
        query = 'INSERT INTO user_data (user_id, user_name, sgo_login, sgo_pass) VALUES ($1, $2, $3, $4)'
        await db_engine.execute(query, params, False)
        await message.answer('Отлично! Авторизация прошла успешно!\nТеперь тебе доступен полный функционал!')
        await main(message, state)
        await state.finish()
        
    else:
        '''если авторизироваться по введённым данным не удалось 
        - отсылаем пользователя назад к вводу логина'''
        await message.answer_sticker(sticker=stickers.st_not_auth)
        await message.answer("\U0001F512 Пользователь с такими данными не найден в СГО\nПоробуй ввести свои данные ещё раз")
        #await state.reset_data()
        await states.Registration.get_name.set()
        await get_name(message, state)




def register_registration_handlers(dp: Dispatcher):
    dp.register_message_handler(main_new_user, commands="start", state="*", is_reg='new_user')
    dp.register_message_handler(get_name,  state=states.Registration.get_name, is_reg='new_user')
    dp.register_message_handler(get_sgo_login, state=states.Registration.get_sgo_login, is_reg='new_user')
    dp.register_message_handler(get_sgo_pass, state=states.Registration.get_sgo_pass, is_reg='new_user')