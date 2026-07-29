from pypdf import PdfReader

# Function to extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)

    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            text = text + page_text + "\n"

    return text