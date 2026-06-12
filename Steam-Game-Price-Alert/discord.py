import requests
import logging

RED = 16711680


def format_money(amount, country_code="US", currency_code=None):
    """Format price using region (BR → R$) or Steam currency code."""
    code = (currency_code or "").upper()
    cc = (country_code or "US").upper()
    if code == "BRL" or cc == "BR":
        return f"R${amount:.2f}"
    if code == "EUR":
        return f"€{amount:.2f}"
    if code == "GBP":
        return f"£{amount:.2f}"
    return f"${amount:.2f}"


def short_game_name(game_name):
    """Trim common suffixes so titles read like normal speech."""
    name = (game_name or "").strip()
    if name.endswith(" Edition"):
        return name[:-len(" Edition")]
    return name


def build_notification_content(discord_role_id=None, mention_text=None):
    """Plain text above the embed: role ping only."""
    if mention_text is not None:
        text = mention_text.strip()
    elif discord_role_id:
        text = f"<@&{discord_role_id}>"
    else:
        text = ""
    return text or None


def construct_embed(
    game_name,
    current_price,
    discount_percent,
    image_url,
    app_id,
    country_code="US",
    currency_code=None,
    store_url=None,
):
    """Embed preview: short discount title, price line, banner image."""
    price = format_money(current_price, country_code, currency_code)
    title = f"Discount: {short_game_name(game_name)}"
    description = f"{price} — {discount_percent}% off"

    return {
        "title": title,
        "description": description,
        "url": store_url or f"https://store.steampowered.com/app/{app_id}/",
        "color": RED,
        "image": {"url": image_url},
    }


def send_discord_notification(
    game_name: str,
    current_price: float,
    discount_percent: float,
    image_url: str,
    webhook_url: str,
    bot_name: str,
    bot_avatar: str,
    app_id: int,
    country_code: str = "US",
    currency_code: str = None,
    store_url: str = None,
    discord_role_id: str = None,
    mention_text: str = None,
) -> None:
    """Post webhook: role line above, Steam preview embed below."""
    page_url = store_url or f"https://store.steampowered.com/app/{app_id}/"
    content = build_notification_content(
        discord_role_id=discord_role_id,
        mention_text=mention_text,
    )
    payload = {
        "username": bot_name,
        "avatar_url": bot_avatar,
        "embeds": [
            construct_embed(
                game_name,
                current_price,
                discount_percent,
                image_url,
                app_id,
                country_code=country_code,
                currency_code=currency_code,
                store_url=page_url,
            )
        ],
    }
    if content:
        payload["content"] = content

    try:
        logging.info("Sending Discord notification...")
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Notification sent successfully.")
    except requests.Timeout:
        logging.error("Timeout while sending Discord notification")
    except requests.RequestException as e:
        logging.error(f"Error sending Discord notification: {e}")
    except Exception as e:
        logging.error(f"Unexpected error sending Discord notification: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
