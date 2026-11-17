import streamlit as st
import base64
import hashlib
import html
import io
import json
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
        "analyzing": "מנתח את הקובץ...",
        "share": "שתף",
        "share_tooltip": "שיתוף ישיר לוואטסאפ / מייל / כל אפליקציה, בלי להוריד",
        "share_unsupported": "הדפדפן הזה לא תומך בשיתוף קבצים. השתמשו ב'הורדה' (בטלפון: Chrome באנדרואיד או Safari באייפון).",
        "share_blocked": "הדפדפן חסם את השיתוף. נסו ללחוץ שוב, או השתמשו ב'הורדה'.",
        "share_error": "השיתוף נכשל. השתמשו ב'הורדה'.",
        "share_missing": "הקובץ לא נטען בדפדפן. רעננו את הדף ונסו שוב.",
        "merged_pages": "📎 מאוחד: עמודים {pages}",
        "merged_with": "↳ מאוחד עם עמוד {n}",
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
        "analyzing": "Analyzing the file...",
        "share": "Share",
        "share_tooltip": "Share directly to WhatsApp / email / any app, no download needed",
        "share_unsupported": "This browser can't share files. Use 'Download' instead (on phones: Chrome on Android or Safari on iPhone).",
        "share_blocked": "The browser blocked sharing. Tap again, or use 'Download'.",
        "share_error": "Sharing failed. Use 'Download' instead.",
        "share_missing": "The file isn't loaded in the browser. Refresh the page and try again.",
        "merged_pages": "📎 Merged: pages {pages}",
        "merged_with": "↳ Merged with page {n}",
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



# ---------------------------------------------------------------------------
# ניתוח העמודים / Page analysis
# ---------------------------------------------------------------------------
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


# המטמון מזוהה לפי hash התוכן (פרמטרים שמתחילים ב-_ לא נכנסים למפתח המטמון).
# The cache is keyed by the content hash; "_" params are excluded from the key.
# ttl קצר: התלושים נשמרים בזיכרון השרת רק לזמן קצר.
@st.cache_data(ttl=900, max_entries=20, show_spinner=False)
def analyze_pdf(file_hash, anchor, _file_bytes):
    reader = PdfReader(io.BytesIO(_file_bytes))
    return [analyze_page(page, anchor) for page in reader.pages]


@st.cache_data(ttl=900, max_entries=500, show_spinner=False)
def build_pdf(file_hash, page_indices, _file_bytes):
    """PDF של עמוד אחד או כמה עמודים (עובד עם כמה עמודים מאוחד לקובץ אחד)."""
    reader = PdfReader(io.BytesIO(_file_bytes))
    writer = PdfWriter()
    for i in page_indices:
        writer.add_page(reader.pages[i])
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@st.cache_data(ttl=900, max_entries=20, show_spinner=False)
def build_zip(file_hash, groups, _file_bytes):
    """groups: tuple של (שם קובץ, tuple של אינדקסי עמודים)."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, pages in groups:
            zf.writestr(filename, build_pdf(file_hash, pages, _file_bytes))
    return zip_buffer.getvalue()


# תווים שאסורים בשמות קבצים ב-Windows/macOS/Linux, כולל תווי בקרה
_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL",
                     *(f"COM{i}" for i in range(1, 10)),
                     *(f"LPT{i}" for i in range(1, 10))}


def sanitize_name(name, page_num):
    """מסיר רק תווים אסורים במערכת הקבצים; שומר על גרש (ג'ורג'), נקודות וכו'."""
    clean = _FORBIDDEN_CHARS.sub(" ", str(name or ""))
    clean = re.sub(r"\s+", " ", clean).strip()[:80]
    clean = clean.strip(" .")  # Windows לא מרשה נקודה/רווח בסוף השם
    if clean.upper() in _WINDOWS_RESERVED:
        clean += "_"
    return clean or f"page_{page_num + 1}"


