import streamlit as st
from PIL import Image
import numpy as np
import io
import random

# Configurazione pagina
st.set_page_config(page_title="GlitchLabLoop507", layout="centered")
st.title("🎛️ GlitchLabLoop507")
st.write("Carica una foto e genera 3 versioni glitchate: VHS, Distruttivo e Random!")

# Caricamento immagine
uploaded_file = st.file_uploader("📷 Carica un'immagine", type=["jpg", "jpeg", "png"])

# Effetto glitch VHS
def glitch_vhs(img):
    img = img.convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape
    for y in range(0, h, 4):
        shift = int(5 * np.sin(y / 5))
        arr[y:y+1, :, :] = np.roll(arr[y:y+1, :, :], shift, axis=1)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    r = np.roll(r, 2, axis=1)
    b = np.roll(b, -2, axis=1)
    arr = np.stack([r, g, b], axis=2)
    return Image.fromarray(arr)

# Effetto glitch distruttivo
def glitch_distruttivo(img):
    img = img.convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape
    for _ in range(20):
        x = random.randint(0, w - 20)
        y = random.randint(0, h - 20)
        w_block = random.randint(5, 20)
        h_block = random.randint(5, 20)
        dx = random.randint(-10, 10)
        dy = random.randint(-10, 10)
        block = arr[y:y+h_block, x:x+w_block].copy()
        x_new = np.clip(x + dx, 0, w - w_block)
        y_new = np.clip(y + dy, 0, h - h_block)
        arr[y_new:y_new+h_block, x_new:x_new+w_block] = block
    return Image.fromarray(arr)

# Glitch casuale tra i due
def glitch_random(img):
    return random.choice([glitch_vhs, glitch_distruttivo])(img)

# Funzione per conversione in PNG
def convert_img(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# Se immagine caricata
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, caption="🖼️ Originale", use_column_width=True)

    with st.spinner("🎨 Generazione glitch in corso..."):
        vhs = glitch_vhs(img)
        distr = glitch_distruttivo(img)
        rand = glitch_random(img)

    st.subheader("🌀 Risultati glitch")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.image(vhs, caption="VHS", use_column_width=True)
        st.download_button("⬇️ Scarica VHS", convert_img(vhs), "vhs_glitch.png", "image/png")

    with col2:
        st.image(distr, caption="Distruttivo", use_column_width=True)
        st.download_button("⬇️ Scarica Distruttivo", convert_img(distr), "distruttivo_glitch.png", "image/png")

    with col3:
        st.image(rand, caption="Random", use_column_width=True)
        st.download_button("⬇️ Scarica Random", convert_img(rand), "random_glitch.png", "image/png")
