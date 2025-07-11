import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import io
import random

# Configurazione della pagina
st.set_page_config(page_title="GlitchLabLoop507", layout="centered")

st.title("🎛️ GlitchLabLoop507")
st.write("Carica una foto e genera 3 versioni glitchate: VHS, Distruttivo e Random!")

# File uploader
uploaded_file = st.file_uploader("📷 Carica un'immagine", type=["jpg", "jpeg", "png"])

def glitch_vhs(img):
    """Effetto glitch stile VHS con scanlines e distorsione colore"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Aggiungi scanlines con distorsione sinusoidale
        for y in range(0, h, 2):
            shift = int(15 * np.sin(y / 4))
            if shift != 0:
                arr[y:y+1, :, :] = np.roll(arr[y:y+1, :, :], shift, axis=1)
        
        # Separazione canali colore (aberrazione cromatica)
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        r = np.roll(r, 10, axis=1)
        b = np.roll(b, -10, axis=1)
        arr = np.stack([r, g, b], axis=2)
        
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto VHS: {str(e)}")
        return img

def glitch_distruttivo(img):
    """Effetto glitch distruttivo con spostamento di blocchi"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Assicurati che le dimensioni siano sufficienti
        if w < 100 or h < 100:
            st.warning("Immagine troppo piccola per l'effetto distruttivo")
            return img
        
        # Crea blocchi distorti
        for _ in range(60):
            x = random.randint(0, max(0, w - 50))
            y = random.randint(0, max(0, h - 50))
            w_block = random.randint(20, min(60, w - x))
            h_block = random.randint(20, min(60, h - y))
            
            if w_block > 0 and h_block > 0:
                dx = random.randint(-30, 30)
                dy = random.randint(-30, 30)
                
                # Copia il blocco
                block = arr[y:y+h_block, x:x+w_block].copy()
                
                # Calcola nuova posizione
                x_new = np.clip(x + dx, 0, w - w_block)
                y_new = np.clip(y + dy, 0, h - h_block)
                
                # Posiziona il blocco
                arr[y_new:y_new+h_block, x_new:x_new+w_block] = block
        
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto distruttivo: {str(e)}")
        return img

def glitch_noise(img):
    """Effetto glitch con rumore casuale"""
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int16)
        
        # Genera rumore
        noise = np.random.randint(-50, 50, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Errore nell'effetto noise: {str(e)}")
        return img

def glitch_random(img):
    """Applica un effetto glitch casuale"""
    try:
        effects = [glitch_vhs, glitch_distruttivo, glitch_noise]
        return random.choice(effects)(img)
    except Exception as e:
        st.error(f"Errore nell'effetto random: {str(e)}")
        return img

def convert_img(img):
    """Converte l'immagine in bytes per il download"""
    try:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"Errore nella conversione: {str(e)}")
        return None

# Logica principale
if uploaded_file is not None:
    try:
        # Carica l'immagine
        img = Image.open(uploaded_file).convert("RGB")
        
        # Mostra l'immagine originale
        st.image(img, caption="🖼️ Originale", use_container_width=True)
        
        # Informazioni sull'immagine
        st.info(f"Dimensioni: {img.size[0]}x{img.size[1]} pixel")
        
        # Genera gli effetti glitch
        with st.spinner("🎨 Generazione glitch in corso..."):
            vhs = glitch_vhs(img)
            distr = glitch_distruttivo(img)
            rand = glitch_random(img)
        
        # Mostra i risultati
        st.subheader("🌀 Risultati glitch")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.image(vhs, caption="VHS", use_container_width=True)
            vhs_data = convert_img(vhs)
            if vhs_data:
                st.download_button(
                    "⬇️ Scarica VHS", 
                    vhs_data, 
                    "vhs_glitch.png", 
                    "image/png"
                )
        
        with col2:
            st.image(distr, caption="Distruttivo", use_container_width=True)
            distr_data = convert_img(distr)
            if distr_data:
                st.download_button(
                    "⬇️ Scarica Distruttivo", 
                    distr_data, 
                    "distruttivo_glitch.png", 
                    "image/png"
                )
        
        with col3:
            st.image(rand, caption="Random", use_container_width=True)
            rand_data = convert_img(rand)
            if rand_data:
                st.download_button(
                    "⬇️ Scarica Random", 
                    rand_data, 
                    "random_glitch.png", 
                    "image/png"
                )
                
    except Exception as e:
        st.error(f"Errore nel caricamento dell'immagine: {str(e)}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")

else:
    st.info("👆 Carica un'immagine per iniziare!")
    
# Footer
st.markdown("---")
st.markdown("🎨 **GlitchLabLoop507** - Crea effetti glitch unici per le tue foto!")
