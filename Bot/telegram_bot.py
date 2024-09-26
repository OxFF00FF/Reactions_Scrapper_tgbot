from Bot.setup_logging import logger

import json
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telethon.utils import get_input_peer
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

from Bot.utils import line_before, line_after, DateTimeEncoder, read_file, save_file, get_user_data
from Bot.colors import *


class EmotionsScrapperTelegramBot:
    def __init__(self, config, session_name: str = 'root'):
        self.client = TelegramClient(f'sessions/{session_name}', config['api_id'], config['api_hash'])
        self.config = config

    async def get_messages(self, input_channel=None, total_count=1, start_date=None, end_date=None, offset_id=0, limit=100) -> list[dict]:
        """
        :param phone_number: Номер телефона в международном формате
        :param offset_id: С какого ID сообщения начать. по умолчанию с самого последнего
        :param limit: Сколько сообщений получать за 1 запрос. По умолчанию 100
        """

        try:
            await self.client.start()

            if not await self.client.is_user_authorized():
                print("⚠️  Не удалось найти сессию или войти в существующую")
                print("ℹ️  Чтобы создать сессию, укажите номер телефона телеграм аккаунта в международном формате\n")
                await self.client.send_code_request(self.config['phone'])

                try:
                    await self.client.sign_in(self.config['phone'], input('Enter the code: '))
                except SessionPasswordNeededError:
                    await self.client.sign_in(password=input('Password: '))

            me = await self.client.get_me()
            print(f"{DARK_GRAY}✅  Вы вошли как {me.first_name} {me.last_name} ({me.username}){WHITE}")

        except Exception as e:
            print(f"🚫 Не удалось войти в аккаунт")
            logger.error(e)
            exit(1)

        if total_count > limit:
            line_before()

        total_messages = 0
        all_messages = []

        if input_channel.isdigit():
            entity = PeerChannel(int(input_channel))
        else:
            entity = input_channel

        channel = await self.client.get_entity(entity)
        input_peer = get_input_peer(channel)
        while True:
            history = await self.client(GetHistoryRequest(
                peer=input_peer,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break

            messages = history.messages

            # Если выбран диапазон дат
            if start_date and end_date:
                for message in messages:
                    message_date = message.date.replace(tzinfo=None)
                    if start_date <= message_date <= end_date:
                        all_messages.append(message.to_dict())
                    elif message_date < start_date:
                        break

            # Если выбрано количество сообщений
            if total_count:
                for message in messages:
                    all_messages.append(message.to_dict())
                    total_messages = len(all_messages)
                    if total_messages >= total_count:
                        break

                if total_count != 0 and total_messages >= total_count:
                    break

            offset_id = messages[-1].id
            total_messages = len(all_messages)
            if len(messages) < limit:
                break

            print(f"🆔  Смещение ID: {offset_id} · Всего сообщений: {total_messages}")

        if total_count > limit:
            line_after()

        # Печать итогового количества сообщений
        print(f"{YELLOW}ℹ️  Получено сообщений: {total_messages}{WHITE}\n")

        return all_messages

    def parse_messages(self, channel_url: str, messages: list = None) -> list:
        print(f"{YELLOW}ℹ️  Парсим сообщения{WHITE}\n")

        result = []
        emoji_counts = {}
        thumbs_up_counts = {}

        if messages:
            data = messages
        else:
            data = read_file()

        for item in data:
            if item['_'] == 'Message':
                message_id = item['id']
                post_url = f"{channel_url}/{message_id}"

                iso_date_str = item['date']
                date_obj = datetime.fromisoformat(iso_date_str)
                post_date = date_obj.strftime("%d-%m-%Y %H:%M")

                reactions = item.get('reactions')
                if reactions:
                    results = reactions.get('results')
                    for reaction in results:
                        emoji = reaction['reaction']['emoticon']
                        count = reaction['count']

                        if post_url not in emoji_counts:
                            emoji_counts[post_url] = {}

                        if emoji not in emoji_counts[post_url]:
                            emoji_counts[post_url][emoji] = 0

                        emoji_counts[post_url][emoji] += count

                        if emoji == '👍':
                            thumbs_up_counts[post_url] = thumbs_up_counts.get(post_url, 0) + count

        for url in emoji_counts:
            if url not in thumbs_up_counts:
                thumbs_up_counts[url] = 0

        sorted_posts = sorted(thumbs_up_counts.items(), key=lambda x: x[1], reverse=True)

        for e, (url, _) in enumerate(sorted_posts):
            emojis = emoji_counts.get(url, {})
            thumbs_up_count = emojis.pop('👍', 0)

            post_date = None
            for item in data:
                if item['_'] == 'Message':
                    message_id = item['id']
                    if f"{channel_url}/{message_id}" == url:
                        iso_date_str = item['date']
                        date_obj = datetime.fromisoformat(iso_date_str)
                        post_date = date_obj.strftime("%d-%m-%Y %H:%M")
                        break
            if post_date is None:
                post_date = "Unknown date"

            emoji_info = f"{YELLOW}👍{WHITE}: {GREEN}{thumbs_up_count:<3}{WHITE} | " + " / ".join(f"{DARK_GRAY}{emoji}: {count}{WHITE}" for emoji, count in emojis.items())
            result.append(f"{e + 1:<3} | {CYAN}{post_date}{WHITE} | {YELLOW}Пост: {url}{WHITE} · {emoji_info}")

        return result

    async def get_top_posts(self):
        user_input = get_user_data()
        channel = user_input['channel']

        if 'date_range' in user_input:
            start = user_input['date_range']['start']
            end = user_input['date_range']['end']
            channel_messages = await self.get_messages(input_channel=channel, start_date=start, end_date=end)

        if 'messages_count' in user_input:
            count = int(user_input['messages_count'])
            channel_messages = await self.get_messages(input_channel=channel, total_count=count)

        # Сохранение полученных сообщений в json файл
        try:
            save_file(channel_messages)
            print(f"{LIGHT_GREEN}✅  Файл успешно сохранен{WHITE}\n")
        except Exception as e:
            logger.error(f"{RED}❌  Не удалось сохранить файл{WHITE}\n{e}")

        # top_posts = self.parse_messages(channel, channel_messages)
        # for post in top_posts:
        #     print(post)

    def run(self):
        # try:
        with self.client:
            self.client.loop.run_until_complete(self.get_top_posts())

        # except ConnectionError as e:
        #     logger.error(f"{RED}❌  Не удалось получить ответ от телеграм API{WHITE}\n{e}")
