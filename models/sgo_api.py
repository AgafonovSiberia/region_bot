from netschoolapi import NetSchoolAPI
from aiogram import types

import json
import config
from models import engine
import re
import datetime
from keyboards import keyboard
from yageocode import geocode

from html2image import Html2Image

from bs4 import BeautifulSoup


async def test_connect(sgo_login, sgo_pass):
    api = NetSchoolAPI(config.url_sgo)
    try:
        await api.login(sgo_login, sgo_pass, config.name_school)
        await api.logout()
        return True
    except Exception as error:
        return False


async def get_diary(message, start, end, suff):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    diary = await api.diary(start=start, end=end)
    await api.logout()
    result = '\U0001F4CCРасписание уроков ' + suff + '\n'
    for day in diary['weekDays']:
        result += '\n\U0001F4C6 <b>Дата:</b> ' + str(day['date'])[:10] + '\n\n'
        for lesson in day['lessons']:
            result += '<b>' + str(lesson["number"]) + '.</b> ' + str(lesson["subjectName"]) + ' - Кабинет: ' + str(
                lesson["room"]) + '\n'
    return result


async def get_homework(message, start, end, suff_header):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    diary = await api.diary(start=start, end=end)
    result = ''
    result += '\U0001F4D9 Домашнее задание <b>' + suff_header + '</b>'
    for day in diary['weekDays']:
        result += f"\n\n\U0001F538<b>День:</b>{re.search('(.*)T00:00:00', day['date']).group(1)}\n"
        for lesson in day["lessons"]:
            try:
                for assignment in lesson["assignments"]:
                    ass = await api.get_assign(assignment['id'])
                    assign_description = 'Подробно: ' + ass['description'] if ass['description'] != None else ''
                    result += '<b>\U000025AA' + str(lesson["subjectName"]) + "</b>:" + str(
                        assignment["assignmentName"]) + " : <i> " + assign_description + '</i>\n'

            except Exception as error:
                pass
    await api.logout()
    return result


async def get_school(message):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    return result


# чистый список оценок
async def get_marks(message):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    period = await api.get_period()
    period = period['filterSources'][2]['defaultValue'].split(' - ')
    start = datetime.datetime.strptime(period[0], '%Y-%m-%dT%H:%M:%S.0000000')
    end = datetime.datetime.strptime(period[1], '%Y-%m-%dT%H:%M:%S.0000000')
    diary = await api.diary(start=start, end=end)
    await api.logout()
    'составляем чистый словарь оценок'
    marks = {}
    for days in diary['weekDays']:
        for lesson in days['lessons']:
            if lesson['subjectName'] not in marks.keys():
                marks[lesson['subjectName']] = []
            if 'assignments' in lesson.keys():
                for assignment in lesson['assignments']:
                    if 'mark' in assignment.keys() and 'mark' in assignment['mark']:

                        if assignment['mark']['mark'] != None:
                            marks[lesson['subjectName']].append(assignment['mark']['mark'])

    result = ''
    for lesson in marks.keys():
        if marks[lesson]:
            marks[lesson] = [mark for mark in marks[lesson] if mark]
            general_sum = round(sum(marks[lesson]) / len(marks[lesson]), 1)
            marks[lesson] = ' '.join(str(e) for e in marks[lesson])
            result += f"<b>\n{lesson}</b>: {marks[lesson]} | <i><b>{general_sum}</b></i>"
    if not result:
        result = '❌Нет оценок'
    return result


async def get_detail_marks(message):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    period = await api.get_period()

    period = period['filterSources'][2]['defaultValue'].split(' - ')
    start = datetime.datetime.strptime(period[0], '%Y-%m-%dT%H:%M:%S.0000000')
    end = datetime.datetime.strptime(period[1], '%Y-%m-%dT%H:%M:%S.0000000')
    diary = await api.diary(start=start, end=end)
    await api.logout()

    result_to_db = []
    result_to_user = ''
    for days in diary['weekDays']:
        for lesson in days['lessons']:
            if 'assignments' in lesson.keys():
                for assignment in lesson['assignments']:
                    if 'mark' in assignment.keys() and 'mark' in assignment['mark']:
                        date = datetime.datetime.strptime(assignment['dueDate'], '%Y-%m-%dT%H:%M:%S')
                        date = str(date.day) + '.' + str(date.month)
                        str_json_to_db = {"date": str(date), "lesson": str(lesson['subjectName']),
                                          "mark": str(assignment['mark']['mark']),
                                          "mark_data": assignment['assignmentName']}
                        # result_to_user += f"\n<b>{date} {lesson['subjectName']} </b>: {assignment['mark']['mark']} || <i>{assignment['assignmentName']}</i>"
                        result_to_db.append(str_json_to_db)

    return result_to_db


