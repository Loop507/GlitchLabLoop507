import streamlit as st
from PIL import Image, ImageOps
import io

st.title("Test Caricamento Immagine e Inversione Colori")

uploaded_file = st.file_uploader("Carica un'immagine", type=["jpg", "jpeg", "png"])

def convert_img(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

if uploaded_file is not None:
    try:
        img = Image.open(uploaded_file)
        st.write(f"✅ Immagine caricata con successo!")
        st.write(f"📏 Dimensioni: {img.size}")
        st.write(f"🎨 Modalità colore: {img.mode}")
        img = img.convert("RGB")

        st.image(img, caption="Originale", use_container_width=True)

        inverted = ImageOps.invert(img)
        st.image(inverted, caption="Invertito", use_container_width=True)

        st.download_button("Scarica immagine invertita", convert_img(inverted), "invertita.png", "image/png")

    except Exception as e:
        st.error(f"❌ Errore nel caricamento o elaborazione immagine: {e}")
else:
    st.info("Carica un file immagine per iniziare.")
