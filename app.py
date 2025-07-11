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
    """Effetto glitch stile VHS POTENZIATO con scanlines e distorsione colore"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Scanlines più intense e irregolari
        for y in range(0, h, 1):  # Ogni riga invece di ogni 2
            # Distorsione sinusoidale più forte
            shift = int(30 * np.sin(y / 8) + 15 * np.sin(y / 3))
            if shift != 0:
                arr[y:y+1, :, :] = np.roll(arr[y:y+1, :, :], shift, axis=1)
            
            # Aggiungi rumore su alcune righe
            if y % 3 == 0:
                noise = np.random.randint(-20, 20, (1, w, 3))
                arr[y:y+1, :, :] = np.clip(arr[y:y+1, :, :] + noise, 0, 255)
        
        # Separazione canali colore più estrema
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        r = np.roll(r, 25, axis=1)  # Spostamento maggiore
        b = np.roll(b, -25, axis=1)
        g = np.roll(g, 5, axis=0)   # Spostamento verticale del verde
        
        # Saturazione colori per effetto VHS
        r = np.clip(r * 1.2, 0, 255)
        g = np.clip(g * 0.8, 0, 255)
        b = np.clip(b * 1.1, 0, 255)
        
        arr = np.stack([r, g, b], axis=2)
        
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto VHS: {str(e)}")
        return img

def glitch_distruttivo(img):
    """Effetto glitch distruttivo POTENZIATO con spostamento di blocchi"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        st.info(f"Debug: Dimensioni immagine {w}x{h}")
        
        # Riduci requisiti minimi
        if w < 60 or h < 60:
            st.warning("Immagine troppo piccola per l'effetto distruttivo")
            return img
        
        # Aumenta numero di blocchi e dimensioni
        num_blocks = min(120, w * h // 1000)  # Più blocchi per immagini grandi
        st.info(f"Debug: Generando {num_blocks} blocchi")
        
        for i in range(num_blocks):
            # Blocchi di dimensioni variabili
            max_block_w = min(80, w // 3)
            max_block_h = min(80, h // 3)
            
            w_block = random.randint(10, max_block_w)
            h_block = random.randint(10, max_block_h)
            
            # Posizione iniziale
            x = random.randint(0, max(0, w - w_block))
            y = random.randint(0, max(0, h - h_block))
            
            # Spostamento più estremo
            dx = random.randint(-w//4, w//4)
            dy = random.randint(-h//4, h//4)
            
            # Copia il blocco
            if y + h_block <= h and x + w_block <= w:
                block = arr[y:y+h_block, x:x+w_block].copy()
                
                # Calcola nuova posizione
                x_new = np.clip(x + dx, 0, w - w_block)
                y_new = np.clip(y + dy, 0, h - h_block)
                
                # Applica distorsione al blocco
                if random.random() < 0.3:  # 30% chance
                    block = np.roll(block, random.randint(-10, 10), axis=1)
                
                # Posiziona il blocco
                arr[y_new:y_new+h_block, x_new:x_new+w_block] = block
        
        st.success("Effetto distruttivo completato!")
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto distruttivo: {str(e)}")
        return img

def glitch_noise(img):
    """Effetto glitch con rumore casuale POTENZIATO"""
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int16)
        h, w, _ = arr.shape
        
        st.info("Debug: Applicando effetto noise")
        
        # Rumore più intenso e variabile
        noise_intensity = random.randint(30, 80)
        noise = np.random.randint(-noise_intensity, noise_intensity, arr.shape)
        
        # Aggiungi rumore a bande
        for i in range(0, h, random.randint(10, 50)):
            end_i = min(i + random.randint(5, 20), h)
            band_noise = np.random.randint(-100, 100, (end_i - i, w, 3))
            arr[i:end_i] += band_noise
        
        # Aggiungi rumore generale
        arr += noise
        
        # Saturazione casuale dei canali
        if random.random() < 0.5:
            arr[:,:,0] = np.clip(arr[:,:,0] * 1.3, 0, 255)  # Rosso
        if random.random() < 0.5:
            arr[:,:,1] = np.clip(arr[:,:,1] * 0.7, 0, 255)  # Verde
        if random.random() < 0.5:
            arr[:,:,2] = np.clip(arr[:,:,2] * 1.2, 0, 255)  # Blu
        
        # Clip finale
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        st.success("Effetto noise completato!")
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
            st.write("🔄 Generando effetto VHS...")
            vhs = glitch_vhs(img)
            
            st.write("🔄 Generando effetto Distruttivo...")
            distr = glitch_distruttivo(img)
            
            st.write("🔄 Generando effetto Random...")
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
