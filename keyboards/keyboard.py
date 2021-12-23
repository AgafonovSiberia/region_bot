from aiogram.types import  InlineKeyboardMarkup, InlineKeyboardButton

#стартовая клавиатура
keyboard_main = InlineKeyboardMarkup(row_width=3)
keyboard_main.add(
    InlineKeyboardButton(text="Расписание", callback_data="get_diary"), 
    InlineKeyboardButton(text="График звонков", callback_data="get_timetable"),
    InlineKeyboardButton(text="Объявления", callback_data="get_board"),
    InlineKeyboardButton(text="Мои оценки", callback_data="get_marks"),
    InlineKeyboardButton(text="Моё ДЗ", callback_data="get_homework"),
    InlineKeyboardButton(text="Моя школа", callback_data="get_school_info")
)

keyboard_main.add(
    InlineKeyboardButton(text="Мои отчёты", callback_data="get_report"))

keyboard_main.add(
    InlineKeyboardButton(text="Изменить NickName", callback_data="edit_nickname"),
    InlineKeyboardButton(text="Удалить профиль", callback_data="delete_profile"))


keyboard_report = InlineKeyboardMarkup(row_width=2)
keyboard_report.add(
    InlineKeyboardButton(text="Итоговые оценки", callback_data="get_report_total_marks"),
    InlineKeyboardButton(text="Средний балл", callback_data='get_report_average_mark'),
    InlineKeyboardButton(text="Динамика ср.балла", callback_data='get_report_average_mark_dynamic'),
    InlineKeyboardButton(text="Справка для родителей", callback_data='get_report_parrentInfoLetter'))



#клавиатура для выбора дней расписания
keyboard_diary_change = InlineKeyboardMarkup(row_width=2)
keyboard_diary_change.add(
    InlineKeyboardButton(text="Сегодня", callback_data="today"), 
    InlineKeyboardButton(text="Завтра", callback_data="tomorrow"),
    InlineKeyboardButton(text="Текущая неделя", callback_data="week"),
      InlineKeyboardButton(text="Следующая неделя", callback_data="next_week"))

#клавиатура обратно в меню
keyboard_to_main = InlineKeyboardMarkup(row_width=3)
keyboard_to_main.add(
    InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu"))


#запрос на удаление профиля
keyboard_change_delete_profile =InlineKeyboardMarkup(row_width=3)
keyboard_change_delete_profile.add(
    InlineKeyboardButton(text="Да, удалить", callback_data="yes_delete_profile"),
    InlineKeyboardButton(text="Нет, не нужно", callback_data="no_delete_profile"))


#детализация оценок
keyboard_get_marks_detail =InlineKeyboardMarkup(row_width=3)
keyboard_get_marks_detail.add(
    InlineKeyboardButton(text="Детализация оценок", callback_data="get_marks_detail"),
    InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu"))




#клавиатура для админа
keyboard_to_admin=InlineKeyboardMarkup(row_width=3)
keyboard_to_admin.add(
    InlineKeyboardButton(text="Send message to users", callback_data="send_message_to_users"))




async def get_keyboard_url(urls:list):
    keyboard_geo_url = InlineKeyboardMarkup(row_width=2)
    keyboard_geo_url.add(
        InlineKeyboardButton(text="Школа на карте", url=urls[0]),
        InlineKeyboardButton(text="Панорама", url=urls[1]))
    keyboard_geo_url.add(
        InlineKeyboardButton(text="Главное меню", callback_data="to_main_menu"))
    return keyboard_geo_url

