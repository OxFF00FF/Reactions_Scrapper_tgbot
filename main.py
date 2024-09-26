from Bot.setup_logging import logger

import os
from Bot.telegram_bot import EmotionsScrapperTelegramBot
from dotenv import load_dotenv


def main():
    # Read .env file
    load_dotenv()
    required_values = ['API_ID', 'API_HASH']
    missing_values = [value for value in required_values if os.environ.get(value) is None]
    if len(missing_values) > 0:
        logger.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)

    # Setting configuration values
    telegram_config = {
        'api_id': int(os.environ.get('API_ID')),
        'api_hash': str(os.environ.get('API_HASH')),
        'phone': str(os.environ.get('PHONE_NUMBER')),
        'token': str(os.environ['TELEGRAM_BOT_TOKEN']),
        'bot_username': os.environ.get('TELEGRAM_BOT_USERNAME', 'n/a'),
        'chat_id': int(os.environ.get('CHAT_ID')),
    }

    if not os.path.exists('sessions'):
        os.makedirs('sessions')

    telegram_bot = EmotionsScrapperTelegramBot(config=telegram_config)
    logger.info(f"Bot started As `{telegram_config['bot_username'].capitalize()}` · https://t.me/{telegram_config['bot_username'].capitalize()}")
    telegram_bot.run()


if __name__ == "__main__":
    main()
