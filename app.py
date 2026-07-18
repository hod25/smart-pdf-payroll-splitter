import streamlit as st
import io
import zipfile
import re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="SmartSplit — Universal PDF Splitter", page_icon="🤖", layout="centered")

# ---------------------------------------------------------------------------
# תגיות Open Graph לתצוגה מקדימה יפה בשיתוף קישור (WhatsApp / Facebook / LinkedIn)
# Open Graph tags for a rich link preview when sharing the URL.
# הערה: עדכן את og:url לכתובת ה-Render הסופית שלך.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <meta property="og:type" content="website">
    <meta property="og:title" content="SmartSplit - מפצל קבצי PDF חכם ומאובטח">
    <meta property="og:description" content="כלי מהיר וגנרי לפיצול תלושי שכר, חשבוניות ומסמכים לפי שדה עוגן מותאם אישית. העיבוד מתבצע בזיכרון ה-RAM בלבד ללא שמירת מידע בשרת.">
    <meta property="og:image" content="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop">
    <meta property="og:url" content="https://smart-split.onrender.com">
    <meta name="twitter:card" content="summary_large_image">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# תרגומים / Translations (He / En)
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    "he": {
        "lang_label": "🌐 שפה / Language",
        "title": "SmartSplit — מפצל קבצי PDF חכם 🤖✂️",
        "intro": "העלה קובץ PDF מרובה-עמודים (תלושים, חשבוניות, מסמכים). המערכת תנחש אוטומטית את השם לפי שדה העוגן, ותאפשר לך לתקן ידנית ולהוריד כל עמוד בנפרד. העיבוד מתבצע בזיכרון בלבד, ללא שמירה בשרת.",
        "uploader": "בחר קובץ PDF לפיצול",
        "anchor_label": "🔑 הזן את שדה העוגן (מילת המפתח לחיפוש):",
        "anchor_help": "השם יחולץ מהטקסט שמימין למילת המפתח הזו (למשל: מחלקה:, לכבוד:, חשבונית מס:).",
        "confirm_subheader": "📋 אישור השמות (הניחוש האוטומטי כבר מסומן)",
        "confirm_help": "לכל עמוד נבחר שם אוטומטית. ניתן לשנות כל עמוד בנפרד ולהוריד אותו מיד, או להוריד את הכל כ-ZIP בתחתית:",
        "page_label": "עמוד {n}",
        "expander": "📄 עמוד {n} — {name}",
        "preview_caption": "תצוגה מקדימה של הטקסט בעמוד:",
        "no_text": "לא זוהה טקסט בעמוד זה.",
        "select_label": "👤 בחר/י שם לעמוד {n}:",
        "download_single": "הורדה",
        "final_subheader": "💾 הורדת כל העמודים כ-ZIP",
        "zip_button": "🚀 צור קובץ ZIP מפוצל",
        "zip_ready": "קובץ ה-ZIP מוכן להורדה!",
        "zip_download": "📥 הורד קובץ ZIP",
    },
    "en": {
        "lang_label": "🌐 שפה / Language",
        "title": "SmartSplit — Universal PDF Splitter 🤖✂️",
        "intro": "Upload a multi-page PDF (payslips, invoices, documents). The app auto-detects the name by your anchor field, lets you correct it manually, and download each page individually. Processing is fully in-memory — nothing is stored on the server.",
        "uploader": "Choose a PDF file to split",
        "anchor_label": "🔑 Enter the anchor field (keyword to search for):",
        "anchor_help": "The name is extracted from the text to the right of this keyword (e.g. מחלקה:, לכבוד:, Invoice No:).",
        "confirm_subheader": "📋 Confirm names (the auto-guess is pre-selected)",
        "confirm_help": "Each page has an auto-selected name. You can change any page individually and download it instantly, or grab everything as a ZIP at the bottom:",
        "page_label": "Page {n}",
        "expander": "📄 Page {n} — {name}",
        "preview_caption": "Preview of the page text:",
        "no_text": "No text detected on this page.",
        "select_label": "👤 Choose a name for page {n}:",
        "download_single": "Download",
        "final_subheader": "💾 Download all pages as ZIP",
        "zip_button": "🚀 Generate split ZIP file",
        "zip_ready": "The ZIP file is ready to download!",
        "zip_download": "📥 Download ZIP file",
    },
}

# ---------------------------------------------------------------------------
# בחירת שפה / Language selection
# ---------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "he"

