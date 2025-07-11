import streamlit as st
from PIL import Image, ImageOps
import io

st.title("Test Glitch - Inverti colori")

uploaded_file = st.file_uploader("Carica un'immagine", type=["jpg", "jpeg", "png"])

def convert_img(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

if uploaded_file is not None:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, caption="Originale", use_container_width=True)

    # Effetto semplice: inverti colori
    inverted = ImageOps.invert(img)
    st.image(inverted, caption="Invertito", use_container_width=True)

    st.download_button("Scarica invertito", convert_img(inverted), "invertito.png", "image/png")
