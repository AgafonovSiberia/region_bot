async def delete_account(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'DELETE FROM user_data WHERE user_id=$1'
        params = message.chat.id
        status = await session.execute(query, params)
    return 

async def get_status(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'SELECT * FROM user_data WHERE user_id=$1'
        params = message.chat.id
        status = await session.fetch(query, params)
    return status


async def get_name(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'SELECT user_name FROM user_data WHERE user_id=$1'
        params = message.chat.id
        name_user = await session.fetch(query, params)
    if name_user:
        return name_user[0][0]
    else:
        return None



async def get_login_pass(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'SELECT sgo_login, sgo_pass FROM user_data WHERE user_id=$1'
        params = message.chat.id
        data_sgo = await session.fetch(query, params)
    if data_sgo:
        return data_sgo[0][0], data_sgo[0][1]
    else:
        return None


async def update_nickname(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'UPDATE user_data SET user_name=$1 WHERE user_id=$2'
        params = message.text, message.chat.id
        await session.execute(query, *params)
    return None


async def insert_update_marks(message, marks_json):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = '''INSERT INTO marks_data(user_id, marks_json)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET marks_json=$2'''
        params = message.chat.id, marks_json
        await session.execute(query, *params)
    return None

async def get_marks_detail_from_db(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'SELECT marks_json FROM marks_data WHERE user_id=$1'
        params = message.chat.id
        marks_json = await session.fetch(query, params)

    return marks_json[0][0]


async def get_list_id_users(message):
    pool = message.bot.get('conn')
    async with pool.acquire() as session:
        query = 'SELECT user_id FROM user_data'
        list_id_users = await session.fetch(query)
    return list_id_users





