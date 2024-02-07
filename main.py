import uvicorn
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import fitz  # PyMuPDF
import json

class RequestCounterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, counter):
        super().__init__(app)
        self.counter = counter

    async def dispatch(self, request: Request, call_next):
        # Check if the request path matches one of the targeted endpoints
        if request.url.path in ["/pdf-gdrive-to-json/", "/pdf-to-json/"]:
            self.counter['count'] += 1  # Increment the counter for specific paths
        response = await call_next(request)
        return response
    
app = FastAPI()

# Define a mutable counter
request_counter = {'count': 0}

# Add the middleware to the FastAPI application, passing the counter
app.add_middleware(RequestCounterMiddleware, counter=request_counter)

class PDFRequest(BaseModel):
    url: str

def get_google_drive_direct_link(drive_url: str) -> str:
    """Convert Google Drive share link to direct download link."""
    try:
        file_id = drive_url.split('/d/')[1].split('/')[0]
        direct_download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        return direct_download_url
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google Drive URL: {e}")

def read_pdf_from_url(url: str) -> list:
    """Download and read PDF content from URL without saving locally."""
    if "drive.google.com" in url:
        url = get_google_drive_direct_link(url)
    
    response = requests.get(url, allow_redirects=True)  # Ensure redirection is followed for Google Drive links
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to download the PDF.")
    
    pdf_bytes = response.content
    text_data = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            text_data.append({'page': page_num + 1, 'text': text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF from memory: {e}")
    
    return text_data

@app.get("/")
async def root():
    return {"message": "Once you pass the PDF link through /pdf-to-json or /pdf-gdrive-to-json it should give the response back"}

@app.get("/request-count/")
async def get_request_count():
    return {"request_count": request_counter['count']}

@app.post("/pdf-to-json/")
async def pdf_to_json_endpoint(request: PDFRequest):
    """Endpoint to convert PDF content from URL to JSON without downloading the file."""
    text_data = read_pdf_from_url(request.url)
    return json.loads(json.dumps(text_data, ensure_ascii=False))

@app.post("/pdf-gdrive-to-json/")
async def pdf_gdrive_to_json_endpoint(request: PDFRequest):
    """Endpoint specifically for converting Google Drive PDF content to JSON without downloading the file."""
    # Validate if the URL is a Google Drive link
    if "drive.google.com" not in request.url:
        raise HTTPException(status_code=400, detail="URL is not a valid Google Drive link.")
    text_data = read_pdf_from_url(request.url)
    return json.loads(json.dumps(text_data, ensure_ascii=False))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