async def get_board(message):
    result = ''
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    data = await api.announcements()
    await api.logout()

    try:
        result += '<b>Автор:</b>  ' + data[0]['author']['fio'] + '\n\n<b>Объявление:</b>\n' + re.sub('<[^>]*>', '',
                                                                                                     data[0][
                                                                                                         'description'])
    except Exception:
        result = ''
    return result


async def get_school(message):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)
    info = await api.school()
    await api.logout()
    client = geocode.Client(config.ya_api_token)
    coordinates = client.coordinates(info['contactInfo']['postAddress'])
    url_geo = 'https://yandex.ru/maps/?pt=' + str(geocode.Decimal(coordinates[0])) + ',' + str(
        geocode.Decimal(coordinates[1])) + '&z=158&l=map'
    url_panarams = 'https://yandex.ru/maps/?panorama[point]=' + str(geocode.Decimal(coordinates[0])) + ',' + str(
        geocode.Decimal(coordinates[1])) + '&panorama[direction]=15,6.060547&panorama[span]=130.000000,71.919192'
    result = (
            '<b>\U0001F538 Наименование: </b>' + info['commonInfo']['fullSchoolName'] + '\n\n'
                                                                                        '<b>\U0001F464 Директор: </b>' +
            info['managementInfo']['director'] + '\n\n'
                                                 '<b>\U0001F4CC Адрес: </b>' + info['contactInfo'][
                'postAddress'] + '\n\n'
                                 '<b>\U0000260E Телефон: </b>' + info['contactInfo']['phones'] + '\n\n'
                                                                                                 '<b>\U0001F4E7 Email: </b>' +
            info['contactInfo']['email'] + '\n\n'
                                           '<b>\U0001F4F2 Сайт: </b>' + info['contactInfo']['web'] + '\n\n'
    )

    keyboard_geo_url = await keyboard.get_keyboard_url([url_geo, url_panarams])

    return result, keyboard_geo_url


async def get_report(message, call):
    api = NetSchoolAPI(config.url_sgo)
    login_sgo, pass_sgo = await engine.get_login_pass(message)
    await api.login(login_sgo, pass_sgo, config.name_school)

    # отёт итоговые оценки
    if call.data == 'get_report_total_marks':
        html_page, css_file = await api.get_total_marks_from_report()
        resize_params = (750, 900)
        save_path_img = 'data/total_marks'

    if call.data == 'get_report_parrentInfoLetter':
        html_page, css_file = await api.get_parrentInfoLetter_from_report()
        resize_params = (700, 700)
        save_path_img = 'data/parrentInfoLetter'

    if call.data == 'get_report_average_mark':
        period = await api.get_period()
        start = datetime.datetime.strptime(str(period['filterSources'][2]['range']['start']), '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(str(period['filterSources'][2]['range']['end']), '%Y-%m-%dT%H:%M:%S')
        start = str(start.day) + '.' + str(start.month) + '.' + str(start.year)
        end = str(end.day) + '.' + str(end.month) + '.' + str(end.year)

        html_page, css_file = await api.get_average_mark_from_Report(start, end)
        resize_params = (1100, 480)
        save_path_img = 'data/averageMark'

    if call.data == 'get_report_average_mark_dynamic':
        period = await api.get_period()
        start = datetime.datetime.strptime(str(period['filterSources'][2]['range']['start']), '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(str(period['filterSources'][2]['range']['end']), '%Y-%m-%dT%H:%M:%S')
        start = str(start.day) + '.' + str(start.month) + '.' + str(start.year)
        end = str(end.day) + '.' + str(end.month) + '.' + str(end.year)

        html_page, css_file = await api.get_average_mark_dynamic_from_Report(start, end)
        resize_params = (1100, 480)
        save_path_img = 'data/averageMarkDyn'
        # await api.get_fullreport_from_Report() ///попытка получить полный отчёт успеваемости и посещаемости

    await api.logout()
    hti = Html2Image(output_path=save_path_img, custom_flags = [ '--no-sandbox'] )
    hti.screenshot(html_str=html_page, css_str=css_file, save_as=str(message.chat.id)+'.jpeg', size=resize_params)
    photo = types.InputFile(save_path_img+'/'+str(message.chat.id)+'.jpeg')
    return photo

