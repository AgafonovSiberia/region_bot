from keyboards import keyboard
from datetime import timedelta
import datetime
import config
from models.states import Diary, Registration
from handlers import registration
from aiogram import Dispatcher
from aiogram import types
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher import FSMContext
from aiogram.utils.parts import split_text, safe_split_text

from db.db_engine import DB_engine
import json
from models import stickers, engine, sgo_api


async def to_main_menu(call, state: FSMContext):
    await call.bot.answer_callback_query(call.id)
    await main(call.message, state)

async def main (message, state: FSMContext):
    name_user = await engine.get_name(message)
    await message.bot.send_sticker(chat_id=message.chat.id, sticker=stickers.st_hello)
    await message.answer('Приветствую тебя, '+str(name_user)+'!\n\nМеня зовут <b>бот-Енот</b>!\nЯ твой персональный помощник!', reply_markup=keyboard.keyboard_main, parse_mode="HTML")


async def main_change_period(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    await call.message.answer('Выберите период', reply_markup=keyboard.keyboard_diary_change)
    if call.data=='get_homework':
        await Diary.get_homework.set()
    if call.data=='get_diary':
        await Diary.get_diary.set()


async def get_shedule_or_homework(call: types.CallbackQuery, state:FSMContext):
    "Выбор периода для расписания и домашнего задания"
    await call.bot.answer_callback_query(call.id)
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    if call.data=='today':
        start=end=datetime.date.today()
        suff_header = 'на сегодня'
    if call.data=='tomorrow':
        start=end=datetime.date.today() + datetime.timedelta(days=1)
        suff_header = 'на завтра'
    if call.data=='week':
        start=end=None
        suff_header = 'на неделю'
    if call.data=='next_week':
        start = (datetime.date.today() - timedelta(days=datetime.date.today().weekday()))+timedelta(weeks=1)
        end = start + timedelta(days=6)
        suff_header= 'на следующую неделю'
    state_name = await state.get_state()
    if state_name=='Diary:get_diary':
        data = await sgo_api.get_diary(call.message, start, end, suff_header)
        await call.message.answer(data, reply_markup=keyboard.keyboard_to_main, parse_mode="HTML")
    if state_name=='Diary:get_homework':
        data = await sgo_api.get_homework(call.message, start, end, suff_header)
        await call.message.answer(data, reply_markup=keyboard.keyboard_to_main, parse_mode="HTML")
    await state.finish()


async def get_marks(call: types.CallbackQuery, state:FSMContext):
    '''Успеваемость за текущий период'''
    await call.bot.answer_callback_query(call.id)
    marks = await sgo_api.get_marks(call.message)
    marks_to_db = await sgo_api.get_detail_marks(call.message)

    await call.message.answer(marks, reply_markup=keyboard.keyboard_get_marks_detail, parse_mode="HTML")
    try:
        await engine.insert_update_marks(call.message, json.dumps(marks_to_db))
    except Exception as error:
        print(error)
 

async def get_marks_detail(call: types.CallbackQuery, state:FSMContext):
    '''Детализация оценок за текущий период'''
    await call.bot.answer_callback_query(call.id)
    marks_json = json.loads(await engine.get_marks_detail_from_db(call.message))
    result = ''
    marks_json = sorted(marks_json, key=lambda items: items['lesson'])
    mark_lost = ''
    for marks in marks_json:
        if marks['lesson'] != mark_lost:
            result+='\n'
        mark_lost=marks['lesson']
        result += f"\n<b>{marks['date']}. {marks['lesson']} </b>: {marks['mark']} || {marks['mark_data']}"  
    if len(result)>4096:
        data_result = safe_split_text(text=result, split_separator='\n')
        for data in data_result:
            await call.message.answer(data, reply_markup=keyboard.keyboard_to_main, parse_mode="HTML")
    else:
        await call.message.answer(result, reply_markup=keyboard.keyboard_to_main, parse_mode="HTML")


   
async def get_report_main(call: types.CallbackQuery, state:FSMContext):
      await call.bot.answer_callback_query(call.id)
      await call.message.answer('\U0001F4C9 Какой отчёт ты хочешь просмотреть? ', reply_markup=keyboard.keyboard_report)


async def get_report_from_Reports(call: types.CallbackQuery, state:FSMContext):
    ''' Итоговые отметки (отчёт) '''
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.bot.answer_callback_query(call.id)
    photo_bytes = await sgo_api.get_report(call.message, call)
    await call.message.answer_photo(photo=photo_bytes, reply_markup=keyboard.keyboard_to_main)



async def get_timetable(call: types.CallbackQuery, state:FSMContext):
    '''Получить расписание (today, tomorrow, week'''
    await call.bot.answer_callback_query(call.id)
    with open ('data/shedule.png', 'rb') as shedule:
        await call.message.answer_photo(photo=shedule) 




async def main_delete_profile(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    await call.message.answer('Ты точно желаешь удалить свой профиль?', reply_markup=keyboard.keyboard_change_delete_profile)


async def delete_profile(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    if call.data=='yes_delete_profile':
        '''Удалить данные профиля из БД'''
        await engine.delete_account(call.message)
        await registration.main_new_user(call.message, state)
    if call.data=='no_delete_profile':
        pass
    

async def get_board(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    board = await sgo_api.get_board(call.message)
    if not(board):
        await call.message.answer('Нет новых объявлений', reply_markup=keyboard.keyboard_to_main)
    else:
        await call.message.answer(str(board), reply_markup=keyboard.keyboard_to_main, parse_mode="HTML")


async def get_school_info(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    school_info, keyboard_geo_url = await sgo_api.get_school(call.message)
    await call.message.answer(school_info, reply_markup=keyboard_geo_url, parse_mode='HTML')


async def edit_nickname(call: types.CallbackQuery, state:FSMContext):
    await call.bot.answer_callback_query(call.id)
    await call.message.answer_sticker(sticker=stickers.st_new_nickname)
    await call.message.answer('Хочешь что-нибудь поменять в своей жизни?\nКак мне теперь к тебе обращаться?')
    await Registration.get_new_name.set()

async def update_new_nickname(message: types.Message, state: FSMContext):
    await engine.update_nickname(message)
    await message.answer('Отлично, '+message.text+', я запомнил и даже записал себе в БД')
    await main(message, state)
    await state.finish()


def register_registration_handlers(dp: Dispatcher):
    dp.register_message_handler(main, commands="start", state="*", is_reg='auth_user')
    dp.register_callback_query_handler(edit_nickname, lambda call: call.data == "edit_nickname", state="*")
    dp.register_message_handler(update_new_nickname, state=Registration.get_new_name)
    #выбор периода для расписания и домашнего задания
    dp.register_callback_query_handler(main_change_period, lambda call: call.data in ['get_diary', 'get_homework'], state="*")
    dp.register_callback_query_handler(get_shedule_or_homework, lambda call: call.data in ['today', 'tomorrow', 'week', 'next_week'], state=[Diary.get_diary, Diary.get_homework])
    #расписание звонков
    dp.register_callback_query_handler(get_timetable, lambda call: call.data == 'get_timetable', state='*')
    #оценки
    dp.register_callback_query_handler(get_marks, lambda call: call.data == 'get_marks', state='*')
    #удаление профиля
    dp.register_callback_query_handler(delete_profile, lambda call: call.data in ['yes_delete_profile','no_delete_profile'], state='*')
    dp.register_callback_query_handler(main_delete_profile, lambda call: call.data == 'delete_profile', state='*')
    #получение объявлений
    dp.register_callback_query_handler(get_board, lambda call: call.data == 'get_board', state='*')
    #информация по школе
    dp.register_callback_query_handler(get_school_info, lambda call: call.data == 'get_school_info', state='*')
    #назад в главное меню
    dp.register_callback_query_handler(to_main_menu, lambda call: call.data == 'to_main_menu', state='*')

    dp.register_callback_query_handler(get_marks_detail, lambda call: call.data == 'get_marks_detail', state='*')

    dp.register_callback_query_handler(get_report_main, lambda call: call.data == 'get_report', state='*')

    dp.register_callback_query_handler(get_report_from_Reports, lambda call: call.data in ['get_report_total_marks', 'get_report_parrentInfoLetter', 'get_report_average_mark','get_report_average_mark_dynamic'], state='*')
