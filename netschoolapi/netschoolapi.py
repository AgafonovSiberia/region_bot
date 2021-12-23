from datetime import date, timedelta
from hashlib import md5
from io import BytesIO
from typing import Optional, Dict, List, Union

import httpx
from httpx import AsyncClient, Response
#from httpx.types import CookieTypes

from netschoolapi import data, errors, schemas

__all__ = ['NetSchoolAPI']



async def _die_on_bad_status(response: Response):
    response.raise_for_status()
#/webapi

class NetSchoolAPI:
    def __init__(self, url: str):
        url = url.rstrip('/')
        self._client = AsyncClient(
            base_url=f'{url}',
            headers={'user-agent': 'NetSchoolApi', 'referer': url},
            event_hooks={'response': [_die_on_bad_status]},
        )
        self._student_id = -1
        self._year_id = -1
        self._school_id = -1
        self._assignment_types: Dict[int, str] = {}
        self._login_data = ()
        self._at=-1

    async def __aenter__(self) -> 'NetSchoolAPI':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()

    async def login(self, user_name: str, password: str, school: str):
        response_with_cookies = await self._client.get('webapi/logindata')
        self._client.cookies.extract_cookies(response_with_cookies)
         
     
        response = await self._client.post('webapi/auth/getdata')
        login_meta = response.json()
        salt = login_meta.pop('salt')
        self._ver = login_meta['ver']


        encoded_password = md5(
            password.encode('windows-1251')
        ).hexdigest().encode()
        pw2 = md5(salt.encode() + encoded_password).hexdigest()
        pw = pw2[: len(password)]

        try:
            response = await self._client.post(
                '/webapi/login',
                data={
                    'loginType': 1,
                    **(await self._address(school)),
                    'un': user_name,
                    'pw': pw,
                    'pw2': pw2,
                    **login_meta,
                },
                headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
                "Accept":"application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive"
                }
                
            )
        except httpx.HTTPStatusError as http_status_error:
            await self._client.post('webapi/auth/logout')
            await self._client.aclose()
            if http_status_error.response.status_code == httpx.codes.CONFLICT:
                raise errors.AuthError("Incorrect username or password!")
            else:
                raise http_status_error
                
        auth_result = response.json()
      

        if 'at' not in auth_result:
            raise errors.AuthError(auth_result['message'])
    
        self._client.headers['AT'] = auth_result['at']
        self._at=auth_result['at']
     

        response = await self._client.get('webapi/student/diary/init')
        diary_info = response.json()
    
        student = diary_info['students'][diary_info['currentStudentId']]
        self._student_id = student['studentId']
        self._class_id = student['classId']
    
        

        response = await self._client.get('webapi/years/current')
        year_reference = response.json()
        self._year_id = year_reference['id']    
        response = await self._client.get(
            'webapi/grade/assignment/types', params={'all': False}
        )
        assignment_reference = response.json()

        self._assignment_types = {
            assignment['id']: assignment['name']
            for assignment in assignment_reference
        }


        self._login_data = (user_name, password, school)

    #данные по моей школе
    async def school(self):
        response = await self._request_with_optional_relogin(
            'webapi/schools/{0}/card'.format(self._school_id)
        )
        return response.json()

    #получаем список школ
    async def schools(self):
        response = await self._client.get(
            'webapi/addresses/schools', params={'funcType': 2}
        )
        return response.json()


    #получаем текущий период обучения
    async def get_period(self):
        response = await self._client.get(
            'webapi/reports/studenttotal'
        )
        return response.json()

    async def _request_with_optional_relogin(
            self, path: str, method="GET", params: dict = None,
            json: dict = None, cookies: httpx._types.CookieTypes=None,
            headers:dict = None):
        try:
            response = await self._client.request(
                method, path, params=params, json=json, cookies=cookies, headers=headers)
            
        except httpx.HTTPStatusError as http_status_error:
            if (
                http_status_error.response.status_code
                == httpx.codes.UNAUTHORIZED
            ):
                if self._login_data:
                    await self.login(*self._login_data)
                    cookies = self._client.cookies.extract_cookies(response)
                    return await self._client.request(
                        method, path, params=params, json=json, cookies=cookies, headers=headers
                    )
                else:
                    raise errors.AuthError(
                    )
            else:
                raise http_status_error
        else:
            return response

    #скачиваем прикреплённый файл
    async def download_attachment(
            self, attachment: data.Attachment,
            path_or_file: Union[BytesIO, str] = None):
        """
        If `path_to_file` is a string, it should contain absolute path to file
        """
        if path_or_file is None:
            file = open(attachment.name, "wb")
        elif isinstance(path_or_file, str):
            file = open(path_or_file, "wb")
        else:
            file = path_or_file
        file.write((
            await self._request_with_optional_relogin(
                f"attachments/{attachment.id}"
            )
        ).content)


    #получаем прикреплённый файл
    async def download_attachment_as_bytes(
            self, attachment: data.Attachment) -> BytesIO:
        attachment_contents_buffer = BytesIO()
        await self.download_attachment(
            attachment, path_or_file=attachment_contents_buffer
        )
        return attachment_contents_buffer

    #получаем весь дневник
    async def diary(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> data.Diary:
        if not start:
            monday = date.today() - timedelta(days=date.today().weekday())
            start = monday
        if not end:
            end = start + timedelta(days=5)

        response = await self._request_with_optional_relogin(
            'webapi/student/diary',
            params={
                'studentId': self._student_id,
                'yearId': self._year_id,
                'weekStart': start.isoformat(),
                'weekEnd': end.isoformat(),
            },
        )
        return response.json()

    async def overdue(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> List[data.Assignment]:
        if not start:
            monday = date.today() - timedelta(days=date.today().weekday())
            start = monday
        if not end:
            end = start + timedelta(days=5)

        response = await self._request_with_optional_relogin(
            'webapi/student/diary/pastMandatory',
            params={
                'studentId': self._student_id,
                'yearId': self._year_id,
                'weekStart': start.isoformat(),
                'weekEnd': end.isoformat(),
            },
        )
        assignments = schemas.Assignment().load(response.json(), many=True)
        return [data.Assignment(**assignment) for assignment in assignments]

    async def announcements(
            self, take: Optional[int] = -1) -> List[dict]:
        response = await self._request_with_optional_relogin(
            '/announcements', params={'take': take}
        )

     
        return response.json()


    async def get_assign(self, id_assign:int) -> List[dict]:
        response = await self._client.get(
            url='webapi/student/diary/assigns/'+str(id_assign), 
            params={'studentId': self._student_id}
        )
        return response.json()
    

    async def attachments(
            self, assignment: data.Assignment) -> List[data.Attachment]:
        response = await self._request_with_optional_relogin(
            method="POST",
            path='student/diary/get-attachments',
            params={'studentId': self._student_id},
            json={'assignId': [assignment.id]},
        )
        attachments_json = response.json()[0]['attachments']

        attachments = schemas.Attachment().load(attachments_json, many=True)
        return [data.Attachment(**attachment) for attachment in attachments]


    async def logout(self):
        await self._client.post('webapi/auth/logout')
        await self._client.aclose()

    async def _address(self, school: str) -> Dict[str, int]:
        response = await self._client.get(
            'webapi/addresses/schools', params={'funcType': 2}
        )

        schools_reference = response.json()
        for school_ in schools_reference:
            if school_['name'] == school:
                self._school_id = school_['id']

                return {
                    'cid': school_['countryId'],
                    'sid': school_['stateId'],
                    'pid': school_['municipalityDistrictId'],
                    'cn': school_['cityId'],
                    'sft': 2,
                    'scid': school_['id'],
                }
        raise errors.SchoolNotFoundError(school)


    async def get_total_marks_from_report(self):
        response_with_cookies = await self._client.post(
            url='asp/Reports/ReportStudentTotalMarks.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'RPNAME': 'Итоговые отметки',
                'RPTID': 'StudentTotalMarks',      
            })

        self._client.cookies.extract_cookies(response_with_cookies) 

        response = await self._client.post(
            url='asp/Reports/StudentTotalMarks.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'LoginType': '0',
                'RPTID' :'StudentTotalMarks',
                'SID': self._student_id,
                'PCLID': self._class_id,
            })
        response_file = await self._client.get('static/dist/pages/common/css/export-tables.min.css')
        return response.text, response_file.text


    async def get_parrentInfoLetter_from_report(self):
        response_with_cookies = await self._client.post(
            url='/asp/Reports/ReportParentInfoLetter.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'RPNAME': 'Информационное письмо для родителей',
                'RPTID': 'ParentInfoLetter'
            })
        self._client.cookies.extract_cookies(response_with_cookies) 

        response = await self._client.post(
            url='asp/Reports/ParentInfoLetter.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'LoginType': '0',
                'RPTID' :'ParentInfoLetter',
                'SID': self._student_id,
                'PCLID': self._class_id,
                'ReportType':'2',
                'TERMID': 26904
            })
        response_file = await self._client.get('static/dist/pages/common/css/export-tables.min.css')

        return response.text, response_file.text



    async def get_average_mark_from_Report(self, start, end):
        response_with_cookies = await self._client.post(
            url='/asp/Reports/ReportStudentAverageMark.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'RPNAME': 'Средний балл',
                'RPTID': 'StudentAverageMark'
            })
        self._client.cookies.extract_cookies(response_with_cookies) 

        response = await self._client.post(
            url='asp/Reports/StudentAverageMark.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'LoginType': '0',
                'RPTID' :'StudentAverageMark',
                'SID': self._student_id,
                'PCLID': self._class_id,
                'ADT': start,
                'DDT': end
            })
        response_file = await self._client.get('static/dist/pages/common/css/export-tables.min.css')

        return response.text, response_file.text

            
    async def get_average_mark_dynamic_from_Report(self, start, end):
        response_with_cookies = await self._client.post(
            url='asp/Reports/ReportStudentAverageMarkDyn.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'RPNAME': 'Динамика среднего балла',
                'RPTID': 'StudentAverageMarkDyn',
            })
        self._client.cookies.extract_cookies(response_with_cookies) 
     
        response = await self._client.post(
            url='asp/Reports/StudentAverageMarkDyn.asp',
            data = {
                'AT': self._at,
                'VER': self._ver,
                'LoginType': '0',
                'RPTID' :'StudentAverageMarkDyn',
                'SID': self._student_id,
                'ADT': start,
                'DDT': end
            })
        response_file = await self._client.get('static/dist/pages/common/css/export-tables.min.css')
        return response.text, response_file.text






    #попытка получить отчёт успеваемости и посещаемости
    # async def get_fullreport_from_Report(self):
    #     response_with_cookies = await self._client.post(
    #         url='/angular/school/reports/studenttotal',
    #         data = {
    #             'AT': self._at,
    #             'VER': self._ver,
    #         })
    #     self._client.cookies.extract_cookies(response_with_cookies) 
     

    #     conn_token_response = await self._client.get(
    #         url='/WebApi/signalr/negotiate',
    #         params = {
    #             'clientProtocol': 1.5,
    #             'at': self._at,
    #             'connectionData': '[{"name":"queuehub"}]',
    #             '_':1634887902450
    #             }
    #             )

    #     conn_token_response = conn_token_response.json()
    #     conn_token = conn_token_response['ConnectionToken']
    #     conn_id = conn_token_response['ConnectionId']
    #     conn_url = conn_token_response['Url']

    #     print(conn_token)

                            
    #     response = await self._client.get(
    #         url='/WebApi/signalr/poll',
    #         params={
    #             'transport':'longPolling',
    #             'AT': self._at,
    #             'connectionToken': conn_token,
    #             'connectionData': '[{"name":"queuehub"}]'

    #         })

    #     print(response.json())
    #     #response_file = await self._client.get('static/dist/pages/common/css/export-tables.min.css')
    #     return response.text, response_file.text