# כפתור החלפת שפה קומפקטי בפינה העליונה — לחיצה אחת מחליפה שפה
toggle_col, _spacer = st.columns([1, 5])
with toggle_col:
    _other = "en" if st.session_state["lang"] == "he" else "he"
    _btn_label = "🌐 EN" if _other == "en" else "🌐 עב"
    if st.button(_btn_label, key="lang_toggle"):
        st.session_state["lang"] = _other
        st.rerun()

lang = st.session_state["lang"]
T = TRANSLATIONS[lang]
is_rtl = lang == "he"
direction = "rtl" if is_rtl else "ltr"
align = "right" if is_rtl else "left"

# ---------------------------------------------------------------------------
# עיצוב: כיוון דינמי + התאמה למובייל / Styling: dynamic direction + mobile
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ direction: {direction}; text-align: {align}; }}
    div[data-testid="stFileUploader"] {{ direction: {direction}; text-align: {align}; }}

    /* כפתורים ידידותיים למגע / touch-friendly buttons */
    .stButton > button, .stDownloadButton > button {{
        width: 100%;
        padding: 0.7rem 1rem;
        font-size: 1.05rem;
        border-radius: 10px;
    }}

    /* התאמה למסכי מובייל / mobile screens */
    @media (max-width: 640px) {{
        .block-container {{ padding: 1rem 0.8rem 3rem 0.8rem; }}
        h1 {{ font-size: 1.5rem !important; }}
        h2, h3 {{ font-size: 1.2rem !important; }}
        .stApp {{ font-size: 1.05rem; }}
    }}

    /* כפתור החלפת שפה קטן מאוד בפינה העליונה */
    div[data-testid="stButton"]:has(button[kind="secondary"]) {{ margin-top: -0.5rem; }}
    .st-key-lang_toggle button {{
        width: auto !important;
        min-height: 0 !important;
        padding: 0.1rem 0.55rem !important;
        font-size: 0.75rem !important;
        line-height: 1.4 !important;
        border-radius: 999px !important;
    }}

    /* הסתרת רכיבי ברירת המחדל של Streamlit (דיפלוי, תפריט, כותרת, פווטר) */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    .stDeployButton {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}

    /* שורות קומפקטיות + יישור כפתור ההורדה לתחתית מול תיבת הבחירה */
    [data-testid="stHorizontalBlock"] {{ align-items: flex-end; gap: 0.5rem; }}
    .stSelectbox {{ margin-bottom: 0 !important; }}

    /* כיווץ מיוחד למובייל */
    @media (max-width: 640px) {{
        [data-testid="stHorizontalBlock"] {{ gap: 0.35rem; }}
        [data-testid="stVerticalBlock"] {{ gap: 0.5rem; }}
        .stButton > button, .stDownloadButton > button {{
            padding: 0.6rem 0.5rem;
            font-size: 0.95rem;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(T["title"])
st.write(T["intro"])

anchor_field = st.text_input(T["anchor_label"], value="מחלקה", help=T["anchor_help"]).strip()

uploaded_file = st.file_uploader(T["uploader"], type=["pdf"])

def analyze_page(page, anchor):
    """ניתוח עמוד על בסיס קואורדינטות פיזיות.

    מחזיר שני ערכים:
      guessed_name - ניחוש חכם לשם: הטקסט שמימין לשדה העוגן (anchor)
                     באותה שורה ויזואלית (מחובר ללא רווחים לאיחוד אותיות מפוצלות).
      clean_lines  - כל השורות הנקיות בעמוד, לבחירה ידנית בתיבת הבחירה.
    """
    frags = []
    def v(t, cm, tm, fd, fs):
        if t and t.strip():
            frags.append((round(tm[5]), round(tm[4]), t))

    page.extract_text(visitor_text=v)

    # קיבוץ הקטעים לשורות ויזואליות לפי קואורדינטת y
    lines = []
    for y, x, t in sorted(frags, key=lambda a: (-a[0], -a[1])):
        for L in lines:
            if abs(L['y'] - y) <= 3:
                L['items'].append((x, t))
                break
        else:
            lines.append({'y': y, 'items': [(x, t)]})

    clean_lines = []
    guessed_name = None
    for L in lines:
        items = sorted(L['items'], key=lambda a: -a[0])

        # שורה נקייה לתצוגה (מחוברת ברווחים)
        s = ' '.join(t for x, t in items).replace(chr(240), 'נ')
        s = re.sub(r'\s+', ' ', s).strip()
        if s:
            clean_lines.append(s)

        # ניחוש השם: הקטעים שמימין לשדה העוגן, מחוברים ללא רווח
        if guessed_name is None and anchor:
            idx = next((k for k, (x, t) in enumerate(items) if anchor in t), None)
            if idx is not None and idx > 0:
                name = ''.join(t for x, t in items[:idx]).replace(chr(240), 'נ')
                name = re.sub(r'\s+', ' ', name).strip()
                if name:
                    guessed_name = name

    return guessed_name, clean_lines


def sanitize_name(name, page_num):
    """ניקוי שם לשימוש בשם קובץ, עם נפילה לשם עמוד אם ריק."""
    clean = "".join(x for x in name if x.isalnum() or x in " -_")
    clean = clean[:50].strip()
    if not clean:
        clean = f"page_{page_num + 1}"
    return clean


def build_page_pdf(page):
    """יצירת PDF של עמוד בודד בזיכרון (io.BytesIO) והחזרת ה-bytes."""
    writer = PdfWriter()
    writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()

if uploaded_file is not None:
    # חילוץ תאריך משם הקובץ המקורי (למשל 5.26)
    pattern = r'\b(\d+\.\d+)\b'
    match = re.search(pattern, uploaded_file.name)
    date_prefix = f"{match.group(1)} " if match else ""

    # טעינת ה-PDF ל-Session State כדי למנוע טעינה מחדש בכל קליק
    if 'pdf_reader' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
        st.session_state['pdf_reader'] = PdfReader(uploaded_file)
        st.session_state['file_name'] = uploaded_file.name
        st.session_state['chosen_names'] = {}

    reader = st.session_state['pdf_reader']
    total_pages = len(reader.pages)

    st.subheader(T["confirm_subheader"])
    st.write(T["confirm_help"])

    # ריצה על עמודי ה-PDF — רשימה שטוחה ונוחה למובייל (ללא expander)
    for page_num in range(total_pages):
        guessed_name, page_lines = analyze_page(reader.pages[page_num], anchor_field)

        # בניית רשימת האפשרויות: הניחוש החכם ראשון (ברירת מחדל),
        # ואחריו כל השורות שחולצו מהעמוד לתיקון ידני במידת הצורך.
        options = []
        if guessed_name:
            options.append(guessed_name)
        options.extend(line for line in page_lines if line != guessed_name)
        if not options:
            options = [f"page_{page_num + 1}"]

        # שורה שטוחה: תיבת בחירה (רחבה) + כפתור הורדה (צר)
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            chosen_line = st.selectbox(
                T["select_label"].format(n=page_num + 1),
                options=options,
                index=0,
                key=f"page_select_{page_num}"
            )

        # שמירת השם שנבחר (בין אם הוא האוטומטי ובין אם המשתמש שינה)
        st.session_state['chosen_names'][page_num] = chosen_line

        # כפתור הורדה בודד: יוצר PDF של העמוד הזה בלבד בזיכרון
        single_clean = sanitize_name(chosen_line, page_num)
        single_filename = f"{date_prefix}{single_clean}.pdf"
        with col_btn:
            st.download_button(
                label=T["download_single"],
                data=build_page_pdf(reader.pages[page_num]),
                file_name=single_filename,
                mime="application/pdf",
                key=f"page_download_{page_num}"
            )

    st.write("---")
    st.subheader(T["final_subheader"])

    if st.button(T["zip_button"]):
        zip_buffer = io.BytesIO()
        used_names = {}

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(total_pages):
                page = reader.pages[page_num]

                # שליפת השם הסופי (אוטומטי או ידני)
                selected_name = st.session_state['chosen_names'].get(page_num, f"page_{page_num + 1}")

                # ניקוי תווים לא חוקיים לשמירה במערכת ההפעלה
                clean_name = sanitize_name(selected_name, page_num)

                output_filename = f"{date_prefix}{clean_name}.pdf"

                # מניעת דריסה של קבצים כשיש שם זהה לשני עמודים
                count = used_names.get(output_filename, 0)
                used_names[output_filename] = count + 1
                if count > 0:
                    output_filename = f"{date_prefix}{clean_name} ({count}).pdf"

                # הזרקה ישירה לתוך ה-ZIP בזיכרון
                zip_file.writestr(output_filename, build_page_pdf(page))

        st.success(T["zip_ready"])

        st.download_button(
            label=T["zip_download"],
            data=zip_buffer.getvalue(),
            file_name="split_payroll_slips.zip",
            mime="application/zip"
        )
