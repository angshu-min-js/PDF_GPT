import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import fitz  # PyMuPDF
import json

app = FastAPI()

class URLPayload(BaseModel):
    url: str

def download_pdf_from_google_drive(url: str) -> str:
    """Download PDF from a Google Drive URL and save locally."""
    try:
        file_id = url.split('/d/')[1].split('/')[0]
        direct_download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(direct_download_url)
        filename = 'temp_gdrive.pdf'
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF from Google Drive: {e}")

def download_pdf(url: str) -> str:
    """Download PDF from URL and save locally."""
    try:
        response = requests.get(url)
        filename = 'temp.pdf'
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

def read_pdf(filename: str) -> list:
    """Read PDF content, handle PDF errors, and return text."""
    text_data = []
    try:
        doc = fitz.open(filename)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_data.append({'page': page_num + 1, 'text': text})
        return text_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {e}")
        
@app.get("/")
async def root():
    return {"message": "Once you pass the PDF link through /pdf-to-json or /pdf-gdrive-to-json it should give the response back"}

@app.post("/pdf-to-json/")
async def pdf_to_json(payload: URLPayload):
    """Endpoint to download PDF from a normal link, read content, and convert to JSON."""
    filename = download_pdf(payload.url)
    text_data = read_pdf(filename)
    return json.loads(json.dumps(text_data, ensure_ascii=False))

@app.post("/pdf-gdrive-to-json/")
async def pdf_gdrive_to_json(payload: URLPayload):
    """Endpoint to download Google Drive PDF, read content, and convert to JSON."""
    filename = download_pdf_from_google_drive(payload.url)
    text_data = read_pdf(filename)
    return json.loads(json.dumps(text_data, ensure_ascii=False))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
