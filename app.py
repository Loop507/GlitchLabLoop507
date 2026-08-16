import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import io
import zipfile
import random
import inspect
from datetime import datetime
try:
    from scipy.ndimage import uniform_filter as _scipy_uniform_filter
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

if hasattr(st, "fragment"):
    _fragment = st.fragment
else:
    # Streamlit troppo vecchio (serve 1.37+): niente rerun isolato per
    # singolo effetto, l'app resta funzionante ma torna a rieseguire
    # l'intero script ad ogni interazione (piu' lento, mai rotto).
    def _fragment(func):
        return func

st.set_page_config(page_title="GlitchLabLoop507", layout="wide")
st.title("🔥 GlitchLabLoop507")
st.write("Carica una foto e applica 41 effetti glitch — Live o Manuale.")


def img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    # compress_level basso: su immagini glitch/rumorose il guadagno di
    # dimensione del livello massimo (default 6) e' minimo, ma il costo in
    # tempo e' alto — livello 1 e' quasi il doppio piu' veloce a parita' di peso.
    img.save(buf, format="PNG", compress_level=1)
    return buf.getvalue()


def img_to_preview_bytes(img: Image.Image, max_dim: int = 900) -> bytes:
    """Genera un'anteprima leggera (JPEG, lato lungo max_dim) da mostrare a
    schermo con st.image(). Streamlit ritrasmette al browser TUTTE le
    immagini di TUTTI gli effetti gia' generati a ogni singola interazione
    (ogni slider, ogni click, ovunque nella pagina causa un rerun completo):
    usare qui il PNG a piena risoluzione — anche solo su una decina di
    effetti generati su una foto da alcuni megapixel — significa spedire
    decine di MB ad ogni interazione, rendendo l'interfaccia lentissima o
    apparentemente bloccata. Il file a piena risoluzione resta comunque
    disponibile per il download e lo ZIP (vedi img_to_bytes)."""
    preview = img.convert("RGB") if img.mode == "RGBA" else img
    w, h = preview.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        preview = preview.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.LANCZOS)
    buf = io.BytesIO()
    preview.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  EFFETTI
# ══════════════════════════════════════════════════════════════════════════════

def glitch_vhs(img, intensity=1.0, scanline_freq=1.0, color_shift=1.0):
    """Sbavatura nastro VHS: righe orizzontali che scivolano + color split."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        base_intensity = 15 + 30 * intensity
        freq1 = 3 + 9 * scanline_freq
        freq2 = 1 + 5 * scanline_freq
        ys = np.arange(h)
        shifts = (base_intensity * np.sin(ys / freq1) + (base_intensity / 2) * np.sin(ys / freq2)).astype(int)
        for y_idx in range(h):
            s = int(shifts[y_idx])
            if s:
                arr[y_idx] = np.roll(arr[y_idx], s, axis=0)
        noise_prob = 0.1 + 0.3 * intensity
        noise_mask = np.random.random(h) < noise_prob
        noise_int = int(10 + 20 * intensity)
        noise = np.random.randint(-noise_int, noise_int, (h, w, 3), dtype=np.int16)
        arr[noise_mask] = np.clip(arr[noise_mask] + noise[noise_mask], 0, 255)
        sm = color_shift
        r_shift = int(8 * sm + 12 * sm)
        b_shift = int(-8 * sm - 12 * sm)
        r = np.clip(np.roll(arr[:, :, 0], r_shift, axis=1), 0, 255)
        g = arr[:, :, 1]
        b = np.clip(np.roll(arr[:, :, 2], b_shift, axis=1), 0, 255)
        return Image.fromarray(np.stack([r, g, b], axis=2).astype(np.uint8))
    except Exception as e:
        st.error(f"VHS: {e}"); return img


def glitch_distruttivo(img, block_size=1.0, num_blocks=1.0, displacement=1.0):
    """Blocchi rettangolari strappati e riposizionati — collage distruttivo."""
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        if w < 60 or h < 60:
            return img
        base_blocks = min(80, w * h // 1500)
        total_blocks = int(base_blocks * (0.5 + 1.5 * num_blocks))
        max_bw = max(5, int(min(60, w // 4) * (0.3 + 1.4 * block_size)))
        max_bh = max(5, int(min(60, h // 4) * (0.3 + 1.4 * block_size)))
        max_disp = max(1, int(min(w // 4, h // 4) * displacement))
        for _ in range(total_blocks):
            bw = random.randint(max(5, max_bw // 3), max_bw)
            bh = random.randint(max(5, max_bh // 3), max_bh)
            x = random.randint(0, max(0, w - bw))
            y = random.randint(0, max(0, h - bh))
            if y + bh > h or x + bw > w:
                continue
            block = arr[y:y + bh, x:x + bw].copy()
            x_new = int(np.clip(x + random.randint(-max_disp, max_disp), 0, w - bw))
            y_new = int(np.clip(y + random.randint(-max_disp, max_disp), 0, h - bh))
            arr[y_new:y_new + bh, x_new:x_new + bw] = block
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Distruttivo: {e}"); return img


def glitch_noise(img, intensita=1.0, copertura=1.0, tipo=0.0):
    """Rumore digitale: 0=bande, 0.5=pixel sparsi, 1=onde."""
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int32)
        h, w, _ = arr.shape
        base = int(30 + 90 * intensita)

        if tipo < 0.33:
            # Bande orizzontali
            n_bands = int(5 + 20 * copertura)
            for _ in range(n_bands):
                sy = random.randint(0, h - 1)
                ey = min(sy + int(2 + 20 * intensita), h)
                arr[sy:ey] += np.random.randint(-base, base, (ey - sy, w, 3))
        elif tipo < 0.66:
            # Pixel sparsi
            num_pix = int(w * h * 0.05 * copertura)
            xs = np.random.randint(0, w, num_pix)
            ys = np.random.randint(0, h, num_pix)
            for i in range(num_pix):
                arr[ys[i], xs[i]] = np.random.randint(0, 256, 3)
        else:
            # Onde di rumore
            for y in range(0, h, max(1, int(h * (1 - copertura) * 0.5 + 1))):
                ws = int(base * 0.8 * np.sin(y * 0.15))
                arr[y:y + 1] += np.random.randint(-base // 2, base // 2, (1, w, 3))
                if ws:
                    arr[y:y + 1] = np.roll(arr[y:y + 1], ws, axis=1)

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Noise: {e}"); return img


def glitch_pixel_sort(img, soglia=0.5, asse=0.0, span_max=1.0):
    """Ordina pixel per luminosità in segmenti contigui — colature nette."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        thresh = soglia * 255
        max_span = max(4, int(span_max * max(h, w) * 0.8))

        if asse < 0.5:
            # Sort orizzontale per righe
            for y in range(h):
                row_lum = lum[y]
                x = 0
                while x < w:
                    if row_lum[x] > thresh:
                        end = x
                        while end < w and row_lum[end] > thresh and (end - x) < max_span:
                            end += 1
                        if end - x > 1:
                            seg = arr[y, x:end]
                            sk = 0.299 * seg[:, 0] + 0.587 * seg[:, 1] + 0.114 * seg[:, 2]
                            arr[y, x:end] = seg[np.argsort(sk)]
                        x = end
                    else:
                        x += 1
        else:
            # Sort verticale per colonne
            for x in range(w):
                col_lum = lum[:, x]
                y = 0
                while y < h:
                    if col_lum[y] > thresh:
                        end = y
                        while end < h and col_lum[end] > thresh and (end - y) < max_span:
                            end += 1
                        if end - y > 1:
                            seg = arr[y:end, x]
                            sk = 0.299 * seg[:, 0] + 0.587 * seg[:, 1] + 0.114 * seg[:, 2]
                            arr[y:end, x] = seg[np.argsort(sk)]
                        y = end
                    else:
                        y += 1
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Pixel Sort: {e}"); return img


def glitch_wave_warp(img, ampiezza=1.0, frequenza=1.0, asse=0.5):
    """Deformazione sinusoidale — effetto liquido/jello."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = np.zeros_like(arr)
        amp_x = int(20 + 60 * ampiezza)
        amp_y = int(15 + 45 * ampiezza)
        freq_x = 0.01 + 0.09 * frequenza
        freq_y = 0.008 + 0.07 * frequenza
        xs = np.arange(w)
        ys = np.arange(h)

        if asse <= 0.5:
            # Warp orizzontale (righe che oscillano)
            dx = (amp_x * np.sin(ys * freq_x)).astype(int)
            for y in range(h):
                src_x = np.clip(xs + dx[y], 0, w - 1)
                out[y] = arr[y, src_x]
        else:
            # Warp verticale (colonne che oscillano)
            dy = (amp_y * np.sin(xs * freq_y)).astype(int)
            for x in range(w):
                src_y = np.clip(ys + dy[x], 0, h - 1)
                out[:, x] = arr[src_y, x]

        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Wave Warp: {e}"); return img


def glitch_chromatic(img, forza=1.0, angolo=0.0, zoom_aberr=0.5):
    """Aberrazione cromatica: R/G/B spostati in direzioni diverse."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = np.zeros_like(arr)
        max_shift = int(5 + 40 * forza)
        a = angolo * 2 * np.pi

        # Tre canali si spostano in direzioni a 120° tra loro
        for ch, angle_offset in enumerate([a, a + 2.094, a + 4.189]):
            sx = int(max_shift * np.cos(angle_offset))
            sy = int(max_shift * np.sin(angle_offset))
            out[:, :, ch] = np.roll(np.roll(arr[:, :, ch], sx, axis=1), sy, axis=0)

        # Zoom aberrazione: i canali si zoomano leggermente (bordi scoloriti)
        if zoom_aberr > 0.05:
            scale = 1.0 + zoom_aberr * 0.05
            for ch in [0, 2]:
                ch_img = Image.fromarray(out[:, :, ch])
                new_w = int(w * scale)
                new_h = int(h * scale)
                zoomed = np.array(ch_img.resize((new_w, new_h), Image.BILINEAR))
                y0 = (new_h - h) // 2
                x0 = (new_w - w) // 2
                out[:, :, ch] = zoomed[y0:y0+h, x0:x0+w]

        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Chromatic: {e}"); return img


def glitch_datamosh(img, block_size=1.0, decay=0.5, num_blocks=0.5):
    """Blocchi di frame congelati sovrapposti — corruzione video."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_blocks = int(15 + 60 * num_blocks)
        bw = max(8, int((w // 6) * (0.3 + 1.4 * block_size)))
        bh = max(8, int((h // 6) * (0.3 + 1.4 * block_size)))
        alpha = 0.4 + 0.55 * decay

        for _ in range(n_blocks):
            x1 = random.randint(0, max(0, w - bw))
            y1 = random.randint(0, max(0, h - bh))
            x2 = random.randint(0, max(0, w - bw))
            y2 = random.randint(0, max(0, h - bh))
            src = arr[y1:y1 + bh, x1:x1 + bw]
            dst = arr[y2:y2 + bh, x2:x2 + bw]
            if src.shape == dst.shape:
                arr[y2:y2 + bh, x2:x2 + bw] = alpha * src + (1 - alpha) * dst
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Datamosh: {e}"); return img


def glitch_scanline_burn(img, intensita=1.0, densita=0.4, color_bleed=0.5):
    """Righe bruciate CRT: bianche, nere o RGB puri."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_burns = int(3 + 50 * densita)

        for _ in range(n_burns):
            y = random.randint(0, h - 1)
            bh = random.randint(1, max(1, int(6 * intensita)))
            ey = min(y + bh, h)
            mode = random.random()
            if mode < 0.33:
                arr[y:ey] = 255
            elif mode < 0.66:
                arr[y:ey] = 0
            else:
                ch = random.randint(0, 2)
                arr[y:ey] = 0
                arr[y:ey, :, ch] = 255

        if color_bleed > 0.05:
            px = int(2 + 15 * color_bleed)
            arr[:, :, 0] = np.roll(arr[:, :, 0], px, axis=1)
            arr[:, :, 2] = np.roll(arr[:, :, 2], -px, axis=1)

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Scanline Burn: {e}"); return img


def glitch_psychedelic(img, hue_shift=0.3, saturazione=0.5, inversione=0.0):
    """Rotazione hue + saturazione estrema + inversione canale."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        h, w, _ = arr.shape
        shift = hue_shift * 2 * np.pi
        cos_h, sin_h = np.cos(shift), np.sin(shift)
        hue_matrix = np.array([
            [0.213 + cos_h * 0.787 - sin_h * 0.213,
             0.213 - cos_h * 0.213 - sin_h * 0.143,
             0.213 - cos_h * 0.213 + sin_h * 0.140],
            [0.715 - cos_h * 0.715 - sin_h * 0.715,
             0.715 + cos_h * 0.285 + sin_h * 0.140,
             0.715 - cos_h * 0.715 + sin_h * 0.140],
            [0.072 - cos_h * 0.072 + sin_h * 0.928,
             0.072 - cos_h * 0.072 - sin_h * 0.283,
             0.072 + cos_h * 0.928 + sin_h * 0.283],
        ])
        arr = np.clip((arr.reshape(-1, 3) @ hue_matrix.T).reshape(h, w, 3), 0, 1)
        gray = arr.mean(axis=2, keepdims=True)
        arr = np.clip(gray + (arr - gray) * (1.0 + saturazione * 4.0), 0, 1)
        if inversione > 0.05:
            for ch in range(3):
                if random.random() < inversione:
                    arr[:, :, ch] = 1.0 - arr[:, :, ch]
        return Image.fromarray((arr * 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Psychedelic: {e}"); return img


def glitch_channel_swap(img, modalita=0.0, blend=0.6, shift_px=0.0):
    """Scambia canali RGB + shift orizzontale opzionale."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8).astype(np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        combos = [
            (g, b, r),              # GBR
            (b, r, g),              # BRG
            (r, b, g),              # RBG
            (b, g, r),              # BGR
            (g, r, b),              # GRB
            (255 - r, g, 255 - b),  # inversione parziale
        ]
        idx = int(modalita * (len(combos) - 0.01))
        nr, ng, nb = combos[idx]
        result = np.stack([
            r * (1 - blend) + nr * blend,
            g * (1 - blend) + ng * blend,
            b * (1 - blend) + nb * blend,
        ], axis=2)
        if shift_px > 0.01:
            s = int(shift_px * 40)
            result[:, :, 0] = np.roll(result[:, :, 0], s, axis=1)
            result[:, :, 2] = np.roll(result[:, :, 2], -s, axis=1)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Channel Swap: {e}"); return img


