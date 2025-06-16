import streamlit as st
import pdfplumber
import docx
import pandas as pd
import re
import io

st.title("Kenya Forest Service Table Extractor")

# Allow upload of PDF or DOCX files
uploaded_file = st.file_uploader("Upload your document (.pdf or .docx)", type=["pdf", "docx"])

# Helper function to extract numbers
def extract_numbers(text):
    if text:
        numbers = re.findall(r'\d+', text)
        return [int(num) for num in numbers]
    else:
        return []

# Function to parse DOCX files
def parse_docx(file):
    doc = docx.Document(file)
    data = []
    for table in doc.tables:
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                numbers = extract_numbers(cell.text)
                row_data.append(numbers)
            data.append(row_data)
    return data

# Function to parse PDF files
def parse_pdf(file):
    data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_data = []
                    for cell in row:
                        numbers = extract_numbers(cell)
                        row_data.append(numbers)
                    data.append(row_data)
    return data

if uploaded_file:
    # Determine file type
    if uploaded_file.name.endswith('.docx'):
        data = parse_docx(uploaded_file)
    elif uploaded_file.name.endswith('.pdf'):
        file_bytes = io.BytesIO(uploaded_file.read())
        data = parse_pdf(file_bytes)
    else:
        st.error("Unsupported file type.")
        st.stop()

    # Flatten data for display
    flat_data = []
    for row in data:
        flat_row = []
        for cell in row:
            flat_row.append(",".join(map(str, cell)))
        flat_data.append(flat_row)

    # Convert to DataFrame
    df = pd.DataFrame(flat_data)

    st.write("Extracted Table Data:")
    st.dataframe(df)

    # CSV download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "extracted_data.csv", "text/csv")

