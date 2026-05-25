#!/usr/bin/env python3
"""Send one test sale notification (no real role ping). Run on the VPS after user_info.json exists."""

import sys

from discord import send_discord_notification
from saved_info import load_user_info

BUNDLE_URL = "https://store.steampowered.com/bundle/6998/Assetto_Corsa_Ultimate_Edition/"


def main():
    info = load_user_info()
    if not info:
        print("Missing user_info.json — run main.py setup first.")
        sys.exit(1)

    send_discord_notification(
        game_name="Assetto Corsa Ultimate Edition",
        current_price=184.03,
        discount_percent=30,
        image_url=(
            "https://shared.akamai.steamstatic.com/store_item_assets/steam/"
            "bundles/6998/o2zrf7m5jxtaxbn8/header_ratio.jpg?t=1524219134"
        ),
        webhook_url=info["webhook_url"],
        bot_name=info.get("bot_name", "AC Ultimate Promo na Steam"),
        bot_avatar=info["bot_avatar"],
        app_id="6998",
        country_code=info["country_code"],
        currency_code="BRL",
        is_historical_low=False,
        historical_low=None,
        store_url=BUNDLE_URL,
        discord_role_id=None,
        mention_text="@alert-role",
    )
    print("Test message sent. Check your Discord channel.")


if __name__ == "__main__":
    main()
