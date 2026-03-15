"""
fill_pdf.py — ממלא הצעת מחיר עם PIL
הערה: הקואורדינטות מה-editor הן ישירות (ללא היפוך)
כי ה-editor מציג את הדף ב-LTR אבל הקואורדינטות מחושבות ביחס לרוחב הדף
"""
import json, os, io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'quote_template.pdf')
FIELDS_PATH   = os.path.join(BASE_DIR, 'fields_template.json')

FONT_CANDIDATES = [
    os.path.join(BASE_DIR, 'NotoSansHebrew.ttf'),
    '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
]

def get_font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def fix_bidi(text):
    try:
        from bidi.algorithm import get_display
        return get_display(text)
    except ImportError:
        return text

def fill_quote_pdf(data):
    with open(FIELDS_PATH, encoding='utf-8') as f:
        config = json.load(f)

    fields     = config['fields']
    page_w_pdf = float(config.get('page_width',  595.276))
    page_h_pdf = float(config.get('page_height', 841.89))
    DPI        = 200

    pages  = convert_from_path(TEMPLATE_PATH, dpi=DPI, first_page=1, last_page=1)
    img    = pages[0].copy()
    img_w, img_h = img.size
    draw   = ImageDraw.Draw(img)
    scale_x = img_w / page_w_pdf
    scale_y = img_h / page_h_pdf
    font_path = get_font_path()

    for field in fields:
        key   = field['key']
        value = str(data.get(key, '') or '').strip()
        if not value:
            continue

        # קואורדינטות ישירות מה-editor — ללא היפוך
        x_pdf = float(field['x'])
        y_pdf = float(field['y'])
        w_pdf = float(field['w'])
        h_pdf = float(field.get('h', 14))
        fs    = float(field.get('font_size', 10))
        align = field.get('align', 'right')
        is_ltr = field.get('ltr', False)

        # הוסף ש"ח אחרי הסכום הכולל
        if key == 'total':
            value = value + ' ש"ח'

        x_px  = x_pdf * scale_x
        y_px  = y_pdf * scale_y
        w_px  = w_pdf * scale_x
        fs_px = max(8, int(fs * scale_y * 1.15))

        font = None
        if font_path:
            try:
                font = ImageFont.truetype(font_path, fs_px)
            except Exception:
                pass
        if font is None:
            font = ImageFont.load_default()

        # עברית RTL — תיקון bidi
        display = value if is_ltr else fix_bidi(value)

        bbox   = draw.textbbox((0, 0), display, font=font)
        text_w = bbox[2] - bbox[0]

        if align == 'right':
            tx = x_px + w_px - text_w
        elif align == 'center':
            tx = x_px + (w_px - text_w) / 2
        else:
            tx = x_px

        draw.text((tx, y_px), display, fill=(0, 0, 0), font=font)

    tmp_img = os.path.join(BASE_DIR, '_tmp_filled.jpg')
    img.save(tmp_img, 'JPEG', quality=93)

    pdf_buf = io.BytesIO()
    c = rl_canvas.Canvas(pdf_buf, pagesize=A4)
    c.drawImage(tmp_img, 0, 0, width=page_w_pdf, height=page_h_pdf)
    c.showPage()
    c.save()
    pdf_buf.seek(0)

    reader = PdfReader(TEMPLATE_PATH)
    writer = PdfWriter()
    writer.add_page(PdfReader(pdf_buf).pages[0])
    if len(reader.pages) > 1:
        writer.add_page(reader.pages[1])

    try:
        os.remove(tmp_img)
    except Exception:
        pass

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
