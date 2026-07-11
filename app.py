import streamlit as st
import io
import zipfile
import re
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="מפצל תלושים חכם", page_icon="🤖", layout="centered")

# התאמת ממשק ל-RTL (עברית)
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stFileUploader"] { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

st.title("מפצל תלושי שכר חכם ואינטראקטיבי 🤖✂️")
st.write("העלה קובץ PDF. המערכת תנחש אוטומטית את שמות העובדים, ותאפשר לך לתקן ידנית במידת הצורך.")

uploaded_file = st.file_uploader("בחר קובץ PDF של תלושים", type=["pdf"])

def analyze_page(page):
    """ניתוח עמוד על בסיס קואורדינטות פיזיות.

    מחזיר שני ערכים:
      guessed_name - ניחוש חכם לשם העובד: הטקסט שמימין לתווית "מחלקה:" באותה
                     שורה ויזואלית (מחובר ללא רווחים כדי לאחד אותיות מפוצלות).
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

        # ניחוש השם: הקטעים שמימין לתווית "מחלקה:", מחוברים ללא רווח
        if guessed_name is None:
            idx = next((k for k, (x, t) in enumerate(items) if 'מחלקה' in t), None)
            if idx is not None and idx > 0:
                name = ''.join(t for x, t in items[:idx]).replace(chr(240), 'נ')
                name = re.sub(r'\s+', ' ', name).strip()
                if name:
                    guessed_name = name

    return guessed_name, clean_lines

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

    st.subheader("📋 אישור שמות העובדים (הניחוש האוטומטי כבר מסומן)")
    st.write("המערכת זיהתה את השמות הבאים. באפשרותך לשנות כל עמוד בנפרד במידת הצורך:")

    # ריצה על עמודי ה-PDF והצגת אפשרות הבחירה
    for page_num in range(total_pages):
        guessed_name, page_lines = analyze_page(reader.pages[page_num])

        # בניית רשימת האפשרויות: הניחוש החכם ראשון (ברירת מחדל),
        # ואחריו כל השורות שחולצו מהעמוד לתיקון ידני במידת הצורך.
        options = []
        if guessed_name:
            options.append(guessed_name)
        options.extend(line for line in page_lines if line != guessed_name)
        if not options:
            options = [f"page_{page_num + 1}"]

        # יצירת תיבת הבחירה כשהניחוש האוטומטי מסומן מראש (index=0)
        chosen_line = st.selectbox(
            f"👤 עמוד {page_num + 1} מתוך {total_pages}:",
            options=options,
            index=0,
            key=f"page_select_{page_num}"
        )

        # שמירת השם שנבחר (בין אם הוא האוטומטי ובין אם המשתמש שינה)
        st.session_state['chosen_names'][page_num] = chosen_line

    st.write("---")
    st.subheader("💾 שלב סופי: הורדת התלושים")

    if st.button("🚀 לחץ כאן ליצירת קובץ ZIP מפוצל"):
        zip_buffer = io.BytesIO()
        used_names = {}

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(total_pages):
                page = reader.pages[page_num]

                # שליפת השם הסופי (אוטומטי או ידני)
                selected_name = st.session_state['chosen_names'].get(page_num, f"page_{page_num + 1}")

                # ניקוי תווים לא חוקיים לשמירה במערכת ההפעלה
                clean_name = "".join(x for x in selected_name if x.isalnum() or x in " -_")
                clean_name = clean_name[:50].strip()  # הגבלת אורך
                if not clean_name:
                    clean_name = f"page_{page_num + 1}"

                output_filename = f"{date_prefix}{clean_name}.pdf"

                # מניעת דריסה של קבצים כשיש שם זהה לשני עמודים
                count = used_names.get(output_filename, 0)
                used_names[output_filename] = count + 1
                if count > 0:
                    output_filename = f"{date_prefix}{clean_name} ({count}).pdf"

                # פיצול העמוד בזיכרון ה-RAM
                pdf_writer = PdfWriter()
                pdf_writer.add_page(page)

                page_buffer = io.BytesIO()
                pdf_writer.write(page_buffer)
                page_buffer.seek(0)

                # הזרקה ישירה לתוך ה-ZIP בזיכרון
                zip_file.writestr(output_filename, page_buffer.getvalue())

        st.success("קובץ ה-ZIP מוכן להורדה!")

        st.download_button(
            label="📥 הורד קובץ ZIP",
            data=zip_buffer.getvalue(),
            file_name="split_payroll_slips.zip",
            mime="application/zip"
        )