def glitch_image_feedback(img, zoom=0.5, iterazioni=0.4, decay=0.5):
    """Zoom ricorsivo con dissolvenza — effetto telecamera sul monitor."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_iters = int(2 + 8 * iterazioni)
        zoom_factor = 1.03 + 0.1 * zoom
        fade = 0.4 + 0.5 * decay
        accumulated = arr.copy()

        for i in range(n_iters):
            scale = zoom_factor ** (i + 1)
            new_h = int(h / scale)
            new_w = int(w / scale)
            if new_h < 4 or new_w < 4:
                break
            y0 = (h - new_h) // 2
            x0 = (w - new_w) // 2
            layer = np.array(
                Image.fromarray(arr[y0:y0+new_h, x0:x0+new_w].astype(np.uint8)).resize((w, h), Image.BILINEAR),
                dtype=np.float32
            )
            weight = fade ** (i + 1)
            accumulated = accumulated * (1 - weight * 0.25) + layer * weight * 0.25

        return Image.fromarray(np.clip(accumulated, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Image Feedback: {e}"); return img


def glitch_destruction_art(img, tagli=0.5, scatter=0.4, orientamento=0.0):
    """Taglia l'immagine in strisce e le ricompone — orientamento controllato."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = np.zeros_like(arr)
        n_cuts = int(5 + 40 * tagli)
        vertical = orientamento > 0.5  # 0=orizzontale, 1=verticale

        if vertical:
            indices = sorted(random.sample(range(1, w), min(n_cuts, w - 1)))
            boundaries = [0] + indices + [w]
            strips = [arr[:, boundaries[i]:boundaries[i+1]].copy() for i in range(len(boundaries)-1) if boundaries[i+1] > boundaries[i]]
            random.shuffle(strips)
            x = 0
            for strip in strips:
                sw = strip.shape[1]
                if x + sw <= w:
                    if scatter > 0.1:
                        dx = random.randint(-int(scatter * 15), int(scatter * 15))
                        cols = np.clip(np.arange(sw) + dx, 0, sw - 1)
                        strip = strip[:, cols]
                    out[:, x:x + sw] = strip
                    x += sw
        else:
            indices = sorted(random.sample(range(1, h), min(n_cuts, h - 1)))
            boundaries = [0] + indices + [h]
            strips = [arr[boundaries[i]:boundaries[i+1], :].copy() for i in range(len(boundaries)-1) if boundaries[i+1] > boundaries[i]]
            random.shuffle(strips)
            y = 0
            for strip in strips:
                sh = strip.shape[0]
                if y + sh <= h:
                    if scatter > 0.1:
                        dy = random.randint(-int(scatter * 15), int(scatter * 15))
                        rows = np.clip(np.arange(sh) + dy, 0, sh - 1)
                        strip = strip[rows, :]
                    out[y:y + sh, :] = strip
                    y += sh

        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Destruction Art: {e}"); return img


def glitch_analogic(img, sync_loss=0.5, color_bleed=0.4, static=0.3):
    """TV analogica mal sintonizzata: righe che scivolano + static."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape

        # Righe che scivolano lateralmente in modo irregolare
        n_desync = int(h * (0.05 + 0.6 * sync_loss))
        desync_rows = np.random.choice(h, n_desync, replace=False)
        for y in desync_rows:
            shift = int(np.random.normal(0, 25 * sync_loss))
            arr[y] = np.roll(arr[y], shift, axis=0)

        # Blocchi di righe che scivolano insieme (sync loss a blocchi)
        if sync_loss > 0.3:
            n_blocks = int(3 + 8 * sync_loss)
            for _ in range(n_blocks):
                y0 = random.randint(0, max(0, h - 5))
                y1 = min(y0 + random.randint(3, 20), h)
                shift = int(np.random.normal(0, 40 * sync_loss))
                arr[y0:y1] = np.roll(arr[y0:y1], shift, axis=1)

        # Color bleed verticale
        if color_bleed > 0.05:
            s = int(2 + 10 * color_bleed)
            for ch in range(3):
                arr[:, :, ch] = arr[:, :, ch] * 0.75 + np.roll(arr[:, :, ch], s, axis=0) * 0.25

        # Static
        if static > 0.05:
            n_st = int(w * h * 0.008 * static)
            xs = np.random.randint(0, w, n_st)
            ys = np.random.randint(0, h, n_st)
            v = np.random.choice([0.0, 255.0], n_st)
            for i in range(n_st):
                arr[ys[i], xs[i]] = v[i]

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Analogic: {e}"); return img


def glitch_displacement_map(img, forza=0.5, blur_scala=0.4, canale=0.0):
    """L'immagine si sposta seguendo se stessa — effetto organico/liquido."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        blur_r = max(1, int(2 + 15 * blur_scala))
        disp_map = np.array(
            Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur_r)),
            dtype=np.float32
        )
        ch_x = int(canale * 2.99)
        ch_y = (ch_x + 1) % 3
        map_x = (disp_map[:, :, ch_x] / 255.0 - 0.5) * 2
        map_y = (disp_map[:, :, ch_y] / 255.0 - 0.5) * 2
        max_d = int(10 + 90 * forza)
        ys_g, xs_g = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        src_x = np.clip(xs_g + (map_x * max_d).astype(int), 0, w - 1)
        src_y = np.clip(ys_g + (map_y * max_d).astype(int), 0, h - 1)
        return Image.fromarray(arr[src_y, src_x].astype(np.uint8))
    except Exception as e:
        st.error(f"Displacement Map: {e}"); return img


def glitch_op_art_circles(img, frequenza=0.5, contrasto=0.6, blend=0.5):
    """Cerchi concentrici che invertono l'immagine — Op Art ipnotica."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w]
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        freq = 0.03 + 0.2 * frequenza
        wave = np.sin(dist * freq) * 0.5 + 0.5
        wave3 = wave[:, :, np.newaxis]
        inverted = 255 - arr
        result = arr * (1 - blend * wave3) + inverted * (blend * wave3)
        # Boost contrasto
        mean = result.mean()
        result = np.clip((result - mean) * (1 + contrasto) + mean, 0, 255)
        result = np.nan_to_num(result, nan=0.0, posinf=255.0, neginf=0.0)
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Op Art Circles: {e}"); return img


def glitch_halftone(img, dim_punto=0.4, sfondo_bianco=1.0, colore=0.7):
    """Retino tipografico: punti proporzionali alla luminosità."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        cell = max(3, int(3 + 17 * dim_punto))
        bg_val = 255.0 * sfondo_bianco
        out = np.full((h, w, 3), bg_val, dtype=np.float32)

        for y in range(0, h, cell):
            for x in range(0, w, cell):
                patch = arr[y:y+cell, x:x+cell]
                if patch.size == 0:
                    continue
                avg = patch.mean(axis=(0, 1))
                lum = (avg[0]*0.299 + avg[1]*0.587 + avg[2]*0.114) / 255.0
                radius = int((cell / 2) * (1.0 - lum) * 1.8)
                if radius < 1:
                    continue
                cy_p = y + cell // 2
                cx_p = x + cell // 2
                ys_p = np.arange(max(0, cy_p - radius - 1), min(h, cy_p + radius + 2))
                xs_p = np.arange(max(0, cx_p - radius - 1), min(w, cx_p + radius + 2))
                if len(ys_p) == 0 or len(xs_p) == 0:
                    continue
                yy, xx = np.meshgrid(ys_p, xs_p, indexing='ij')
                mask = (xx - cx_p)**2 + (yy - cy_p)**2 <= radius**2
                dot_color = avg if colore > 0.5 else (np.array([0, 0, 0]) if sfondo_bianco > 0.5 else np.array([255, 255, 255]))
                out[yy[mask], xx[mask]] = dot_color

        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Halftone: {e}"); return img


def glitch_moire(img, freq1=0.4, freq2=0.6, angolo=0.3):
    """Due griglie sovrapposte: interferenza ottica vibrante."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        a = float(angolo) * np.pi
        f1 = 0.03 + 0.2 * float(freq1)
        f2 = 0.025 + 0.18 * float(freq2)
        grid1 = np.sin(xs * f1 * np.cos(a) + ys * f1 * np.sin(a))
        grid2 = np.sin(xs * f2 * np.cos(a + 0.25) + ys * f2 * np.sin(a + 0.25))
        moire = np.nan_to_num((grid1 * grid2) * 0.5 + 0.5, nan=0.5, posinf=1.0, neginf=0.0)
        moire = moire[:, :, np.newaxis]
        result = arr * moire + (255 - arr) * (1 - moire)
        result = np.nan_to_num(result, nan=0.0, posinf=255.0, neginf=0.0)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Moire: {e}"); return img


def glitch_drip(img, soglia=0.4, separazione_rgb=0.5, asse=0.0):
    """Pixel sort a stalattiti: segmenti contigui ordinati per luminosità + color bleed."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = arr.copy().astype(np.float32)
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        thresh = soglia * 255

        # Offset cromatico per canale: crea la separazione ciano/magenta
        # R verso sinistra, G al centro, B verso destra (o su/giù per asse V)
        offsets = [
            int(-separazione_rgb * 12),   # R
            0,                             # G
            int(separazione_rgb * 12),     # B
        ]

        vertical = asse > 0.5

        for ch in range(3):
            ch_arr = arr[:, :, ch].copy()
            offset = offsets[ch]

            if not vertical:
                # COLONNE: ordina dall'alto verso il basso (stalattiti verticali)
                for x in range(w):
                    # Canale con offset orizzontale (color split)
                    src_x = int(np.clip(x + offset, 0, w - 1))
                    col = ch_arr[:, src_x].copy()
                    col_lum = lum[:, src_x]
                    y = 0
                    while y < h:
                        if col_lum[y] > thresh:
                            end = y
                            while end < h and col_lum[end] > thresh:
                                end += 1
                            if end - y > 1:
                                col[y:end] = np.sort(col[y:end])  # ascendente = scuro in cima, chiaro in basso
                            y = end
                        else:
                            y += 1
                    out[:, x, ch] = col
            else:
                # RIGHE: ordina da sinistra a destra (stalattiti orizzontali)
                for y in range(h):
                    src_y = int(np.clip(y + offset, 0, h - 1))
                    row = ch_arr[src_y, :].copy()
                    row_lum = lum[src_y, :]
                    x = 0
                    while x < w:
                        if row_lum[x] > thresh:
                            end = x
                            while end < w and row_lum[end] > thresh:
                                end += 1
                            if end - x > 1:
                                row[x:end] = np.sort(row[x:end])
                            x = end
                        else:
                            x += 1
                    out[y, :, ch] = row

        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Drip: {e}"); return img


def glitch_oil_paint(img, raggio=0.4, livelli=0.5, blend=0.7):
    """Pennellate Kuwahara vettoriale: ogni pixel prende il colore del quadrante più omogeneo.
    Le finestre scorrevoli (sliding_window_view) sono pesanti su foto reali ad
    alta risoluzione: l'elaborazione avviene su una copia ridotta e il
    risultato viene poi riportato alla dimensione originale (da 30s+ a
    pochi secondi su una foto da alcuni megapixel, senza perdita percepibile
    dato che l'effetto pittorico e' comunque a bassa frequenza)."""
    try:
        orig_w, orig_h = img.size
        img_work, _ = _downscale_for_work(img.convert("RGB"), max_dim=1200)
        img = img_work.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        r = max(2, int(2 + 8 * raggio))

        # Kuwahara vettoriale via summed-area table (SAT): mean/var di ogni
        # quadrante calcolati con 4 sottrazioni per pixel, O(h*w) totale.
        # Molto piu' veloce di sliding_window_view + var/mean (che iterano
        # su memoria non contigua ed erano il vero collo di bottiglia).
        pad = r
        padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
        lum_pad = (padded[:, :, 0]*0.299 + padded[:, :, 1]*0.587 + padded[:, :, 2]*0.114)

        def sat(a):
            c = np.cumsum(np.cumsum(a, axis=0), axis=1)
            pad_shape = [(1, 0), (1, 0)] + [(0, 0)] * (a.ndim - 2)
            return np.pad(c, pad_shape, mode="constant")

        I_lum = sat(lum_pad)
        I_lum_sq = sat(lum_pad * lum_pad)
        I_col = sat(padded)   # (Hpad+1, Wpad+1, 3)

        def box_sum(I, soy, sox):
            t1 = I[soy + r:soy + r + h, sox + r:sox + r + w]
            t2 = I[soy:soy + h, sox + r:sox + r + w]
            t3 = I[soy + r:soy + r + h, sox:sox + w]
            t4 = I[soy:soy + h, sox:sox + w]
            return t1 - t2 - t3 + t4

        best_var = np.full((h, w), np.inf, dtype=np.float32)
        out = np.zeros_like(arr)
        area = float(r * r)

        for (soy, sox) in [(0, 0), (0, r), (r, 0), (r, r)]:   # TL, TR, BL, BR
            s_lum = box_sum(I_lum, soy, sox)
            s_lum_sq = box_sum(I_lum_sq, soy, sox)
            mean_lum = s_lum / area
            var = s_lum_sq / area - mean_lum * mean_lum
            mean_col = box_sum(I_col, soy, sox) / area   # (h, w, 3)

            mask = var < best_var
            best_var[mask] = var[mask]
            out[mask] = mean_col[mask]

        # Posterizzazione finale per accentuare l'effetto pittorico
        lev = max(2, int(2 + 6 * livelli))
        step = 256.0 / lev
        out_post = (np.floor(out / step) * step).clip(0, 255)
        result = arr * (1 - blend) + out_post * blend
        result_img = Image.fromarray(result.astype(np.uint8))
        if result_img.size != (orig_w, orig_h):
            result_img = result_img.resize((orig_w, orig_h), Image.LANCZOS)
        return result_img
    except Exception as e:
        st.error(f"Oil Paint: {e}"); return img


def glitch_posterize(img, livelli=0.4, dither=0.4, color_shift=0.3):
    """Riduce i colori a fasce piatte — estetica serigrafica."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lev = max(2, int(2 + 6 * livelli))
        step = 256.0 / lev
        if dither > 0.02:
            noise = np.random.uniform(-step * dither * 0.6, step * dither * 0.6, arr.shape)
            arr = np.clip(arr + noise, 0, 255)
        posterized = (np.floor(arr / step) * step).clip(0, 255)
        if color_shift > 0.02:
            s = int(color_shift * 25)
            posterized[:, :, 0] = np.roll(posterized[:, :, 0], s, axis=1)
            posterized[:, :, 2] = np.roll(posterized[:, :, 2], -s, axis=1)
        return Image.fromarray(posterized.astype(np.uint8))
    except Exception as e:
        st.error(f"Posterize: {e}"); return img


def glitch_neon_glow(img, soglia=0.5, ampiezza=0.5, colore=0.2):
    """Bordi luminosi neon su sfondo scuro — estetica cyberpunk."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        gw = max(2, int(1 + 8 * ampiezza))
        blur_s = np.array(img.filter(ImageFilter.GaussianBlur(1)), dtype=np.float32)
        blur_l = np.array(img.filter(ImageFilter.GaussianBlur(gw)), dtype=np.float32)
        edges = np.abs(blur_s - blur_l).mean(axis=2)
        edges = edges / (edges.max() + 1e-8)
        intensity = np.clip((edges - soglia * 0.1) * 5, 0, 1)[:, :, np.newaxis]

        palettes = [
            [0, 255, 255],    # ciano
            [255, 0, 255],    # magenta
            [0, 255, 0],      # verde
            [255, 200, 0],    # giallo
            [255, 80, 0],     # arancio
        ]
        idx = int(colore * (len(palettes) - 0.01))
        neon = np.array(palettes[idx], dtype=np.float32)
        # Sfondo scuro + bordi neon
        dark_bg = arr * 0.15
        result = dark_bg * (1 - intensity) + neon * intensity
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Neon Glow: {e}"); return img


