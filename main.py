import easyocr
import cv2
import numpy as np
from datetime import datetime
import re
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import os

# Load pretrained EasyOCR model
reader = easyocr.Reader(['en'])

# Initialize FastAPI app
app = FastAPI(
    title="OCR Date Extraction API",
    description="API to extract manufacturing and expiry dates from images using OCR",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def parse_date(date_str):
    """Parse date string with multiple formats, prioritizing YYYY/MM/DD."""
    formats = [
        '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', '%d/%m/%y', '%m/%d/%y',
        '%d.%m.%Y', '%d.%m.%y', '%d-%m-%Y', '%d-%m-%y',
        '%d %b %y', '%d %b %Y', '%b %d %y', '%b %d %Y'
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            if parsed.year < 100:
                parsed = parsed.replace(year=parsed.year + 2000)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return "Parsing failed"

def extract_dates_from_image(image):
    """
    Extract dates from image.
    Args:
        image: Can be a file path (str) or numpy array (cv2 image)
    Returns:
        dict: Dictionary with 'MFG' and/or 'EXP' dates
    """
    # Read image - handle both file path and numpy array
    if isinstance(image, str):
        img = cv2.imread(image)
    else:
        img = image
    
    if img is None:
        raise ValueError("Could not read image")
    
    # Extract text using OCR
    result = reader.readtext(img)
    extracted_text = ' '.join([text for _, text, _ in result]).upper()  # Uppercase for matching
    print(f"Extracted text: {extracted_text}")
    dates = {}
    
    # Expanded keywords
    expiry_keywords = ["EXP", "EXPIRY", "EXP.", "BEST BEFORE", "USE BY", "BBE"]
    mfg_keywords = ["MFG", "MANUFACTURE", "MADE ON", "PRODUCTION", "MFD", "PRO", "PRO:"]
    
    # Date pattern
    date_pattern = r'(\d{4}/\d{2}/\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+[A-Z]{3}\s+\d{2,4})'
    
    # Try to find MFG with keywords
    mfg_pat = rf'(?:{"|".join(re.escape(k) for k in mfg_keywords)})\s*[:\.]?\s*({date_pattern})'
    mfg_match = re.search(mfg_pat, extracted_text)
    if mfg_match and mfg_match.group(1):
        dates['MFG'] = parse_date(mfg_match.group(1))
    
    # Try to find EXP with keywords
    expiry_pat = rf'(?:{"|".join(re.escape(k) for k in expiry_keywords)})\s*[:\.]?\s*({date_pattern})?'
    exp_match = re.search(expiry_pat, extracted_text)
    if exp_match and exp_match.group(1):
        dates['EXP'] = parse_date(exp_match.group(1))
    
    # If MFG is found but EXP is missing, look for the next date
    if 'MFG' in dates and 'EXP' not in dates:
        mfg_pos = re.search(mfg_pat, extracted_text).end()
        remaining_text = extracted_text[mfg_pos:]
        all_dates = re.findall(date_pattern, remaining_text)
        if all_dates:
            dates['EXP'] = parse_date(all_dates[0])  # Assign the next date as EXP
    
    # If no keywords but dates exist, use first two dates with verification
    if 'MFG' not in dates or 'EXP' not in dates:
        all_dates = re.findall(date_pattern, extracted_text)
        if len(all_dates) >= 2:
            mfg_date = parse_date(all_dates[0])
            exp_date = parse_date(all_dates[1])
            if mfg_date != "Parsing failed" and exp_date != "Parsing failed":
                mfg_dt = datetime.strptime(mfg_date, '%Y-%m-%d')
                exp_dt = datetime.strptime(exp_date, '%Y-%m-%d')
                if mfg_dt > exp_dt:
                    dates['MFG'] = exp_date
                    dates['EXP'] = mfg_date
                else:
                    dates['MFG'] = mfg_date
                    dates['EXP'] = exp_date
        elif len(all_dates) == 1:
            dates['EXP'] = parse_date(all_dates[0])
    
    # Ensure EXP is always present if any date is found
    if 'EXP' not in dates and re.findall(date_pattern, extracted_text):
        all_dates = re.findall(date_pattern, extracted_text)
        dates['EXP'] = parse_date(all_dates[-1])  # Last date as fallback EXP
    
    return dates


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "OCR Date Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "/upload": "POST - Upload an image to extract dates",
            "/docs": "GET - API documentation"
        }
    }


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image and extract manufacturing and expiry dates.
    
    Args:
        file: Image file (jpg, jpeg, png, etc.)
    
    Returns:
        JSON response with extracted dates (MFG and/or EXP)
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Could not decode image. Please ensure the file is a valid image."
            )
        
        # Extract dates
        dates = extract_dates_from_image(image)
        print(dates)
        
        status = True if dates else False
        # Prepare response
        response = {
            "filename": file.filename,
            "status": status,
            "dates": dates
        }
        
        return JSONResponse(content=response)
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)