import requests
import logging

RED = 16711680
GREEN = 32768


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


def build_notification_content(discord_role_id=None, mention_text=None, is_historical_low=False):
    """Plain text above the embed: role ping only."""
    if mention_text is not None:
        text = mention_text.strip()
    elif discord_role_id:
        text = f"<@&{discord_role_id}>"
    else:
        text = ""
    if is_historical_low and text:
        text += "\n⭐ Menor preço que já vimos!"
    return text or None


def construct_embed(
    game_name,
    current_price,
    discount_percent,
    image_url,
    app_id,
    country_code="US",
    currency_code=None,
    is_historical_low=False,
    historical_low=None,
    store_url=None,
):
    """Embed preview: clickable title, price line, banner image."""
    price = format_money(current_price, country_code, currency_code)
    description_parts = []

    if discount_percent > 0:
        description_parts.append(f"{price} — {discount_percent}% de desconto")
        color = RED
    else:
        description_parts.append(f"Meta de preço: {price}")
        color = GREEN

    if is_historical_low:
        description_parts.append("⭐ Menor preço registrado")
    elif historical_low and historical_low < current_price:
        description_parts.append(
            f"Menor preço antes: {format_money(historical_low, country_code, currency_code)}"
        )

    return {
        "title": game_name,
        "description": "\n".join(description_parts),
        "url": store_url or f"https://store.steampowered.com/app/{app_id}/",
        "color": color,
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
    is_historical_low: bool = False,
    historical_low: float = None,
    store_url: str = None,
    discord_role_id: str = None,
    mention_text: str = None,
) -> None:
    """Post webhook: role line above, Steam preview embed below."""
    page_url = store_url or f"https://store.steampowered.com/app/{app_id}/"
    content = build_notification_content(
        discord_role_id=discord_role_id,
        mention_text=mention_text,
        is_historical_low=is_historical_low,
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
                is_historical_low=is_historical_low,
                historical_low=historical_low,
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
