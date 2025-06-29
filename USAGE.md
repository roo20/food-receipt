# Usage Guide for Telegram Food Receipt Bot

## Bot Commands

### Start the Bot
Send `/start` to your bot to begin. The bot will confirm it's working and ready to generate receipts.

### Generate Receipts
Send a message in the format: `food [number]`

Examples:
- `food 5` - Generate receipts for the last 5 working days
- `Food 3` - Generate receipts for the last 3 working days  
- `FOOD 1` - Generate a receipt for the last working day

**Note:** The bot only considers working days (Monday through Friday). Weekends are automatically skipped.

## What the Bot Does

1. **Calculates Working Days**: When you request receipts for N days, the bot counts backwards from today, including only Monday-Friday.

2. **Generates Realistic Receipts**: Each receipt includes:
   - Random food items from a predefined list
   - Realistic prices and tax calculations
   - Random transaction times between 8 AM and 6 PM
   - Unique transaction IDs and receipt numbers
   - Proper REWE store format

3. **Creates Images**: Each receipt is converted to a PNG image that looks like a real receipt.

4. **Sends Separately**: Each working day gets its own image sent to the chat with a caption showing the day and date.

## Example Workflow

1. You send: `food 3`
2. Bot calculates the last 3 working days (e.g., Wed, Thu, Fri)
3. Bot generates 3 different receipts with random items and prices
4. Bot sends 3 separate PNG images to your chat
5. Each image is captioned with "Receipt 1/3 - Wednesday, 26.06.2025" etc.

## Sample Items

The bot randomly selects from these items:
- **Produce (7% tax)**: Gurke, Bananen, Apfel, Presseerzeugnis
- **Dairy (7% tax)**: Milch, Butter, Joghurt  
- **Other Food (7% tax)**: Kaffee Crema
- **Packaged Foods (19% tax)**: Vollkornbrot, Salami, Käse, Energy Drink, Wasser

## Receipt Details

Each receipt includes:
- **Store Info**: REWE Ballindamm 40, Hamburg
- **Items**: Random selection totaling at least 7 EUR
- **Payment**: Mastercard contactless payment
- **Timestamps**: Realistic transaction and receipt times
- **Tax Breakdown**: Proper German VAT calculation (7% and 19%)
- **Transaction IDs**: Beleg-Nr, Trace-Nr, Bon-Nr, etc.

## Limitations

- **Working Days Only**: Weekends are never included in the count
- **Single User**: Only responds to the configured user ID
- **Maximum Days**: Limited to 30 days back to prevent spam
- **German Format**: Receipts are in German format (REWE store)

## Troubleshooting

### "Not authorized" message
- Check that ALLOWED_USER_ID in config.py matches your Telegram user ID
- Get your user ID from @userinfobot on Telegram

### Bot doesn't respond
- Verify BOT_TOKEN is correct in config.py
- Make sure the bot is running (check terminal for errors)
- Try sending `/start` first

### Invalid format message
- Make sure you're sending `food [number]` format
- The word "food" can be in any case (food, Food, FOOD)
- The number must be between 1 and 30

### Receipt images look wrong
- This is a limitation of the pure Python image generation
- Try the alternative version (main.py) with wkhtmltopdf for better formatting

## Privacy & Security

- The bot only responds to one specific user ID
- No data is stored or logged permanently
- Each receipt is generated fresh with random data
- Bot token should be kept secret and not shared
