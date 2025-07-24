import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import io
import random

# Configurazione della pagina
st.set_page_config(page_title="GlitchLabLoop507", layout="centered")

st.title("🔥️ GlitchLabLoop507")
st.write("Carica una foto e genera 3 versioni glitchate: VHS, Distruttivo e Random!")

# File uploader
uploaded_file = st.file_uploader("📁 Carica un'immagine", type=["jpg", "jpeg", "png"])

def glitch_vhs(img, intensity=1.0, scanline_freq=1.0, color_shift=1.0):
    """Effetto glitch stile VHS POTENZIATO con controlli personalizzabili"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Parametri basati sui controlli utente
        base_intensity = int(15 + (30 * intensity))  # 15-45
        freq1 = 3 + (9 * scanline_freq)  # 3-12
        freq2 = 1 + (5 * scanline_freq)  # 1-6
        
        # Scanlines più intense e irregolari
        for y in range(0, h, 1):
            # Distorsione sinusoidale con parametri controllabili
            shift = int(base_intensity * np.sin(y / freq1) + (base_intensity//2) * np.sin(y / freq2))
            if shift != 0:
                arr[y:y+1, :, :] = np.roll(arr[y:y+1, :, :], shift, axis=1)
            
            # Aggiungi rumore su alcune righe
            if random.random() < (0.2 + 0.2 * intensity):  # 20-40% chance
                noise_intensity = int(10 + (20 * intensity))
                noise = np.random.randint(-noise_intensity, noise_intensity, (1, w, 3))
                arr[y:y+1, :, :] = np.clip(arr[y:y+1, :, :] + noise, 0, 255)
        
        # Separazione canali colore controllabile
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
        shift_multiplier = color_shift
        r_shift = int(15 * shift_multiplier + random.randint(0, int(20 * shift_multiplier)))
        b_shift = int(-15 * shift_multiplier + random.randint(int(-20 * shift_multiplier), 0))
        g_shift = int(random.randint(int(-10 * shift_multiplier), int(10 * shift_multiplier)))
        
        r = np.roll(r, r_shift, axis=1)
        b = np.roll(b, b_shift, axis=1)
        g = np.roll(g, g_shift, axis=0)
        
        # Saturazione colori controllabile
        sat_range = 0.3 * color_shift
        r_sat = 1.0 + random.uniform(0, sat_range)
        g_sat = 1.0 - random.uniform(0, sat_range * 0.8)
        b_sat = 1.0 + random.uniform(-sat_range * 0.5, sat_range)
        
        r = np.clip(r * r_sat, 0, 255)
        g = np.clip(g * g_sat, 0, 255)
        b = np.clip(b * b_sat, 0, 255)
        
        arr = np.stack([r, g, b], axis=2)
        
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto VHS: {str(e)}")
        return img

def glitch_distruttivo(img, block_size=1.0, num_blocks=1.0, displacement=1.0):
    """Effetto glitch distruttivo POTENZIATO con controlli personalizzabili"""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Riduci requisiti minimi
        if w < 60 or h < 60:
            st.warning("Immagine troppo piccola per l'effetto distruttivo")
            return img
        
        # Numero di blocchi controllabile
        base_blocks = min(80, w * h // 1500)
        total_blocks = int(base_blocks * (0.5 + 1.5 * num_blocks))  # 0.5x - 2x
        
        for i in range(total_blocks):
            # Dimensioni blocchi controllabili
            base_max_w = min(60, w // 4)
            base_max_h = min(60, h // 4)
            
            max_block_w = int(base_max_w * (0.3 + 1.4 * block_size))  # 0.3x - 1.7x
            max_block_h = int(base_max_h * (0.3 + 1.4 * block_size))
            
            w_block = random.randint(max(5, max_block_w//3), max_block_w)
            h_block = random.randint(max(5, max_block_h//3), max_block_h)
            
            # Posizione iniziale
            x = random.randint(0, max(0, w - w_block))
            y = random.randint(0, max(0, h - h_block))
            
            # Spostamento controllabile
            base_displacement = min(w//6, h//6)
            max_displacement = int(base_displacement * displacement)
            dx = random.randint(-max_displacement, max_displacement)
            dy = random.randint(-max_displacement, max_displacement)
            
            # Copia il blocco
            if y + h_block <= h and x + w_block <= w:
                block = arr[y:y+h_block, x:x+w_block].copy()
                
                # Calcola nuova posizione
                x_new = np.clip(x + dx, 0, w - w_block)
                y_new = np.clip(y + dy, 0, h - h_block)
                
                # Applica distorsione al blocco (più probabile con displacement alto)
                if random.random() < (0.1 + 0.4 * displacement):
                    distortion = int(5 + 10 * displacement)
                    block = np.roll(block, random.randint(-distortion, distortion), axis=1)
                
                # Posiziona il blocco
                arr[y_new:y_new+h_block, x_new:x_new+w_block] = block
        
        return Image.fromarray(arr.astype(np.uint8))
    except Exception as e:
        st.error(f"Errore nell'effetto distruttivo: {str(e)}")
        return img

def glitch_noise(img, noise_intensity=1.0, coverage=1.0, chaos=1.0):
    """Effetto glitch con rumore casuale POTENZIATO e controllabile"""
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int16)
        h, w, _ = arr.shape
        
        # Parametri controllabili
        base_intensity = int(30 + (90 * noise_intensity))
        coverage_factor = 0.3 + (0.7 * coverage)  # Quanto dell'immagine toccare
        
        # Tipo di noise basato sul chaos
        if chaos < 0.3:
            noise_type = 'bands'
        elif chaos < 0.6:
            noise_type = 'pixels'
        elif chaos < 0.8:
            noise_type = 'waves'
        else:
            noise_type = 'mixed'
        
        if noise_type == 'bands':
            # Rumore a bande
            num_bands = int(5 + (15 * coverage))
            for _ in range(num_bands):
                start_y = random.randint(0, h-1)
                band_height = int(3 + (27 * noise_intensity))
                end_y = min(start_y + band_height, h)
                
                band_noise = np.random.randint(-base_intensity, base_intensity, (end_y - start_y, w, 3))
                arr[start_y:end_y] += band_noise
        
        elif noise_type == 'pixels':
            # Rumore pixel casuali
            base_pixels = w * h // 30
            num_pixels = int(base_pixels * coverage * (1 + chaos))
            for _ in range(num_pixels):
                x = random.randint(0, w-1)
                y = random.randint(0, h-1)
                pixel_noise = np.random.randint(-base_intensity, base_intensity, 3)
                arr[y, x] += pixel_noise
        
        elif noise_type == 'waves':
            # Rumore ondulatorio
            wave_coverage = int(h * coverage_factor)
            for y in range(0, h, max(1, h//wave_coverage)):
                wave_intensity = int(base_intensity * 0.7)
                wave_freq = 0.1 + (0.4 * chaos)
                wave_shift = int(wave_intensity * np.sin(y * wave_freq))
                
                if wave_shift != 0:
                    # Applica rumore sulla riga
                    row_noise = np.random.randint(-base_intensity//2, base_intensity//2, (1, w, 3))
                    arr[y:y+1] += row_noise
                    # Shifta la riga
                    arr[y:y+1] = np.roll(arr[y:y+1], wave_shift, axis=1)
        
        else:  # mixed
            # Combina tutti gli effetti
            # Rumore generale
            general_intensity = int(base_intensity * 0.5)
            general_noise = np.random.randint(-general_intensity, general_intensity, arr.shape)
            arr += general_noise
            
            # Alcune bande
            num_bands = int(3 + (5 * coverage))
            for _ in range(num_bands):
                start_y = random.randint(0, h-10)
                end_y = start_y + random.randint(2, int(10 + 5 * noise_intensity))
                band_noise = np.random.randint(-base_intensity, base_intensity, (end_y - start_y, w, 3))
                arr[start_y:end_y] += band_noise
        
        # Saturazione casuale dei canali (controllata dal chaos)
        if chaos > 0.4:
            num_channels = int(1 + (2 * chaos))
            channel_effects = random.sample([0, 1, 2], min(3, num_channels))
            for channel in channel_effects:
                multiplier = 0.5 + (1.5 * chaos)
                multiplier = random.uniform(1/multiplier, multiplier)
                arr[:,:,channel] = np.clip(arr[:,:,channel] * multiplier, 0, 255)
        
        # Clip finale
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Errore nell'effetto noise: {str(e)}")
        return img

def glitch_random(img, randomness=1.0):
    """Applica un effetto glitch completamente casuale"""
    try:
        # Scelta casuale più bilanciata
        effects = [
            (glitch_vhs, random.random(), random.random(), random.random()),
            (glitch_distruttivo, random.random(), random.random(), random.random()),
            (glitch_noise, random.random(), random.random(), random.random())
        ]
        
        # Possibilità di combinare due effetti basata sul randomness
        combo_chance = 0.1 + (0.4 * randomness)  # 10-50% chance
        if random.random() < combo_chance:
            st.info("🎲 Generando combo di effetti!")
            effect1, p1, p2, p3 = random.choice(effects)
            effect2, p4, p5, p6 = random.choice(effects)
            
            # Applica primo effetto
            temp_img = effect1(img, p1, p2, p3)
            # Applica secondo effetto con parametri ridotti per non sovracaricare
            return effect2(temp_img, p4 * 0.7, p5 * 0.7, p6 * 0.7)
        else:
            # Singolo effetto casuale
            chosen_effect, p1, p2, p3 = random.choice(effects)
            # Amplifica i parametri casuali in base al randomness
            p1 = min(1.0, p1 * (0.5 + randomness))
            p2 = min(1.0, p2 * (0.5 + randomness))
            p3 = min(1.0, p3 * (0.5 + randomness))
            
            effect_name = chosen_effect.__name__.replace('glitch_', '')
            st.info(f"🎲 Effetto casuale scelto: {effect_name}")
            return chosen_effect(img, p1, p2, p3)
    
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
        
        # --- CONTROLLI EFFETTI ---
        st.markdown("### 🎛️ Controlli Effetti")
        
        # Organize controls in expandable sections
        with st.expander("📺 Controlli VHS", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                vhs_intensity = st.slider("Intensità Distorsione", 0.0, 2.0, 1.0, 0.1, key="vhs_int")
            with col2:
                vhs_scanlines = st.slider("Frequenza Scanlines", 0.0, 2.0, 1.0, 0.1, key="vhs_scan")
            with col3:
                vhs_colors = st.slider("Separazione Colori", 0.0, 2.0, 1.0, 0.1, key="vhs_col")
        
        with st.expander("💥 Controlli Distruttivo", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                dest_blocks = st.slider("Dimensione Blocchi", 0.0, 2.0, 1.0, 0.1, key="dest_size")
            with col2:
                dest_number = st.slider("Numero Blocchi", 0.0, 2.0, 1.0, 0.1, key="dest_num")
            with col3:
                dest_displacement = st.slider("Spostamento", 0.0, 2.0, 1.0, 0.1, key="dest_disp")
        
        with st.expander("🌀 Controlli Noise", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                noise_intensity = st.slider("Intensità Rumore", 0.0, 2.0, 1.0, 0.1, key="noise_int")
            with col2:
                noise_coverage = st.slider("Copertura", 0.0, 2.0, 1.0, 0.1, key="noise_cov")
            with col3:
                noise_chaos = st.slider("Caos", 0.0, 1.0, 0.5, 0.1, key="noise_chaos")
        
        with st.expander("🎲 Controlli Random", expanded=False):
            random_level = st.slider("Livello Casualità", 0.0, 2.0, 1.0, 0.1, key="random_lev")
        
        # Genera gli effetti glitch
        with st.spinner("🔥 Generazione glitch in corso..."):
            st.write("📺 Generando effetto VHS...")
            vhs = glitch_vhs(img, vhs_intensity, vhs_scanlines, vhs_colors)
            
            st.write("💥 Generando effetto Distruttivo...")
            distr = glitch_distruttivo(img, dest_blocks, dest_number, dest_displacement)
            
            st.write("🎲 Generando effetto Random...")
            rand = glitch_random(img, random_level)
        
        # Pulsante per rigenerare con nuova casualità
        if st.button("🔄 Rigenera tutti gli effetti con nuova casualità"):
            st.rerun()
        
        # Mostra i risultati
        st.subheader("🔥 Risultati glitch")
        
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
    st.info("📁 Carica un'immagine per iniziare!")

# Footer
st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** - Crea effetti glitch unici per le tue foto!")
st.markdown("*💡 Usa i controlli per personalizzare ogni effetto secondo i tuoi gusti!*")
