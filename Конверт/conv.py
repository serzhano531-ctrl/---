import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from pdf2docx import Converter
from docx import Document
from reportlab.pdfgen import canvas

# Telegram токеніңді осында қой
TOKEN = "8058847913:AAGzTStOMid5020KUyDKwV5MSgh4lNJi_W0"

# Уақытша файлдар сақталатын папка
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# /start командасы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['PDF → DOCX', 'DOCX → PDF'], ['JPG → PNG', 'PNG → JPG'], ['Фото → PDF']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Файлды жібере тұрыңыз және конвертация түрін таңдаңыз:", 
        reply_markup=reply_markup
    )

# Файлды сақтау (v20+)
async def save_file(file, filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    # get_file() – await керек, download_to_drive – await керек
    telegram_file = await file.get_file()
    await telegram_file.download_to_drive(file_path)
    return file_path

# PDF → DOCX
def pdf_to_docx(pdf_path, output_path):
    cv = Converter(pdf_path)
    cv.convert(output_path)
    cv.close()

# DOCX → PDF
def docx_to_pdf(docx_path, output_path):
    doc = Document(docx_path)
    c = canvas.Canvas(output_path)
    textobject = c.beginText(40, 800)
    for para in doc.paragraphs:
        textobject.textLine(para.text)
    c.drawText(textobject)
    c.save()

# JPG → PNG
def jpg_to_png(image_path, output_path):
    img = Image.open(image_path)
    img.save(output_path, 'PNG')

# PNG → JPG
def png_to_jpg(image_path, output_path):
    img = Image.open(image_path).convert('RGB')
    img.save(output_path, 'JPEG')

# Фото → PDF
def photo_to_pdf(image_path, output_path):
    img = Image.open(image_path)
    img.save(output_path, 'PDF', resolution=100.0)

# Қолданушы жіберген файлмен жұмыс
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = context.user_data.get('choice')
    if not user_choice:
        await update.message.reply_text("Алдымен конвертация түрін таңдаңыз.")
        return

    # Қандай файл келгенін тексеру
    file = update.message.document if update.message.document else update.message.photo[-1]
    filename = file.file_name if hasattr(file, 'file_name') else "photo.jpg"

    # Файлды сақтау
    file_path = await save_file(file, filename)

    # Шығыс файл жолы
    output_path = os.path.join(UPLOAD_DIR, f"converted_{filename}")

    try:
        if user_choice == 'PDF → DOCX':
            pdf_to_docx(file_path, output_path.replace('.pdf','.docx'))
            output_path = output_path.replace('.pdf','.docx')
        elif user_choice == 'DOCX → PDF':
            docx_to_pdf(file_path, output_path.replace('.docx','.pdf'))
            output_path = output_path.replace('.docx','.pdf')
        elif user_choice == 'JPG → PNG':
            jpg_to_png(file_path, output_path.replace('.jpg','.png'))
            output_path = output_path.replace('.jpg','.png')
        elif user_choice == 'PNG → JPG':
            png_to_jpg(file_path, output_path.replace('.png','.jpg'))
            output_path = output_path.replace('.png','.jpg')
        elif user_choice == 'Фото → PDF':
            photo_to_pdf(file_path, output_path.replace('.jpg','.pdf'))
            output_path = output_path.replace('.jpg','.pdf')
        else:
            await update.message.reply_text("Белгісіз конвертация түрі.")
            return

        # Дайын файлды қолданушыға жіберу
        await update.message.reply_document(open(output_path, 'rb'))

    except Exception as e:
        await update.message.reply_text(f"Қате шықты: {e}")

# Қолданушы таңдаған конвертацияны сақтау
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['choice'] = update.message.text
    await update.message.reply_text(f"Сіз таңдадыңыз: {update.message.text}\nЕнді файл жіберіңіз.")

# Ботты іске қосу
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choice_handler))
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

print("Бот іске қосылды...")
app.run_polling()
