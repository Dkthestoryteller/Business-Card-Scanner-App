import streamlit as st
import openai
import base64
import re
from PIL import Image
import os

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]


def extract_business_card_text(image):
    # Encode the image to base64
    buffered = base64.b64encode(image).decode("utf-8")

    # Use OpenAI's GPT-4 Vision model to extract text
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Extract all relevant contact details from this business card image to create a vCard."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{buffered}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content


def create_vcard_from_text(text):
    # Check if the extracted text contains vCard content
    vcard_match = re.search(r"(BEGIN:VCARD.*END:VCARD)", text, re.S)

    if vcard_match:
        vcard_content = vcard_match.group(1).strip()
    else:
        # Parse text and manually construct vCard (fallback)
        name = re.search(r"Name[:\-]?\s*(.+)", text, re.I)
        phone = re.search(r"Mobile[:\-]?\s*([\+\d\s]+)", text, re.I)
        email = re.search(r"Email[:\-]?\s*([\w\.\-]+@[\w\.\-]+)", text, re.I)
        company = re.search(r"Company[:\-]?\s*(.+)", text, re.I)

        vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{name.group(1) if name else 'Unknown'}
TEL;TYPE=CELL:{phone.group(1) if phone else ''}
EMAIL;TYPE=WORK:{email.group(1) if email else ''}
ORG:{company.group(1) if company else ''}
END:VCARD"""

    return vcard_content


def save_vcard(vcard_content, file_name):
    with open(file_name, "w", encoding="utf-8", newline="\r\n") as file:
        file.write(vcard_content)
    return file_name


# Streamlit App
st.title("Business Card Scanner")
st.write("Upload a business card image to extract details and generate a vCard.")

# File upload
uploaded_file = st.file_uploader("Upload a business card image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    try:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        with st.spinner("Extracting text..."):
            image_bytes = uploaded_file.read()
            extracted_text = extract_business_card_text(image_bytes)

        st.subheader("Extracted Details:")
        st.text(extracted_text)

        with st.spinner("Creating vCard..."):
            vcard_content = create_vcard_from_text(extracted_text)
            vcard_file = save_vcard(vcard_content, "business_contact.vcf")

        st.success("vCard created successfully!")

        # Provide download link
        with open(vcard_file, "rb") as file:
            btn = st.download_button(
                label="Download vCard",
                data=file,
                file_name="business_contact.vcf",
                mime="text/vcard"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
