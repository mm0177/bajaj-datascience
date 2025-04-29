from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from PIL import Image
import pytesseract
import numpy as np
import cv2
import io
import re
from rapidfuzz import fuzz

# Tesseract path (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# FastAPI app
app = FastAPI(title="Lab Report OCR Service")

# === Response models ===
class LabTest(BaseModel):
    test_name: str
    test_value: str
    test_unit: str
    bio_reference_range: str
    lab_test_out_of_range: bool

class LabTestResponse(BaseModel):
    is_success: bool
    data: List[LabTest]

# === Preprocessing function ===
def preprocess_image(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    thresh = cv2.adaptiveThreshold(
        resized, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        35, 10
    )
    return thresh

# === Known lab tests for validation/fuzzy match ===
KNOWN_TESTS = [
    "HB ESTIMATION", "HAEMOGLOBIN", "PCV", "KETONE BODIES", "URINE FOR KETONES",
    "BLOOD SUGAR", "RBC COUNT", "WBC COUNT", "PLATELET COUNT",
    "NEUTROPHILS", "LYMPHOCYTES", "TRIGLYCERIDES", "CHOLESTEROL",
    "BILIRUBIN", "CREATININE", "UREA", "SODIUM", "POTASSIUM"
]

def is_probable_lab_test(name: str) -> bool:
    return any(kw in name for kw in KNOWN_TESTS)

def fuzzy_match_test(name: str) -> str:
    best = max(KNOWN_TESTS, key=lambda t: fuzz.ratio(t, name))
    return best if fuzz.ratio(best, name) > 75 else name

# === Parse extracted text into structured lab tests ===
def parse_lab_text(text: str) -> List[LabTest]:
    lab_tests = []

    pattern = re.compile(r"""
        (?P<name>[A-Z\s\(\)\-/]+?)[:\-]?\s+         # Test name
        (?P<value>[A-Z]+|\d+\.?\d*)\s*              # Value (e.g. NEGATIVE or 9.4)
        (?P<unit>[a-zA-Z/%µ\d]*)?\s*               # Unit (optional)
        \(?(?P<range>\d+\.?\d*\s*-\s*\d+\.?\d*)?\)? # Ref range (optional)
    """, re.VERBOSE | re.IGNORECASE)

    for match in pattern.finditer(text):
        raw_name = match.group("name").strip().upper()
        value = match.group("value").strip().upper()
        unit = (match.group("unit") or "").strip()
        range_ = (match.group("range") or "").strip().replace(" ", "")

        name = fuzzy_match_test(raw_name)

        # Skip short/junk names unless known
        if not is_probable_lab_test(name) and len(name) < 4:
            continue

        # Out-of-range logic (only for numeric values with range)
        out_of_range = False
        try:
            if value.replace('.', '', 1).isdigit() and range_:
                low, high = map(float, range_.split("-"))
                val = float(value)
                out_of_range = not (low <= val <= high)
        except:
            pass

        lab_tests.append(LabTest(
            test_name=name,
            test_value=value,
            test_unit=unit,
            bio_reference_range=range_,
            lab_test_out_of_range=out_of_range
        ))

    return lab_tests

# === API Endpoint ===
@app.post("/get-lab-tests", response_model=LabTestResponse)
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # OCR
        processed = preprocess_image(cv_img)
        text = pytesseract.image_to_string(processed, config="--psm 4")

        # Parse
        results = parse_lab_text(text)

        return LabTestResponse(is_success=True, data=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
