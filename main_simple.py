import os
import platform
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
from io import BytesIO

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_handlers = [logging.StreamHandler()]

# Add file handler if logs directory exists or can be created
try:
    os.makedirs('logs', exist_ok=True)
    log_handlers.append(logging.FileHandler('logs/bot.log'))
except (OSError, PermissionError):
    pass  # Continue with just console logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, log_level, logging.INFO),
    handlers=log_handlers
)

# Disable httpx verbose logging
logging.getLogger('httpx').setLevel(logging.WARNING)

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

    def get_working_days(self, days_back: int) -> List[datetime]:
        """Get list of working days going back from today"""
        working_days = []
        current_date = datetime.now()
        days_found = 0
        
        while days_found < days_back:
            # Monday = 0, Sunday = 6 (so 0-4 are weekdays)
            if current_date.weekday() < 7:  # Monday to Friday
                working_days.append(current_date)
                days_found += 1
            current_date -= timedelta(days=1)
        
        return list(reversed(working_days))  # Return in chronological order

    def generate_random_shopping_cart(self) -> List[Dict[str, Any]]:
        """Generate a random shopping cart with total over 7 EUR"""
        shopping_cart = []
        current_total = 0
        
        # Keep track of used items to avoid duplicates
        available_items = self.possible_items.copy()
        
        while current_total < 7 and available_items:
            random_item = random.choice(available_items)
            shopping_cart.append(random_item.copy())
            current_total += random_item['price']
            # Remove the selected item from available items
            available_items.remove(random_item)
            
        # If we run out of unique items but haven't reached minimum total,
        # just return what we have so far
        
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
            'total': total,
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

    def create_svg_logo(self, width: int, height: int = 40) -> Image.Image:
        """Create REWE logo from SVG data using PIL - black and white for thermal receipt style"""
        try:
            # Create a high-quality logo using PIL based on the SVG design
            logo_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            logo_draw = ImageDraw.Draw(logo_img)
            
            # Use FontManager to get the best available font
            logo_font = FontManager.get_logo_font(int(height * 0.6))
            
            # Draw REWE text in authentic style
            text = "REWE"
            text_bbox = logo_draw.textbbox((0, 0), text, font=logo_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Create a clean black logo on white background (thermal receipt style)
            # Draw the text in black for thermal receipt authenticity
            logo_draw.text((x, y), text, fill=(0, 0, 0), font=logo_font)
            
            return logo_img
            
        except Exception as e:
            logger.warning(f"Error creating SVG-style logo: {e}, using text logo")
            return None

    def create_text_logo(self, width: int) -> Image.Image:
        """Create a simple text-based REWE logo - clean black text on white for thermal receipt style"""
        logo_height = 35  # Optimized height for better proportions
        logo_img = Image.new('RGBA', (width, logo_height), (255, 255, 255, 0))
        logo_draw = ImageDraw.Draw(logo_img)
        
        # Use FontManager to get the best available font
        logo_font = FontManager.get_logo_font(22)
        
        # Draw REWE text - simple black text for thermal receipt authenticity
        text = "REWE"
        text_bbox = logo_draw.textbbox((0, 0), text, font=logo_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (logo_height - text_height) // 2
        
        # Draw simple black text (like thermal receipt printing)
        logo_draw.text((x, y), text, fill=(0, 0, 0), font=logo_font)
        
        return logo_img

    def download_logo(self, logo_url: str) -> Image.Image:
        """Download and return the REWE logo image"""
        try:
            response = requests.get(logo_url, timeout=10)
            response.raise_for_status()
            
            # Handle SVG files by converting to PNG first
            if logo_url.endswith('.svg'):
                try:
                    # Try to use cairosvg if available
                    import cairosvg
                    png_data = cairosvg.svg2png(bytestring=response.content, output_width=200)
                    logo_img = Image.open(BytesIO(png_data))
                except ImportError:
                    logger.info("cairosvg not available, using text logo")
                    return None
                except Exception as e:
                    logger.warning(f"Error converting SVG: {e}, using text logo")
                    return None
            else:
                logo_img = Image.open(BytesIO(response.content))
            
            # Convert to RGBA if not already
            if logo_img.mode != 'RGBA':
                logo_img = logo_img.convert('RGBA')
            
            return logo_img
        except Exception as e:
            logger.warning(f"Could not download logo: {e}, using text logo")
            return None

    def create_receipt_image(self, target_date: datetime) -> bytes:
        """Create a receipt image using PIL - taller and narrower like real receipts with high DPI"""
        data = self.generate_receipt_data(target_date)
        
        # Image settings - optimized resolution for Docker compatibility
        dpi_scale = 4  # Reduced from 7 to 4 for better Docker performance
        width = 300 * dpi_scale  # 1200px final width
        height = 900 * dpi_scale  # 3600px final height
        background_color = 'white'
        text_color = 'black'
        
        # Create image with high resolution
        img = Image.new('RGB', (width, height), color=background_color)
        draw = ImageDraw.Draw(img)
        
        # Scale font sizes accordingly
        base_font_size = 10 * dpi_scale
        bold_font_size = 12 * dpi_scale
        
        # Try to use a monospace font, fallback to default if not available
        font = FontManager.get_monospace_font(base_font_size)
        
        # Try to get a bold font for headers
        bold_font = FontManager.get_bold_font(bold_font_size)
        
        # Current y position for drawing text (scaled)
        y = 10 * dpi_scale
        line_height = 12 * dpi_scale
        
        def draw_text(text, x=5*dpi_scale, center=False, bold=False):
            nonlocal y
            current_font = bold_font if bold else font
            if center:
                text_width = draw.textlength(text, font=current_font)
                x = (width - text_width) // 2
            draw.text((x, y), text, fill=text_color, font=current_font)
            y += line_height
        
        def draw_separator(height=3):
            nonlocal y
            y += height * dpi_scale
        
        def draw_line(char="=", length=40):
            nonlocal y
            line_text = char * length
            text_width = draw.textlength(line_text, font=font)
            x = (width - text_width) // 2
            draw.text((x, y), line_text, fill=text_color, font=font)
            y += line_height
        
        # Add REWE logo at the top - prioritize vector-style logo
        logo_width = (width - 40*dpi_scale) // dpi_scale
        logo_height = 35  # Optimized height for better proportions
        
        # Try vector-style logo first (most professional)
        vector_logo = self.create_rewe_vector_logo(logo_width, logo_height)
        if vector_logo:
            # Scale up the vector logo
            logo_scaled = vector_logo.resize(
                (vector_logo.width * dpi_scale, vector_logo.height * dpi_scale), 
                Image.Resampling.LANCZOS
            )
            logo_x = (width - logo_scaled.width) // 2  # Center the logo
            # Paste with proper alpha handling
            if logo_scaled.mode == 'RGBA':
                img.paste(logo_scaled, (logo_x, y), logo_scaled)
            else:
                img.paste(logo_scaled, (logo_x, y))
            y += logo_scaled.height + 6*dpi_scale  # Optimized padding
        else:
            # Try enhanced logo as fallback
            svg_logo = self.create_svg_logo(logo_width, logo_height)
            if svg_logo:
                # Scale up the enhanced logo
                logo_scaled = svg_logo.resize(
                    (svg_logo.width * dpi_scale, svg_logo.height * dpi_scale), 
                    Image.Resampling.LANCZOS
                )
                logo_x = (width - logo_scaled.width) // 2  # Center the logo
                # Paste with proper alpha handling
                if logo_scaled.mode == 'RGBA':
                    img.paste(logo_scaled, (logo_x, y), logo_scaled)
                else:
                    img.paste(logo_scaled, (logo_x, y))
                y += logo_scaled.height + 6*dpi_scale  # Optimized padding
            else:
                # Final fallback to simple text logo
                text_logo = self.create_text_logo(logo_width)
                logo_scaled = text_logo.resize(
                    (text_logo.width * dpi_scale, text_logo.height * dpi_scale), 
                    Image.Resampling.LANCZOS
                )
                logo_x = (width - logo_scaled.width) // 2  # Center the logo
                # Paste with proper alpha handling
                if logo_scaled.mode == 'RGBA':
                    img.paste(logo_scaled, (logo_x, y), logo_scaled)
                else:
                    img.paste(logo_scaled, (logo_x, y))
                y += logo_scaled.height + 6*dpi_scale  # Optimized padding
        
        draw_separator(5)
        
        # Store header (without REWE since we have the logo)
        draw_text("Reichenhainer Str. 55", center=True)
        draw_text("09126 Chemnitz", center=True)
        draw_text("Tel.: 0371-24088670", center=True)
        draw_text("UID Nr.: DE812706034", center=True)
        draw_separator(10)
        
        # Items section - reduced spacing for tighter look
        for item in data['items']:
            tax_code = 'B' if item['tax_rate'] == 7 else 'A'
            name = item['name'][:22]  # Allow slightly longer names in narrow format
            price_str = f"EUR {item['price']:6.2f} {tax_code} *"
            
            # Left align item name, right align price - much tighter spacing
            draw.text((8*dpi_scale, y), name, fill=text_color, font=font)
            price_width = draw.textlength(price_str, font=font)
            draw.text((width - price_width - 7*dpi_scale-100, y), price_str, fill=text_color, font=font)
            y += int(line_height * 0.9)  # Reduced line height for tighter spacing
        
        # Separator line
        draw_line("=", 38)
        
        # Total section
        
        total_str = f" SUMME                           EUR {data['total']:6.2f}"
        draw_text(total_str, x=5*dpi_scale)
        draw_line("=", 38)
        payment_str = f" Geg. Mastercard                 EUR {data['total']:6.2f}"
        draw_text(payment_str, x=5*dpi_scale)
        draw_separator(10)
        
        # Customer receipt section
        draw_text("* * Kundenbeleg * *", center=True, bold=True)
        draw_separator(8)
        
        draw_text(f"Datum:      {data['date']}", x=5*dpi_scale)
        draw_text(f"Uhrzeit:    {data['time1']}:{data['seconds1']} Uhr", x=5*dpi_scale)
        draw_text(f"Beleg-Nr.   {data['beleg_nr']}", x=5*dpi_scale)
        draw_text(f"Trace-Nr.   {data['trace_nr']}", x=5*dpi_scale)
        draw_separator(8)
        
        # Payment info
        draw_text("Bezahlung", center=True)
        draw_text("Kontaktlos", center=True)
        draw_text("DEBIT MASTERCARD", center=True)
        draw_text(f"############{data['last4_digits']} 0001", center=True)
        draw_text("Nr.", x=5*dpi_scale)
        draw_text(f"VU-Nr.                   {data['vu_nr']}", x=5*dpi_scale)
        draw_text(f"Terminal-ID              {data['terminal_id']}", x=5*dpi_scale)
        draw_text("Pos-Info                 00 073 00", x=5*dpi_scale)
        draw_text(f"AS-Zeit {data['date'][:5]}.             {data['time1']} Uhr", x=5*dpi_scale)
        draw_text("AS-Proc-Code = 00 075 00", x=5*dpi_scale)
        draw_text("Capt.-Ref. = 0000", x=5*dpi_scale)
        draw_text("00 GENEHMIGT", x=5*dpi_scale)
        draw_text(f"Betrag EUR               {data['total']:6.2f}", x=5*dpi_scale)
        draw_separator(8)
        
        draw_text("Zahlung erfolgt", center=True)
        draw_separator(8)
        
        # Tax summary
        draw_text("Steuer %  Netto  Steuer  Brutto", x=5*dpi_scale, bold=True)
        
        if data['tax_summary'][7]['brutto'] > 0:
            tax_7 = data['tax_summary'][7]
            draw_text(f"B=  7,0%  {tax_7['net']:5.2f}  {tax_7['tax']:5.2f}  {tax_7['brutto']:5.2f}", x=5*dpi_scale)
        
        if data['tax_summary'][19]['brutto'] > 0:
            tax_19 = data['tax_summary'][19]
            draw_text(f"A= 19,0%  {tax_19['net']:5.2f}  {tax_19['tax']:5.2f}  {tax_19['brutto']:5.2f}", x=5*dpi_scale)
        
        gesamt_netto = data['tax_summary'][7]['net'] + data['tax_summary'][19]['net']
        gesamt_tax = data['tax_summary'][7]['tax'] + data['tax_summary'][19]['tax']
        draw_text(f"Gesamtbetrag {gesamt_netto:5.2f}  {gesamt_tax:5.2f}  {data['total']:5.2f}", x=5*dpi_scale)
        draw_separator(10)
        
        # Footer with date and transaction details
        footer_line1 = f"{data['date']}     {data['time2']}  Bon-Nr.:{data['bon_nr']}"
        draw_text(footer_line1, x=5*dpi_scale)
        footer_line2 = f"Markt:0112         Kasse:{data['kasse_nr']}  Bed.:{data['bed_nr']}"
        draw_text(footer_line2, x=5*dpi_scale)
        
        # Stars separator
        draw_line("*", 38)
        
        # PAYBACK section
        draw_text("Jetzt mit PAYBACK Punkten bezahlen!", x=5*dpi_scale)
        draw_text("Einfach REWE Guthaben am Service-Punkt", x=5*dpi_scale)
        draw_text("aufladen.", center=True)
        draw_separator(5)
        
        draw_text("Für die mit * gekennzeichneten Produkte", x=5*dpi_scale)
        draw_text("erhalten Sie leider keine Rabatte", x=5*dpi_scale)
        draw_text("oder PAYBACK Punkte.", center=True)
        
        # Stars separator
        draw_line("*", 38)
        draw_separator(5)
        
        # Final footer
        draw_text("REWE Markt GmbH", center=True, bold=True)
        draw_text("Vielen Dank für Ihren Einkauf", center=True)
        draw_text("Bitte beachten Sie unsere kunden-", x=5*dpi_scale)
        draw_text("freundlichen Öffnungszeiten am Markt", x=5*dpi_scale)
        draw_separator(8)
        draw_text("Sie haben Fragen?", center=True)
        draw_text("Antworten gibt es unter", center=True)
        draw_text("www.rewe.de", center=True, bold=True)
        
        # Convert to high-quality PNG
        buffer = BytesIO()
        # Scale down while maintaining high quality
        final_img = img.resize((width // dpi_scale, height // dpi_scale), Image.Resampling.LANCZOS)
        final_img.save(buffer, format='PNG', optimize=True, dpi=(300, 300))
        return buffer.getvalue()

    def create_rewe_vector_logo(self, width: int, height: int = 35) -> Image.Image:
        """Create a proper REWE vector-style logo based on the official design"""
        try:
            logo_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            logo_draw = ImageDraw.Draw(logo_img)
            
            # Use FontManager to get the best available font
            logo_font = FontManager.get_logo_font(int(height * 0.65))
            
            # Calculate text dimensions
            text = "REWE"
            text_bbox = logo_draw.textbbox((0, 0), text, font=logo_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw the REWE logo in pure black for thermal receipt style
            # This mimics how corporate logos appear on thermal receipts
            logo_draw.text((x, y), text, fill=(0, 0, 0), font=logo_font)
            
            # Add a subtle underline to make it look more official
            underline_y = y + text_height + 2
            logo_draw.line([(x, underline_y), (x + text_width, underline_y)], 
                          fill=(0, 0, 0), width=1)
            
            return logo_img
            
        except Exception as e:
            logger.warning(f"Error creating vector-style logo: {e}")
            return None

class FontManager:
    """Manages font selection across different platforms"""
    
    @staticmethod
    def get_monospace_font(size: int) -> ImageFont.FreeTypeFont:
        """Get the best available monospace font for the platform"""
        # Define font fallback order for different platforms
        if platform.system() == "Windows":
            fonts = [
                "consola.ttf",      # Consolas (Windows)
                "courier.ttf",      # Courier New (Windows)
                "cour.ttf",         # Courier (Windows)
            ]
        else:  # Linux/Docker
            fonts = [
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/system/fonts/DroidSansMono.ttf",  # Android fallback
                "DejaVuSansMono.ttf",
                "LiberationMono-Regular.ttf",
                "FreeMono.ttf",
            ]
        
        logger.info(f"Trying to load monospace font with size {size} on {platform.system()}")
        
        for font_path in fonts:
            try:
                font = ImageFont.truetype(font_path, size)
                logger.info(f"Successfully loaded font: {font_path}")
                return font
            except (OSError, IOError) as e:
                logger.debug(f"Failed to load font {font_path}: {e}")
                continue
        
        # Ultimate fallback
        logger.warning("Using default font fallback")
        return ImageFont.load_default()
    
    @staticmethod
    def get_bold_font(size: int) -> ImageFont.FreeTypeFont:
        """Get the best available bold font for the platform"""
        if platform.system() == "Windows":
            fonts = [
                "consolab.ttf",     # Consolas Bold (Windows)
                "courbd.ttf",       # Courier New Bold (Windows)
                "arialbd.ttf",      # Arial Bold (Windows)
            ]
        else:  # Linux/Docker
            fonts = [
                "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "DejaVuSansMono-Bold.ttf",
                "LiberationMono-Bold.ttf",
                "LiberationSans-Bold.ttf",
                "FreeSansBold.ttf",
            ]
        
        logger.debug(f"Trying to load bold font with size {size} on {platform.system()}")
        
        for font_path in fonts:
            try:
                font = ImageFont.truetype(font_path, size)
                logger.debug(f"Successfully loaded bold font: {font_path}")
                return font
            except (OSError, IOError) as e:
                logger.debug(f"Failed to load bold font {font_path}: {e}")
                continue
        
        # Fallback to regular monospace font
        logger.info("Using regular monospace font as bold fallback")
        return FontManager.get_monospace_font(size)
    
    @staticmethod
    def get_logo_font(size: int) -> ImageFont.FreeTypeFont:
        """Get the best available font for the REWE logo"""
        if platform.system() == "Windows":
            fonts = [
                "ariblk.ttf",       # Arial Black (Windows)
                "arialbd.ttf",      # Arial Bold (Windows)
                "arial.ttf",        # Arial (Windows)
                "calibrib.ttf",     # Calibri Bold (Windows)
            ]
        else:  # Linux/Docker
            fonts = [
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                "LiberationSans-Bold.ttf",
                "DejaVuSans-Bold.ttf",
                "NotoSans-Bold.ttf",
                "FreeSansBold.ttf",
            ]
        
        logger.debug(f"Trying to load logo font with size {size} on {platform.system()}")
        
        for font_path in fonts:
            try:
                font = ImageFont.truetype(font_path, size)
                logger.debug(f"Successfully loaded logo font: {font_path}")
                return font
            except (OSError, IOError) as e:
                logger.debug(f"Failed to load logo font {font_path}: {e}")
                continue
        
        # Fallback to regular font
        logger.info("Using monospace font as logo fallback")
        return FontManager.get_monospace_font(size)


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
                        # Generate receipt image
                        png_data = self.receipt_generator.create_receipt_image(day)
                        
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
        # Try to get Docker image information if available
        docker_info = "Not running in Docker"
        try:
            # Check if running in Docker by looking for .dockerenv file or cgroup
            if os.path.exists('/.dockerenv') or '/docker' in open('/proc/1/cgroup', 'r').read():
                # Try to get image info from environment variables
                image_name = os.getenv('DOCKER_IMAGE_NAME', 'Unknown')
                image_tag = os.getenv('DOCKER_IMAGE_TAG', 'Unknown')
                image_sha = os.getenv('DOCKER_IMAGE_SHA', 'Unknown')
                
                docker_info = f"Docker Image: {image_name}:{image_tag}"
                if image_sha != 'Unknown':
                    docker_info += f" (SHA: {image_sha})"
                
                logger.info(f"Running in Docker container: {docker_info}")
            else:
                logger.info("Not running in Docker container")
        except Exception as e:
            logger.debug(f"Error detecting Docker environment: {e}")

        self.application.run_polling()


if __name__ == "__main__":
    # Try to load configuration from multiple sources
    BOT_TOKEN = None
    ALLOWED_USER_ID = None
    
    # First, try environment variables (from .env file or system)
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ALLOWED_USER_ID_STR = os.getenv('ALLOWED_USER_ID')
    
    if ALLOWED_USER_ID_STR:
        try:
            ALLOWED_USER_ID = int(ALLOWED_USER_ID_STR)
        except ValueError:
            print("Error: ALLOWED_USER_ID must be a number")
            exit(1)
    
    # If not found in environment, try config.py
    if not BOT_TOKEN or not ALLOWED_USER_ID:
        try:
            from config import BOT_TOKEN as CONFIG_BOT_TOKEN, ALLOWED_USER_ID as CONFIG_ALLOWED_USER_ID
            BOT_TOKEN = BOT_TOKEN or CONFIG_BOT_TOKEN
            ALLOWED_USER_ID = ALLOWED_USER_ID or CONFIG_ALLOWED_USER_ID
        except ImportError:
            pass
    
    # Check if we have valid configuration
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Bot token not found!")
        print("Please set BOT_TOKEN in one of these ways:")
        print("1. Create a .env file with: BOT_TOKEN=your_token_here")
        print("2. Set environment variable: BOT_TOKEN=your_token_here")
        print("3. Copy config_template.py to config.py and fill in BOT_TOKEN")
        print()
        print("Get your bot token from @BotFather on Telegram")
        exit(1)
    
    if not ALLOWED_USER_ID:
        print("User ID not found!")
        print("Please set ALLOWED_USER_ID in one of these ways:")
        print("1. Create a .env file with: ALLOWED_USER_ID=123456789")
        print("2. Set environment variable: ALLOWED_USER_ID=123456789")
        print("3. Copy config_template.py to config.py and fill in ALLOWED_USER_ID")
        print()
        print("Get your user ID from @userinfobot on Telegram")
        exit(1)
    
    print(f"Starting bot for user ID: {ALLOWED_USER_ID}")
    bot = TelegramBot(BOT_TOKEN, ALLOWED_USER_ID)
    bot.run()