def glitch_duotone(img, colore1=0.1, colore2=0.6, blend=0.8):
    """Due colori hue-based: ombre e luci mappate su due tinte."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255.0

        def hue_rgb(h):
            h = h % 1.0
            r = np.clip(abs(h * 6 - 3) - 1, 0, 1)
            g = np.clip(2 - abs(h * 6 - 2), 0, 1)
            b = np.clip(2 - abs(h * 6 - 4), 0, 1)
            return np.array([r, g, b]) * 255

        c1 = hue_rgb(colore1)
        c2 = hue_rgb(colore2)
        t = lum[:, :, np.newaxis]
        duotone = c1 * (1 - t) + c2 * t
        result = arr * (1 - blend) + duotone * blend
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Duotone: {e}"); return img


def glitch_solarize(img, soglia=0.5, forza=0.8, channel_split=0.3):
    """Inverte i pixel sopra soglia — estetica camera oscura."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        thresh = soglia * 255
        inverted = np.where(arr > thresh, 255 - arr, arr)
        result = arr * (1 - forza) + inverted * forza
        if channel_split > 0.02:
            s = int(channel_split * 25)
            result[:, :, 0] = np.roll(result[:, :, 0], s, axis=1)
            result[:, :, 2] = np.roll(result[:, :, 2], -s, axis=0)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Solarize: {e}"); return img


def glitch_thermal(img, palette=0.0, rumore=0.2, contrasto=0.6):
    """Falsi colori termografici: freddo→caldo mappato in colori."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255.0
        if rumore > 0.01:
            lum = np.clip(lum + np.random.uniform(-rumore*0.15, rumore*0.15, lum.shape), 0, 1)
        lum = np.clip((lum - 0.5) * (1 + contrasto * 1.5) + 0.5, 0, 1)

        palettes = [
            # Classica termica: nero→blu→ciano→verde→giallo→rosso→bianco
            [(0,0,0),(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0,0),(1,1,1)],
            # Infrarosso: viola→blu→verde→giallo→bianco
            [(0.2,0,0.4),(0,0,1),(0,0.8,0.2),(1,1,0),(1,1,1)],
            # Calore: nero→rosso→arancio→giallo→bianco
            [(0,0,0),(0.6,0,0),(1,0.3,0),(1,1,0),(1,1,1)],
        ]
        pal = palettes[int(palette * (len(palettes) - 0.01))]
        n = len(pal) - 1
        t = lum * n
        idx = np.clip(t.astype(int), 0, n - 1)
        frac = (t - idx)[:, :, np.newaxis]
        c_lo = np.array(pal)[idx]
        c_hi = np.array(pal)[np.clip(idx + 1, 0, n)]
        result = (c_lo * (1 - frac) + c_hi * frac) * 255
        result = np.nan_to_num(result, nan=0.0, posinf=255.0, neginf=0.0)
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Thermal: {e}"); return img


def glitch_polar(img, forza=0.6, rotazione=0.0, zoom=0.5):
    """Coordinate polari — immagine avvolta su se stessa."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (xs / w - 0.5) * 2
        ny = (ys / h - 0.5) * 2
        r = np.sqrt(nx**2 + ny**2) * (0.5 + zoom)
        angle = np.arctan2(ny, nx) + rotazione * np.pi
        px = np.clip(((angle / (2 * np.pi) + 0.5) * w * forza + w * (1 - forza) * 0.5).astype(int), 0, w - 1)
        py = np.clip((r * h * 0.8).astype(int), 0, h - 1)
        px = np.nan_to_num(px, nan=0).astype(int)
        py = np.nan_to_num(py, nan=0).astype(int)
        return Image.fromarray(arr[py, px])
    except Exception as e:
        st.error(f"Polar: {e}"); return img


def glitch_tunnel_zoom(img, strati=0.5, velocita=0.5, color_shift=0.3):
    """Zoom a tunnel: strati concentrici con color shift progressivo."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n = int(3 + 7 * strati)
        accumulated = np.zeros_like(arr)
        total_w = 0.0

        for i in range(n):
            scale = 1.0 / (1.2 + i * 0.5 * velocita)
            nw = max(1, min(w, int(w * scale)))
            nh = max(1, min(h, int(h * scale)))
            small = np.array(
                Image.fromarray(arr.astype(np.uint8)).resize((nw, nh), Image.BILINEAR),
                dtype=np.float32
            )
            layer = np.zeros_like(arr)
            py = (h - nh) // 2
            px = (w - nw) // 2
            layer[py:py+nh, px:px+nw] = small
            if color_shift > 0.02:
                s = int(i * color_shift * 6)
                layer[:, :, 0] = np.roll(layer[:, :, 0], s, axis=1)
                layer[:, :, 2] = np.roll(layer[:, :, 2], -s, axis=1)
            wt = 1.0 / (i + 1)
            accumulated += layer * wt
            total_w += wt

        return Image.fromarray(np.clip(accumulated / total_w, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Tunnel Zoom: {e}"); return img


def glitch_mirror_kaleidoscope(img, specchi=0.3, rotazione=0.0, zoom=0.5):
    """4/6/8 specchi radiali — simmetria pura."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        n_m = 4 if specchi < 0.33 else (6 if specchi < 0.66 else 8)
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        dy, dx = ys - cy, xs - cx
        angles = np.arctan2(dy, dx) + rotazione * np.pi
        radii = np.sqrt(dx**2 + dy**2)
        seg = np.pi / n_m
        angles_mod = angles % (2 * seg)
        angles_mod = np.where(angles_mod > seg, 2 * seg - angles_mod, angles_mod)
        scale = 0.4 + 0.8 * zoom
        src_x = np.clip((cx + radii * np.cos(angles_mod) * scale).astype(int), 0, w - 1)
        src_y = np.clip((cy + radii * np.sin(angles_mod) * scale).astype(int), 0, h - 1)
        return Image.fromarray(arr[src_y, src_x])
    except Exception as e:
        st.error(f"Mirror Kaleidoscope: {e}"); return img


def glitch_crosshatch(img, densita=0.5, angolo=0.3, spessore=0.3):
    """Tratteggi incrociati — intensità proporzionale alle zone scure."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255.0
        spacing = max(2, int(2 + 12 * (1 - densita)))
        thick = max(1, int(1 + 3 * spessore))
        a = angolo * np.pi * 0.5
        out = np.ones((h, w, 3), dtype=np.float32) * 255
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        line1 = (xs * np.cos(a) + ys * np.sin(a)) % spacing
        line2 = (xs * np.cos(a + np.pi/2) + ys * np.sin(a + np.pi/2)) % spacing
        line3 = (xs * np.cos(a + np.pi/4) + ys * np.sin(a + np.pi/4)) % (spacing * 1.5)
        hatch1 = line1 < thick
        hatch2 = line2 < thick
        hatch3 = line3 < thick
        # Zone molto scure: 3 direzioni
        very_dark = lum < 0.25
        dark = (lum >= 0.25) & (lum < 0.5)
        medium = (lum >= 0.5) & (lum < 0.75)
        out[very_dark & (hatch1 | hatch2 | hatch3)] = arr[very_dark & (hatch1 | hatch2 | hatch3)] * 0.05
        out[dark & (hatch1 | hatch2)] = arr[dark & (hatch1 | hatch2)] * 0.1
        out[medium & hatch1] = arr[medium & hatch1] * 0.3
        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Crosshatch: {e}"); return img


def glitch_stippling(img, densita=0.5, dim_punto=0.4, colore=0.6):
    """Puntinismo: punti concentrati nelle zone scure."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255.0
        bg = 255.0 if colore < 0.5 else 0.0
        out = np.full((h, w, 3), bg, dtype=np.float32)
        n_dots = int(w * h * 0.025 * densita)
        max_r = max(1, int(1 + 4 * dim_punto))
        prob = 1.0 - lum
        prob = np.clip(prob, 0.001, None)
        prob = prob / prob.sum()
        flat_idx = np.random.choice(h * w, size=min(n_dots, h * w), replace=False, p=prob.ravel())
        ys_d = flat_idx // w
        xs_d = flat_idx % w
        for i in range(len(ys_d)):
            y, x = ys_d[i], xs_d[i]
            r = random.randint(1, max_r)
            y0, y1 = max(0, y-r), min(h, y+r+1)
            x0, x1 = max(0, x-r), min(w, x+r+1)
            dot_color = arr[y, x] if colore > 0.5 else (np.array([0.0, 0.0, 0.0]) if bg > 128 else np.array([255.0, 255.0, 255.0]))
            out[y0:y1, x0:x1] = dot_color
        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Stippling: {e}"); return img


