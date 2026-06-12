import json
import os
import logging

SALE_REMINDER_FILE = "sale_reminder.json"

def load_sale_reminders():
    """Load last seen discount per store item."""
    if not os.path.exists(SALE_REMINDER_FILE):
        return {}
    try:
        with open(SALE_REMINDER_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing sale reminder JSON: {e}")
        try:
            os.rename(SALE_REMINDER_FILE, f"{SALE_REMINDER_FILE}.backup")
        except Exception:
            pass
        return {}
    except IOError as e:
        logging.error(f"Error reading sale reminder file: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error loading sale reminders: {e}")
        return {}

def get_remembered_discount(app_id):
    """Last saved discount percent, or None if this item was never recorded."""
    entry = load_sale_reminders().get(str(app_id))
    if not entry:
        return None
    value = entry.get("discount_percent")
    if value is None:
        return None
    return int(value)

def should_post_sale(app_id, discount_percent):
    """Post when on sale and we have no record yet, or the discount changed."""
    discount = int(discount_percent)
    if discount <= 0:
        return False
    remembered = get_remembered_discount(app_id)
    if remembered is None:
        return True
    return remembered != discount

def remember_discount_state(app_id, game_name, current_price, discount_percent):
    """Save the current discount so the next run can compare it."""
    try:
        sale_reminders = load_sale_reminders()
        sale_reminders[str(app_id)] = {
            "game_name": game_name,
            "current_price": current_price,
            "discount_percent": int(discount_percent),
        }
        with open(SALE_REMINDER_FILE, "w") as file:
            json.dump(sale_reminders, file, indent=4)
        logging.info(
            "Remembered %s: %s%% off (R$%.2f)",
            game_name,
            int(discount_percent),
            current_price,
        )
    except IOError as e:
        logging.error(f"Error saving sale reminder: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving sale reminder: {e}")

def save_sale_reminder(app_id, game_name, current_price, discount_percent):
    """Alias used by legacy menu paths."""
    remember_discount_state(app_id, game_name, current_price, discount_percent)

def is_sale_notified(app_id):
    """True when a positive discount was last remembered (legacy menu paths)."""
    remembered = get_remembered_discount(app_id)
    return remembered is not None and remembered > 0

def remove_expired_sale(app_id):
    """Set remembered discount to 0% (legacy menu paths)."""
    try:
        entry = load_sale_reminders().get(str(app_id))
        if not entry:
            return
        remember_discount_state(
            app_id,
            entry.get("game_name", ""),
            entry.get("current_price", 0),
            0,
        )
    except Exception as e:
        logging.error(f"Unexpected error clearing sale state: {e}")

# Backwards-compatible alias
should_notify_discount_change = should_post_sale
