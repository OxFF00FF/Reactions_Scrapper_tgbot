import asyncio
import traceback
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
from telethon.utils import get_input_peer

from Bot.colors import *
from Bot.setup_logging import logger
from Bot.utils import line_before, line_after, save_file, get_user_data, file_path, parse_messages, most_popular_posts


class EmotionsScrapperTelegramBot:
    channel = 'https://t.me/gosnomersale'

    def __init__(self, config, session_name: str = 'root'):
        self.client = TelegramClient(f'sessions/{session_name}', config['api_id'], config['api_hash'])
        self.config = config

    async def start_command(self, event: events.NewMessage.Event):
        await event.reply("Привет! Я ваш бот. Чем могу помочь?")

    async def help_command(self, event):
        await event.reply(
            "Доступные команды: \n"
            "/start - Начать работу \n"
            "/help - Помощь \n"
            "/top_week - Топ сообщений по количеству 👍 за неделю \n"
            "/top_month - Топ сообщений по количеству 👍 за месяц"
        )

    async def top_week_command(self, event: events.NewMessage.Event):
        user_id = event.chat_id
        message = event.message.id

        channel_messages = await self.get_messages(self.channel, 10)

        data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages)
        top_posts = self.sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, zero_target_emoji=False)

        text = most_popular_posts(top_posts)
        await self.client.send_message(user_id, f'Топ сообщений за неделю\n{text}', parse_mode='md', link_preview=False, reply_to=message)

    async def top_month_command(self, event):
        await event.reply('Топ сообщений за месяц')

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

    async def get_top_posts(self):
        user_input = get_user_data()
        channel = user_input['channel']
        emoji = user_input['emoji']

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

        data, emoji_counts, target_emoji_counts = parse_messages(channel, channel_messages, target_emoji=emoji)
        top_posts = self.sorting_by_emoji(channel, data, emoji_counts, target_emoji_counts,
                                          target_emoji=emoji, zero_target_emoji=False)

        if top_posts:
            print(f"\n{BOLD}Топ: {LIGHT_CYAN}{len(top_posts)}{WHITE} постов · По количеству эмоджи: {YELLOW}{emoji}{WHITE} · Всего сообщений: {LIGHT_MAGENTA}{len(data)}{RESET}")
            line_before(blank_line=False, width=71)
            for post in top_posts:
                print(post['formatted_string'])
            line_after(width=71)

            most_popular_posts(top_posts, emoji)

        else:
            print(f"ℹ️  Не найдено постов с эмоджи: {YELLOW}{emoji}{WHITE} в указанном диапозоне дат или количестве постов")

    async def start_bot(self):
        await self.client.start()
        logger.info(f"Bot started As `{self.config['bot_username'].capitalize()}` · https://t.me/{self.config['bot_username'].capitalize()}")

        self.client.add_event_handler(self.start_command, events.NewMessage(pattern='/start'))
        self.client.add_event_handler(self.help_command, events.NewMessage(pattern='/help'))
        self.client.add_event_handler(self.top_week_command, events.NewMessage(pattern='/top_week'))
        self.client.add_event_handler(self.top_month_command, events.NewMessage(pattern='/top_month'))

        await self.client.run_until_disconnected()

    def run(self):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.start_bot())

        except ConnectionError as e:
            logger.error(f"{RED}❌  Не удалось получить ответ от телеграм API{WHITE}\n{e}")

        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")

        except KeyboardInterrupt:
            logger.info("Application stopped...")