def glitch_rutt_etra(img, intensity=1.0, line_spacing=1.0, displacement=1.0):
    """Emulazione Rutt-Etra (scan processor video anni '70, tecnica di dominio pubblico):
    ogni scanline viene ridisegnata con la posizione verticale spinta dalla luminosità
    locale, mantenendo il colore reale per-pixel (non una media di riga) e un'alta densità
    di linee, così l'intero frame viene trasformato e non solo un'area isolata."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        gray = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255.0
        step = int(np.clip(round(6 / max(0.2, line_spacing)), 1, 20))
        max_disp = displacement * (h * 0.15)
        canvas = np.zeros_like(arr)
        xs = np.arange(w)

        for y in range(0, h, step):
            lum_row = gray[y, :]
            new_ys = np.clip(y - lum_row * max_disp, 0, h - 1).astype(np.int32)
            colors = arr[y, :]  # colore reale per-pixel della riga sorgente
            canvas[new_ys, xs] = colors
            ys_plus = np.clip(new_ys + 1, 0, h - 1)
            canvas[ys_plus, xs] = colors  # piccolo spessore per continuità visiva

        blend = float(np.clip((intensity / 3.0) ** 0.4, 0.02, 1.0))
        out = arr.astype(np.float32) * (1 - blend) + canvas.astype(np.float32) * blend
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Rutt-Etra: {e}"); return img


# Palette Commodore 64 (16 colori, valori RGB misurati da Philip "Pepto" Timmermann —
# dati tecnici di riferimento standard, non contenuto creativo)
RETRO_PALETTE_16 = np.array([
    [0,0,0],[255,255,255],[104,55,43],[112,164,178],
    [111,61,134],[88,141,67],[53,40,121],[184,199,111],
    [111,79,37],[67,57,0],[154,103,89],[68,68,68],
    [108,108,108],[154,210,132],[108,94,181],[149,149,149]
], dtype=np.float32)

_BAYER4 = np.array([
    [ 0, 8, 2,10],
    [12, 4,14, 6],
    [ 3,11, 1, 9],
    [15, 7,13, 5]
], dtype=np.float32) / 16.0 - 0.5

def glitch_retro_palette(img, intensity=1.0, dither=0.5, pixel_size=1.0):
    """Retro Palette 16: pixelizzazione + quantizzazione sulla palette fissa a 16 colori del
    Commodore 64, con dithering ordinato (Bayer) opzionale. Il quantizing avviene
    sull'immagine già pixelizzata (bassa risoluzione) per performance."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        block = max(1, int(2 + 14 * (pixel_size / 3.0)))
        sw, sh = max(1, w // block), max(1, h // block)
        small = np.array(Image.fromarray(arr).resize((sw, sh), Image.BOX), dtype=np.float32)

        rgb = small.copy()
        if dither > 0.5:
            tile = np.tile(_BAYER4, (sh // 4 + 1, sw // 4 + 1))[:sh, :sw]
            spread = 40.0 * (dither - 0.5) * 2
            rgb = rgb + tile[..., None] * spread

        flat = rgb.reshape(-1, 3)
        dists = np.sum((flat[:, None, :] - RETRO_PALETTE_16[None, :, :]) ** 2, axis=2)
        nearest = np.argmin(dists, axis=1)
        quantized_small = RETRO_PALETTE_16[nearest].reshape(sh, sw, 3).astype(np.uint8)

        pixelated = np.array(Image.fromarray(quantized_small).resize((w, h), Image.NEAREST), dtype=np.uint8)

        blend = float(np.clip((intensity / 3.0) ** 0.4, 0.02, 1.0))
        out = arr.astype(np.float32) * (1 - blend) + pixelated.astype(np.float32) * blend
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Retro Palette: {e}"); return img


_ASCII_RAMP = " .:-=+*#%@"  # rampa di densità crescente, convenzione standard ascii-art

def glitch_ascii_art(img, intensity=1.0, colore=0.5, dim_cella=1.0):
    """ASCII Art: l'immagine viene ricostruita a blocchi, ogni blocco sostituito da un
    carattere scelto in base alla luminosità media locale (rampa ' .:-=+*#%@'), in stile
    terminale monocromatico (verde su nero) oppure a colori reali per carattere."""
    try:
        from PIL import ImageDraw, ImageFont
        img = img.convert("RGB")
        w0, h0 = img.size
        arr0 = np.array(img, dtype=np.uint8)

        font = ImageFont.load_default()
        ch_w = max(1, max(font.getbbox(c)[2] for c in _ASCII_RAMP))
        ch_h = max(1, max(font.getbbox(c)[3] for c in _ASCII_RAMP))

        max_cols = 100
        cols = max(10, min(max_cols, int(max_cols / max(0.2, dim_cella))))
        cell = max(2, w0 // cols)
        cols = max(1, w0 // cell)
        rows = max(1, h0 // cell)

        canvas = Image.new("RGB", (cols * ch_w, rows * ch_h), (0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        mono_color = (60, 220, 90)  # verde terminale

        for ry in range(rows):
            y0, y1 = ry * cell, min(h0, (ry + 1) * cell)
            row_block = arr0[y0:y1]
            for rx in range(cols):
                x0, x1 = rx * cell, min(w0, (rx + 1) * cell)
                block = row_block[:, x0:x1]
                if block.size == 0:
                    continue
                avg_color = block.reshape(-1, 3).mean(axis=0)
                lum = (avg_color[0]*0.299 + avg_color[1]*0.587 + avg_color[2]*0.114) / 255.0
                ch = _ASCII_RAMP[min(len(_ASCII_RAMP) - 1, int(lum * (len(_ASCII_RAMP) - 1)))]
                col = tuple(int(c) for c in avg_color) if colore > 0.5 else mono_color
                draw.text((rx * ch_w, ry * ch_h), ch, fill=col, font=font)

        ascii_img = np.array(canvas.resize((w0, h0), Image.NEAREST), dtype=np.float32)

        blend = float(np.clip((intensity / 3.0) ** 0.4, 0.02, 1.0))
        out = arr0.astype(np.float32) * (1 - blend) + ascii_img * blend
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"ASCII Art: {e}"); return img


def glitch_pop_art_warhol(img, contrasto=0.6, palette=0.0, misregistrazione=0.4):
    """Pop Art stile serigrafia Warhol: l'immagine viene posterizzata in poche
    fasce tonali e ricolorata con una palette acida — come nelle stampe
    serigrafiche (Marilyn, Flowers). Foto singola, dimensione originale
    invariata (utile per poi affiancare piu' versioni con palette diverse
    in un collage/griglia fatto manualmente). Aggiunge una leggera
    mis-registrazione dei canali per l'effetto "fuori registro" tipico
    della serigrafia manuale.

    contrasto         : 0-1, quante fasce tonali (piu' alto = meno fasce, look piu' netto/pop)
    palette           : 0-1, seleziona una delle combinazioni di colori acidi
    misregistrazione  : 0-1, quanto i canali R/B sono disallineati
    """
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        lum = (arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114) / 255.0

        n_levels = max(2, min(4, int(round(4 - 2 * contrasto))))
        band = np.clip((lum * n_levels).astype(int), 0, n_levels - 1)

        PALETTES = [
            [(10, 10, 10), (230, 0, 122), (255, 210, 0), (0, 180, 190)],
            [(35, 0, 55), (255, 90, 0), (0, 200, 120), (255, 240, 190)],
            [(15, 15, 15), (0, 140, 255), (255, 0, 90), (255, 245, 0)],
            [(55, 0, 30), (255, 150, 0), (150, 230, 0), (255, 255, 255)],
            [(0, 25, 55), (255, 0, 150), (0, 235, 200), (255, 235, 0)],
            [(45, 0, 0), (255, 200, 0), (0, 175, 255), (255, 255, 255)],
            [(25, 25, 0), (0, 210, 130), (255, 60, 160), (255, 255, 255)],
        ]

        pal_idx = int(np.clip(palette, 0, 0.999) * len(PALETTES))
        pal_full = PALETTES[pal_idx]
        idxs = np.linspace(0, 3, n_levels).round().astype(int)
        colors = np.array([pal_full[k] for k in idxs], dtype=np.float32)
        out_arr = colors[band]

        if misregistrazione > 0.02:
            shift = int(2 + 14 * misregistrazione)
            out_arr = out_arr.copy()
            out_arr[:, :, 0] = np.roll(out_arr[:, :, 0], shift, axis=1)
            out_arr[:, :, 2] = np.roll(out_arr[:, :, 2], -shift, axis=0)

        return Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Pop Art Warhol: {e}"); return img


def glitch_temporal_bands(img, intensity=0.7, ampiezza_bande=0.5, spostamento=0.6):
    """Temporal Band Slicer: la foto viene tagliata in bande orizzontali di altezza
    variabile; ciascuna banda viene ricollocata da una diversa posizione spaziale
    della stessa immagine (spostamento orizzontale E verticale ampio, come nel
    riferimento Snorpey/Rosa Menkman), senza alterare colori, luminosita' o
    contrasto — puro displacement geometrico, nessun blend, nessuna ricompressione.

    intensity        : 0-1, probabilita' che una banda venga spostata (piu' alto = piu' bande "rotte")
    ampiezza_bande   : 0-1, quanto sono grandi/irregolari le bande (0 = sottili e uniformi, 1 = larghe e caotiche)
    spostamento      : 0-1, quanto lontano (in % di larghezza/altezza) puo' saltare una banda
    """
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape

        rng = np.random.RandomState(42)

        # ampiezza massima dello spostamento, come frazione di w/h (arriva a coprire
        # gran parte dell'immagine, cosi' una banda puo' "pescare" da una zona
        # completamente diversa della foto, come nel riferimento)
        max_shift_x = max(10, int(w * (0.05 + 0.55 * spostamento)))
        max_shift_y = max(6, int(h * (0.03 + 0.45 * spostamento)))

        prob_band = float(np.clip(0.15 + 0.8 * intensity, 0.1, 0.95))

        # altezze bande variabili (non uniformi)
        min_band = max(4, int(6 + 10 * (1.0 - ampiezza_bande)))
        max_band = max(min_band + 10, int(25 + 150 * ampiezza_bande))
        heights = []
        remaining = h
        while remaining > 0:
            bh = rng.randint(min_band, max_band + 1)
            bh = min(bh, remaining)
            heights.append(bh)
            remaining -= bh

        out = arr.copy()
        y = 0
        for bh in heights:
            y_end = min(y + bh, h)
            if rng.random() < prob_band:
                dx = rng.randint(-max_shift_x, max_shift_x + 1)
                dy = rng.randint(-max_shift_y, max_shift_y + 1)
                shifted = np.roll(arr, (dy, dx), axis=(0, 1))  # solo traslazione, nessun cambio colore
                out[y:y_end] = shifted[y:y_end]
            y = y_end

        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Temporal Band Slicer: {e}"); return img


def _box_blur_numpy(a, r):
    """Box blur via cumsum, pura numpy (fallback se scipy non e' installato)."""
    size = 2 * r + 1
    pad = [(r, r), (r, r)] + [(0, 0)] * (a.ndim - 2)
    ap = np.pad(a, pad, mode="reflect")
    c = np.cumsum(np.cumsum(ap, axis=0), axis=1)
    c = np.pad(c, [(1, 0), (1, 0)] + [(0, 0)] * (a.ndim - 2), mode="constant")
    h, w = a.shape[0], a.shape[1]
    return (c[size:size+h, size:size+w] - c[0:h, size:size+w]
            - c[size:size+h, 0:w] + c[0:h, 0:w]) / (size * size)


def _box_blur(a, r):
    """Box blur veloce via scipy.ndimage.uniform_filter (C-ottimizzato); se
    scipy non e' disponibile (es. manca dal requirements.txt su Streamlit
    Cloud) ricade automaticamente sulla versione pura numpy, piu' lenta ma
    sempre funzionante — l'app non si rompe mai per questa dipendenza."""
    if r < 1:
        return a
    if _HAS_SCIPY:
        size = 2 * r + 1
        if a.ndim == 2:
            return _scipy_uniform_filter(a, size=size, mode="reflect")
        axes_size = [size, size] + [1] * (a.ndim - 2)
        return _scipy_uniform_filter(a, size=axes_size, mode="reflect")
    return _box_blur_numpy(a, r)


def _downscale_for_work(img, max_dim):
    """Riduce l'immagine per l'elaborazione pesante se supera max_dim sul lato
    lungo; ritorna (immagine_ridotta, scala) dove scala = dim_originale/dim_ridotta.
    La riduzione agisce anche da filtro passa-basso: elimina il rumore ad alta
    frequenza che altrimenti guiderebbe tagli/decisioni casuali sull'immagine."""
    w, h = img.size
    long_side = max(w, h)
    if long_side <= max_dim:
        return img, 1.0
    scale = long_side / max_dim
    new_w, new_h = max(1, round(w / scale)), max(1, round(h / scale))
    small = img.resize((new_w, new_h), Image.LANCZOS)
    return small, scale


def _sobel(gray):
    """Gradienti Sobel Gx, Gy vettorizzati via padding (no scipy)."""
    gp = np.pad(gray, 1, mode="reflect")
    gx = (gp[0:-2, 2:] + 2*gp[1:-1, 2:] + gp[2:, 2:]) - (gp[0:-2, 0:-2] + 2*gp[1:-1, 0:-2] + gp[2:, 0:-2])
    gy = (gp[2:, 0:-2] + 2*gp[2:, 1:-1] + gp[2:, 2:]) - (gp[0:-2, 0:-2] + 2*gp[0:-2, 1:-1] + gp[0:-2, 2:])
    return gx, gy


def glitch_mondrian(img, complessita=0.55, spessore=0.5, vivacita=0.6, variation_seed=None):
    """Mondrian / De Stijl 'puro': la STRUTTURA della griglia (dove tagliare)
    e' guidata dalla foto — partizione ricorsiva content-aware su una copia
    ridotta e sfocata, che elimina il rumore ad alta frequenza e produce
    composizioni diverse a seconda della foto caricata. Il COLORE di ogni
    cella pero' non deriva mai dalla foto: viene assegnato dalla palette
    classica De Stijl (bianco predominante, blocchi rosso/giallo/blu, rari
    accenti neri) con probabilita' pesate, come in un vero Mondrian — non un
    tentativo di 'tradurre' i colori reali della foto.

    complessita     : 0-1, profondita' massima di ricorsione (piu' celle)
    spessore        : 0-1, spessore delle linee nere
    vivacita        : 0-1, quanta parte della composizione resta bianca (basso)
        o si riempie di rosso/giallo/blu (alto)
    variation_seed  : opzionale. Se None (default, uso normale) la scelta del
        taglio e la palette sono deterministiche per la stessa foto/parametri.
        Se specificato (usato dal generatore di varianti) sceglie fra i tagli
        migliori con probabilita' pesata sulla loro forza, e usa un'assegnazione
        colore diversa — cosi' ogni variante ha sia composizione che palette
        genuinamente diverse, non solo lievi sfumature.
    """
    try:
        w, h = img.size

        # analisi su versione ridotta + sfocata: elimina il rumore fotografico
        # che altrimenti farebbe scegliere tagli a caso pixel-per-pixel
        analysis_img, scale = _downscale_for_work(img.convert("RGB"), max_dim=500)
        rgb_a = np.array(analysis_img, dtype=np.float32)
        ah, aw = rgb_a.shape[:2]
        lum_a = rgb_a[..., 0]*0.299 + rgb_a[..., 1]*0.587 + rgb_a[..., 2]*0.114
        blur_r = max(1, round(min(ah, aw) * 0.015))
        lum_a = _box_blur(lum_a, blur_r)

        max_depth = 2 + round(complessita * 5)
        line_px = max(1, int(round(1 + spessore * (min(w, h) * 0.02))))

        WHITE = np.array([246, 244, 238])
        RED = np.array([196, 30, 30])
        YELLOW = np.array([232, 190, 20])
        BLUE = np.array([25, 55, 150])
        BLACK = np.array([18, 18, 18])

        # palette dei colori assegnati per probabilita', NON dal contenuto
        # della foto: vivacita' bassa -> per lo piu' bianco (De Stijl classico,
        # pochi accenti colorati); vivacita' alta -> composizione piu' densa
        # di rosso/giallo/blu. Rosso/giallo/blu hanno sempre la STESSA
        # probabilita' fra loro, cosi' nessuno dei tre e' strutturalmente
        # sfavorito.
        p_white = max(0.15, 0.75 - 0.55 * vivacita)
        p_black = 0.08
        p_each_color = max(0.0, (1.0 - p_white - p_black) / 3.0)

        # seed per l'assegnazione colore: se non specificato un variation_seed
        # (uso normale), lo derivo dai parametri stessi -> stessa foto e stessi
        # parametri producono sempre la stessa identica composizione colore,
        # deterministica. Con un variation_seed esplicito (varianti) i colori
        # cambiano assieme alla struttura.
        if variation_seed is not None:
            color_seed = variation_seed
        else:
            color_seed = hash((round(complessita, 4), round(spessore, 4),
                                round(vivacita, 4), w, h)) & 0xFFFFFFFF
        color_rng = random.Random(color_seed)

        def pick_color():
            r = color_rng.random()
            if r < p_white:
                return WHITE
            r -= p_white
            if r < p_black:
                return BLACK
            r -= p_black
            if r < p_each_color:
                return RED
            r -= p_each_color
            if r < p_each_color:
                return YELLOW
            return BLUE

        variation_rng = random.Random(variation_seed) if variation_seed is not None else None

        cuts_a = []   # tagli in coordinate dell'immagine di analisi (ridotta)
        leaves_a = []  # rettangoli foglia in coordinate di analisi

        def best_split(x0, y0, x1, y1, parent_axis=None):
            sub = lum_a[y0:y1, x0:x1]
            sh, sw = sub.shape
            candidates = []  # (axis, pos, strength)
            margin_w = max(5, round(sw * 0.10))
            margin_h = max(5, round(sh * 0.10))
            if sw > 10:
                col_mean = sub.mean(axis=0)
                grad = np.abs(np.diff(col_mean))
                if grad.size > 0:
                    k = min(3, grad.size)
                    for idx in np.argpartition(grad, -k)[-k:]:
                        pos = x0 + max(margin_w, min(sw - margin_w, int(idx) + 1))
                        candidates.append(("v", pos, float(grad[idx])))
            if sh > 10:
                row_mean = sub.mean(axis=1)
                gradr = np.abs(np.diff(row_mean))
                if gradr.size > 0:
                    k = min(3, gradr.size)
                    for idx in np.argpartition(gradr, -k)[-k:]:
                        pos = y0 + max(margin_h, min(sh - margin_h, int(idx) + 1))
                        candidates.append(("h", pos, float(gradr[idx])))
            if not candidates:
                return ("v", x0 + sw // 2) if sw >= sh else ("h", y0 + sh // 2)
            # penalita' se il taglio e' nella STESSA direzione del genitore:
            # senza questo, la ricorsione tende a tagliare sempre nello stesso
            # verso (es. solo orizzontale) producendo tante strisce sottili
            # impilate invece di una vera griglia di rettangoli come nel
            # Mondrian classico. La penalita' scoraggia ma non vieta — se una
            # direzione e' nettamente piu' forte vince comunque.
            if parent_axis is not None:
                candidates = [(a, p, s * (0.5 if a == parent_axis else 1.0)) for a, p, s in candidates]
            if variation_rng is None:
                axis, pos, _ = max(candidates, key=lambda c: c[2])
                return axis, pos
            # scelta pesata sulla forza del gradiente: i tagli piu' netti
            # restano i piu' probabili, ma non vince sempre lo stesso identico
            # taglio -> varianti con composizioni geometriche diverse.
            weights = [c[2] ** 2 + 1e-6 for c in candidates]
            r = variation_rng.random() * sum(weights)
            acc = 0.0
            for c, wgt in zip(candidates, weights):
                acc += wgt
                if r <= acc:
                    return c[0], c[1]
            return candidates[-1][0], candidates[-1][1]

        def recurse(x0, y0, x1, y1, depth, parent_axis=None):
            w_, h_ = x1 - x0, y1 - y0
            min_size = min(aw, ah) * 0.09
            if depth >= max_depth or w_ < min_size or h_ < min_size:
                leaves_a.append((x0, y0, x1, y1))
                return
            axis, pos = best_split(x0, y0, x1, y1, parent_axis)
            if axis == "v":
                cuts_a.append((pos, y0, pos, y1))
                recurse(x0, y0, pos, y1, depth + 1, axis)
                recurse(pos, y0, x1, y1, depth + 1, axis)
            else:
                cuts_a.append((x0, pos, x1, pos))
                recurse(x0, y0, x1, pos, depth + 1, axis)
                recurse(x0, pos, x1, y1, depth + 1, axis)

        recurse(0, 0, aw, ah, 0)

        # riscalo tagli e foglie sulla risoluzione piena
        sx, sy = w / aw, h / ah

        out = np.full((h, w, 3), 250, dtype=np.float32)
        for (x0, y0, x1, y1) in leaves_a:
            X0, Y0 = int(round(x0*sx)), int(round(y0*sy))
            X1, Y1 = int(round(x1*sx)), int(round(y1*sy))
            X0, Y0 = min(X0, w - 1), min(Y0, h - 1)      # mai oltre l'ultimo pixel valido
            X1, Y1 = max(X1, X0 + 1), max(Y1, Y0 + 1)    # cella sempre non-vuota
            X1, Y1 = min(X1, w), min(Y1, h)               # mai oltre il bordo immagine
            out[Y0:Y1, X0:X1] = pick_color()

        result = out.astype(np.uint8).copy()
        for (x0, y0, x1, y1) in cuts_a:
            if x0 == x1:
                X = int(round(x0*sx))
                Y0, Y1 = int(round(y0*sy)), int(round(y1*sy))
                xs = slice(max(0, X - line_px // 2), min(w, X + line_px - line_px // 2))
                result[Y0:Y1, xs] = 15
            else:
                Y = int(round(y0*sy))
                X0, X1 = int(round(x0*sx)), int(round(x1*sx))
                ys = slice(max(0, Y - line_px // 2), min(h, Y + line_px - line_px // 2))
                result[ys, X0:X1] = 15
        result[0:line_px, :] = 15
        result[-line_px:, :] = 15
        result[:, 0:line_px] = 15
        result[:, -line_px:] = 15

        return Image.fromarray(result, mode="RGB")
    except Exception as e:
        st.error(f"Mondrian: {e}"); return img


def glitch_van_gogh(img, turbolenza=0.6, pennellata=0.5, saturazione=0.5):
    """Pittura ad olio 'Notte Stellata': tensore di struttura (Sobel + blur)
    per trovare l'orientamento locale dei contorni -> pennellate direzionali
    (smear lungo la tangente, non a caso). Vortice gaussiano centrato sul
    punto piu' luminoso dell'immagine, rotazione che decade con la distanza.
    Quantizzazione + boost colore finale per l'effetto materico. Come Rothko,
    l'elaborazione (la piu' pesante del pacchetto, per via delle pennellate
    campionate piu' volte) avviene su una copia ridotta e viene poi
    riportata alla risoluzione originale: su una foto vera passa da
    30-40 secondi a pochi secondi, e l'effetto pittorico non perde nulla
    (anzi la leggera morbidezza dell'upscale aiuta l'aspetto materico).

    turbolenza  : 0-1, forza del vortice attorno al punto piu' luminoso
    pennellata  : 0-1, lunghezza dello smear direzionale (pennellata)
    saturazione : 0-1, boost colore + posterizzazione materica
    """
    try:
        orig_w, orig_h = img.size
        work_img, _ = _downscale_for_work(img.convert("RGB"), max_dim=1100)
        rgb = np.array(work_img, dtype=np.float32)
        h, w = rgb.shape[:2]
        gray = (rgb[..., 0]*0.299 + rgb[..., 1]*0.587 + rgb[..., 2]*0.114) / 255.0

        blurred_lum = _box_blur(gray, max(2, min(h, w) // 20))
        cy, cx = np.unravel_index(np.argmax(blurred_lum), blurred_lum.shape)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx, dy = xx - cx, yy - cy
        r = np.sqrt(dx*dx + dy*dy)
        R = min(h, w) * 0.55
        k = turbolenza * 2.8
        angle = k * np.exp(-(r / R) ** 2)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        src_x = cx + dx*cos_a - dy*sin_a
        src_y = cy + dx*sin_a + dy*cos_a
        ix = np.clip(np.round(src_x).astype(np.int32), 0, w - 1)
        iy = np.clip(np.round(src_y).astype(np.int32), 0, h - 1)
        swirled = rgb[iy, ix]

        sw_gray = (swirled[..., 0]*0.299 + swirled[..., 1]*0.587 + swirled[..., 2]*0.114) / 255.0
        gx, gy = _sobel(sw_gray)
        Jxx = _box_blur(gx * gx, 2)
        Jyy = _box_blur(gy * gy, 2)
        Jxy = _box_blur(gx * gy, 2)
        theta = 0.5 * np.arctan2(2 * Jxy, (Jxx - Jyy) + 1e-6)

        L = 2.0 + pennellata * 16.0
        N = 7
        acc = np.zeros_like(swirled)
        ct, st_ = np.cos(theta), np.sin(theta)
        for t in np.linspace(-L / 2, L / 2, N):
            sx = np.clip(np.round(xx + t * ct).astype(np.int32), 0, w - 1)
            sy = np.clip(np.round(yy + t * st_).astype(np.int32), 0, h - 1)
            acc += swirled[sy, sx]
        painted = acc / N

        mean = painted.mean(axis=-1, keepdims=True)
        painted = mean + (painted - mean) * (1.0 + saturazione * 1.4)
        levels = 18 - saturazione * 8
        painted = np.round(painted / levels) * levels

        out = np.clip(painted, 0, 255).astype(np.uint8)
        result = Image.fromarray(out, mode="RGB")
        if result.size != (orig_w, orig_h):
            result = result.resize((orig_w, orig_h), Image.LANCZOS)
        return result
    except Exception as e:
        st.error(f"Van Gogh Swirl: {e}"); return img


def glitch_rothko(img, bande=0.4, sfumatura=0.5, grana=0.4, variation_seed=None):
    """Color field alla Rothko: la STRUTTURA (dove cadono i confini fra le
    bande orizzontali) e' guidata dalla foto — individuata nei punti di
    massima variazione di luminanza, non su una griglia fissa, cosi' foto
    diverse producono partiture di bande diverse. Il COLORE di ogni banda
    pero' non deriva mai dalla foto (niente media dei pixel reali): viene
    scelto da una palette curata di toni densi e vellutati ispirati alle
    serie Seagram/Multiform di Rothko — come in Mondrian, e' la palette a
    decidere le sfumature, non il contenuto dell'immagine. Feathering
    gaussiano ai bordi (bleed morbido tipico) e grana di tela sovrapposta
    completano l'effetto. L'elaborazione pesante (blur, feathering, grana)
    avviene su una copia ridotta dell'immagine e viene poi riportata alla
    risoluzione originale: sulle foto vere (alcuni megapixel) questo taglia
    i tempi da decine di secondi a meno di un secondo, senza perdita
    percepibile (le bande Rothko sono comunque campi di colore piatto, non
    serve dettaglio pixel-per-pixel).

    bande          : 0-1, numero di bande di colore (2-5)
    sfumatura      : 0-1, quanto le bande sfumano l'una nell'altra
    grana          : 0-1, intensita' della grana di tela
    variation_seed : opzionale. Se None (default) l'assegnazione colore e'
        deterministica per la stessa foto/parametri. Se specificato (usato
        dal generatore di varianti) rimescola la scelta della palette per
        banda, cosi' ogni variante ha una combinazione di colori diversa.
    """
    try:
        orig_w, orig_h = img.size
        work_img, _ = _downscale_for_work(img.convert("RGB"), max_dim=1000)
        rgb = np.array(work_img, dtype=np.float32)
        h, w = rgb.shape[:2]
        lum = rgb[..., 0]*0.299 + rgb[..., 1]*0.587 + rgb[..., 2]*0.114
        row_mean = lum.mean(axis=1)
        row_mean_s = _box_blur(row_mean.reshape(-1, 1), max(2, h // 40)).ravel()

        n_bands = 2 + round(bande * 3)
        grad = np.abs(np.diff(row_mean_s))
        min_gap = h // (n_bands * 2)
        cuts = []
        grad_work = grad.copy()
        for _ in range(n_bands - 1):
            if grad_work.size == 0:
                break
            idx = int(np.argmax(grad_work))
            if grad_work[idx] <= 0:
                break
            cuts.append(idx + 1)
            lo, hi = max(0, idx - min_gap), min(len(grad_work), idx + min_gap)
            grad_work[lo:hi] = -1
        cuts = sorted(cuts)
        bounds = [0] + cuts + [h]

        # Palette Rothko: toni densi e vellutati ispirati alle serie
        # Seagram/Multiform — assegnata per PROBABILITA', mai letta dai
        # pixel della foto (quella decide solo dove cadono i confini,
        # sopra). Stessa logica di Mondrian: e' la palette a scegliere le
        # sfumature, non il contenuto dell'immagine.
        ROTHKO_PALETTE = [
            (176, 34, 28),    # rosso cadmio
            (94, 24, 24),     # bordeaux profondo
            (198, 93, 30),    # arancio bruciato
            (200, 148, 40),   # ocra dorata
            (210, 170, 90),   # giallo caldo/sabbia
            (25, 22, 20),     # nero/carbone
            (20, 35, 70),     # blu notte
            (70, 30, 60),     # viola prugna
            (176, 100, 90),   # rosa sbiadito
            (110, 20, 35),    # bordeaux acceso
        ]

        # seed per l'assegnazione colore: se non specificato un
        # variation_seed (uso normale), lo derivo dai parametri stessi ->
        # stessa foto e stessi parametri producono sempre la stessa
        # identica combinazione di colori, deterministica.
        if variation_seed is not None:
            color_seed = variation_seed
        else:
            color_seed = hash((round(bande, 4), round(sfumatura, 4),
                                round(grana, 4), w, h)) & 0xFFFFFFFF
        color_rng = random.Random(color_seed)

        def pick_band_color(prev_color):
            # evita (quando possibile) che due bande adiacenti prendano
            # esattamente lo stesso colore
            choices = [c for c in ROTHKO_PALETTE if c != prev_color] or ROTHKO_PALETTE
            return color_rng.choice(choices)

        field = np.zeros_like(rgb)
        prev_color = None
        for i in range(len(bounds) - 1):
            y0, y1 = bounds[i], bounds[i + 1]
            if y1 <= y0:
                continue
            color = pick_band_color(prev_color)
            prev_color = color
            field[y0:y1, :] = np.array(color, dtype=np.float32)

        feather_r = int(2 + sfumatura * (h * 0.06))
        soft = np.stack([_box_blur(field[..., c], feather_r) for c in range(3)], axis=-1)
        mix = 0.25 + sfumatura * 0.6
        out = field * (1 - mix) + soft * mix

        # seed grana: legato a variation_seed quando presente, cosi' anche
        # la texture di tela cambia fra una variante e l'altra (prima era
        # fisso a 7 e restava identico su tutte le varianti generate).
        grain_seed = variation_seed if variation_seed is not None else 7
        rng = np.random.default_rng(grain_seed)
        noise = rng.normal(0, 1, (h, w))
        noise = _box_blur(noise, 1)
        noise = (noise - noise.mean()) / (noise.std() + 1e-6)
        out = out * (1 + noise[..., None] * grana * 0.10)

        out = np.clip(out, 0, 255).astype(np.uint8)
        result = Image.fromarray(out, mode="RGB")
        if result.size != (orig_w, orig_h):
            result = result.resize((orig_w, orig_h), Image.LANCZOS)
        return result
    except Exception as e:
        st.error(f"Rothko: {e}"); return img


def glitch_lichtenstein_comic(img, contrasto=0.5, dimensione_puntini=0.5, spessore_contorno=0.4):
    """Pop-art fumetto: rilevo i bordi (Sobel) e li dilato per il contorno nero
    spesso; quantizzo i colori a pochi livelli piatti e saturi; sovrappongo
    una vera griglia di puntini Ben-Day (dot-screen) la cui dimensione per
    punto dipende dalla luminanza locale, limitata alle zone di mezzotono
    (le luci restano pulite, le ombre non affogano nei puntini).

    contrasto           : 0-1, saturazione e numero di livelli colore piatti
    dimensione_puntini   : 0-1, dimensione della cella dei puntini Ben-Day
    spessore_contorno    : 0-1, spessore del contorno nero (dilatazione bordi)
    """
    try:
        orig_w, orig_h = img.size
        work_img, _ = _downscale_for_work(img.convert("RGB"), max_dim=1400)
        rgb = np.array(work_img, dtype=np.float32)
        h, w = rgb.shape[:2]
        gray = (rgb[..., 0]*0.299 + rgb[..., 1]*0.587 + rgb[..., 2]*0.114) / 255.0

        mean = rgb.mean(axis=-1, keepdims=True)
        sat_boost = 1.0 + contrasto * 1.2
        boosted = np.clip(mean + (rgb - mean) * sat_boost, 0, 255)
        levels = max(2, round(5 - contrasto * 3))
        step = 255.0 / levels
        flat = np.round(boosted / step) * step

        cell = max(3, round(4 + dimensione_puntini * 10))
        yy, xx = np.mgrid[0:h, 0:w]
        cyc_x = (xx % cell) - cell / 2.0
        cyc_y = (yy % cell) - cell / 2.0
        dist = np.sqrt(cyc_x**2 + cyc_y**2)
        dot_radius = (1.0 - gray) * (cell * 0.62)
        dot_mask = dist < dot_radius
        midtone = (gray > 0.15) & (gray < 0.80)
        dot_mask = dot_mask & midtone

        ink = np.array([25, 25, 30], dtype=np.float32)
        with_dots = flat.copy()
        with_dots[dot_mask] = with_dots[dot_mask] * 0.35 + ink * 0.65

        gx, gy = _sobel(gray)
        edge_mag = np.sqrt(gx*gx + gy*gy)
        thr = np.percentile(edge_mag, 100 - 12)
        edge_mask = edge_mag > max(thr, 0.05)
        dilate_iters = max(0, round(spessore_contorno * 3))
        for _ in range(dilate_iters):
            edge_mask = (edge_mask
                         | np.roll(edge_mask, 1, axis=0) | np.roll(edge_mask, -1, axis=0)
                         | np.roll(edge_mask, 1, axis=1) | np.roll(edge_mask, -1, axis=1))

        out = with_dots.copy()
        out[edge_mask] = [10, 10, 12]

        out = np.clip(out, 0, 255).astype(np.uint8)
        result = Image.fromarray(out, mode="RGB")
        if result.size != (orig_w, orig_h):
            result = result.resize((orig_w, orig_h), Image.LANCZOS)
        return result
    except Exception as e:
        st.error(f"Lichtenstein Comic: {e}"); return img


def glitch_klimt_mosaico(img, dim_tessere=0.5, doratura=0.6, irregolarita=0.4):
    """Klimt 'fase dorata': mosaico di tessere irregolari (Voronoi su griglia
    jittered, ricerca vettoriale sui 9 vicini di griglia -> veloce anche su
    foto grandi) colorate col tono medio reale della zona ma spinte verso
    una palette oro/bronzo/smeraldo; bordi scuri fra tessera e tessera;
    luccichio metallico per-tessera per simulare la foglia oro.

    dim_tessere   : 0-1, dimensione media delle tessere
    doratura      : 0-1, quanto il colore viene spinto verso la palette oro/Klimt
    irregolarita  : 0-1, quanto i centri delle tessere sono jitterati (organicita')
    """
    try:
        orig_w, orig_h = img.size
        work_img, _ = _downscale_for_work(img.convert("RGB"), max_dim=1400)
        rgb = np.array(work_img, dtype=np.float32)
        h, w = rgb.shape[:2]

        cell = max(6, round(10 + dim_tessere * 34))
        jitter_amt = irregolarita * cell * 0.42

        rows = int(np.ceil(h / cell)) + 2
        cols = int(np.ceil(w / cell)) + 2
        rng = np.random.default_rng(11)
        base_gy = (np.arange(rows) - 1) * cell
        base_gx = (np.arange(cols) - 1) * cell
        gcy, gcx = np.meshgrid(base_gy, base_gx, indexing="ij")
        gcy = gcy + rng.uniform(-jitter_amt, jitter_amt, size=gcy.shape)
        gcx = gcx + rng.uniform(-jitter_amt, jitter_amt, size=gcx.shape)

        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        row_i = np.floor(yy / cell).astype(np.int32) + 1
        col_i = np.floor(xx / cell).astype(np.int32) + 1

        best_d = np.full((h, w), 1e18, dtype=np.float32)
        best_id = np.zeros((h, w), dtype=np.int32)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr = np.clip(row_i + dr, 0, rows - 1)
                cc = np.clip(col_i + dc, 0, cols - 1)
                cx = gcx[rr, cc]
                cy = gcy[rr, cc]
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                mask = d < best_d
                best_d = np.where(mask, d, best_d)
                best_id = np.where(mask, rr * cols + cc, best_id)

        n_ids = rows * cols
        ids_flat = best_id.ravel()
        counts = np.bincount(ids_flat, minlength=n_ids).astype(np.float32)
        counts_safe = np.maximum(counts, 1)
        mean_color = np.zeros((n_ids, 3), dtype=np.float32)
        for c in range(3):
            sums = np.bincount(ids_flat, weights=rgb[..., c].ravel(), minlength=n_ids)
            mean_color[:, c] = sums / counts_safe

        GOLD_PALETTE = np.array([
            [201, 162, 39], [176, 124, 33], [222, 190, 90],
            [120, 40, 40], [30, 90, 70], [15, 15, 18],
        ], dtype=np.float32)
        lum = mean_color[:, 0]*0.299 + mean_color[:, 1]*0.587 + mean_color[:, 2]*0.114
        gold_idx = np.clip((lum/255.0 * (len(GOLD_PALETTE)-1)).astype(np.int32), 0, len(GOLD_PALETTE)-1)
        gold = GOLD_PALETTE[gold_idx]
        glint = rng.uniform(0.85, 1.18, size=n_ids).astype(np.float32)[:, None]
        tess_color = (mean_color*(1-doratura) + gold*doratura) * glint

        out = tess_color[best_id]

        border = (np.roll(best_id, 1, axis=0) != best_id) | (np.roll(best_id, 1, axis=1) != best_id)
        out[border] = out[border] * 0.25

        out = np.clip(out, 0, 255).astype(np.uint8)
        result = Image.fromarray(out, mode="RGB")
        if result.size != (orig_w, orig_h):
            result = result.resize((orig_w, orig_h), Image.LANCZOS)
        return result
    except Exception as e:
        st.error(f"Klimt Mosaico: {e}"); return img


def glitch_munch_onde(img, ampiezza_onde=0.5, frequenza=0.5, intensita_colore=0.5):
    """Munch 'L'Urlo': campo di flusso concentrico (onde multi-ottava attorno
    a un centro fuori quadro) che deforma i pixel lungo linee curve tangenti;
    remap colore verso la palette espressionista (blu/nero profondi nelle
    ombre, arancio/rosso bruciato nelle luci); banding di luminosita'
    visibile anche sui fondali piatti per le pennellate concentriche.

    ampiezza_onde     : 0-1, intensita' della deformazione a onde concentriche
    frequenza         : 0-1, quante onde (frequenza spaziale delle bande)
    intensita_colore  : 0-1, quanto il colore viene spinto verso la palette Munch
    """
    try:
        orig_w, orig_h = img.size
        work_img, _ = _downscale_for_work(img.convert("RGB"), max_dim=1400)
        rgb = np.array(work_img, dtype=np.float32)
        h, w = rgb.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

        ccx, ccy = w * 0.5, -h * 0.35
        dx, dy = xx - ccx, yy - ccy
        r = np.sqrt(dx*dx + dy*dy) + 1e-6
        base_angle = np.arctan2(dy, dx)
        tx, ty = -dy / r, dx / r

        freq = 0.015 + frequenza * 0.05
        amp = ampiezza_onde * (8 + frequenza * 10)
        wave = (np.sin(r * freq) * 1.0
                + np.sin(r * freq * 2.3 + 1.7) * 0.5
                + np.sin(base_angle * 6.0 + r * freq * 0.5) * 0.35)
        disp = wave * amp

        src_x = np.clip(np.round(xx + tx * disp).astype(np.int32), 0, w - 1)
        src_y = np.clip(np.round(yy + ty * disp).astype(np.int32), 0, h - 1)
        warped = rgb[src_y, src_x]

        lum = (warped[..., 0]*0.299 + warped[..., 1]*0.587 + warped[..., 2]*0.114) / 255.0
        DEEP = np.array([15, 25, 60], dtype=np.float32)
        MID = np.array([140, 60, 40], dtype=np.float32)
        HOT = np.array([235, 110, 30], dtype=np.float32)
        t = lum[..., None]
        munch_col = np.where(t < 0.5,
                              DEEP*(1-t*2) + MID*(t*2),
                              MID*(1-(t-0.5)*2) + HOT*((t-0.5)*2))

        mean = warped.mean(axis=-1, keepdims=True)
        desat = mean + (warped - mean) * 0.4
        out = desat * (1 - intensita_colore) + munch_col * intensita_colore

        wave_norm = wave / 1.85
        out = out * (1 + 0.14 * ampiezza_onde * wave_norm[..., None])

        out = np.clip(out, 0, 255).astype(np.uint8)
        result = Image.fromarray(out, mode="RGB")
        if result.size != (orig_w, orig_h):
            result = result.resize((orig_w, orig_h), Image.LANCZOS)
        return result
    except Exception as e:
        st.error(f"Munch Onde: {e}"); return img


def glitch_wave_interference(img, freq=0.55, warp=0.65, chroma=0.5):
    """Griglia sinusoidale verticale la cui fase e' deformata dalla luminanza
    locale (le zone chiare piegano le righe, il nero resta piatto/vuoto).
    Canali RGB separati leggermente in X -> frangia cromatica sui bordi.
    Ricostruisce il look 'scan line portrait' / interferenza ottica a righe
    ondulate con aberrazione cromatica.

    freq   : 0-1, spaziatura delle righe (piu' alto = righe piu' fitte)
    warp   : 0-1, quanto la luminanza deforma la fase della griglia
    chroma : 0-1, sfasamento R/G/B (aberrazione cromatica)
    """
    try:
        rgb = np.array(img.convert("RGB"), dtype=np.float32) / 255.0
        lum = rgb[..., 0]*0.299 + rgb[..., 1]*0.587 + rgb[..., 2]*0.114
        h, w = lum.shape

        xs = np.arange(w, dtype=np.float32)
        X = np.broadcast_to(xs, (h, w))

        period = 18.0 - freq * 14.0
        base_k = 2.0 * np.pi / period
        phase_amp = warp * 6.0

        def render_channel(shift_px):
            Xs = X + shift_px
            phase = lum * phase_amp
            grating = 0.5 + 0.5 * np.sin(Xs * base_k + phase * 2.0 * np.pi)
            return grating * (lum ** 0.8)

        shift = chroma * 3.0
        R = render_channel(-shift)
        G = render_channel(0.0)
        B = render_channel(shift)

        out = np.clip(np.stack([R, G, B], axis=-1), 0, 1)
        out = (out * 255).astype(np.uint8)
        return Image.fromarray(out, mode="RGB")
    except Exception as e:
        st.error(f"Wave Interference: {e}"); return img


# ══════════════════════════════════════════════════════════════════════════════
#  CATALOGO EFFETTI
# ══════════════════════════════════════════════════════════════════════════════

EFFECTS = [
    ("ascii_art", "ASCII Art", "🔤", glitch_ascii_art, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "as_int"),
        ("Colore",         0.0, 1.0, 0.5, 0.05, "as_col"),
        ("Dim. Cella",     0.2, 3.0, 1.0, 0.1, "as_cel"),
    ]),
    ("channel_swap", "Channel Swap", "🔁", glitch_channel_swap, [
        ("Modalità (0-5)", 0.0, 1.0, 0.0, 0.2,  "cs_mode"),
        ("Blend",          0.0, 1.0, 0.6, 0.05, "cs_blend"),
        ("Shift px",       0.0, 1.0, 0.0, 0.05, "cs_shift"),
    ]),
    ("chromatic", "Chromatic Ab.", "🌈", glitch_chromatic, [
        ("Forza",          0.0, 1.0, 0.5, 0.05, "chr_forza"),
        ("Angolo",         0.0, 1.0, 0.0, 0.05, "chr_ang"),
        ("Zoom aberr.",    0.0, 1.0, 0.3, 0.05, "chr_zoom"),
    ]),
    ("crosshatch", "Crosshatch", "✏️", glitch_crosshatch, [
        ("Densità",        0.0, 1.0, 0.5, 0.05, "ch_den"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05, "ch_ang"),
        ("Spessore",       0.0, 1.0, 0.3, 0.05, "ch_thick"),
    ]),
    ("datamosh", "Datamosh", "📼", glitch_datamosh, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dm_block"),
        ("Decay",          0.0, 1.0, 0.5, 0.05, "dm_decay"),
        ("N. Blocchi",     0.0, 1.0, 0.5, 0.05, "dm_num"),
    ]),
    ("destruction_art", "Destruction Art", "✂️", glitch_destruction_art, [
        ("Tagli",          0.0, 1.0, 0.5, 0.05, "da_cuts"),
        ("Scatter",        0.0, 1.0, 0.4, 0.05, "da_scatter"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 0.0, 0.5,  "da_asse"),
    ]),
    ("displacement_map", "Displacement Map", "🌊", glitch_displacement_map, [
        ("Forza",          0.0, 1.0, 0.5, 0.05, "dsp_forza"),
        ("Blur Scala",     0.0, 1.0, 0.4, 0.05, "dsp_blur"),
        ("Canale (R/G/B)", 0.0, 1.0, 0.0, 0.5,  "dsp_canale"),
    ]),
    ("distruttivo", "Distruttivo", "💥", glitch_distruttivo, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dest_size"),
        ("Num. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dest_num"),
        ("Spostamento",    0.0, 2.0, 1.0, 0.1,  "dest_disp"),
    ]),
    ("drip", "Drip Sort", "🌊💧", glitch_drip, [
        ("Soglia lum.",    0.0, 1.0, 0.3, 0.05, "drip_soglia"),
        ("Sep. RGB",       0.0, 1.0, 0.5, 0.05, "drip_rgb"),
        ("Asse (0=V 1=H)", 0.0, 1.0, 0.0, 0.5,  "drip_asse"),
    ]),
    ("duotone", "Duotone", "🎭", glitch_duotone, [
        ("Colore 1 (hue)", 0.0, 1.0, 0.1, 0.05, "dt_c1"),
        ("Colore 2 (hue)", 0.0, 1.0, 0.6, 0.05, "dt_c2"),
        ("Blend",          0.0, 1.0, 0.8, 0.05, "dt_blend"),
    ]),
    ("analogic", "Glitch Analogic", "📻", glitch_analogic, [
        ("Sync Loss",      0.0, 1.0, 0.5, 0.05, "ag_sync"),
        ("Color Bleed",    0.0, 1.0, 0.4, 0.05, "ag_bleed"),
        ("Static",         0.0, 1.0, 0.3, 0.05, "ag_static"),
    ]),
    ("halftone", "Halftone", "🔵", glitch_halftone, [
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05, "ht_size"),
        ("Sfondo bianco",  0.0, 1.0, 1.0, 0.5,  "ht_sfondo"),
        ("Colore",         0.0, 1.0, 0.7, 0.05, "ht_color"),
    ]),
    ("image_feedback", "Image Feedback", "📡🔁", glitch_image_feedback, [
        ("Zoom",           0.0, 1.0, 0.5, 0.05, "fb_zoom"),
        ("Iterazioni",     0.0, 1.0, 0.4, 0.05, "fb_iter"),
        ("Decay",          0.0, 1.0, 0.5, 0.05, "fb_decay"),
    ]),
    ("klimt_mosaico", "Klimt Mosaico", "🟨", glitch_klimt_mosaico, [
        ("Dim. Tessere",   0.0, 1.0, 0.5, 0.05, "kl_size"),
        ("Doratura",       0.0, 1.0, 0.6, 0.05, "kl_gold"),
        ("Irregolarità",   0.0, 1.0, 0.4, 0.05, "kl_irreg"),
    ]),
    ("lichtenstein_comic", "Lichtenstein Comic", "💬", glitch_lichtenstein_comic, [
        ("Contrasto Colori",   0.0, 1.0, 0.5, 0.05, "li_contrast"),
        ("Dimensione Puntini", 0.0, 1.0, 0.5, 0.05, "li_dots"),
        ("Spessore Contorno",  0.0, 1.0, 0.4, 0.05, "li_outline"),
    ]),
    ("mirror_kal", "Mirror Kaleido.", "🪞", glitch_mirror_kaleidoscope, [
        ("Specchi (4/6/8)", 0.0, 1.0, 0.3, 0.1,  "mk_mirrors"),
        ("Rotazione",       0.0, 1.0, 0.0, 0.05, "mk_rot"),
        ("Zoom",            0.0, 1.0, 0.5, 0.05, "mk_zoom"),
    ]),
    ("moire", "Moire Pattern", "🔲", glitch_moire, [
        ("Frequenza 1",    0.0, 1.0, 0.4, 0.05, "mo_f1"),
        ("Frequenza 2",    0.0, 1.0, 0.6, 0.05, "mo_f2"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05, "mo_ang"),
    ]),
    ("mondrian", "Mondrian", "🟦", glitch_mondrian, [
        ("Complessità",     0.0, 1.0, 0.55, 0.05, "mn_complex"),
        ("Spessore Linee",  0.0, 1.0, 0.5,  0.05, "mn_lines"),
        ("Vivacità Colori", 0.0, 1.0, 0.6,  0.05, "mn_vivid"),
    ]),
    ("munch_onde", "Munch Onde", "🌊😱", glitch_munch_onde, [
        ("Ampiezza Onde",     0.0, 1.0, 0.5,  0.05, "mu_amp"),
        ("Frequenza",         0.0, 1.0, 0.5,  0.05, "mu_freq"),
        ("Intensità Colore",  0.0, 1.0, 0.55, 0.05, "mu_col"),
    ]),
    ("neon_glow", "Neon Glow", "💡", glitch_neon_glow, [
        ("Soglia bordi",   0.0, 1.0, 0.3, 0.05, "ng_thresh"),
        ("Ampiezza glow",  0.0, 1.0, 0.5, 0.05, "ng_width"),
        ("Colore (0-4)",   0.0, 1.0, 0.0, 0.25, "ng_color"),
    ]),
    ("noise", "Noise", "🌀", glitch_noise, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "noise_int"),
        ("Copertura",      0.0, 1.0, 0.7, 0.05, "noise_cov"),
        ("Tipo (0=bande 0.5=pixel 1=onde)", 0.0, 1.0, 0.0, 0.01, "noise_tipo"),
    ]),
    ("oil_paint", "Oil Paint", "🖌️", glitch_oil_paint, [
        ("Raggio",         0.0, 1.0, 0.3, 0.05, "op_rad"),
        ("Livelli",        0.0, 1.0, 0.5, 0.05, "op_lev"),
        ("Blend",          0.0, 1.0, 0.7, 0.05, "op_blend"),
    ]),
    ("op_art_circles", "Op Art Circles", "⭕", glitch_op_art_circles, [
        ("Frequenza",      0.0, 1.0, 0.5, 0.05, "oa_freq"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05, "oa_cont"),
        ("Blend",          0.0, 1.0, 0.5, 0.05, "oa_blend"),
    ]),
    ("pixel_sort", "Pixel Sort", "🔀", glitch_pixel_sort, [
        ("Soglia lum.",    0.0, 1.0, 0.4, 0.05, "ps_thresh"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 1.0, 0.5,  "ps_asse"),
        ("Span max",       0.0, 1.0, 0.8, 0.05, "ps_span"),
    ]),
    ("polar", "Polar Coords", "🌀", glitch_polar, [
        ("Forza",          0.0, 1.0, 0.6, 0.05, "pol_str"),
        ("Rotazione",      0.0, 1.0, 0.0, 0.05, "pol_rot"),
        ("Zoom",           0.0, 1.0, 0.5, 0.05, "pol_zoom"),
    ]),
    ("pop_art_warhol", "Pop Art Warhol", "🍅", glitch_pop_art_warhol, [
        ("Contrasto",        0.0, 1.0, 0.6, 0.05, "pa_cont"),
        ("Palette (0-6)",    0.0, 1.0, 0.0, 0.143, "pa_pal"),
        ("Misregistrazione", 0.0, 1.0, 0.4, 0.05, "pa_mis"),
    ]),
    ("posterize", "Posterize", "🎨", glitch_posterize, [
        ("Livelli",        0.0, 1.0, 0.4, 0.05, "po_lev"),
        ("Dither",         0.0, 1.0, 0.4, 0.05, "po_dith"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05, "po_col"),
    ]),
    ("psychedelic", "Psychedelic", "🔮", glitch_psychedelic, [
        ("Hue Shift",      0.0, 1.0, 0.3, 0.05, "psy_hue"),
        ("Saturazione",    0.0, 1.0, 0.5, 0.05, "psy_sat"),
        ("Inversione",     0.0, 1.0, 0.0, 0.05, "psy_inv"),
    ]),
    ("retro_palette", "Retro Palette C64", "🕹️", glitch_retro_palette, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "rp_int"),
        ("Dithering",      0.0, 1.0, 0.5, 0.05, "rp_dit"),
        ("Dim. Pixel",     0.2, 3.0, 1.0, 0.1, "rp_pix"),
    ]),
    ("rothko", "Rothko", "🟪", glitch_rothko, [
        ("Bande",       0.0, 1.0, 0.4, 0.05, "rk_bands"),
        ("Sfumatura",   0.0, 1.0, 0.5, 0.05, "rk_feather"),
        ("Grana Tela",  0.0, 1.0, 0.4, 0.05, "rk_grain"),
    ]),
    ("rutt_etra", "Rutt-Etra", "📺⚡", glitch_rutt_etra, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "re_int"),
        ("Densità Linee",  0.2, 2.0, 1.0, 0.1, "re_spc"),
        ("Spostamento",    0.0, 2.0, 1.0, 0.1, "re_dsp"),
    ]),
    ("scanline_burn", "Scanline Burn", "📟", glitch_scanline_burn, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "sb_int"),
        ("Densità",        0.0, 1.0, 0.4, 0.05, "sb_den"),
        ("Color Bleed",    0.0, 1.0, 0.5, 0.05, "sb_bleed"),
    ]),
    ("solarize", "Solarize", "☀️", glitch_solarize, [
        ("Soglia",         0.0, 1.0, 0.5, 0.05, "sol_thresh"),
        ("Forza",          0.0, 1.0, 0.8, 0.05, "sol_str"),
        ("Channel Split",  0.0, 1.0, 0.3, 0.05, "sol_ch"),
    ]),
    ("stippling", "Stippling", "🔴", glitch_stippling, [
        ("Densità",        0.0, 1.0, 0.5, 0.05, "st_den"),
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05, "st_dot"),
        ("Colore",         0.0, 1.0, 0.6, 0.05, "st_col"),
    ]),
    ("temporal_bands", "Temporal Bands", "⏳🎞️", glitch_temporal_bands, [
        ("Intensità",       0.0, 1.0, 0.7, 0.05, "tbs_int"),
        ("Ampiezza Bande",  0.0, 1.0, 0.5, 0.05, "tbs_amp"),
        ("Spostamento",     0.0, 1.0, 0.6, 0.05, "tbs_spo"),
    ]),
    ("thermal", "Thermal Camera", "🌡️", glitch_thermal, [
        ("Palette (0-2)",  0.0, 1.0, 0.0, 0.5,  "th_pal"),
        ("Rumore",         0.0, 1.0, 0.2, 0.05, "th_noise"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05, "th_cont"),
    ]),
    ("tunnel_zoom", "Tunnel Zoom", "🔭", glitch_tunnel_zoom, [
        ("Strati",         0.0, 1.0, 0.5, 0.05, "tz_layers"),
        ("Velocità",       0.0, 1.0, 0.5, 0.05, "tz_speed"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05, "tz_col"),
    ]),
    ("van_gogh_swirl", "Van Gogh Swirl", "🌌", glitch_van_gogh, [
        ("Turbolenza",  0.0, 1.0, 0.6, 0.05, "vg_turb"),
        ("Pennellata",  0.0, 1.0, 0.5, 0.05, "vg_brush"),
        ("Saturazione", 0.0, 1.0, 0.5, 0.05, "vg_sat"),
    ]),
    ("vhs", "VHS", "📺", glitch_vhs, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "vhs_int"),
        ("Scanlines",      0.0, 2.0, 1.0, 0.1,  "vhs_scan"),
        ("Color Split",    0.0, 2.0, 1.0, 0.1,  "vhs_col"),
    ]),
    ("wave_interference", "Wave Interference", "📶", glitch_wave_interference, [
        ("Frequenza",         0.0, 1.0, 0.55, 0.05, "wi_freq"),
        ("Deformazione",      0.0, 1.0, 0.65, 0.05, "wi_warp"),
        ("Aberr. Cromatica",  0.0, 1.0, 0.5,  0.05, "wi_chroma"),
    ]),
    ("wave_warp", "Wave Warp", "〰️", glitch_wave_warp, [
        ("Ampiezza",       0.0, 2.0, 1.0, 0.1,  "ww_amp"),
        ("Frequenza",      0.0, 2.0, 1.0, 0.1,  "ww_freq"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 0.0, 0.5,  "ww_asse"),
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ══════════════════════════════════════════════════════════════════════════════

EFFECT_QUOTES = {
    "analogic":         "Il segnale ha perso il sincronismo. L'antenna non risponde.",
    "ascii_art":        "L'immagine e' diventata testo. Il carattere ha sostituito il colore.",
    "channel_swap":     "I canali si sono scambiati. Il colore non riconosce se stesso.",
    "chromatic":        "Il prisma ha spezzato la luce. I colori non tornano piu'.",
    "crosshatch":       "Il tratteggio ha sostituito il colore. L'incisione non mente.",
    "datamosh":         "Il frame e' rimasto bloccato. Il tempo non scorre piu'.",
    "destruction_art":  "L'immagine e' stata tagliata. Il collage e' l'unica verita'.",
    "displacement_map": "Il pixel si e' spostato seguendo se stesso. Lo spazio e' curvo.",
    "distruttivo":      "I blocchi si sono spostati. La struttura non esiste piu'.",
    "drip":             "La gravita' ha scelto i colori. Il pixel ha obbedito alla caduta.",
    "duotone":          "Due colori soltanto. La sintesi e' la forma piu' alta.",
    "halftone":         "La stampa ha dissolto l'immagine. Il punto e' tutto cio' che resta.",
    "image_feedback":   "Lo schermo si e' guardato allo specchio. L'infinito e' iniziato.",
    "klimt_mosaico":    "L'oro non decora la superficie, la sostituisce. Ogni tessera e' un frammento di eternita'.",
    "lichtenstein_comic": "Il punto e' l'unita' minima dell'emozione stampata. Whaam.",
    "mirror_kal":       "Gli specchi si sono moltiplicati. La simmetria e' diventata religione.",
    "moire":            "Le griglie si sono scontrate. Il pattern e' nato dal conflitto.",
    "mondrian":         "Linee nere, campi di colore puro. L'ordine e' geometria, non decorazione.",
    "munch_onde":       "Il cielo urla in cerchi concentrici. Il colore non descrive, grida.",
    "neon_glow":        "I bordi si sono accesi. Il buio esalta la luce.",
    "noise":            "Il segnale e' collassato. Il rumore ha preso il controllo.",
    "oil_paint":        "Il pennello ha ridisegnato la realta'. La texture ha vinto sul pixel.",
    "op_art_circles":   "I cerchi hanno ipnotizzato la forma. L'occhio non trova pace.",
    "pixel_sort":       "La luce ha scelto il suo ordine. Il pixel ha obbedito.",
    "polar":            "Lo spazio si e' avvolto su se stesso. Il centro non esiste piu'.",
    "pop_art_warhol":   "Quindici minuti di celebrita', fissati in un fotogramma acido. La serigrafia non perdona.",
    "posterize":        "Il colore e' stato ridotto all'essenziale. La serigrafia non perdona.",
    "psychedelic":      "L'hue ha ruotato oltre il visibile. La realta' e' soggettiva.",
    "retro_palette":    "Sedici colori bastano per ricordare tutto. Il pixel e' tornato all'origine.",
    "rothko":           "Grandi campi di colore che respirano piano. Nessun dettaglio, solo soglia.",
    "rutt_etra":        "Lo scanner ha riscritto la riga secondo la luce. Il segnale e' diventato forma.",
    "scanline_burn":    "Il tubo e' bruciato. Il CRT ricorda ancora.",
    "solarize":         "La luce si e' invertita. La camera oscura ha tradito l'originale.",
    "stippling":        "Il punto e' la minima unita' di verita'. Milioni di punti, una sola immagine.",
    "temporal_bands":   "Ogni riga ricorda un istante diverso. Il tempo non e' piu' uno solo.",
    "thermal":          "Il calore ha riscritto i colori. La temperatura e' la nuova forma.",
    "tunnel_zoom":      "L'immagine e' collassata verso l'interno. Il tunnel non ha fondo.",
    "van_gogh_swirl":   "Il cielo si muove anche quando l'immagine e' ferma. Vortici, non pennellate.",
    "vhs":              "Il nastro ha consumato i colori. La memoria e' distorta.",
    "wave_interference": "La griglia ha imparato la luce. Ogni riga porta la memoria del volto.",
    "wave_warp":        "La materia e' diventata liquida. La forma e' un'illusione.",
}

EFFECT_QUOTES_EN = {
    "analogic":         "The signal lost sync. The antenna no longer answers.",
    "ascii_art":        "The image has become text. The character has replaced color.",
    "channel_swap":     "The channels traded places. Color no longer recognizes itself.",
    "chromatic":        "The prism split the light. The colors never return.",
    "crosshatch":       "Hatching has replaced color. The engraving does not lie.",
    "datamosh":         "The frame got stuck. Time no longer flows.",
    "destruction_art":  "The image has been cut apart. Collage is the only truth.",
    "displacement_map": "The pixel moved, following itself. Space is curved.",
    "distruttivo":      "The blocks have shifted. Structure no longer exists.",
    "drip":             "Gravity chose the colors. The pixel obeyed the fall.",
    "duotone":          "Only two colors. Synthesis is the highest form.",
    "halftone":         "Printing dissolved the image. The dot is all that remains.",
    "image_feedback":   "The screen looked at itself in the mirror. Infinity began.",
    "klimt_mosaico":    "Gold doesn't decorate the surface, it replaces it. Every tessera is a fragment of eternity.",
    "lichtenstein_comic": "The dot is the smallest unit of printed emotion. Whaam.",
    "mirror_kal":       "The mirrors multiplied. Symmetry became religion.",
    "moire":            "The grids collided. The pattern was born from conflict.",
    "mondrian":         "Black lines, fields of pure color. Order is geometry, not decoration.",
    "munch_onde":       "The sky screams in concentric circles. Color doesn't describe, it shouts.",
    "neon_glow":        "The edges lit up. Darkness makes the light shine.",
    "noise":            "The signal collapsed. Noise took control.",
    "oil_paint":        "The brush redrew reality. Texture won over pixel.",
    "op_art_circles":   "The circles hypnotized the shape. The eye finds no rest.",
    "pixel_sort":       "Light chose its own order. The pixel obeyed.",
    "polar":            "Space folded in on itself. The center no longer exists.",
    "pop_art_warhol":   "Fifteen minutes of fame, fixed in an acid frame. The screen print never forgives.",
    "posterize":        "Color has been reduced to its essence. The screen print never forgives.",
    "psychedelic":      "Hue rotated past the visible. Reality is subjective.",
    "retro_palette":    "Sixteen colors are enough to remember everything. The pixel returned to its origin.",
    "rothko":           "Large fields of color breathing slowly. No detail, only threshold.",
    "rutt_etra":        "The scanner rewrote the line according to the light. The signal became form.",
    "scanline_burn":    "The tube is burnt. The CRT still remembers.",
    "solarize":         "The light inverted itself. The darkroom betrayed the original.",
    "stippling":        "The dot is the smallest unit of truth. A million dots, one image.",
    "temporal_bands":   "Every row remembers a different instant. Time is no longer singular.",
    "thermal":          "Heat rewrote the colors. Temperature is the new form.",
    "tunnel_zoom":      "The image collapsed inward. The tunnel has no bottom.",
    "van_gogh_swirl":   "The sky moves even while the image stands still. Vortices, not brushstrokes.",
    "vhs":              "The tape consumed the colors. Memory is distorted.",
    "wave_interference": "The grid learned the light. Every line carries the memory of a face.",
    "wave_warp":        "Matter has become liquid. Form is an illusion.",
}

EFFECT_ENGINES = {
    "analogic":         "analog_sync_engine",
    "ascii_art":        "glyph_luminance_engine",
    "channel_swap":     "channel_matrix_engine",
    "chromatic":        "radial_aberration_core",
    "crosshatch":       "hatch_render_engine",
    "datamosh":         "frame_decay_engine",
    "destruction_art":  "strip_collage_engine",
    "displacement_map": "self_displacement_engine",
    "distruttivo":      "block_fragment_engine",
    "drip":             "directional_drip_sort_engine",
    "duotone":          "dual_color_engine",
    "halftone":         "halftone_dot_engine",
    "image_feedback":   "recursive_zoom_engine",
    "klimt_mosaico":    "voronoi_tessera_gold_engine",
    "lichtenstein_comic": "bendday_dotscreen_edge_engine",
    "mirror_kal":       "radial_symmetry_engine",
    "moire":            "grid_interference_engine",
    "mondrian":         "recursive_bsp_destijl_engine",
    "munch_onde":       "concentric_flowfield_engine",
    "neon_glow":        "edge_neon_engine",
    "noise":            "entropy_noise_core",
    "oil_paint":        "kuwahara_paint_engine",
    "op_art_circles":   "concentric_wave_engine",
    "pixel_sort":       "luminance_sort_engine",
    "polar":            "polar_coords_engine",
    "pop_art_warhol":   "silkscreen_grid_engine",
    "posterize":        "color_quantize_engine",
    "psychedelic":      "hue_rotation_core",
    "retro_palette":    "c64_palette_quantize_engine",
    "rothko":           "band_segmentation_feather_engine",
    "rutt_etra":        "scan_luminance_engine",
    "scanline_burn":    "crt_burn_engine",
    "solarize":         "highlight_invert_engine",
    "stippling":        "pointillism_engine",
    "temporal_bands":   "temporal_band_slicer_engine",
    "thermal":          "false_color_engine",
    "tunnel_zoom":      "tunnel_zoom_engine",
    "van_gogh_swirl":   "structure_tensor_vortex_engine",
    "vhs":              "magnetic_tape_engine",
    "wave_interference": "phase_grating_interference_engine",
    "wave_warp":        "sinusoidal_warp_engine",
}


def build_zip_all_images(effects):
    """Crea uno zip con tutte le immagini e i report già generati (presenti in session_state)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for key, label, emoji, fn, sliders in effects:
            img_bytes = st.session_state.get(f"img_{key}")
            rep_bytes = st.session_state.get(f"rep_{key}")
            if img_bytes:
                zf.writestr(f"{key}_glitch.png", img_bytes)
            if rep_bytes:
                zf.writestr(f"{key}_report.txt", rep_bytes)
    buf.seek(0)
    return buf.getvalue()


def make_report(effect_key, effect_label, img_size, param_vals, param_labels, ts):
    w, h = img_size
    mpx = w * h / 1_000_000
    date_str, time_str = ts.split(" ")
    engine = EFFECT_ENGINES.get(effect_key, "unknown_engine")
    quote_it = EFFECT_QUOTES.get(effect_key, "Il glitch e' la verita'.")
    quote_en = EFFECT_QUOTES_EN.get(effect_key, "The glitch is the truth.")
    avg_pct = int(sum(param_vals) / len(param_vals) / 2.0 * 100) if param_vals else 0
    lines = [
        f"GLITCHLAB [IMAGE] // {effect_label.upper()} // 01 //",
        f":: MOTORE / ENGINE: {engine} [v3.0]",
        f":: PROCESSO / PROCESS: Corruzione Singolo Strato — {effect_label.upper()} "
        f"/ Single-Layer Corruption — {effect_label.upper()}",
        "",
        f'"{quote_it}"',
        f'"{quote_en}"',
        "",
        "> TECHNICAL LOG SHEET:",
        f"* Asset: {w} x {h} px  ({mpx:.2f} Mpx)",
        f"* Data / Date: {date_str}  //  {time_str}",
        f"* Effect Index: {avg_pct}%",
        "",
        f"> {effect_label.upper()} ENGINE — PARAMETRI / PARAMETERS:",
    ]
    for label, val in zip(param_labels, param_vals):
        lines.append(f"* {label:<22}: {val:.2f}")
    lines += [
        "",
        "> Regia e Algoritmo / Direction & Algorithm: Loop507",
        "",
        "#glitchart #glitchlab #loop507 #digitaldestruction",
        "#signalcorruption #experimentalimage #computationalminimalism",
    ]
    return "\n".join(lines).encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

ss_keys = (["processed"]
           + [f"img_{e[0]}"    for e in EFFECTS]
           + [f"rep_{e[0]}"    for e in EFFECTS]
           + [f"params_{e[0]}" for e in EFFECTS])
for k in ss_keys:
    if k not in st.session_state:
        st.session_state[k] = None


# ══════════════════════════════════════════════════════════════════════════════
#  UI PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

uploaded_file = st.file_uploader("📁 Carica un'immagine", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        raw_img = Image.open(uploaded_file)

        has_alpha = raw_img.mode in ("RGBA", "LA") or (
            raw_img.mode == "P" and "transparency" in raw_img.info
        )

        if has_alpha:
            bg_choice = st.radio(
                "🖼️ PNG con trasparenza rilevata — colore di sfondo da usare:",
                ["Bianco", "Nero", "Personalizzato"],
                horizontal=True, key="alpha_bg_choice"
            )
            if bg_choice == "Bianco":
                bg_color = (255, 255, 255)
            elif bg_choice == "Nero":
                bg_color = (0, 0, 0)
            else:
                bg_color = st.color_picker("Scegli colore sfondo", "#FFFFFF", key="alpha_bg_custom")
                bg_color = tuple(int(bg_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

            raw_img = raw_img.convert("RGBA")
            original_alpha = raw_img.split()[-1]
            background = Image.new("RGB", raw_img.size, bg_color)
            background.paste(raw_img, mask=original_alpha)
            img = background

            keep_transparency = st.checkbox(
                "🪟 Mantieni trasparenza originale nell'export (salva come PNG con alpha)",
                value=False, key="keep_transparency"
            )
            st.caption("Nota: per effetti che spostano i pixel (VHS, RGB shift, glitch a blocchi) "
                       "la trasparenza resta ancorata alla posizione originale, quindi ai bordi "
                       "puoi notare un leggero disallineamento tra colore ed area trasparente.")
        else:
            img = raw_img.convert("RGB")
            original_alpha = None
            keep_transparency = False

        transparency_toggled = st.session_state.get("_prev_keep_transparency") != keep_transparency
        st.session_state["_prev_keep_transparency"] = keep_transparency

        st.image(img, caption="🖼️ Originale", width=350)
        st.info(f"Dimensioni: {img.size[0]} × {img.size[1]} px")

        st.markdown("### 🎛️ Controlli Effetti")
        st.markdown("---")
        live_mode = st.checkbox(
            "⚡ Modalità Live — l'anteprima si aggiorna ad ogni slider",
            value=False, key="live_mode"
        )

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        @_fragment
        def _render_variant_explorer(entry, img, ts, keep_transparency, original_alpha):
            """Genera N varianti dello stesso effetto con parametri diversi,
            campionati casualmente entro i range degli slider. Utile per
            esplorare velocemente lo spazio dei parametri di un effetto senza
            regolare gli slider uno alla volta."""
            key, label, emoji, fn, sliders = entry
            st.markdown("#### 🎲 Esplora varianti automatiche")
            st.caption(f"Genera piu' versioni di **{emoji} {label}** con parametri diversi, "
                       "campionati a caso entro i range disponibili.")
            c1, c2 = st.columns([2, 1])
            n_variants = c1.slider("Quante varianti", 4, 30, 12, 1, key="variant_count")
            generate = c2.button("🎲 Genera varianti", key="variant_generate_btn")
            seed_input = st.text_input(
                "🌱 Seed (opzionale) — lascia vuoto per farlo generare in automatico, "
                "oppure incolla qui un seed copiato da una generazione precedente "
                "(anche di un altro effetto) per riottenere la stessa combinazione",
                value="", key="variant_seed"
            ).strip()

            if generate:
                # Se l'utente non specifica un seed, ne generiamo uno noi e lo
                # mostriamo: cosi' e' sempre possibile copiarlo e riusarlo in
                # seguito (anche su un altro effetto) per riottenere esattamente
                # la stessa sequenza di combinazioni.
                seed_used = seed_input if seed_input else str(random.randint(100000, 999999))
                rng = random.Random(seed_used)
                # se la funzione supporta 'variation_seed' (es. Mondrian), lo
                # usiamo per dare ad ogni variante anche una composizione
                # geometrica diversa, non solo colori/profondita' diversi —
                # altrimenti su foto con poche zone di colore grandi molte
                # varianti finiscono quasi indistinguibili fra loro.
                accepts_variation_seed = "variation_seed" in inspect.signature(fn).parameters
                variants = []
                with st.spinner(f"Generazione di {n_variants} varianti..."):
                    for _ in range(n_variants):
                        rvals = []
                        for (slabel, smin, smax, sdef, sstep, skey) in sliders:
                            n_steps = max(1, round((smax - smin) / sstep))
                            rv = smin + rng.randint(0, n_steps) * sstep
                            rvals.append(round(min(smax, max(smin, rv)), 6))
                        if accepts_variation_seed:
                            result_img = fn(img, *rvals, variation_seed=rng.randint(0, 2**31 - 1))
                        else:
                            result_img = fn(img, *rvals)
                        # stessa logica di reinserimento alpha usata dal rendering
                        # normale — prima mancava qui, e i PNG trasparenti
                        # perdevano la trasparenza nelle varianti generate.
                        if keep_transparency and original_alpha is not None:
                            result_img = result_img.convert("RGBA")
                            alpha_to_apply = original_alpha
                            if result_img.size != alpha_to_apply.size:
                                alpha_to_apply = alpha_to_apply.resize(result_img.size)
                            result_img.putalpha(alpha_to_apply)
                        variants.append({
                            "vals": rvals,
                            "preview": img_to_preview_bytes(result_img, max_dim=500),
                            "obj": result_img,
                        })
                st.session_state[f"variants_{key}"] = variants
                st.session_state["variants_key_for"] = key
                st.session_state[f"variants_seed_used_{key}"] = seed_used

            stored = st.session_state.get(f"variants_{key}")
            if stored and st.session_state.get("variants_key_for") == key:
                seed_used = st.session_state.get(f"variants_seed_used_{key}")
                if seed_used:
                    st.caption("🌱 Seed di questa generazione (copialo per riusarlo, "
                               "anche su un altro effetto):")
                    st.code(seed_used, language=None)
                st.caption(f"{len(stored)} varianti generate — "
                           f"{', '.join(s[0] for s in sliders)}")
                cols = st.columns(4)
                for i, v in enumerate(stored):
                    with cols[i % 4]:
                        param_str = " / ".join(f"{s[0]}:{val:.2f}" for s, val in zip(sliders, v["vals"]))
                        st.image(v["preview"], caption=param_str, width=220)

                if st.button("📦 Prepara ZIP di tutte le varianti (piena risoluzione)",
                             key=f"variant_zip_{key}"):
                    with st.spinner("Codifica ZIP in corso..."):
                        buf = io.BytesIO()
                        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                            for i, v in enumerate(stored):
                                png_bytes = img_to_bytes(v["obj"])
                                param_str = "_".join(f"{s[0]}{val:.2f}" for s, val in zip(sliders, v["vals"]))
                                zf.writestr(f"{key}_variante_{i+1:02d}_{param_str}.png", png_bytes)
                        st.session_state[f"variants_zip_{key}"] = buf.getvalue()
                if st.session_state.get(f"variants_zip_{key}"):
                    st.download_button(
                        "⬇️ Scarica ZIP varianti",
                        st.session_state[f"variants_zip_{key}"],
                        f"{key}_varianti.zip", "application/zip",
                        key=f"dl_variant_zip_{key}"
                    )

        live_effect_key = None
        should_process = False
        if live_mode:
            effect_labels = [f"{emoji} {label}" for key, label, emoji, fn, sliders in EFFECTS]
            effect_keys = [key for key, label, emoji, fn, sliders in EFFECTS]
            sel_label = st.selectbox(
                "🎯 Effetto da modificare in Live",
                effect_labels, key="live_effect_select"
            )
            live_effect_key = effect_keys[effect_labels.index(sel_label)]
            st.caption("💡 Solo questo effetto si aggiorna ad ogni slider. Gli altri restano fermi "
                       "all'ultima immagine generata. I download salvano l'ultimo frame generato.")
            st.markdown("---")
            live_entry = [e for e in EFFECTS if e[0] == live_effect_key][0]
            _render_variant_explorer(live_entry, img, ts, keep_transparency, original_alpha)
        else:
            if st.button("✨ Genera tutti gli effetti"):
                should_process = True
        st.markdown("---")

        @_fragment
        def _render_effect(key, label, emoji, fn, sliders, img, live_mode, live_effect_key,
                            should_process, keep_transparency, original_alpha,
                            transparency_toggled, ts):
            with st.expander(f"{emoji} {label}", expanded=False):
                col_ctrl, col_img = st.columns([1, 3])

                vals = []
                with col_ctrl:
                    st.markdown("**🎛️ Parametri**")
                    for (slabel, smin, smax, sdef, sstep, skey) in sliders:
                        v = st.slider(slabel, smin, smax, sdef, sstep, key=skey)
                        vals.append(v)

                prev_vals = st.session_state.get(f"params_{key}")
                if prev_vals is None:
                    # Prima volta che vediamo questo effetto in questa sessione:
                    # memorizziamo i valori di default SENZA generare (per non
                    # elaborare tutti i 41 effetti insieme al caricamento della
                    # foto). Da qui in poi, qualunque modifica reale a uno
                    # slider verra' rilevata correttamente al prossimo rerun.
                    st.session_state[f"params_{key}"] = vals
                    params_changed = False
                else:
                    params_changed = (prev_vals != vals)
                is_live_target = live_mode and (key == live_effect_key)
                needs_process = (
                    should_process
                    or (is_live_target and (params_changed or st.session_state.get(f"img_prev_{key}") is None))
                    or (not live_mode and params_changed)
                    or (transparency_toggled and st.session_state.get(f"img_prev_{key}") is not None)
                )

                if needs_process:
                    with col_img:
                        with st.spinner(f"Elaborazione {label}..."):
                            result_img = fn(img, *vals)
                            if keep_transparency and original_alpha is not None:
                                result_img = result_img.convert("RGBA")
                                alpha_to_apply = original_alpha
                                if result_img.size != alpha_to_apply.size:
                                    alpha_to_apply = alpha_to_apply.resize(result_img.size)
                                result_img.putalpha(alpha_to_apply)
                            st.session_state[f"img_obj_{key}"]  = result_img
                            st.session_state[f"img_prev_{key}"] = img_to_preview_bytes(result_img)
                            st.session_state[f"rep_{key}"]      = make_report(
                                key, label, img.size, vals, [s[0] for s in sliders], ts)
                            st.session_state[f"params_{key}"]   = vals
                            st.session_state.processed          = True
                            # Il PNG a piena risoluzione e' l'operazione piu' lenta (puo'
                            # costare quanto il calcolo dell'effetto stesso su foto grandi):
                            # lo si prepara automaticamente solo con "Genera tutti", non
                            # ad ogni singolo movimento di slider — altrimenti ogni ritocco
                            # pagherebbe due volte il costo (calcolo + codifica PNG) e
                            # l'interfaccia sembrerebbe bloccarsi.
                            if should_process:
                                st.session_state[f"img_{key}"] = img_to_bytes(result_img)
                                st.session_state[f"img_full_params_{key}"] = vals
                            else:
                                st.session_state.pop(f"img_{key}", None)

                if st.session_state.get(f"img_prev_{key}"):
                    prev_bytes = st.session_state[f"img_prev_{key}"]
                    rep_bytes = st.session_state[f"rep_{key}"]
                    with col_img:
                        st.image(prev_bytes, caption=f"{emoji} {label}", width=650)

                    with col_ctrl:
                        st.markdown("**⬇️ Download**")
                        full_ready = (
                            st.session_state.get(f"img_{key}") is not None
                            and st.session_state.get(f"img_full_params_{key}") == vals
                        )
                        if not full_ready:
                            if st.button("🔄 Prepara download\n(piena risoluzione)", key=f"prep_{key}"):
                                with st.spinner("Preparazione file..."):
                                    result_img = st.session_state[f"img_obj_{key}"]
                                    st.session_state[f"img_{key}"] = img_to_bytes(result_img)
                                    st.session_state[f"img_full_params_{key}"] = vals
                                    full_ready = True
                        if full_ready:
                            st.download_button("⬇️ Immagine", st.session_state[f"img_{key}"],
                                                f"{key}_glitch.png", "image/png",
                                                key=f"dl_img_{key}")
                        st.download_button("📄 Report", rep_bytes,
                                            f"{key}_report.txt", "text/plain",
                                            key=f"dl_rep_{key}")

        for key, label, emoji, fn, sliders in EFFECTS:
            _render_effect(key, label, emoji, fn, sliders, img, live_mode, live_effect_key,
                            should_process, keep_transparency, original_alpha,
                            transparency_toggled, ts)

        n_generate = sum(1 for key, *_ in EFFECTS if st.session_state.get(f"img_{key}"))
        if n_generate > 0:
            st.markdown("---")
            zip_bytes = build_zip_all_images(EFFECTS)
            st.download_button(
                f"📦 Scarica tutte le immagini + report ({n_generate}) in ZIP",
                zip_bytes,
                "glitchlab_tutti_effetti.zip",
                "application/zip",
                key="dl_zip_all"
            )
            st.caption("Lo ZIP include solo gli effetti già preparati a piena risoluzione "
                       "(via 'Genera tutti' o il bottone 'Prepara download' su ciascun effetto).")

    except Exception as e:
        st.error(f"Errore: {e}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")
else:
    st.info("📁 Carica un'immagine per iniziare!")

st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** — 29 effetti glitch per le tue foto")
st.markdown("*⚡ Live per lavorare in tempo reale · ✨ Genera per elaborare tutti gli effetti insieme*")
