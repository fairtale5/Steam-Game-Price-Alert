#!/usr/bin/env python3
"""One-shot price check for cron: read config + watchlist, notify if on sale, exit."""

import logging
import sys

from discord import send_discord_notification
from saved_games import (
    get_all_games,
    get_game_link,
    get_historical_low,
    initialize_database,
    save_price_history,
)
from saved_info import get_discord_role_id, load_user_info
from stop_spam import is_sale_notified, remove_expired_sale, save_sale_reminder
from utils import extract_app_id, fetch_store_item, parse_steam_link, store_page_url

logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def main():
    initialize_database()
    info = load_user_info()
    if not info:
        logging.error("user_info.json missing or invalid")
        sys.exit(1)

    games = get_all_games()
    if not games:
        logging.error("Watchlist empty — add a game with main.py option 2")
        sys.exit(1)

    country_code = info["country_code"]
    language = info["language"]
    role_id = get_discord_role_id()

    for game_id, game_name in games:
        game_link = get_game_link(game_id)
        store_id = extract_app_id(game_link)
        _store_id, item_type = parse_steam_link(game_link)
        if not store_id:
            logging.warning("Skipping invalid link for %s", game_name)
            continue

        game_data = fetch_store_item(game_link, country_code, language)
        if not game_data or "price_overview" not in game_data:
            logging.warning("No price for %s", game_name)
            continue

        price_info = game_data["price_overview"]
        current_price = price_info["final"] / 100
        discount_percent = price_info["discount_percent"]
        image_url = game_data["header_image"]
        page_url = store_page_url(store_id, item_type)

        save_price_history(game_id, store_id, current_price, discount_percent)
        historical_low = get_historical_low(game_id, store_id)
        is_historical_low = (
            historical_low is not None and current_price <= historical_low
        )

        logging.info("%s: %.2f, %s%% off", game_name, current_price, discount_percent)

        if discount_percent > 0:
            if not is_sale_notified(store_id):
                send_discord_notification(
                    game_name=game_name,
                    current_price=current_price,
                    discount_percent=discount_percent,
                    image_url=image_url,
                    webhook_url=info["webhook_url"],
                    bot_name=info["bot_name"],
                    bot_avatar=info["bot_avatar"],
                    app_id=store_id,
                    country_code=country_code,
                    currency_code=price_info.get("currency"),
                    is_historical_low=is_historical_low,
                    historical_low=historical_low,
                    store_url=page_url,
                    discord_role_id=role_id,
                )
                save_sale_reminder(store_id, game_name, current_price, discount_percent)
                logging.info("Discord notification sent for %s", game_name)
            else:
                logging.info("Sale already notified for %s", game_name)
        elif is_sale_notified(store_id):
            remove_expired_sale(store_id)
            logging.info("Sale ended for %s", game_name)


if __name__ == "__main__":
    main()
