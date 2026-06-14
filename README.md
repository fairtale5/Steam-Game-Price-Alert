# Steam Game Price Alert Bot

🎮 Never miss a Steam sale again! This bot monitors your wishlist games and instantly notifies you through Discord when prices drop. Perfect for gamers who want to grab their favorite titles at the best prices.

**This fork** ([fairtale5/Steam-Game-Price-Alert](https://github.com/fairtale5/Steam-Game-Price-Alert)) is maintained for [FastFox Racing](https://github.com/fairtale5/FastFox) — Discord **Fox-Promos** alerts on the game server VPS. Upstream: [AliAlboushama/Steam-Game-Price-Alert](https://github.com/AliAlboushama/Steam-Game-Price-Alert).

Python sources live in the **inner** folder `Steam-Game-Price-Alert/` (where `main.py` is). Clone the repo, then `cd Steam-Game-Price-Alert` before installing or running.

## Changes in this fork

Compared to upstream, this copy adds:

- **`run_check.py`** — one-shot watchlist scan for **cron** (read config, check prices, post to Discord, exit). No menu, no long-running loop.
- **Steam bundles** — watchlist links can be `/app/…` or `/bundle/…`. Bundles use Steam `ajaxresolvebundles` (`utils.py`), not the appdetails API alone.
- **Discord layout for Fox-Promos** — webhook `username` from `bot_name`; **role ping** in the plain `content` line (`<@&role_id>`); embed title `Discount: …`, description `R$… — N% off`, banner image, link to the store page.
- **Regional price formatting** — `format_money()` shows `R$` for Brazil (`BR` / `BRL`), plus `€` / `£` / `$` for other regions.
- **`discord_role_id` in `user_info.json`** — optional; when set, cron and scans ping that Discord role above the embed.
- **Smarter duplicate control** — `sale_reminder.json` stores the last discount **percent** per item. A new Discord post goes out when a sale starts or the discount **changes**, not on every hourly cron tick.
- **`test_discord.py`** — send one sample bundle notification (uses `mention_text` instead of a real role ping) to verify webhook layout on the VPS.

Interactive `main.py` (menu, add games, optional long-running scan) still works for setup and manual use.

## ✨ Features

### Core Features
- **Sale Monitoring**: Automatically checks game prices via Steam API hourly
- **Discord Notifications**: Sends rich embeds to your Discord channel when sales are detected
- **Price History Tracking**: Tracks price changes over time in SQLite database
- **Historical Low Detection**: Automatically detects and highlights "Lowest Price Ever!" deals
- **Multiple Scanning Modes**: 
  - Price target mode (notify when price drops below threshold)
  - Normal sale detection mode (notify for any discount)
- **Scan Multiple Games**: Track multiple game sales simultaneously

### Game Management
- **Add/Remove Games**: Manage your watchlist easily
- **View Current Prices**: Check all game prices at once without starting a scan
- **Detailed Game Info**: View comprehensive game information including:
  - Release date
  - Reviews and ratings (Steam reviews + Metacritic)
  - Genres and categories
  - Developers and publishers
  - Game description
  - Historical low prices

### User Experience
- **Input Validation**: Validates country codes, language codes, webhook URLs, and Steam links
- **Persistent Settings**: Saves user preferences (country, language, webhook, bot name/avatar)
- **Error Handling**: Robust error handling with logging throughout
- **Clean Interface**: Auto-refreshing display with ASCII art headers
- **Price Thresholds**: Set custom price targets for individual games

## Screenshots
![Main Page](https://files.catbox.moe/eggd5n.png)

![Scanning Game Sales UI](https://files.catbox.moe/8quot8.png)

## How It Works

1. **Game Addition**: Extracts `app_id` from Steam store links and fetches game details
2. **Price Monitoring**: Fetches current prices from Steam API using country/language settings
3. **Price History**: Automatically saves all price checks to SQLite database
4. **Sale Detection**: 
   - Compares current price with historical data
   - Checks against user-defined price targets (if configured)
   - Detects any discounts or price drops
5. **Historical Low**: Compares current price with all historical prices to identify record lows
6. **Notifications**: Sends rich Discord embeds with:
   - Game name, image, and store link
   - Current price and discount percentage
   - Historical low indicator (when applicable)
7. **Duplicate Prevention**: Tracks active sales to prevent spam notifications
8. **Data Persistence**: All data saved to database and JSON files for reliability

## Discord Notification Preview

Here's how the sale notifications appear in your Discord channel:

![Discord Notification Preview](https://files.catbox.moe/9eiuob.png)

**In this fork**, a typical Fox-Promos message looks like:

- **Username:** `bot_name` from config (e.g. `🎁 Fox-Promos`)
- **Content line:** role ping only — `<@&discord_role_id>` (nothing else in `content`)
- **Embed:** title `Discount: Game Name`, description `R$59.51 — 77% off`, large banner image, link to Steam app or bundle page

Upstream-style embeds (historical-low callouts, longer copy) may differ; this fork keeps the preview minimal for promo channels.

## Requirements

This project requires **Python 3.7+** and the following packages:

- `requests` (>=2.31.0)
- `pyfiglet` (>=1.0.2)

## Installation

1. Clone this fork and enter the inner app folder:
```bash
git clone https://github.com/fairtale5/Steam-Game-Price-Alert.git
cd Steam-Game-Price-Alert/Steam-Game-Price-Alert
```

2. Install required packages:
```bash
# Using pip
pip install -r requirements.txt

# Or install individually
pip install requests pyfiglet
```

3. Set up Discord webhook:
   - Open Discord server settings
   - Create webhook in desired channel
   - Copy webhook URL

4. Run the script:
```bash
python3 main.py
```

## Usage

### First Run Setup

When you first run the script, it will prompt you to enter:
- **Country code** (e.g., US, UK, DE) - Validated as 2-letter uppercase code
- **Language code** (e.g., en, es, fr) - Validated format
- **Discord webhook URL** - Validated Discord webhook format
- **Bot name** - Name displayed in Discord notifications
- **Bot avatar URL** - Optional image URL for bot avatar

These settings are saved in `user_info.json` for future use.

Optional fields used by this fork:

```json
{
    "country_code": "BR",
    "language": "en",
    "webhook_url": "https://discord.com/api/webhooks/...",
    "bot_name": "🎁 Fox-Promos",
    "bot_avatar": "",
    "discord_role_id": "1506941752223993857"
}
```

| Field | Purpose |
|--------|---------|
| `discord_role_id` | Discord role to ping in the line above the embed (`<@&…>`) |
| `sale_content_template` | Unused by current Fox-Promos layout (embed-only body); kept for compatibility |

### Headless mode (cron, recommended for servers)

After setup and adding games with `main.py` (menu **2**), run a single check with:

```bash
python3 run_check.py
```

Example hourly cron on Linux:

```cron
0 * * * * cd /path/to/Steam-Game-Price-Alert && ./venv/bin/python3 run_check.py >> cron.log 2>&1
```

`run_check.py` reads `user_info.json`, scans every game in `saved_games.db`, posts to Discord when `should_post_sale()` is true, updates `sale_reminder.json`, then exits.

Test webhook layout without pinging a real role:

```bash
python3 test_discord.py
```

To force another Discord post while the same sale is still active, remove that product from `sale_reminder.json` (or delete the file).

### Main Menu Options

1. **Scan for sales** - Monitor a single game for price drops
2. **Add a new game** - Add games to your watchlist using Steam store links
3. **Scan multiple games** - Monitor multiple games simultaneously
4. **Remove a game** - Remove games from your watchlist
5. **Set price threshold** - Set custom price targets for games
6. **View current prices** - Check all game prices at once (NEW!)
7. **View detailed game info** - See comprehensive game information (NEW!)

### Adding Games

You can add games by providing a Steam store link:
- App example: `https://store.steampowered.com/app/12345/GameName/`
- Bundle example: `https://store.steampowered.com/bundle/6998/Assetto_Corsa_Ultimate_Edition/`
- The script validates the link format and extracts the store id automatically

### Price Monitoring

The bot offers two scanning modes:

1. **Price Target Mode**: Notifies you when a game's price drops below your set threshold
2. **Normal Sale Detection**: Notifies you whenever any discount is detected

### Historical Low Tracking

- The bot automatically tracks price history for all monitored games
- When a price matches or beats the historical low, you'll see:
  - ⭐ **LOWEST PRICE EVER!** ⭐ indicator in console
  - Special highlight in Discord notifications
  - Historical low price displayed in game info views

### Operation

- The script checks for sales hourly (configurable)
- Sends Discord notifications when sales are detected
- Prevents duplicate notifications for the same sale
- Automatically tracks price history in the database

## Configuration

### Discord Webhook Setup

1. Go to Discord server settings
2. Navigate to Integrations > Webhooks
3. Create new webhook
4. Copy URL for script configuration

### Bot Customization

You can customize:
- Bot name
- Avatar image (via URL)

## File Structure

```
Steam-Game-Price-Alert/
├── main.py              # Interactive menu (setup, add games, optional scan loop)
├── run_check.py         # One-shot check for cron (Fox-Promos production path)
├── test_discord.py      # Send one test webhook message
├── scanner.py           # Scanning functions for single/multiple games
├── discord.py           # Discord webhook notification handler
├── saved_games.py       # Database operations for games and price history
├── saved_info.py        # User settings management (incl. discord_role_id)
├── stop_spam.py         # Remembered discount per item (when to post again)
├── utils.py             # Steam API (apps + bundles), validation, formatting
├── requirements.txt     # Python dependencies
├── saved_games.db       # SQLite database (created automatically)
├── user_info.json       # User configuration (created automatically, do not commit)
└── sale_reminder.json   # Last discount per item (created automatically)
```

## FAQ

**Q: How do I add multiple games?**  
A: Use option 2 in the main menu to add games. You can add multiple games in sequence, or use option 3 to scan multiple games at once.

**Q: Can I change how often prices are checked?**  
A: For servers, use cron with `run_check.py` (e.g. every hour). For the interactive loop in `main.py`, modify `SLEEP_TIME` (default: 3600 seconds = 1 hour).

**Q: Why didn't cron post again on the next hour?**  
A: This fork only posts when the discount is new or **changed**. Same sale, same percent → skipped. Clear that item in `sale_reminder.json` to post again.

**Q: Can I track Steam bundles, not just single games?**  
A: Yes. Add a `/bundle/…` URL in menu **2**. Pricing comes from Steam `ajaxresolvebundles`.

**Q: Not receiving Discord notifications?**  
A: Verify your webhook URL is correct, the webhook is enabled in your Discord server, and check the `debug.log` file for error messages.

**Q: What is the "Historical Low" feature?**  
A: The bot tracks all price changes over time. When a price matches or beats the lowest price ever recorded, it shows a special indicator. This helps you identify the best deals!

**Q: Can I view game information without scanning?**  
A: Yes! Use option 7 "View detailed game info" to see comprehensive information about any game in your watchlist, including reviews, tags, and release dates.

**Q: How does price history tracking work?**  
A: Every time the bot checks a game's price (during scans or when viewing current prices), it saves the price to the database. This creates a historical record that enables the "Lowest Price Ever" feature.

**Q: Will the bot work if I restart my computer?**  
A: The bot saves all data (games, settings, price history) to files and database. You can restart anytime and continue where you left off. However, you'll need to manually restart the scanning process.

## Contributing

Upstream contributions: [AliAlboushama/Steam-Game-Price-Alert](https://github.com/AliAlboushama/Steam-Game-Price-Alert).

For this fork (Fox-Promos / FastFox): open an issue or PR on [fairtale5/Steam-Game-Price-Alert](https://github.com/fairtale5/Steam-Game-Price-Alert).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- Open an issue on GitHub
