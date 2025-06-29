import os
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import tempfile
import base64
from io import BytesIO

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from jinja2 import Template
import imgkit
from PIL import Image

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FoodReceiptGenerator:
    def __init__(self):
        self.possible_items = [
            {'name': 'GURKE', 'price': 0.79, 'tax_rate': 7},
            {'name': 'BANANEN', 'price': 1.29, 'tax_rate': 7},
            {'name': 'REWE Bio Apfel', 'price': 2.49, 'tax_rate': 7},
            {'name': 'Milch 1,5%', 'price': 1.19, 'tax_rate': 7},
            {'name': 'Butter', 'price': 2.29, 'tax_rate': 7},
            {'name': 'Brot', 'price': 2.00, 'tax_rate': 7},
            {'name': 'Joghurt', 'price': 0.59, 'tax_rate': 7},
            {'name': 'Vollkornbrot', 'price': 1.89, 'tax_rate': 19},
            {'name': 'Salami', 'price': 1.99, 'tax_rate': 19},
            {'name': 'Käse', 'price': 2.99, 'tax_rate': 19},
            {'name': 'Energy Drink', 'price': 1.49, 'tax_rate': 19},
            {'name': 'Kaffee Crema', 'price': 0.99, 'tax_rate': 7},
            {'name': 'Wasser', 'price': 5.99, 'tax_rate': 19},
        ]
        
        self.html_template = """
<html>
<head>
  <style>
    body { background-color: #FFF; margin: 0; padding: 0; }
    #receipt { font-family: 'Courier New', Courier, monospace; font-size: 16px; line-height: 1.4; color: #000; background-color: #FFF; padding: 25px; width: 450px; }
    .logo { width: 200px; margin: 0 auto 20px auto; display: block; }
    .center { text-align: center; }
    pre { font-family: 'Courier New', Courier, monospace; font-size: 16px; margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="receipt">
    <img class="logo" src="https://raw.githubusercontent.com/roo20/n8n/refs/heads/main/rewe_logo_icon_248646.svg" alt="REWE Logo" />
    <pre class="center">
REWE
Ballindamm 40
20095 Hamburg
Tel.: 040-27169854
UID Nr.: DE812706034
    </pre>
    <br>
    <pre>
{{ items_html }}
========================================
SUMME                              EUR {{ total | rjust(7) }}
========================================
Geg. Mastercard                    EUR {{ total | rjust(7) }}

           * * Kundenbeleg * *

Datum:      {{ date }}
Uhrzeit:    {{ time1 }}:{{ seconds1 }} Uhr
Beleg-Nr.   {{ beleg_nr }}
Trace-Nr.   {{ trace_nr }}

            Bezahlung
            Kontaktlos
            DEBIT MASTERCARD
            ############{{ last4_digits }} 0001
Nr.
VU-Nr.                             {{ vu_nr }}
Terminal-ID                        {{ terminal_id }}
Pos-Info                           00 073 00
AS-Zeit {{ date[:5] }}.                       {{ time1 }} Uhr
AS-Proc-Code = 00 075 00
Capt.-Ref. = 0000
00 GENEHMIGT
Betrag EUR                         {{ total | rjust(7) }}

            Zahlung erfolgt

{{ tax_table_html }}

{{ date }}         {{ time2 }}      Bon-Nr.:{{ bon_nr }}
Markt:0112             Kasse:{{ kasse_nr }}    Bed.:{{ bed_nr }}
****************************************
Jetzt mit PAYBACK Punkten bezahlen!
Einfach REWE Guthaben am Service-Punkt
                aufladen.

  Für die mit * gekennzeichneten Produkte
   erhalten Sie leider keine Rabatte
           oder PAYBACK Punkte.
****************************************

          REWE Markt GmbH
    Vielen Dank für Ihren Einkauf
Bitte beachten Sie unsere kunden-
freundlichen Öffnungszeiten am Markt

         Sie haben Fragen?
     Antworten gibt es unter
           www.rewe.de
    </pre>
  </div>
</body>
</html>
"""

    def get_working_days(self, days_back: int) -> List[datetime]:
        """Get list of working days going back from today"""
        working_days = []
        current_date = datetime.now()
        days_found = 0
        
        while days_found < days_back:
            # Monday = 0, Sunday = 6 (so 0-4 are weekdays)
            if current_date.weekday() < 5:  # Monday to Friday
                working_days.append(current_date)
                days_found += 1
            current_date -= timedelta(days=1)
        
        return list(reversed(working_days))  # Return in chronological order

    def generate_random_shopping_cart(self) -> List[Dict[str, Any]]:
        """Generate a random shopping cart with total over 7 EUR"""
        shopping_cart = []
        current_total = 0
        
        while current_total < 7:
            random_item = random.choice(self.possible_items)
            shopping_cart.append(random_item.copy())
            current_total += random_item['price']
        
        return shopping_cart

    def calculate_tax_summary(self, shopping_cart: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
        """Calculate tax breakdown for the shopping cart"""
        tax_summary = {
            7: {'net': 0, 'tax': 0, 'brutto': 0},
            19: {'net': 0, 'tax': 0, 'brutto': 0}
        }
        
        for item in shopping_cart:
            rate = item['tax_rate']
            brutto = item['price']
            net = brutto / (1 + rate / 100)
            tax = brutto - net
            
            tax_summary[rate]['net'] += net
            tax_summary[rate]['tax'] += tax
            tax_summary[rate]['brutto'] += brutto
        
        return tax_summary

    def format_items_html(self, shopping_cart: List[Dict[str, Any]]) -> str:
        """Format shopping cart items for HTML display"""
        items_html = []
        for item in shopping_cart:
            tax_code = 'B' if item['tax_rate'] == 7 else 'A'
            name_padded = item['name'].ljust(28)
            price_padded = f"{item['price']:.2f}".rjust(7)
            items_html.append(f"{name_padded}EUR {price_padded} {tax_code} *")
        
        return '\n'.join(items_html)

    def format_tax_table_html(self, tax_summary: Dict[int, Dict[str, float]], total: float) -> str:
        """Format tax summary table for HTML display"""
        lines = ['Steuer %      Netto      Steuer      Brutto']
        
        if tax_summary[7]['brutto'] > 0:
            lines.append(f"B=  7,0%     {tax_summary[7]['net']:7.2f}     {tax_summary[7]['tax']:7.2f}     {tax_summary[7]['brutto']:7.2f}")
        
        if tax_summary[19]['brutto'] > 0:
            lines.append(f"A= 19,0%     {tax_summary[19]['net']:7.2f}     {tax_summary[19]['tax']:7.2f}     {tax_summary[19]['brutto']:7.2f}")
        
        gesamt_netto = tax_summary[7]['net'] + tax_summary[19]['net']
        gesamt_tax = tax_summary[7]['tax'] + tax_summary[19]['tax']
        lines.append(f"Gesamtbetrag  {gesamt_netto:7.2f}     {gesamt_tax:7.2f}     {total:7.2f}")
        
        return '\n'.join(lines)

    def generate_receipt_data(self, target_date: datetime) -> Dict[str, Any]:
        """Generate all data needed for a receipt for a specific date"""
        shopping_cart = self.generate_random_shopping_cart()
        total = sum(item['price'] for item in shopping_cart)
        tax_summary = self.calculate_tax_summary(shopping_cart)
        
        # Generate random times between 8 AM and 6 PM
        receipt_hour = random.randint(8, 17)
        receipt_minute = random.randint(0, 59)
        receipt_second = random.randint(0, 59)
        
        receipt_time = target_date.replace(hour=receipt_hour, minute=receipt_minute, second=receipt_second)
        transaction_time = receipt_time - timedelta(minutes=random.randint(3, 5))
        
        return {
            'items': shopping_cart,
            'total': f"{total:.2f}",
            'tax_summary': tax_summary,
            'date': target_date.strftime('%d.%m.%Y'),
            'time1': transaction_time.strftime('%H:%M'),
            'seconds1': transaction_time.strftime('%S'),
            'time2': receipt_time.strftime('%H:%M'),
            'beleg_nr': f"{random.randint(1000, 9999):04d}",
            'trace_nr': f"{random.randint(100000, 999999):06d}",
            'bon_nr': str(random.randint(5000, 9999)),
            'bed_nr': f"{random.randint(100000, 999999):06d}",
            'kasse_nr': str(random.randint(10, 99)),
            'vu_nr': f"{random.randint(100000000, 999999999):09d}",
            'terminal_id': f"{random.randint(10000000, 99999999):08d}",
            'last4_digits': f"{random.randint(1000, 9999):04d}",
        }

    def generate_receipt_html(self, target_date: datetime) -> str:
        """Generate HTML for a receipt for a specific date"""
        data = self.generate_receipt_data(target_date)
        
        # Format items and tax table
        data['items_html'] = self.format_items_html(data['items'])
        data['tax_table_html'] = self.format_tax_table_html(data['tax_summary'], float(data['total']))
        
        template = Template(self.html_template)
        return template.render(**data)

    def html_to_png(self, html_content: str) -> bytes:
        """Convert HTML content to PNG bytes"""
        try:
            # Configure imgkit options
            options = {
                'width': 500,
                'height': 800,
                'crop-h': 800,
                'crop-w': 500,
                'crop-x': 0,
                'crop-y': 0,
                'encoding': 'UTF-8',
                'format': 'png'
            }
            
            # Convert HTML to PNG
            png_data = imgkit.from_string(html_content, False, options=options)
            return png_data
            
        except Exception as e:
            logger.error(f"Error converting HTML to PNG: {e}")
            # Fallback: create a simple text image
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (500, 800), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Receipt generation failed: {str(e)}", fill='black')
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()


class TelegramBot:
    def __init__(self, token: str, allowed_user_id: int):
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.receipt_generator = FoodReceiptGenerator()
        self.application = Application.builder().token(token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command"""
        if update.effective_user.id != self.allowed_user_id:
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        await update.message.reply_text(
            "Welcome! Send me a message like 'food 5' or 'Food 3' to generate receipts for the last N working days."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages"""
        if update.effective_user.id != self.allowed_user_id:
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        message_text = update.message.text.strip().lower()
        
        # Parse the message (e.g., "food 5" or "Food 3")
        if message_text.startswith('food '):
            try:
                days_str = message_text.split('food ')[1].strip()
                days_back = int(days_str)
                
                if days_back <= 0 or days_back > 30:
                    await update.message.reply_text("Please specify a number between 1 and 30.")
                    return
                
                await update.message.reply_text(f"Generating receipts for the last {days_back} working days...")
                
                # Get working days
                working_days = self.receipt_generator.get_working_days(days_back)
                
                # Generate and send receipts
                for i, day in enumerate(working_days, 1):
                    try:
                        # Generate HTML receipt
                        html_content = self.receipt_generator.generate_receipt_html(day)
                        
                        # Convert to PNG
                        png_data = self.receipt_generator.html_to_png(html_content)
                        
                        # Send the image
                        caption = f"Receipt {i}/{len(working_days)} - {day.strftime('%A, %d.%m.%Y')}"
                        await update.message.reply_photo(
                            photo=BytesIO(png_data),
                            caption=caption
                        )
                        
                        # Small delay between messages
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error generating receipt for {day}: {e}")
                        await update.message.reply_text(f"Error generating receipt for {day.strftime('%d.%m.%Y')}: {str(e)}")
                
                await update.message.reply_text("All receipts have been generated!")
                
            except ValueError:
                await update.message.reply_text("Invalid format. Please use 'food [number]', for example: 'food 5'")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await update.message.reply_text(f"An error occurred: {str(e)}")
        else:
            await update.message.reply_text("Please send a message like 'food 5' to generate receipts.")

    def run(self):
        """Start the bot"""
        logger.info("Starting bot...")
        self.application.run_polling()


if __name__ == "__main__":
    # Configuration - Replace with your actual values
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get this from @BotFather on Telegram
    ALLOWED_USER_ID = 123456789  # Replace with your Telegram user ID
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your BOT_TOKEN in the script!")
        print("1. Message @BotFather on Telegram to create a new bot")
        print("2. Replace BOT_TOKEN with the token you receive")
        print("3. Replace ALLOWED_USER_ID with your Telegram user ID")
        exit(1)
    
    bot = TelegramBot(BOT_TOKEN, ALLOWED_USER_ID)
    bot.run()
