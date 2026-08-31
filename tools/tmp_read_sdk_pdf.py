import re

import pdfplumber


PDF_PATH = r"C:\Program Files\Rhino 8\Plug-ins\RhinoCAM 2025 for R8\SDK\Doc\RhinoCAM API User doc.pdf"
PATTERNS = [
    r"Create.*MOp",
    r"Drill",
    r"Pocket",
    r"PostProcess",
    r"MOpManager",
]


with pdfplumber.open(PDF_PATH) as pdf:
    for page_number, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        lines = [
            line
            for line in text.splitlines()
            if any(re.search(pattern, line, re.I) for pattern in PATTERNS)
        ]
        if lines:
            print("--- PAGE {} ---".format(page_number))
            for line in lines:
                print(line[:220])
