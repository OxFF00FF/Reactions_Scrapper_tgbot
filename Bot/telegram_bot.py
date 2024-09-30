import asyncio
import sys
import traceback

from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, BotCommand
from telethon.utils import get_input_peer

from Bot.colors import *
from Bot.setup_logging import logger
from Bot.utils import parse_messages, most_popular_posts, sorting_by_emoji, get_start_end_date, save_file, file_path, get_user_data, line_before, line_after, is_allowed


class EmotionsScrapperTelegramBot:
    channel = 'https://t.me/gosnomersale'

    def __init__(self, config, session_name: str = 'client'):
        # Init Bot and Client
        self.client = TelegramClient(f'sessions/{session_name}', config['api_id'], config['api_hash']).start()
        self.bot = TelegramClient(f'sessions/bot', config['api_id'], config['api_hash']).start(bot_token=config['token'])

        # Set bot commands
        self.commands = [
            BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='help', description='Получить справку'),
            BotCommand(command='top_week', description='Топ за неделю'),
            BotCommand(command='top_month', description='Топ за месяц'),
            BotCommand(command='topfor', description='Топ за период и эмоджи')
        ]

        self.session_name = session_name
        self.config = config

    # ===== UTILS ===== #
    async def save_message(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender, log=False):
            await self.send_disallowed_message(event)
            return

        user_id = sender.id
        user_name = sender.first_name if sender else 'Unknown'
        user_last_name = sender.last_name if sender else 'Unknown'
        message_text = event.message.message

        if event.is_private:
            logger.info(f"📩  ADD new message: {LIGHT_YELLOW}`{message_text}`{WHITE} FROM user: {user_name} {user_last_name} · {user_id}")

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
            print(f"\r🆔  Offset ID: {offset_id} · Total messages: {total_messages}", end="", flush=True)

        print()
        logger.info(f"{YELLOW}ℹ️  Recieved messages: {total_messages}{WHITE}")
        return all_messages

    async def post_init(self) -> None:
        """
        Post initialization hook for the bot.
        """
        bot = await self.bot.get_me()
        logger.info(f"{LIGHT_BLUE}Bot started as {WHITE}{bot.first_name.capitalize()} · https://t.me/{bot.username}{WHITE}")

        me = await self.client.get_me()
        logger.info(f"{LIGHT_BLUE}Client started as {WHITE}{me.first_name} {me.last_name}{LIGHT_BLUE} ({me.username}) · {me.id} {WHITE}")

        # Add commands to bot commands list
        await self.bot(functions.bots.SetBotCommandsRequest(types.BotCommandScopeDefault(), lang_code='ru', commands=self.commands))
    # ===== /UTILS ===== #

    ####################################################

    # ===== COMMANDS ===== #
    async def start_command(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender):
            await self.send_disallowed_message(event)
            return

        text = f"👋  Привет. Я бот для получения сообщений из тегерам каналов\n\n" \
               f"Список доступных команд:  /help"
        await event.reply(text)

    async def help_command(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender):
            await self.send_disallowed_message(event)
            return

        await event.reply(
            "⚙️  Доступные команды: \n\n"
            "·  /start - Приветсвтенное сообщение \n"
            "·  /help - Помощь \n"
            "·  /top_week - Топ сообщений по количеству 👍 за неделю \n"
            "·  /top_month - Топ сообщений по количеству 👍 за месяц \n"
            "·  /topfor - Топ сообщений выбранный период и выбранному эмоджи\n\n"
            "ℹ️  __**Как использовать команду topfor**__\n\n"
            "⚙️  **Синтаксис: `/topfor_<days>_<top_count>_<emoji>`**\n"
            "**days** - Количество дней от текущей даты за которое будут получены сообщения (по умолчанию 1)\n"
            "**top_count** - Количество строчек в топе (по умолчанию 5)\n"
            "**emoji** - Выбранный эмоджи по которому сортируется топ (по умолчанию 👍)\n\n"
            "⚙️  __**Использование:**__\n"
            "/topfor_5 - Получит и отсортирует посты за 5 дней, по количеству 👍 и выведет первые 5\n\n"
            "/topfor_7_10 - Получит отсортирует, посты за 7 дней, по количеству 👍 и выведет первые 10\n\n"
            "/topfor_3_😂 - Получит отсортирует, посты за 3 дня, по количеству 😂 и выведет первые 5\n\n"
            "/topfor_30_7_👎 - Получит и отсортирует посты за 30 дней, по количеству 👎 и выведет первые 7\n"
        )

    async def top_week_command(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender):
            await self.send_disallowed_message(event)
            return

        user_id = sender.id

        loading_message = await self.bot.send_message(entity=user_id, message='⏳')

        async def _execute():
            start_date, end_date = get_start_end_date(7)
            logger.info(f"{YELLOW}ℹ️  Getting messages for period: {LIGHT_MAGENTA}{start_date} - {end_date}{WHITE}")

            channel_messages = await self.get_messages(self.channel, start_date=start_date, end_date=end_date)

            data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages)
            top_posts = sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, zero_target_emoji=False)

            result = f'Топ сообщений за неделю\n{most_popular_posts(top_posts)}'
            await event.reply(result, link_preview=False)
            return result
        text = await _execute()

        await self.bot.delete_messages(entity=user_id, message_ids=loading_message.id)

        if event.is_private:
            logger.info(f"📨  SEND message: {LIGHT_YELLOW}`{text[:20]}...{text[-20:]}`{WHITE} TO user: {user_id}".replace('\n', ''))

    async def top_month_command(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender):
            await self.send_disallowed_message(event)
            return

        user_id = sender.id

        loading_message = await self.bot.send_message(entity=user_id, message='⏳')

        async def _execute():
            start_date, end_date = get_start_end_date(30)
            logger.info(f"{YELLOW}ℹ️  Getting messages for period: {LIGHT_MAGENTA}{start_date} - {end_date}{WHITE}")

            channel_messages = await self.get_messages(self.channel, start_date=start_date, end_date=end_date)

            data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages)
            top_posts = sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, zero_target_emoji=False)

            result = f'Топ сообщений за месяц\n{most_popular_posts(top_posts)}'
            await event.reply(result, link_preview=False)
        text = await _execute()

        await self.bot.delete_messages(entity=user_id, message_ids=loading_message.id)

        if event.is_private:
            logger.info(f"📨  SEND message: {LIGHT_YELLOW}`{text[:20]}...{text[-20:]}`{WHITE} TO user: {user_id}".replace('\n', ''))

    async def top_for_command(self, event: events.NewMessage.Event):
        sender = await event.get_sender()
        if not await is_allowed(self.config, sender):
            await self.send_disallowed_message(event)
            return

        user_id = sender.id

        loading_message = await self.bot.send_message(entity=user_id, message='⏳')

        async def _execute():
            message = event.message.message.split('_')

            days = 1
            top_count = 5
            emoji = '👍'

            try:
                # /topfor_<days>_<top_count>_<emoji>
                if len(message) == 2:  # /topfor_<days>
                    days = int(message[1])
                elif len(message) == 3:  # /topfor_<days>_<emoji>
                    days = int(message[1])
                    emoji = message[2]
                    if emoji.isdigit():
                        top_count = message[2]
                elif len(message) == 4:  # /topfor_<days>_<top_count>_<emoji>
                    days = int(message[1])
                    top_count = int(message[2])
                    emoji = str(message[3])
                else:
                    await event.reply(f"Для работы команды `topfor` нужно передать параметры. Подробнее: /help")
                    return ''

            except ValueError:
                await event.reply('days или top_count не являются числом', link_preview=False)
                return ''

            start_date, end_date = get_start_end_date(days)
            logger.info(f"{YELLOW}ℹ️  Getting messages for period: {LIGHT_MAGENTA}{start_date} - {end_date}{WHITE}")
            logger.info(f"{YELLOW}ℹ️  Sorting by: {emoji} · Top count: {top_count}")

            channel_messages = await self.get_messages(self.channel, start_date=start_date, end_date=end_date)

            data, emoji_counts, target_emoji_counts = parse_messages(self.channel, channel_messages, target_emoji=emoji)
            top_posts = sorting_by_emoji(self.channel, data, emoji_counts, target_emoji_counts, target_emoji=emoji, zero_target_emoji=False)

            result = f'Топ сообщений за {days} дней\n{most_popular_posts(top_posts, emoji, top_count)}'
            await event.reply(result, link_preview=False)
            return result
        text = await _execute()

        await self.bot.delete_messages(entity=user_id, message_ids=loading_message.id)

        if event.is_private:
            if text != '':
                logger.info(f"📨  SEND message: {LIGHT_YELLOW}`{text[:20]}...{text[-20:]}`{WHITE} TO user: {user_id}".replace('\n', ''))
            else:
                logger.info(f"📨  Nothing to send")
    # ===== /COMMANDS ===== #

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
            logger.info(f"{LIGHT_GREEN}✅  Файл успешно сохранен по пути:{WHITE}")
            logger.info(f"{LIGHT_GREEN}💾  {file_path}{WHITE}")
        except Exception as e:
            logger.error(f"\n{RED}❌  Не удалось сохранить файл{WHITE}\n{e}\n")

        data, emoji_counts, target_emoji_counts = parse_messages(channel, channel_messages, target_emoji=emoji)
        top_posts = sorting_by_emoji(channel, data, emoji_counts, target_emoji_counts,
                                     target_emoji=emoji, zero_target_emoji=False)

        if top_posts:
            print(f"\n{BOLD}Топ: {LIGHT_CYAN}{len(top_posts)}{WHITE} постов · По количеству эмоджи: {YELLOW}{emoji}{WHITE} · Всего постов: {LIGHT_MAGENTA}{len(data)}{RESET}")
            line_before(width=71, blank_line=False)
            for post in top_posts:
                print(post['formatted_string'])
            line_after(width=71)

        else:
            print(f"ℹ️  Не найдено постов с эмоджи: {YELLOW}{emoji}{WHITE} в указанном диапозоне дат или количестве")

    async def send_disallowed_message(self, event: events.NewMessage.Event):
        """
        Sends the disallowed message to the user.
        """
        await event.reply("🚫  Извините, вам не разрешено использовать этого бота", link_preview=False)

    def run(self):
        try:
            """
            Runs the bot indefinitely until the user presses Ctrl+C
            """
            # === BOT handlers === #

            # Message handlers
            self.bot.add_event_handler(self.save_message, events.NewMessage())

            # Command handlers
            self.bot.add_event_handler(self.start_command, events.NewMessage(pattern=r'^/start$'))
            self.bot.add_event_handler(self.help_command, events.NewMessage(pattern=r'^/help$'))
            self.bot.add_event_handler(self.top_week_command, events.NewMessage(pattern=r'^/top_week$'))
            self.bot.add_event_handler(self.top_month_command, events.NewMessage(pattern=r'^/top_month$'))
            self.bot.add_event_handler(self.top_for_command, events.NewMessage(pattern=r'^/topfor'))


            # Starting async tasks Client and Bot
            self.client.loop.run_until_complete(self.post_init())
            asyncio.gather(self.client.run_until_disconnected(), self.bot.run_until_disconnected())

        except ConnectionError as e:
            logger.error(f"{RED}❌  Не удалось получить ответ от телеграм API{WHITE}\n{e}")
            exit(1)

        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            exit(1)

        except KeyboardInterrupt:
            logger.info("Application stopped...")
            sys.exit(0)

    def run_console(self):
        self.client.loop.run_until_complete(self.get_top_posts())
