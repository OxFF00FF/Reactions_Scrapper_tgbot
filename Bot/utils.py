import os
from datetime import datetime, timedelta
import json
from Bot.colors import *
from Bot.setup_logging import logger

filename = 'channel_messages.json'
file_path = os.path.join(os.path.abspath('data'), filename)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


def get_start_end_date(days: int) -> tuple[datetime, datetime]:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    start_date = start_date.strftime('%d.%m.%Y')
    end_date = end_date.strftime('%d.%m.%Y')

    start_date = datetime.strptime(start_date, '%d.%m.%Y')
    end_date = datetime.strptime(end_date, '%d.%m.%Y')

    end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
    return start_date, end_date


def sorting_by_emoji(channel_url: str, data: list, emoji_counts: dict, target_emoji_counts: dict, target_emoji='👍', zero_target_emoji=False) -> list:
    logger.info(f"{YELLOW}ℹ️  Sorting messages{WHITE}")

    result = []

    for url in emoji_counts:
        if url not in target_emoji_counts:
            target_emoji_counts[url] = 0

    sorted_posts = sorted(target_emoji_counts.items(), key=lambda x: emoji_counts.get(x[0], {}).get(target_emoji, 0), reverse=True)

    for e, (url, _) in enumerate(sorted_posts):
        emojis = emoji_counts.get(url, {})
        target_emoji_count = emojis.pop(target_emoji, 0)

        if not zero_target_emoji and target_emoji_count == 0:
            continue

        post_date = None
        post_message = None

        for item in data:
            if item['_'] == 'Message':
                message_id = item['id']
                if f"{channel_url}/{message_id}" == url:
                    post_message = item['message']
                    iso_date_str = str(item['date'])
                    date_obj = datetime.fromisoformat(iso_date_str)
                    post_date = date_obj.strftime("%d-%m-%Y %H:%M")
                    break

        if post_message and post_message.startswith('⚡️'):
            continue

        if post_date is None:
            post_date = "Unknown date"

        post_info = {
            "target_emoji": target_emoji,
            "target_emoji_count": target_emoji_count,
            "emoji_counts": {emoji: count for emoji, count in emojis.items()},
            "post_date": post_date,
            "url": url
        }

        emoji_info = f"{YELLOW}{post_info['target_emoji']}{WHITE}: {BOLD}{LIGHT_CYAN}{post_info['target_emoji_count']:<3}{RESET}{WHITE} │ " + \
                     " / ".join(f"{DARK_GRAY}{emoji}: {count}{WHITE}" for emoji, count in post_info['emoji_counts'].items())
        formatted_string = f"{e + 1:<3} │ {CYAN}{post_date}{WHITE} │ Пост: {url} · {emoji_info}"
        post_info["formatted_string"] = formatted_string

        result.append(post_info)

    logger.info(f"{GREEN}✅  Done{WHITE}")
    return result


def most_popular_posts(posts, emoji: str = '👍', top_count=5) -> str:
    message = f"**По количеству** {emoji}\n\n"
    for i in range(min(top_count, len(posts))):
        message += f"{i + 1}️⃣  [Место]({posts[i]['url']}) · {posts[i]['target_emoji_count']}\n"
    return message


def parse_messages(channel_url: str, messages: list, target_emoji: str = '👍') -> tuple:
    logger.info(f"{YELLOW}ℹ️  Parse messages{WHITE}")

    emoji_counts = {}
    target_emoji_counts = {}
    result = []

    if messages:
        data = messages

    for item in data:
        if item['_'] == 'Message':
            message_id = item['id']

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

            result.append(item)

    logger.info(f"{GREEN}✅  Done{WHITE}")
    return result, emoji_counts, target_emoji_counts


def get_user_data() -> dict:
    print(f"\n{YELLOW}👋  Привет. Я бот для получения сообщений из тегерам каналов{WHITE}\n")

    result = {}
    print(f"🤖  Откуда получить сообщения?")
    input_channel = input(f'{CYAN}▶️  URL телеграм канала: {WHITE}')

    if input_channel.startswith('https://t.me/') or input_channel.startswith('t.me/'):
        result['channel'] = input_channel

        print(f"\n🤖  По какому эмоджи сортировать? (по умолчанию 👍)")
        choice_emoji = input(f"{CYAN}▶️  Укажите эмоджи (Enter пропустить): ")
        if choice_emoji == '':
            result['emoji'] = '👍'
        else:
            result['emoji'] = choice_emoji

        print(f"\n🤖  Как нужно получить сообщения?\n"
              f"{LIGHT_YELLOW}1 │  {RESET}📅  {YELLOW}Диапазон дат (от начальной до конечной даты) {WHITE}\n"
              f"{LIGHT_YELLOW}2 │  {RESET}🔢  {YELLOW}Количество (от последнего от указанного количества) {WHITE}")
        choice = input(f"{CYAN}▶️  Выберите действие (1/2): {WHITE}")

        if choice == '1':
            print(f"\n{YELLOW}ℹ️  Укажите диапазон дат в формате: {BOLD}{LIGHT_BLUE}ДД.ММ.ГГГГ{RESET}{WHITE}")
            print(f"{YELLOW}ℹ️  Например: {BOLD}{LIGHT_BLUE}01.01.2024, 30.01.2024{RESET}{WHITE}\n")

            start_date = input(f"{CYAN}▶️  Начальная дата: ")
            end_date = input(f"{CYAN}▶️  Конечная дата:  ")
            try:
                start_date = datetime.strptime(start_date, '%d.%m.%Y')
                end_date = datetime.strptime(end_date, '%d.%m.%Y')
                end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
            except Exception as e:
                print(f"\n{LIGHT_RED}🚫 Неверно указан формат даты: {e}")
                exit(1)

            if start_date >= end_date:
                print(f"{RED}🚫  Дата начала должна быть меньше конечной даты{WHITE}")

            print(f"\n{YELLOW}ℹ️  Получаем сообщения за период: {BOLD}{LIGHT_BLUE}{start_date} - {end_date}\n{WHITE}")
            result['date_range'] = {'start': start_date, 'end': end_date}

        elif choice == '2':
            print(f"\n🤖  Сколько сообщений нужно получить?")
            total_count_limit = input(f"{CYAN}▶️  Укажите количество: {WHITE}")

            if total_count_limit.isdigit():
                print(f"{YELLOW}ℹ️  Получаем сообщений: {total_count_limit}{WHITE}\n")
                result['messages_count'] = int(total_count_limit)
            else:
                print(f"\n{LIGHT_RED}🚫  Количество должно быть числом{WHITE}")

        else:
            print(f"\n{LIGHT_RED}🚫  Такой опции нет: {choice}{WHITE}")
            exit(1)

    else:
        print(f"\n{LIGHT_RED}🚫  Указанный url не является телеграм каналом{WHITE}")
        exit(1)

    return result


def save_file(messages):
    if not os.path.exists('data'):
        os.makedirs('data')

    with open(file_path, 'w') as f:
        json.dump(messages, f, cls=DateTimeEncoder, ensure_ascii=True, indent=4)


def read_file():
    with open(file_path, 'r') as file:
        data = json.loads(file.read())
        return data


def line_before(blank_line=True, width=50):
    text = "\n┌" + "─" * width + "┐"
    if blank_line:
        print(text)
    else:
        print(text.strip())


def line_after(blank_line=True, width=50):
    text = "└" + "─" * width + "┘\n"
    if blank_line:
        print(text)
    else:
        print(text.strip())
