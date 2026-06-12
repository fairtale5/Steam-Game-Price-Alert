#!/usr/bin/env python3
"""One-shot price check for cron: read config + watchlist, notify if on sale, exit."""

import logging
import sys

from discord import send_discord_notification
from saved_games import get_all_games, get_game_link, initialize_database
from saved_info import get_discord_role_id, load_user_info
from stop_spam import get_remembered_discount, remember_discount_state, should_post_sale
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
        discount_percent = int(price_info["discount_percent"])
        image_url = game_data["header_image"]
        page_url = store_page_url(store_id, item_type)
        remembered = get_remembered_discount(store_id)

        logging.info(
            "%s: %.2f, %s%% off (remembered: %s)",
            game_name,
            current_price,
            discount_percent,
            remembered if remembered is not None else "none",
        )

        if should_post_sale(store_id, discount_percent):
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
                store_url=page_url,
                discord_role_id=role_id,
            )
            logging.info("Posted Discord alert for %s (%s%% off)", game_name, discount_percent)
        elif discount_percent > 0:
            logging.info("Skipped %s — same discount as last run (%s%%)", game_name, discount_percent)
        else:
            logging.info("Skipped %s — full price, no discount", game_name)

        remember_discount_state(store_id, game_name, current_price, discount_percent)


if __name__ == "__main__":
    main()
