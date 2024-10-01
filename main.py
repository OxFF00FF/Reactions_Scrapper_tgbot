from Bot.setup_logging import logger

import os
from Bot.telegram_bot import EmotionsScrapperTelegramBot
from dotenv import load_dotenv
import argparse
from Bot.colors import *


def main(console=False):
    logger.info(f"⚡️  {YELLOW}Application starting...{WHITE}")

    # Read .env file
    load_dotenv()
    required_values = ['API_ID', 'API_HASH', 'TELEGRAM_BOT_TOKEN']
    missing_values = [value for value in required_values if os.environ.get(value) is None]
    if len(missing_values) > 0:
        logger.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)

    # Setting configuration values
    telegram_config = {
        'api_id': int(os.environ.get('API_ID')),
        'api_hash': str(os.environ.get('API_HASH')),
        'token': str(os.environ['TELEGRAM_BOT_TOKEN']),
        'allowed_user_ids': os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '*'),
        'admin_user_ids': os.environ.get('ADMIN_USER_IDS', '-'),
        'logs_group': os.environ.get('BOT_LOGS_GROUP_ID')
    }

    if not os.path.exists('sessions'):
        os.makedirs('sessions')

    telegram_bot = EmotionsScrapperTelegramBot(config=telegram_config)

    if console:
        telegram_bot.run_console()
    else:
        telegram_bot.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск main с опцией -c для console.")
    parser.add_argument('-c', '--console', action='store_true', help="Запуск с console=True")
    args = parser.parse_args()

    main(console=args.console)