# ---------------------------------------------------------------------------
# כפתור שיתוף (Web Share API) / Share button
# רץ ישירות בדף (st.html, בלי iframe): ל-iframe של components.html אין
# הרשאת web-share, ולכן navigator.share עלול להיחסם שם.
# ---------------------------------------------------------------------------
_SHARE_CSS = """
<style>
.ss-share { width:100%; padding:0.7rem 0.5rem; font-size:1.05rem; border-radius:10px;
  border:1px solid #1da851; background:#25D366; color:#fff; cursor:pointer;
  font-family:inherit; line-height:1.6; }
.ss-share:hover { background:#1ebe5b; }
.ss-share.ss-unsup { background:transparent; color:inherit; border-color:rgba(128,128,128,.45); opacity:.7; }
.ss-share-msg { font-size:0.8rem; margin-top:4px; color:#c0392b; }
.ss-share-msg:empty { display:none; }
@media (max-width:640px) { .ss-share { padding:0.6rem 0.5rem; font-size:0.95rem; } }
</style>
"""

_SHARE_JS = """
<script>
(function () {
  var W = window;
  W.__ssFiles = W.__ssFiles || {};
  var REC = __REC__;
  if (REC) { W.__ssFiles[REC.key] = REC; }
  W.__ssMsgs = __MSGS__;

  function canShareFiles() {
    try {
      var f = new File([new Uint8Array([37])], "t.pdf", {type: "application/pdf"});
      return !!(navigator.share && navigator.canShare && navigator.canShare({files: [f]}));
    } catch (e) { return false; }
  }
  // סימון מראש של כפתורים בדפדפן שלא תומך (טולטיפ ברור)
  setTimeout(function () {
    if (canShareFiles()) return;
    document.querySelectorAll(".ss-share").forEach(function (b) {
      b.classList.add("ss-unsup");
      b.title = W.__ssMsgs.unsupported;
    });
  }, 0);

  if (W.__ssInit) return;
  W.__ssInit = true;
  document.addEventListener("click", function (ev) {
    var btn = ev.target && ev.target.closest && ev.target.closest(".ss-share");
    if (!btn) return;
    ev.preventDefault();
    var M = W.__ssMsgs;
    var msgEl = btn.parentElement && btn.parentElement.querySelector(".ss-share-msg");
    function say(t) { if (msgEl) msgEl.textContent = t; }
    say("");
    var rec = W.__ssFiles[btn.getAttribute("data-file-key")];
    if (!rec) { say(M.missing); return; }
    if (!rec.file) {
      // המרה סינכרונית (בתוך הלחיצה) כדי לא לאבד את "מחוות המשתמש"
      var bin = atob(rec.b64), arr = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      rec.file = new File([arr], rec.name, {type: "application/pdf"});
    }
    var data = {files: [rec.file], title: rec.name};
    if (!navigator.share || !navigator.canShare || !navigator.canShare(data)) {
      say(M.unsupported); return;
    }
    navigator.share(data).catch(function (err) {
      var n = err && err.name;
      if (n === "AbortError") return;           // המשתמש סגר את חלון השיתוף
      if (n === "NotAllowedError") say(M.blocked);
      else say(M.error + (n ? " (" + n + ")" : ""));
    });
  }, true);
})();
</script>
"""


def share_button(pdf_bytes, filename):
    """כפתור שיתוף לקובץ בזיכרון. הקובץ נשלח לדפדפן פעם אחת בלבד בכל סשן;
    בריצות הבאות נשלח רק המזהה (חוסך מגה-בייטים בכל שינוי בתיבת בחירה)."""
    key = hashlib.md5(pdf_bytes + filename.encode("utf-8")).hexdigest()
    sent = st.session_state.setdefault("ss_sent", set())
    rec = None
    if key not in sent:
        rec = {"key": key, "name": filename,
               "b64": base64.b64encode(pdf_bytes).decode("ascii")}
        sent.add(key)
    msgs = {"unsupported": T["share_unsupported"], "blocked": T["share_blocked"],
            "error": T["share_error"], "missing": T["share_missing"]}
    js = (_SHARE_JS.replace("__REC__", json.dumps(rec))
                   .replace("__MSGS__", json.dumps(msgs, ensure_ascii=False)))
    button = (f'<div><button type="button" class="ss-share" data-file-key="{key}" '
              f'title="{html.escape(T["share_tooltip"])}">📤 {html.escape(T["share"])}</button>'
              f'<div class="ss-share-msg"></div></div>')
    st.html(_SHARE_CSS + button + js, unsafe_allow_javascript=True)


