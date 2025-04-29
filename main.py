from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import io
import re

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "working on postman "}

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        print(f" uploaded file correctly : {file.filename}")
        print(f"size of file : {len(contents)} bytes")
        
        image = Image.open(io.BytesIO(contents))
        
        text = pytesseract.image_to_string(image)
        
        extracted_data = extract_lab_data(text)

        response = {
            "is_success": True,
            "data": extracted_data
        }
        return JSONResponse(content=response)

    except Exception as e:
        
        return JSONResponse(
            content={"is_success": False, "data": [], "error": str(e)}
        )

def extract_lab_data(text):
    lines = text.split('\n')
    data = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        pattern = r"(?P<test_name>[\w\s\(\)\-\/]+?)\s*(?P<test_value>\d+\.?\d*)\s*(?P<test_unit>[a-zA-Z/%μ^0-9]*)\s*(?P<bio_reference_range>\d+\.?\d*\s*[-–]\s*\d+\.?\d*)?"
        match = re.search(pattern, line)

        if match:
            test_name = match.group("test_name").strip()
            test_value = match.group("test_value")
            test_unit = match.group("test_unit") or ""
            bio_reference_range = match.group("bio_reference_range") or ""

            lab_test_out_of_range = False

            if bio_reference_range:
                try:
                    range_parts = re.split(r"[-–]", bio_reference_range)
                    range_min = float(range_parts[0].strip())
                    range_max = float(range_parts[1].strip())
                    value = float(test_value)
                    if not (range_min <= value <= range_max):
                        lab_test_out_of_range = True
                except Exception:
                    pass

            data.append({
                "test_name": test_name,
                "test_value": test_value,
                "bio_reference_range": bio_reference_range,
                "test_unit": test_unit,
                "lab_test_out_of_range": lab_test_out_of_range
            })
        else:
            print(f"Line {i} didn't match the expected pattern: {line}")

    return data


