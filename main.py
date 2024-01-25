import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import tempfile
import os
import PyPDF2
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Once you pass the PDF link through /extract_pdf_info it should give the response back"}

class PDFRequest(BaseModel):
    link: str

class PDFResponse(BaseModel):
    extracted_info: str

def reset_eof_of_pdf_return_stream(pdf_stream_in):
    # Convert to bytes if it's a list
    if isinstance(pdf_stream_in, list):
        pdf_stream_in = b'\n'.join(pdf_stream_in)

    # Check if EOF marker exists; if not, append it
    if b'%%EOF' not in pdf_stream_in:
        pdf_stream_in += b'\n%%EOF'

    return pdf_stream_in

@app.post("/extract_pdf_info", response_model=PDFResponse, operation_id="extractPdfInfo")
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

        # Reset the EOF marker in the PDF stream
        corrected_pdf_stream = reset_eof_of_pdf_return_stream(response.content)

        # Create a temporary PDF file with the corrected content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(corrected_pdf_stream)
            pdf_file_path = temp_pdf.name

        # Extract text from the corrected PDF using PyPDF2
        extracted_text = ""
        try:
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_number in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_number]
                    extracted_text += page.extract_text()
        except Exception as e:
            extracted_text = f"Error extracting text: {str(e)}"

        # Clean up the temporary PDF file
        os.remove(pdf_file_path)

        # Create a JSON response with the extracted information
        response_data = PDFResponse(extracted_info=extracted_text.strip())
        return JSONResponse(content=response_data.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
 
class LinkRequest(BaseModel):
    link: str

class ContentResponse(BaseModel):
    content: str

@app.post("/read_link_content", response_model=ContentResponse, operation_id="readLinkContent")
async def read_link_content(link_request: LinkRequest):
    try:
        link = link_request.link

        if not link:
            raise HTTPException(status_code=400, detail="Link is missing in the request")

        # Set a custom User-Agent header
        headers = {"User-Agent": "Your User Agent String"}

        # Fetch the content from the provided link with the custom User-Agent
        response = requests.get(link, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Unable to fetch the content")

        # Extract the content from the response
        content = response.text

        # Create a Pydantic model instance for the response
        response_data = ContentResponse(content=content)
        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
