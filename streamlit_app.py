import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json
import os
from pdf2image import convert_from_bytes
from docx import Document
from io import BytesIO

st.title("Kenya Forest Service OCR Table Extractor")

OCR_SPACE_API_KEY = "fn4XIYfIuQ8gG4DAYGaLxgMpBIUpYYES"

def ocr_space_image(file, overlay=False, api_key=OCR_SPACE_API_KEY, language='eng'):
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
        'OCREngine': 2
    }
    files = {'file': file}
    r = requests.post('https://api.ocr.space/parse/image',
                      files=files,
                      data=payload)
    return r.json()

def render_docx_to_image(doc_bytes):
    doc = Document(io.BytesIO(doc_bytes))
    text = "\n".join([p.text for p in doc.paragraphs])
    # Render text into image (simplified method)
    from PIL import ImageDraw, ImageFont
    img = Image.new('RGB', (1000, 800), color='white')
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((10, 10), text, fill=(0, 0, 0), font=font)
    return img

uploaded_file = st.file_uploader("Upload table file (Image / PDF / DOCX)", type=['jpg', 'jpeg', 'png', 'pdf', 'docx'])

if uploaded_file:
    file_type = uploaded_file.type

    with st.spinner("Preparing file for OCR..."):
        # Convert to image if needed
        if file_type == 'application/pdf':
            images = convert_from_bytes(uploaded_file.read(), first_page=1, last_page=1)
            image = images[0]
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            image = render_docx_to_image(uploaded_file.read())
        else:
            image = Image.open(uploaded_file)

    st.image(image, caption="Preview", use_container_width=True)

    with st.spinner("Extracting text via OCR..."):
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        result = ocr_space_image(img_bytes)

    try:
        parsed_text = result['ParsedResults'][0]['ParsedText']
        st.subheader("Raw OCR Text:")
        st.text(parsed_text)

        rows = parsed_text.split('\n')
        data = []
        for row in rows:
            numbers = [int(n) for n in row.split() if n.isdigit()]
            if numbers:
                data.append(numbers)

        while len(data) < 10:
            data.append([])
        for i in range(10):
            while len(data[i]) < 19:
                data[i].append("")

        df = pd.DataFrame(data, columns=[f"Col {i+1}" for i in range(19)])
        st.subheader("Parsed Table:")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", csv, "extracted_table.csv", "text/csv")

    except Exception as e:
        st.error("OCR failed. Check file content or API key.")
        st.text(result)
