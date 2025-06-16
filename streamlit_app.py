import streamlit as st
import cv2
import pytesseract
import numpy as np
import pandas as pd
from PIL import Image
import io

st.title("Kenya Forest Service Image Table Extractor (Blue Numbers Only)")

uploaded_file = st.file_uploader("Upload table image", type=['png', 'jpg', 'jpeg'])

# Function to extract only blue numbers using color mask
def extract_blue_numbers(image):
    # Convert image to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)

    # Define blue color range (you may adjust these values based on your images)
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Apply mask to get blue regions
    blue_only = cv2.bitwise_and(image_cv, image_cv, mask=mask)
    
    # Convert masked image to grayscale for OCR
    gray = cv2.cvtColor(blue_only, cv2.COLOR_BGR2GRAY)
    
    # OCR configuration: digits only
    config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(gray, config=config)
    
    return text

# Function to parse OCR text into 10x19 table
def parse_to_table(text):
    lines = text.split('\n')
    table = []
    
    for line in lines:
        numbers = [int(num) for num in line.split() if num.isdigit()]
        if numbers:
            table.append(numbers)

    # Handle resizing to exactly 10x19 (if OCR output is messy)
    while len(table) < 10:
        table.append([])
    for i in range(10):
        if len(table[i]) < 19:
            table[i] += [''] * (19 - len(table[i]))
        table[i] = table[i][:19]
    
    return pd.DataFrame(table, columns=[f'Col {i+1}' for i in range(19)], index=[f'Row {i+1}' for i in range(10)])

# Main logic
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    st.write("Extracting blue numbers...")
    extracted_text = extract_blue_numbers(image)
    st.text(extracted_text)

    table_df = parse_to_table(extracted_text)
    st.write("Parsed Table:")
    st.dataframe(table_df)

    csv = table_df.to_csv().encode('utf-8')
    st.download_button("Download as CSV", data=csv, file_name="extracted_table.csv", mime="text/csv")
