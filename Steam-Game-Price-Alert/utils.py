import os
import requests
import logging
import re
from urllib.parse import urlparse
from pyfiglet import Figlet
from saved_games import get_all_games as _get_all_games

# Re-export get_all_games from saved_games to avoid duplication
def get_all_games():
    """Retrieve all games from the database."""
    return _get_all_games()

def clear_screen():
    """Clears the screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Prints a header with a cool design using ASCII art."""
    f = Figlet(font='slant')
    print("\033[1;34m" + f.renderText(title) + "\033[0m")

STEAM_STORE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def parse_steam_link(steam_link):
    """Read store id and kind (app or bundle) from a Steam store URL."""
    try:
        parsed = urlparse(steam_link)
        if "steampowered.com" not in parsed.netloc:
            return None, None
        path = parsed.path or ""
        if "/app/" in path:
            store_id = path.split("/app/")[1].split("/")[0]
            return store_id, "app"
        if "/bundle/" in path:
            store_id = path.split("/bundle/")[1].split("/")[0]
            return store_id, "bundle"
        return None, None
    except Exception as e:
        logging.error(f"Invalid game link: {e}")
        return None, None


def extract_app_id(game_link):
    """Read store id from an /app/ or /bundle/ link (kept for existing callers)."""
    store_id, _kind = parse_steam_link(game_link)
    return store_id


def store_page_url(store_id, item_type="app"):
    """Build the Steam store page URL for an app or bundle id."""
    if item_type == "bundle":
        return f"https://store.steampowered.com/bundle/{store_id}/"
    return f"https://store.steampowered.com/app/{store_id}/"


def get_game_details(app_id, country_code, language):
    """Fetch app details from the Steam appdetails API."""
    try:
        response = requests.get(
            f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc={country_code}&l={language}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get(app_id, {}).get("data")
    except requests.RequestException as e:
        logging.error(f"Error fetching details for app {app_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching details for app {app_id}: {e}")
        return None


def _bundle_row_to_game_data(bundle_row, country_code="US"):
    """Map ajaxresolvebundles JSON into the same shape scanners expect from appdetails."""
    initial = int(bundle_row.get("initial_price") or 0)
    final = int(bundle_row.get("final_price") or 0)
    discount_percent = int(bundle_row.get("bundle_base_discount") or 0)
    if initial > 0 and final < initial:
        calculated = int(round((1 - final / initial) * 100))
        discount_percent = max(discount_percent, calculated)
    currency = "BRL" if country_code.upper() == "BR" else "USD"
    return {
        "name": bundle_row.get("name", "Unknown"),
        "header_image": bundle_row.get("header_image_url") or bundle_row.get("main_capsule", ""),
        "price_overview": {
            "currency": currency,
            "initial": initial,
            "final": final,
            "discount_percent": discount_percent,
        },
    }


def get_bundle_details(bundle_id, country_code, language):
    """Fetch bundle price/name via the store ajaxresolvebundles endpoint."""
    try:
        response = requests.get(
            "https://store.steampowered.com/actions/ajaxresolvebundles",
            params={
                "bundleids": bundle_id,
                "cc": country_code,
                "l": language,
            },
            headers={"User-Agent": STEAM_STORE_UA},
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            logging.error(f"No bundle data returned for bundle {bundle_id}")
            return None
        return _bundle_row_to_game_data(rows[0], country_code)
    except requests.RequestException as e:
        logging.error(f"Error fetching bundle {bundle_id}: {e}")
        return None
    except (ValueError, TypeError, KeyError) as e:
        logging.error(f"Unexpected bundle response for {bundle_id}: {e}")
        return None


def fetch_store_item(steam_link, country_code, language):
    """Fetch app or bundle store data using the link stored in the watchlist."""
    store_id, item_type = parse_steam_link(steam_link)
    if not store_id:
        return None
    if item_type == "bundle":
        return get_bundle_details(store_id, country_code, language)
    return get_game_details(store_id, country_code, language)

def get_detailed_game_info(app_id, country_code, language, steam_link=None):
    """Get detailed game information including release date, reviews, and tags."""
    if steam_link and parse_steam_link(steam_link)[1] == "bundle":
        game_data = get_bundle_details(app_id, country_code, language)
    else:
        game_data = get_game_details(app_id, country_code, language)
    if not game_data:
        return None
    
    info = {
        'name': game_data.get('name', 'Unknown'),
        'release_date': game_data.get('release_date', {}).get('date', 'Unknown'),
        'header_image': game_data.get('header_image', ''),
        'short_description': game_data.get('short_description', 'No description available'),
        'price_overview': game_data.get('price_overview'),
        'genres': [],
        'categories': [],
        'recommendations': game_data.get('recommendations', {}).get('total', 0),
        'metacritic': game_data.get('metacritic', {}).get('score', None),
        'developers': game_data.get('developers', []),
        'publishers': game_data.get('publishers', []),
    }
    
    # Extract genres
    if 'genres' in game_data:
        info['genres'] = [genre.get('description', '') for genre in game_data['genres']]
    
    # Extract categories
    if 'categories' in game_data:
        info['categories'] = [cat.get('description', '') for cat in game_data['categories']]
    
    # Get review summary if available
    if 'reviews' in game_data:
        reviews = game_data['reviews']
        info['review_summary'] = reviews.get('summary', 'No reviews')
        info['review_score'] = reviews.get('review_score', 0)
        info['review_score_desc'] = reviews.get('review_score_desc', 'No reviews')
        info['total_reviews'] = reviews.get('total', 0)
        info['total_positive'] = reviews.get('total_positive', 0)
        info['total_negative'] = reviews.get('total_negative', 0)
    else:
        info['review_summary'] = 'No reviews available'
        info['review_score'] = 0
        info['review_score_desc'] = 'No reviews'
        info['total_reviews'] = 0
        info['total_positive'] = 0
        info['total_negative'] = 0
    
    return info

def validate_country_code(country_code):
    """Validate country code format (2 uppercase letters)."""
    if not country_code or len(country_code) != 2:
        return False
    return country_code.isalpha() and country_code.isupper()

def validate_language_code(language):
    """Validate language code format (2-5 lowercase letters/numbers)."""
    if not language or len(language) < 2 or len(language) > 5:
        return False
    return bool(re.match(r'^[a-z0-9]+$', language))

def validate_webhook_url(webhook_url):
    """Validate Discord webhook URL format."""
    if not webhook_url:
        return False
    try:
        parsed = urlparse(webhook_url)
        return (parsed.scheme in ['http', 'https'] and 
                ('discord.com' in parsed.netloc or 'discordapp.com' in parsed.netloc) and
                '/api/webhooks' in parsed.path)
    except Exception:
        return False

def validate_steam_link(steam_link):
    """Validate Steam store link format (/app/ or /bundle/)."""
    if not steam_link:
        return False
    try:
        parsed = urlparse(steam_link)
        if parsed.scheme not in ("http", "https") or "steampowered.com" not in parsed.netloc:
            return False
        path = parsed.path or ""
        return "/app/" in path or "/bundle/" in path
    except Exception:
        return False