# ---------------------------------------------------------------------------
# זרימה ראשית / Main flow
# ---------------------------------------------------------------------------
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    anchor_key = hashlib.md5(anchor_field.encode("utf-8")).hexdigest()[:8]

    # חילוץ תאריך משם הקובץ המקורי (למשל 5.26)
    match = re.search(r'\b(\d+\.\d+)\b', uploaded_file.name)
    date_prefix = f"{match.group(1)} " if match else ""

    with st.spinner(T["analyzing"]):
        analysis = analyze_pdf(file_hash, anchor_field, file_bytes)

    st.subheader(T["confirm_subheader"])
    st.write(T["confirm_help"])

    # מעבר 1: תיבות בחירה. העמודות נשמרות כדי למלא בהן כפתורים אחרי שכל
    # השמות ידועים (צריך לדעת מראש אילו עמודים מתאחדים).
    rows = []
    filenames = []
    for page_num, (guessed_name, page_lines) in enumerate(analysis):
        options = []
        if guessed_name:
            options.append(guessed_name)
        options.extend(line for line in dict.fromkeys(page_lines) if line != guessed_name)
        if not options:
            options = [f"page_{page_num + 1}"]

        col_select, col_dl, col_share = st.columns([3, 1, 1])
        with col_select:
            chosen = st.selectbox(
                T["select_label"].format(n=page_num + 1),
                options=options,
                index=0,
                accept_new_options=True,  # הקלדת שם חופשי
                # המפתח כולל את hash הקובץ: קובץ חדש (גם עם אותו שם) מתחיל מאפס
                key=f"sel_{file_hash}_{anchor_key}_{page_num}",
            )
        rows.append((col_dl, col_share))
        filenames.append(f"{date_prefix}{sanitize_name(chosen, page_num)}.pdf")

    # קיבוץ עמודים עם אותו שם קובץ -> PDF אחד מרובה עמודים
    groups = {}
    for page_num, fname in enumerate(filenames):
        groups.setdefault(fname, []).append(page_num)

    # מעבר 2: כפתורי הורדה/שיתוף בשורה של העמוד הראשון בכל קבוצה
    for page_num, fname in enumerate(filenames):
        pages = groups[fname]
        col_dl, col_share = rows[page_num]
        if page_num != pages[0]:
            with col_dl:
                st.caption(T["merged_with"].format(n=pages[0] + 1))
            continue
        pdf_bytes = build_pdf(file_hash, tuple(pages), file_bytes)
        with col_dl:
            st.download_button(
                label=T["download_single"],
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                key=f"dl_{file_hash}_{page_num}",
                width="stretch",
            )
            if len(pages) > 1:
                st.caption(T["merged_pages"].format(pages=", ".join(str(p + 1) for p in pages)))
        with col_share:
            share_button(pdf_bytes, fname)

    st.write("---")
    st.subheader(T["final_subheader"])

    if st.button(T["zip_button"]):
        zip_groups = tuple((fname, tuple(pages)) for fname, pages in groups.items())
        zip_bytes = build_zip(file_hash, zip_groups, file_bytes)
        st.success(T["zip_ready"])
        st.download_button(
            label=T["zip_download"],
            data=zip_bytes,
            file_name="split_payroll_slips.zip",
            mime="application/zip",
        )
