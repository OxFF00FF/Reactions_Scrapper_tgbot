import traceback

from Bot.setup_logging import logger

from datetime import datetime

from telethon.utils import get_input_peer
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

from Bot.utils import line_before, line_after, read_file, save_file, get_user_data, file_path
from Bot.colors import *


class EmotionsScrapperTelegramBot:
    def __init__(self, config, session_name: str = 'root'):
        self.client = TelegramClient(f'sessions/{session_name}', config['api_id'], config['api_hash'])
        self.config = config

    async def get_messages(self, input_channel=None, total_count=1, start_date=None, end_date=None, offset_id=0, limit=100) -> list[dict]:
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
            print(f"{DARK_GRAY}✅  Вы вошли как {me.first_name} {me.last_name} ({me.username}){WHITE}\n")

        except Exception as e:
            print(f"🚫 Не удалось войти в аккаунт")
            logger.error(e)
            exit(1)

        line_before(blank_line=False, width=24)

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

        print(f"{YELLOW}ℹ️  Получено сообщений: {total_messages}{WHITE}")
        line_after(width=24)

        return all_messages

    def parse_messages(self, channel_url: str, messages: list = None, target_emoji: str = '👍') -> tuple:
        line_before(width=20)

        print(f"{YELLOW}ℹ️  Парсим сообщения{WHITE}")

        emoji_counts = {}
        target_emoji_counts = {}

        if messages:
            data = messages
        else:
            data = read_file()

        for item in data:
            if item['_'] == 'Message':
                message_id = item['id']
                print(f"\r📨  {message_id}", flush=True, end="")

                post_url = f"{channel_url}/{message_id}"

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
                        if emoji == target_emoji:
                            target_emoji_counts[post_url] = target_emoji_counts.get(post_url, 0) + count

        print(f"\n{GREEN}✅  Готово{WHITE}")
        line_after(width=20)
        return data, emoji_counts, target_emoji_counts

    def sorting_by_emoji(self, channel_url: str, data: list, emoji_counts: dict, target_emoji_counts: dict, target_emoji='👍') -> list:
        print(f"{YELLOW}ℹ️  Сортируем сообщения{WHITE}")

        result = []

        for url in emoji_counts:
            if url not in target_emoji_counts:
                target_emoji_counts[url] = 0

        sorted_posts = sorted(target_emoji_counts.items(), key=lambda x: emoji_counts.get(x[0], {}).get(target_emoji, 0), reverse=True)

        for e, (url, _) in enumerate(sorted_posts):
            emojis = emoji_counts.get(url, {})
            target_emoji_count = emojis.pop(target_emoji, 0)

            post_date = None
            for item in data:
                if item['_'] == 'Message':
                    message_id = item['id']
                    if f"{channel_url}/{message_id}" == url:
                        iso_date_str = str(item['date'])
                        date_obj = datetime.fromisoformat(iso_date_str)
                        post_date = date_obj.strftime("%d-%m-%Y %H:%M")
                        break
            if post_date is None:
                post_date = "Unknown date"

            emoji_info = f"{YELLOW}{target_emoji}{WHITE}: {BOLD}{LIGHT_CYAN}{target_emoji_count:<3}{RESET}{WHITE} │ " + " / ".join(f"{DARK_GRAY}{emoji}: {count}{WHITE}" for emoji, count in emojis.items())
            result.append(f"{e + 1:<3} │ {CYAN}{post_date}{WHITE} │ Пост: {url} · {emoji_info}")

        print(f"{GREEN}✅  Готово{WHITE}")
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
            print(f"{LIGHT_GREEN}✅  Файл успешно сохранен по пути:\n💾  {file_path}{WHITE}")
        except Exception as e:
            logger.error(f"{RED}❌  Не удалось сохранить файл{WHITE}\n{e}")

        emoji = '👍'
        data, emoji_counts, target_emoji_counts = self.parse_messages(channel, channel_messages, target_emoji=emoji)
        top_posts = self.sorting_by_emoji(channel, data, emoji_counts, target_emoji_counts, target_emoji=emoji)

        print(f"\n{BOLD}Топ: {BOLD}{LIGHT_CYAN}{len(top_posts)}{RESET}{WHITE} постов · По количеству эмоджи: {BOLD}{YELLOW}{emoji}{RESET}{WHITE} · Всего сообщений: {len(data)}{RESET}")
        line_before(blank_line=False, width=71)
        for post in top_posts:
            print(post)
        line_after(width=71)

    def run(self):
        try:
            with self.client:
                self.client.loop.run_until_complete(self.get_top_posts())

        except ConnectionError as e:
            logger.error(f"{RED}❌  Не удалось получить ответ от телеграм API{WHITE}\n{e}")

        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
