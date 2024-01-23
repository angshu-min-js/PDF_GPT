from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import tempfile
import os
import PyPDF2
from fastapi.responses import JSONResponse

app = FastAPI()

class PDFRequest(BaseModel):
    link: str

@app.post("/extract_pdf_info")
async def extract_pdf_info(pdf_request: PDFRequest):
    try:
        pdf_link = pdf_request.link

        if not pdf_link:
            raise HTTPException(status_code=400, detail="PDF link is missing in the request")

        # Set a custom User-Agent header
        headers = {"User-Agent": "Your User Agent String"}

        # Fetch the PDF content from the provided link with the custom User-Agent
        response = requests.get(pdf_link, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to fetch the PDF")

        # Save the PDF content to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(response.content)
            pdf_file_path = temp_pdf.name

        # Extract text from the PDF using PyPDF2
        extracted_text = ""
        with open(pdf_file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_number in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_number]
                extracted_text += page.extract_text()

        # Clean up the temporary PDF file
        os.remove(pdf_file_path)

        # Create a JSON response with the extracted information
        response_data = {"extracted_info": extracted_text.strip()}
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
