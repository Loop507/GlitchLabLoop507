import streamlit as st
from PIL import Image
import numpy as np
import io
import random
from datetime import datetime

# ─── Configurazione pagina ────────────────────────────────────────────────────
st.set_page_config(page_title="GlitchLabLoop507", layout="centered")

st.title("🔥 GlitchLabLoop507")
st.write("Carica una foto e genera 3 versioni glitchate: VHS, Distruttivo e Noise!")


# ─── Effetti glitch (vettorizzati) ────────────────────────────────────────────

def glitch_vhs(img, intensity=1.0, scanline_freq=1.0, color_shift=1.0):
    """Effetto glitch stile VHS — completamente vettorizzato con NumPy."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape

        # ── Distorsione scanline vettorizzata ──
        base_intensity = 15 + 30 * intensity          # 15–45 px
        freq1 = 3 + 9 * scanline_freq                 # 3–12
        freq2 = 1 + 5 * scanline_freq                 # 1–6
        ys = np.arange(h)
        shifts = (
            base_intensity * np.sin(ys / freq1)
            + (base_intensity / 2) * np.sin(ys / freq2)
        ).astype(int)

        # Applica shift riga per riga con np.roll vettorizzato
        for y_idx in range(h):
            s = int(shifts[y_idx])
            if s:
                arr[y_idx] = np.roll(arr[y_idx], s, axis=0)

        # ── Rumore su righe casuali (vettorizzato) ──
        noise_prob = 0.2 + 0.2 * intensity
        noise_mask = np.random.random(h) < noise_prob
        noise_intensity = int(10 + 20 * intensity)
        noise = np.random.randint(
            -noise_intensity, noise_intensity,
            (h, w, 3), dtype=np.int16
        )
        arr[noise_mask] = np.clip(
            arr[noise_mask] + noise[noise_mask], 0, 255
        )

        # ── Separazione canali colore ──
        sm = color_shift
        r_shift = int(15 * sm + random.randint(0, max(1, int(20 * sm))))
        b_shift = int(-15 * sm + random.randint(max(-1, int(-20 * sm)), 0))
        g_shift = int(random.randint(max(-1, int(-10 * sm)), max(1, int(10 * sm))))

        r = np.roll(arr[:, :, 0], r_shift, axis=1)
        g = np.roll(arr[:, :, 1], g_shift, axis=0)
        b = np.roll(arr[:, :, 2], b_shift, axis=1)

        sat_range = 0.3 * sm
        r = np.clip(r * (1.0 + random.uniform(0, sat_range)), 0, 255)
        g = np.clip(g * (1.0 - random.uniform(0, sat_range * 0.8)), 0, 255)
        b = np.clip(b * (1.0 + random.uniform(-sat_range * 0.5, sat_range)), 0, 255)

        result = np.stack([r, g, b], axis=2).astype(np.uint8)
        return Image.fromarray(result)
    except Exception as e:
        st.error(f"Errore nell'effetto VHS: {e}")
        return img


def glitch_distruttivo(img, block_size=1.0, num_blocks=1.0, displacement=1.0):
    """Effetto glitch distruttivo con spostamento di blocchi."""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape

        if w < 60 or h < 60:
            st.warning("Immagine troppo piccola per l'effetto distruttivo")
            return img

        base_blocks = min(80, w * h // 1500)
        total_blocks = int(base_blocks * (0.5 + 1.5 * num_blocks))

        base_max_w = min(60, w // 4)
        base_max_h = min(60, h // 4)
        max_bw = max(5, int(base_max_w * (0.3 + 1.4 * block_size)))
        max_bh = max(5, int(base_max_h * (0.3 + 1.4 * block_size)))
        base_displacement = min(w // 6, h // 6)
        max_disp = max(1, int(base_displacement * displacement))

        for _ in range(total_blocks):
            bw = random.randint(max(5, max_bw // 3), max_bw)
            bh = random.randint(max(5, max_bh // 3), max_bh)
            x = random.randint(0, max(0, w - bw))
            y = random.randint(0, max(0, h - bh))

            if y + bh > h or x + bw > w:
                continue

            block = arr[y:y + bh, x:x + bw].copy()

            # Distorsione interna al blocco
            if random.random() < (0.1 + 0.4 * displacement):
                dist = int(5 + 10 * displacement)
                block = np.roll(block, random.randint(-dist, dist), axis=1)

            dx = random.randint(-max_disp, max_disp)
            dy = random.randint(-max_disp, max_disp)
            x_new = int(np.clip(x + dx, 0, w - bw))
            y_new = int(np.clip(y + dy, 0, h - bh))
            arr[y_new:y_new + bh, x_new:x_new + bw] = block

        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Errore nell'effetto distruttivo: {e}")
        return img


def glitch_noise(img, noise_intensity=1.0, coverage=1.0, chaos=1.0):
    """Effetto glitch con rumore casuale — vettorizzato."""
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int32)
        h, w, _ = arr.shape

        base_intensity = int(30 + 90 * noise_intensity)
        coverage_factor = 0.3 + 0.7 * coverage

        # Scegli tipo di rumore in base al chaos
        if chaos < 0.3:
            noise_type = "bands"
        elif chaos < 0.6:
            noise_type = "pixels"
        elif chaos < 0.8:
            noise_type = "waves"
        else:
            noise_type = "mixed"

        if noise_type == "bands":
            num_bands = int(5 + 15 * coverage)
            for _ in range(num_bands):
                sy = random.randint(0, h - 1)
                bh = int(3 + 27 * noise_intensity)
                ey = min(sy + bh, h)
                arr[sy:ey] += np.random.randint(
                    -base_intensity, base_intensity, (ey - sy, w, 3)
                )

        elif noise_type == "pixels":
            num_pix = int(w * h / 30 * coverage * (1 + chaos))
            xs = np.random.randint(0, w, num_pix)
            ys = np.random.randint(0, h, num_pix)
            pix_noise = np.random.randint(-base_intensity, base_intensity, (num_pix, 3))
            for i in range(num_pix):
                arr[ys[i], xs[i]] += pix_noise[i]

        elif noise_type == "waves":
            wave_rows = np.arange(0, h, max(1, int(h * (1 - coverage_factor) + 1)))
            wave_freq = 0.1 + 0.4 * chaos
            for y in wave_rows:
                wave_shift = int(base_intensity * 0.7 * np.sin(y * wave_freq))
                arr[y:y + 1] += np.random.randint(
                    -base_intensity // 2, base_intensity // 2, (1, w, 3)
                )
                if wave_shift:
                    arr[y:y + 1] = np.roll(arr[y:y + 1], wave_shift, axis=1)

        else:  # mixed — vettorizzato al massimo
            general_noise = np.random.randint(
                -base_intensity // 2, base_intensity // 2, arr.shape
            )
            arr += general_noise
            num_bands = int(3 + 5 * coverage)
            for _ in range(num_bands):
                sy = random.randint(0, max(1, h - 10))
                ey = min(sy + random.randint(2, int(10 + 5 * noise_intensity)), h)
                arr[sy:ey] += np.random.randint(
                    -base_intensity, base_intensity, (ey - sy, w, 3)
                )

        # Saturazione canali
        if chaos > 0.4:
            n_ch = min(3, int(1 + 2 * chaos))
            for ch in random.sample([0, 1, 2], n_ch):
                m = 0.5 + 1.5 * chaos
                mult = random.uniform(1 / m, m)
                arr[:, :, ch] = np.clip(arr[:, :, ch] * mult, 0, 255)

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Errore nell'effetto noise: {e}")
        return img


def glitch_random(img, randomness=1.0):
    """Applica un effetto glitch completamente casuale, eventualmente combinato."""
    try:
        effects = [glitch_vhs, glitch_distruttivo, glitch_noise]
        combo_chance = 0.1 + 0.4 * randomness

        def rand_params():
            return random.random(), random.random(), random.random()

        if random.random() < combo_chance:
            e1, e2 = random.sample(effects, 2)
            p1, p2, p3 = rand_params()
            p4, p5, p6 = rand_params()
            temp = e1(img, p1, p2, p3)
            return e2(temp, p4 * 0.7, p5 * 0.7, p6 * 0.7), "combo"
        else:
            chosen = random.choice(effects)
            p1, p2, p3 = rand_params()
            p1 = min(1.0, p1 * (0.5 + randomness))
            p2 = min(1.0, p2 * (0.5 + randomness))
            p3 = min(1.0, p3 * (0.5 + randomness))
            return chosen(img, p1, p2, p3), chosen.__name__.replace("glitch_", "")
    except Exception as e:
        st.error(f"Errore nell'effetto random: {e}")
        return img, "errore"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_report(img_size, params: dict, rand_effect_name: str, ts: str) -> bytes:
    """Report editoriale stilizzato — formato social Loop507."""
    w, h = img_size
    mpx = w * h / 1_000_000

    # Calcola valori derivati leggibili
    vhs_total   = (params['vhs_int'] + params['vhs_scan'] + params['vhs_col']) / 6.0
    dest_total  = (params['dest_size'] + params['dest_num'] + params['dest_disp']) / 6.0
    noise_total = (params['noise_int'] + params['noise_cov'] + params['noise_chaos'] * 2) / 6.0
    chaos_pct   = int(params['noise_chaos'] * 100)
    corruption  = int((vhs_total + dest_total + noise_total) / 3 * 100)
    rand_pct    = int(params['random_lev'] / 2.0 * 100)

    # Mappa noise_chaos → tipo motore
    if params['noise_chaos'] < 0.3:
        engine = "band_decay_engine"
    elif params['noise_chaos'] < 0.6:
        engine = "pixel_scatter_core"
    elif params['noise_chaos'] < 0.8:
        engine = "wave_collapse_engine"
    else:
        engine = "mixed_entropy_core"

    # Mappa rand_effect → nome poetico
    effect_label = {
        "vhs":         "Magnetic Tape Collapse",
        "distruttivo": "Block Fragment Shift",
        "noise":       "Signal Entropy Burst",
        "combo":       "Recursive Dual Corruption",
        "errore":      "Undefined Decay",
    }.get(rand_effect_name, rand_effect_name.upper())

    date_str, time_str = ts.split(" ")

    lines = [
        f"GLITCHLAB [LOOP507] // VOL_01 // {w}x{h}px // PNG",
        f":: MOTORE: {engine} [v2.0]",
        f":: EFFETTO RANDOM: {effect_label}",
        f":: ANALISI: VHS_Scan / Block_Shift / Entropy_Noise",
        f":: PROCESSO: Corruzione Multi-Strato",
        "",
        '"Il pixel e\' stato smontato. Il codice ne ha riscritto la struttura."',
        "",
        "> TECHNICAL LOG SHEET:",
        f"* Asset: {w} x {h} px  ({mpx:.2f} Mpx)",
        f"* Data: {date_str}  //  {time_str}",
        f"* Corruption Index: {corruption}%",
        f"* Chaos Level: {chaos_pct}%  |  Randomness: {rand_pct}%",
        "",
        "> VHS ENGINE:",
        f"* Distorsione: {params['vhs_int']:.1f}  //  Scanlines: {params['vhs_scan']:.1f}  //  Color Split: {params['vhs_col']:.1f}",
        f"* VHS Intensity: {int(vhs_total * 100)}%",
        "",
        "> BLOCK SHIFT ENGINE:",
        f"* Blocchi: {params['dest_size']:.1f}  //  Numero: {params['dest_num']:.1f}  //  Displacement: {params['dest_disp']:.1f}",
        f"* Fragment Density: {int(dest_total * 100)}%",
        "",
        "> NOISE ENGINE:",
        f"* Intensita': {params['noise_int']:.1f}  //  Coverage: {params['noise_cov']:.1f}  //  Chaos: {params['noise_chaos']:.1f}",
        f"* Signal Decay: {int(noise_total * 100)}%  |  Mode: {engine.split('_')[0].upper()}",
        "",
        "> RANDOM ENGINE:",
        f"* Livello Casualita': {params['random_lev']:.1f}  //  Output: {effect_label}",
        "",
        "> Regia e Algoritmo: Loop507",
        "",
        "#glitchart #glitchlab #loop507 #vhsaesthetic #blockshift",
        "#signalcorruption #noisedecay #digitaldestruction #pixelbreak",
        "#computationalminimalism #datadestruction #experimentalimage",
    ]

    return "\n".join(lines).encode("utf-8")


# ─── Sessione ─────────────────────────────────────────────────────────────────
# Chiavi di session_state usate:
#   processed        → True dopo la prima generazione
#   img_vhs          → bytes PNG
#   img_distr        → bytes PNG
#   img_noise        → bytes PNG
#   img_random       → bytes PNG
#   report           → bytes TXT
#   rand_effect_name → str

for key in ["processed", "img_vhs", "img_distr", "img_noise",
            "img_random", "report", "rand_effect_name"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ─── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("📁 Carica un'immagine", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        img = Image.open(uploaded_file).convert("RGB")
        st.image(img, caption="🖼️ Originale", use_container_width=True)
        st.info(f"Dimensioni: {img.size[0]} × {img.size[1]} px")

        # ── Controlli ──────────────────────────────────────────────────────────
        st.markdown("### 🎛️ Controlli Effetti")

        with st.expander("📺 Controlli VHS", expanded=False):
            c1, c2, c3 = st.columns(3)
            vhs_int  = c1.slider("Intensità Distorsione", 0.0, 2.0, 1.0, 0.1, key="vhs_int")
            vhs_scan = c2.slider("Frequenza Scanlines",   0.0, 2.0, 1.0, 0.1, key="vhs_scan")
            vhs_col  = c3.slider("Separazione Colori",    0.0, 2.0, 1.0, 0.1, key="vhs_col")

        with st.expander("💥 Controlli Distruttivo", expanded=False):
            c1, c2, c3 = st.columns(3)
            dest_size = c1.slider("Dimensione Blocchi", 0.0, 2.0, 1.0, 0.1, key="dest_size")
            dest_num  = c2.slider("Numero Blocchi",     0.0, 2.0, 1.0, 0.1, key="dest_num")
            dest_disp = c3.slider("Spostamento",        0.0, 2.0, 1.0, 0.1, key="dest_disp")

        with st.expander("🌀 Controlli Noise", expanded=False):
            c1, c2, c3 = st.columns(3)
            noise_int   = c1.slider("Intensità Rumore", 0.0, 2.0, 1.0, 0.1, key="noise_int")
            noise_cov   = c2.slider("Copertura",        0.0, 2.0, 1.0, 0.1, key="noise_cov")
            noise_chaos = c3.slider("Caos",             0.0, 1.0, 0.5, 0.1, key="noise_chaos")

        with st.expander("🎲 Controlli Random", expanded=False):
            random_lev = st.slider("Livello Casualità", 0.0, 2.0, 1.0, 0.1, key="random_lev")

        params = dict(
            vhs_int=vhs_int, vhs_scan=vhs_scan, vhs_col=vhs_col,
            dest_size=dest_size, dest_num=dest_num, dest_disp=dest_disp,
            noise_int=noise_int, noise_cov=noise_cov, noise_chaos=noise_chaos,
            random_lev=random_lev,
        )

        # ── Modalità: Live vs Manuale ──────────────────────────────────────────
        st.markdown("---")
        live_mode = st.checkbox(
            "⚡ Modalità Live — ogni slider aggiorna le immagini in tempo reale",
            value=False, key="live_mode"
        )

        # Live ON  → elabora ad ogni rerun (ogni slider già triggera rerun da solo)
        # Live OFF → elabora solo al click del pulsante
        should_process = live_mode
        if not live_mode:
            if st.button("✨ Genera effetti glitch"):
                should_process = True

        if should_process:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            spinner_msg = "⚡ Live — aggiornamento..." if live_mode else "🔥 Generazione glitch in corso..."
            with st.spinner(spinner_msg):
                vhs_img   = glitch_vhs(img, vhs_int, vhs_scan, vhs_col)
                distr_img = glitch_distruttivo(img, dest_size, dest_num, dest_disp)
                noise_img = glitch_noise(img, noise_int, noise_cov, noise_chaos)
                rand_img, rand_name = glitch_random(img, random_lev)

            # Salva in session_state → i download_button non triggerano mai rerun
            st.session_state.img_vhs          = img_to_bytes(vhs_img)
            st.session_state.img_distr        = img_to_bytes(distr_img)
            st.session_state.img_noise        = img_to_bytes(noise_img)
            st.session_state.img_random       = img_to_bytes(rand_img)
            st.session_state.rand_effect_name = rand_name
            st.session_state.report           = make_report(img.size, params, rand_name, ts)
            st.session_state.processed        = True

        # ── Mostra risultati se disponibili ───────────────────────────────────
        if st.session_state.processed:
            label = "⚡ Live — ultimo frame" if live_mode else "🔥 Risultati glitch"
            st.subheader(label)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.image(st.session_state.img_vhs,   caption="📺 VHS",         use_container_width=True)
            with c2:
                st.image(st.session_state.img_distr, caption="💥 Distruttivo", use_container_width=True)
            with c3:
                st.image(st.session_state.img_noise, caption="🌀 Noise",       use_container_width=True)
            with c4:
                st.image(st.session_state.img_random,
                         caption=f"🎲 Random ({st.session_state.rand_effect_name})",
                         use_container_width=True)

            # ── Download — sempre fuori da st.button → nessun rerun ───────────
            st.markdown("### ⬇️ Download")
            if live_mode:
                st.caption("💡 I download salvano l'ultimo frame generato.")
            d1, d2, d3, d4, d5 = st.columns(5)
            d1.download_button("📺 VHS",         st.session_state.img_vhs,
                               "vhs_glitch.png",         "image/png",  key="dl_vhs")
            d2.download_button("💥 Distruttivo",  st.session_state.img_distr,
                               "distruttivo_glitch.png", "image/png",  key="dl_distr")
            d3.download_button("🌀 Noise",        st.session_state.img_noise,
                               "noise_glitch.png",       "image/png",  key="dl_noise")
            d4.download_button("🎲 Random",       st.session_state.img_random,
                               "random_glitch.png",      "image/png",  key="dl_random")
            d5.download_button("📄 Report .txt",  st.session_state.report,
                               "glitch_report.txt",      "text/plain", key="dl_report")

    except Exception as e:
        st.error(f"Errore nel caricamento dell'immagine: {e}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")

else:
    st.info("📁 Carica un'immagine per iniziare!")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** — Crea effetti glitch unici per le tue foto!")
st.markdown("*💡 Usa i controlli per personalizzare ogni effetto, poi premi **Genera**.*")
