import traceback

from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, BotCommand
from telethon.utils import get_input_peer

from Bot.colors import *
from Bot.setup_logging import logger
from Bot.utils import parse_messages, most_popular_posts, sorting_by_emoji, get_start_end_date


class EmotionsScrapperTelegramBot:
    channel = 'https://t.me/gosnomersale'

    def __init__(self, config, session_name: str = 'root'):
        self.client = TelegramClient(f'sessions/client', config['api_id'], config['api_hash']).start()
        self.bot = TelegramClient(f'sessions/bot', config['api_id'], config['api_hash']).start(bot_token=config['token'])

        self.commands = [
            BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='help', description='Получить справку'),
            BotCommand(command='top_week', description='Топ сообений за неделю'),
            BotCommand(command='top_month', description='Топ сообений за месяц')
        ]

        self.session_name = session_name
        self.config = config

    async def save_message(self, event: events.NewMessage.Event):
        try:
            user_id = event.message.from_id.user_id
        except:
            user_id = event.message.peer_id.user_id

        sender = await event.get_sender()
        user_name = sender.first_name if sender else 'Unknown'
        user_last_name = sender.last_name if sender else 'Unknown'
        message_text = event.message.message

        if event.is_private:
            logger.info(f"📩  ADD new message: {LIGHT_YELLOW}`{message_text}`{WHITE} FROM user: {user_name} {user_last_name} · {user_id}")

    async def start_command(self, event: events.NewMessage.Event):
        await event.reply("Привет! Я ваш бот. Чем могу помочь?")

    async def help_command(self, event: events.NewMessage.Event):
        await event.reply(
            "Доступные команды: \n"
            "/start - Начать работу \n"
            "/help - Помощь \n"
            "/top_week - Топ сообщений по количеству 👍 за неделю \n"
            "/top_month - Топ сообщений по количеству 👍 за месяц"
        )

    async def top_week_command(self, event: events.NewMessage.Event):
        try:
            user_id = event.message.from_id.user_id
        except:
            user_id = event.message.peer_id.user_id

        start_date, end_date = get_start_end_date(7)
        logger.info(f"{YELLOW}ℹ️  Получаем сообщения за период: {LIGHT_MAGENTA}{start_date} - {end_date}{WHITE}")

        channel_messages = await self.get_messages(self.channel, start_date=start_date, end_date=end_date)

        data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages)
        top_posts = sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, zero_target_emoji=False)

        text = f'Топ сообщений за неделю\n{most_popular_posts(top_posts)}'
        await event.reply(text, link_preview=False)
        logger.info(f"📨  SEND message: {LIGHT_YELLOW}`{text[:20]}...{text[-20:]}`{WHITE} TO user: {user_id}".replace('\n', ''))

    async def top_month_command(self, event: events):
        try:
            user_id = event.message.from_id.user_id
        except:
            user_id = event.message.peer_id.user_id

        start_date, end_date = get_start_end_date(30)
        logger.info(f"{YELLOW}ℹ️  Получаем сообщения за период: {LIGHT_MAGENTA}{start_date} - {end_date}{WHITE}")

        channel_messages = await self.get_messages(self.channel, start_date=start_date, end_date=end_date)

        data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages)
        top_posts = sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, zero_target_emoji=False)

        text = f'Топ сообщений за месяц\n{most_popular_posts(top_posts)}'
        await event.reply(text, link_preview=False)
        logger.info(f"📨  SEND message: {LIGHT_YELLOW}`{text[:20]}...{text[-20:]}`{WHITE} TO user: {user_id}".replace('\n', ''))

    async def get_messages(self, input_channel=None, total_count=None, start_date=None, end_date=None, offset_id=0, limit=100) -> list[dict]:
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
            print(f"\r🆔  Смещение ID: {offset_id} · Всего сообщений: {total_messages}", end="", flush=True)

        logger.info(f"{YELLOW}ℹ️  Получено сообщений: {total_messages}{WHITE}")
        return all_messages

    async def post_init(self) -> None:
        """
        Post initialization hook for the bot.
        """
        await self.client(functions.bots.SetBotCommandsRequest(types.BotCommandScopeDefault(), lang_code='ru', commands=self.commands))

    def run(self):
        try:
            self.client.add_event_handler(self.save_message, events.NewMessage())

            self.client.add_event_handler(self.start_command, events.NewMessage(pattern='/start'))
            self.client.add_event_handler(self.help_command, events.NewMessage(pattern='/help'))
            self.client.add_event_handler(self.top_week_command, events.NewMessage(pattern='/top_week'))
            self.client.add_event_handler(self.top_month_command, events.NewMessage(pattern='/top_month'))

            self.client.loop.run_until_complete(self.post_init())
            self.client.run_until_disconnected()

        except ConnectionError as e:
            logger.error(f"{RED}❌  Не удалось получить ответ от телеграм API{WHITE}\n{e}")
            exit(1)

        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            exit(1)

        except KeyboardInterrupt:
            logger.info("Application stopped...")
