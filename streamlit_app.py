import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import json

st.title("Kenya Forest Service Image Table Extractor (Blue Numbers Only)")

# Your OCR.Space API Key here (replace this with your actual key)
OCR_SPACE_API_KEY = "fn4XIYfIuQ8gG4DAYGaLxgMpBIUpYYES"

# Function to call OCR.Space API
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
                      data=payload,
                      )
    return r.json()

# File uploader
uploaded_file = st.file_uploader("Upload table image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Extracting text via OCR..."):
        result = ocr_space_image(uploaded_file)

    try:
        parsed_results = result['ParsedResults'][0]['ParsedText']
        st.subheader("Raw OCR Extracted Text:")
        st.text(parsed_results)

        # Now parse the text into table (very basic)
        rows = parsed_results.split('\n')
        data = []

        for row in rows:
            # Extract only numbers
            numbers = [int(n) for n in row.split() if n.isdigit()]
            if numbers:
                data.append(numbers)

        # Make sure data is always 10 rows x 19 columns
        while len(data) < 10:
            data.append([])
        for i in range(10):
            while len(data[i]) < 19:
                data[i].append("")

        df = pd.DataFrame(data, columns=[f"Col {i+1}" for i in range(19)])
        st.subheader("Parsed Table:")
        st.dataframe(df)

        # Download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", csv, "extracted_table.csv", "text/csv")

    except Exception as e:
        st.error("OCR failed. Please check your image quality or API key.")
        st.text(result)
