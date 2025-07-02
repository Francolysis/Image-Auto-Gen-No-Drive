# AI Image Generator (No Google Drive)

This Streamlit app generates images using OpenAI's DALL·E 3 from prompts in an Excel file.

## Features
- Upload Excel (.xlsx) with prompts, styles, and sizes
- Auto-generate images with size presets or custom resolution
- Download all generated images as a zip
- Automatically send zip via email

## Setup
1. Clone repo
2. Create `secrets.toml` file (see example)
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run locally:
```bash
streamlit run app.py
```
