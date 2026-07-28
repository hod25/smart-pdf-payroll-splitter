# SmartSplit — Universal PDF Splitter 🤖✂️

A Streamlit web app for splitting a multi-page PDF (payslips, invoices, documents)
into separate files — with automatic name detection based on a **custom anchor
field**, manual correction, and per-page or ZIP download.

## Key Features

- **Generic anchor-based splitting** — the user enters a keyword (default `מחלקה`
  / "department"), and the name is extracted from the text to its right — so you
  can split not only payslips but also invoices and documents.
- **Smart name detection** — coordinate-based extraction that locates the name to
  the right of the anchor field, including a font-encoding fix (`ð` → `נ`).
- **Flat interactive list** — each page has a dropdown (with the guess pre-selected)
  and an individual download button — ideal for mobile.
- **Bilingual (Hebrew / English)** — a compact language-toggle button with dynamic
  RTL/LTR direction.
- **Mobile-friendly** — responsive design, large buttons, and hidden default
  Streamlit chrome.
- **Fully private** — all processing happens in memory (`io.BytesIO`); no file is
  ever stored on the server.
- **ZIP download** — all split pages are bundled into a single ZIP, with
  duplicate-filename protection.
- **Filenames** — in the format `{date} {name}.pdf`, where the date is taken from
  the original file name.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at http://localhost:8501.

## Deploy on Render (Web Service)

- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  ```

## Project Structure

| File | Description |
| --- | --- |
| `app.py` | The Streamlit application |
| `requirements.txt` | Dependencies: `streamlit`, `pypdf` |
| `render.yaml` | Automatic Render deployment config (Blueprint) |
| `.gitignore` | Prevents committing junk and documents (`*.pdf`, `*.zip`, `*.xlsx`) |

## Data Security

Because the tool processes sensitive documents (payslips, invoices), the app never
stores any file on the server — all files are processed in RAM only and are
discarded when the request ends.
