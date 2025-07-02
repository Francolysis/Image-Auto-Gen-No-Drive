import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import time
import requests
import zipfile
from io import BytesIO
from datetime import datetime
from email.message import EmailMessage
import smtplib
import openpyxl

# Set page config
st.set_page_config(page_title="Image Generator (No Google Drive)", layout="wide")
st.title("🖼️ DALL·E 3 Image Generator")

# Load API Key
openai_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_key)

# Upload Excel File
uploaded_file = st.file_uploader("📤 Upload Excel file with prompts", type=[".xlsx"])

# Define available styles and sizes
available_styles = ["cinematic", "realistic", "cartoon", "oil painting", "photograph", "digital art", "anime", "disney", "metro", "ghibli", "illustration"]
available_sizes = {
    "Square (1:1)": "1024x1024",
    "Portrait (9:16)": "1024x1792",
    "Landscape (16:9)": "1792x1024"
}

# User selection defaults
default_style = st.selectbox("🎨 Choose default style for all prompts:", available_styles)
default_size = st.selectbox("📐 Choose default image size:", list(available_sizes.keys()))

project_name = st.text_input("📝 Enter a name for your image zip file", value="generated_images")
email_recipient = st.text_input("📧 Enter email(s) to receive ZIP (comma-separated)")
email_subject = st.text_input("✉️ Email Subject", value="Your Generated Images ZIP")
email_message = st.text_area("📝 Email Message", value="Here is your image zip file and upload log.")
include_log = st.checkbox("📎 Attach upload log CSV to email", value=True)
preview_email = st.checkbox("👁️ Preview email before sending", value=True)

def send_zip_email(recipients, zip_bytes, log_path, zip_filename, subject, message, attach_log):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]

        for email in recipients:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = email
            msg.set_content(message)

            msg.add_attachment(zip_bytes.read(), maintype='application', subtype='zip', filename=zip_filename)
            zip_bytes.seek(0)

            if attach_log:
                with open(log_path, "rb") as log_file:
                    msg.add_attachment(log_file.read(), maintype='text', subtype='csv', filename='upload_log.csv')

            if preview_email:
                st.info(f"Previewing email to: {email}\nSubject: {subject}\nMessage: {message}")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False

# Begin process if file is uploaded
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.capitalize()

        if "Prompt" not in df.columns:
            st.error("❌ Excel file must contain a 'Prompt' column.")
        else:
            df["Style"] = df.get("Style", default_style).fillna(default_style)
            df["Size"] = df.get("Size", available_sizes[default_size]).fillna(available_sizes[default_size])

            st.success(f"Loaded {len(df)} prompts.")
            st.dataframe(df)

            if st.button("🚀 Generate Images"):
                os.makedirs("generated_images", exist_ok=True)
                image_paths = []
                progress = st.progress(0)
                total = len(df)

                for i, row in df.iterrows():
                    try:
                        prompt = str(row["Prompt"]).strip()
                        style = str(row.get("Style", default_style)).strip()
                        size_label = str(row.get("Size", available_sizes[default_size])).strip()
                        size = available_sizes.get(size_label, size_label)

                        full_prompt = f"{prompt}, {style}" if style.lower() not in prompt.lower() else prompt

                        response = openai.images.generate(
                            model="dall-e-3",
                            prompt=full_prompt,
                            size=size,
                            quality="standard",
                            n=1
                        )

                        image_url = response.data[0].url
                        image_data = requests.get(image_url).content

                        filename = f"image_{i+1}.png"
                        local_path = os.path.join("generated_images", filename)
                        with open(local_path, "wb") as f:
                            f.write(image_data)

                        image_paths.append(local_path)
                    except Exception as e:
                        st.error(f"❌ Error with prompt {i+1}: {e}")

                    progress.progress((i + 1) / total)

                if image_paths:
                    st.success(f"✅ Generated {len(image_paths)} images.")
                    with st.expander("📂 Preview Images"):
                        for path in image_paths:
                            st.image(path, use_column_width=True)

    except Exception as e:
        st.error(f"❌ Failed to load Excel: {e}")
