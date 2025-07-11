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
        
        # Parametri casuali per ogni generazione
        freq1 = random.uniform(3, 12)  # Frequenza sinusoidale casuale
        freq2 = random.uniform(1, 6)   # Seconda frequenza
        intensity = random.randint(15, 45)  # Intensità distorsione
        
        # Scanlines più intense e irregolari
        for y in range(0, h, 1):
            # Distorsione sinusoidale con parametri casuali
            shift = int(intensity * np.sin(y / freq1) + (intensity//2) * np.sin(y / freq2))
            if shift != 0:
                arr[y:y+1, :, :] = np.roll(arr[y:y+1, :, :], shift, axis=1)
            
            # Aggiungi rumore su alcune righe (casualità)
            if random.random() < 0.3:  # 30% chance invece di ogni 3
                noise_intensity = random.randint(10, 30)
                noise = np.random.randint(-noise_intensity, noise_intensity, (1, w, 3))
                arr[y:y+1, :, :] = np.clip(arr[y:y+1, :, :] + noise, 0, 255)
        
        # Separazione canali colore con spostamenti casuali
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        r_shift = random.randint(15, 35)
        b_shift = random.randint(-35, -15)
        g_shift = random.randint(-10, 10)
        
        r = np.roll(r, r_shift, axis=1)
        b = np.roll(b, b_shift, axis=1)
        g = np.roll(g, g_shift, axis=0)
        
        # Saturazione colori casuale
        r_sat = random.uniform(1.0, 1.4)
        g_sat = random.uniform(0.6, 1.0)
        b_sat = random.uniform(0.9, 1.3)
        
        r = np.clip(r * r_sat, 0, 255)
        g = np.clip(g * g_sat, 0, 255)
        b = np.clip(b * b_sat, 0, 255)
        
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
        
        st.info("Debug: Applicando effetto noise casuale")
        
        # Parametri casuali per ogni generazione
        noise_type = random.choice(['bands', 'pixels', 'waves', 'mixed'])
        
        if noise_type == 'bands':
            # Rumore a bande casuali
            num_bands = random.randint(5, 20)
            for _ in range(num_bands):
                start_y = random.randint(0, h-1)
                band_height = random.randint(3, 30)
                end_y = min(start_y + band_height, h)
                
                intensity = random.randint(40, 120)
                band_noise = np.random.randint(-intensity, intensity, (end_y - start_y, w, 3))
                arr[start_y:end_y] += band_noise
        
        elif noise_type == 'pixels':
            # Rumore pixel casuali
            num_pixels = random.randint(w*h//20, w*h//5)
            for _ in range(num_pixels):
                x = random.randint(0, w-1)
                y = random.randint(0, h-1)
                pixel_noise = np.random.randint(-100, 100, 3)
                arr[y, x] += pixel_noise
        
        elif noise_type == 'waves':
            # Rumore ondulatorio
            for y in range(h):
                wave_intensity = random.randint(20, 80)
                wave_freq = random.uniform(0.1, 0.5)
                wave_shift = int(wave_intensity * np.sin(y * wave_freq))
                
                if wave_shift != 0:
                    # Applica rumore sulla riga
                    row_noise = np.random.randint(-30, 30, (1, w, 3))
                    arr[y:y+1] += row_noise
                    # Shifta la riga
                    arr[y:y+1] = np.roll(arr[y:y+1], wave_shift, axis=1)
        
        else:  # mixed
            # Combina tutti gli effetti
            # Rumore generale
            general_noise = np.random.randint(-40, 40, arr.shape)
            arr += general_noise
            
            # Alcune bande
            for _ in range(random.randint(3, 8)):
                start_y = random.randint(0, h-10)
                end_y = start_y + random.randint(2, 15)
                intensity = random.randint(50, 100)
                band_noise = np.random.randint(-intensity, intensity, (end_y - start_y, w, 3))
                arr[start_y:end_y] += band_noise
        
        # Saturazione casuale dei canali
        channel_effects = random.sample([0, 1, 2], random.randint(1, 3))
        for channel in channel_effects:
            multiplier = random.uniform(0.3, 2.0)
            arr[:,:,channel] = np.clip(arr[:,:,channel] * multiplier, 0, 255)
        
        # Clip finale
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        st.success(f"Effetto noise '{noise_type}' completato!")
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Errore nell'effetto noise: {str(e)}")
        return img

def glitch_random(img):
    """Applica un effetto glitch completamente casuale"""
    try:
        # Scelta casuale più bilanciata
        effects = [glitch_vhs, glitch_distruttivo, glitch_noise]
        
        # Possibilità di combinare due effetti
        if random.random() < 0.3:  # 30% chance di combo
            st.info("🎲 Generando combo di effetti!")
            effect1 = random.choice(effects)
            effect2 = random.choice(effects)
            
            # Applica primo effetto
            temp_img = effect1(img)
            # Applica secondo effetto con intensità ridotta
            if effect2 == glitch_noise:
                # Per il noise, riduci l'intensità nella combo
                return effect2(temp_img)
            else:
                return effect2(temp_img)
        else:
            # Singolo effetto casuale
            chosen_effect = random.choice(effects)
            effect_name = chosen_effect.__name__.replace('glitch_', '')
            st.info(f"🎲 Effetto casuale scelto: {effect_name}")
            return chosen_effect(img)
            
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
            
        # Pulsante per rigenerare con nuova casualità
        if st.button("🎲 Rigenera tutti gli effetti con nuova casualità"):
            st.rerun()
        
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
