import streamlit as st
from PIL import Image, ImageFilter
import numpy as np
import io
import random
from datetime import datetime

st.set_page_config(page_title="GlitchLabLoop507", layout="wide")
st.title("🔥 GlitchLabLoop507")
st.write("Carica una foto e applica 29 effetti glitch — Live o Manuale.")


def img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
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
                y0 = random.randint(0, h - 5)
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
        a = angolo * np.pi
        f1 = 0.03 + 0.2 * freq1
        f2 = 0.025 + 0.18 * freq2
        grid1 = np.sin(xs * f1 * np.cos(a) + ys * f1 * np.sin(a))
        grid2 = np.sin(xs * f2 * np.cos(a + 0.25) + ys * f2 * np.sin(a + 0.25))
        moire = ((grid1 * grid2) * 0.5 + 0.5)[:, :, np.newaxis]
        result = arr * moire + (255 - arr) * (1 - moire)
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
    """Pennellate Kuwahara vettoriale: ogni pixel prende il colore del quadrante più omogeneo."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        r = max(2, int(2 + 8 * raggio))

        # Kuwahara vettoriale: usa integral images per calcolare mean e var di ogni quadrante in O(h*w)
        pad = r
        padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
        # Luminosità per calcolo varianza
        lum_pad = (padded[:,:,0]*0.299 + padded[:,:,1]*0.587 + padded[:,:,2]*0.114)

        best_var = np.full((h, w), np.inf)
        out = np.zeros_like(arr)

        # 4 quadranti: (top-left, top-right, bottom-left, bottom-right) del pixel corrente
        for (dy0, dy1, dx0, dx1) in [
            (0,   r, 0,   r),   # top-left
            (0,   r, r,  2*r),  # top-right
            (r,  2*r, 0,  r),   # bottom-left
            (r,  2*r, r, 2*r),  # bottom-right
        ]:
            # Estrae la finestra [dy0:dy1, dx0:dx1] intorno a ogni pixel (tramite slicing)
            ph, pw = dy1 - dy0, dx1 - dx0
            # Regione del padded array che corrisponde al quadrante per ogni (y,x) originale
            win_lum   = np.lib.stride_tricks.sliding_window_view(lum_pad, (ph, pw))
            win_color = np.lib.stride_tricks.sliding_window_view(padded,  (ph, pw, 3))

            # sliding_window_view su 3D restituisce (H, W, 1, ph, pw, 3) — prendiamo [..,0,..,:]
            win_lum   = win_lum  [dy0:dy0+h, dx0:dx0+w]            # (h, w, ph, pw)
            win_color = win_color[dy0:dy0+h, dx0:dx0+w, 0]         # (h, w, ph, pw, 3)

            var  = win_lum.var(axis=(-2, -1))                       # (h, w)
            mean = win_color.mean(axis=(-3, -2))                    # (h, w, 3)

            mask = var < best_var
            best_var[mask] = var[mask]
            out[mask] = mean[mask]

        # Posterizzazione finale per accentuare l'effetto pittorico
        lev = max(2, int(2 + 6 * livelli))
        step = 256.0 / lev
        out_post = (np.floor(out / step) * step).clip(0, 255)
        result = arr * (1 - blend) + out_post * blend
        return Image.fromarray(result.astype(np.uint8))
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
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Thermal: {e}"); return img


def glitch_polar(img, forza=0.6, rotazione=0.0, zoom=0.5):
    """Coordinate polari — immagine avvolta su se stessa."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (xs / w - 0.5) * 2
        ny = (ys / h - 0.5) * 2
        r = np.sqrt(nx**2 + ny**2) * (0.5 + zoom)
        angle = np.arctan2(ny, nx) + rotazione * np.pi
        px = np.clip(((angle / (2 * np.pi) + 0.5) * w * forza + w * (1 - forza) * 0.5).astype(int), 0, w - 1)
        py = np.clip((r * h * 0.8).astype(int), 0, h - 1)
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
            nw = max(4, int(w * scale))
            nh = max(4, int(h * scale))
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


# ══════════════════════════════════════════════════════════════════════════════
#  CATALOGO EFFETTI
# ══════════════════════════════════════════════════════════════════════════════

EFFECTS = [
    ("vhs", "VHS", "📺", glitch_vhs, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "vhs_int"),
        ("Scanlines",      0.0, 2.0, 1.0, 0.1,  "vhs_scan"),
        ("Color Split",    0.0, 2.0, 1.0, 0.1,  "vhs_col"),
    ]),
    ("distruttivo", "Distruttivo", "💥", glitch_distruttivo, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dest_size"),
        ("Num. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dest_num"),
        ("Spostamento",    0.0, 2.0, 1.0, 0.1,  "dest_disp"),
    ]),
    ("noise", "Noise", "🌀", glitch_noise, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "noise_int"),
        ("Copertura",      0.0, 1.0, 0.7, 0.05, "noise_cov"),
        ("Tipo (0=bande 0.5=pixel 1=onde)", 0.0, 1.0, 0.0, 0.01, "noise_tipo"),
    ]),
    ("pixel_sort", "Pixel Sort", "🔀", glitch_pixel_sort, [
        ("Soglia lum.",    0.0, 1.0, 0.4, 0.05, "ps_thresh"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 1.0, 1.0,  "ps_asse"),
        ("Span max",       0.0, 1.0, 0.8, 0.05, "ps_span"),
    ]),
    ("wave_warp", "Wave Warp", "〰️", glitch_wave_warp, [
        ("Ampiezza",       0.0, 2.0, 1.0, 0.1,  "ww_amp"),
        ("Frequenza",      0.0, 2.0, 1.0, 0.1,  "ww_freq"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 0.0, 1.0,  "ww_asse"),
    ]),
    ("chromatic", "Chromatic Ab.", "🌈", glitch_chromatic, [
        ("Forza",          0.0, 1.0, 0.5, 0.05, "chr_forza"),
        ("Angolo",         0.0, 1.0, 0.0, 0.05, "chr_ang"),
        ("Zoom aberr.",    0.0, 1.0, 0.3, 0.05, "chr_zoom"),
    ]),
    ("datamosh", "Datamosh", "📼", glitch_datamosh, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1,  "dm_block"),
        ("Decay",          0.0, 1.0, 0.5, 0.05, "dm_decay"),
        ("N. Blocchi",     0.0, 1.0, 0.5, 0.05, "dm_num"),
    ]),
    ("scanline_burn", "Scanline Burn", "📟", glitch_scanline_burn, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1,  "sb_int"),
        ("Densità",        0.0, 1.0, 0.4, 0.05, "sb_den"),
        ("Color Bleed",    0.0, 1.0, 0.5, 0.05, "sb_bleed"),
    ]),
    ("psychedelic", "Psychedelic", "🔮", glitch_psychedelic, [
        ("Hue Shift",      0.0, 1.0, 0.3, 0.05, "psy_hue"),
        ("Saturazione",    0.0, 1.0, 0.5, 0.05, "psy_sat"),
        ("Inversione",     0.0, 1.0, 0.0, 0.05, "psy_inv"),
    ]),
    ("channel_swap", "Channel Swap", "🔁", glitch_channel_swap, [
        ("Modalità (0-5)", 0.0, 1.0, 0.0, 0.2,  "cs_mode"),
        ("Blend",          0.0, 1.0, 0.6, 0.05, "cs_blend"),
        ("Shift px",       0.0, 1.0, 0.0, 0.05, "cs_shift"),
    ]),
    ("image_feedback", "Image Feedback", "📡🔁", glitch_image_feedback, [
        ("Zoom",           0.0, 1.0, 0.5, 0.05, "fb_zoom"),
        ("Iterazioni",     0.0, 1.0, 0.4, 0.05, "fb_iter"),
        ("Decay",          0.0, 1.0, 0.5, 0.05, "fb_decay"),
    ]),
    ("destruction_art", "Destruction Art", "✂️", glitch_destruction_art, [
        ("Tagli",          0.0, 1.0, 0.5, 0.05, "da_cuts"),
        ("Scatter",        0.0, 1.0, 0.4, 0.05, "da_scatter"),
        ("Asse (0=H 1=V)", 0.0, 1.0, 0.0, 1.0,  "da_asse"),
    ]),
    ("analogic", "Glitch Analogic", "📻", glitch_analogic, [
        ("Sync Loss",      0.0, 1.0, 0.5, 0.05, "ag_sync"),
        ("Color Bleed",    0.0, 1.0, 0.4, 0.05, "ag_bleed"),
        ("Static",         0.0, 1.0, 0.3, 0.05, "ag_static"),
    ]),
    ("displacement_map", "Displacement Map", "🌊", glitch_displacement_map, [
        ("Forza",          0.0, 1.0, 0.5, 0.05, "dsp_forza"),
        ("Blur Scala",     0.0, 1.0, 0.4, 0.05, "dsp_blur"),
        ("Canale (R/G/B)", 0.0, 1.0, 0.0, 0.5,  "dsp_canale"),
    ]),
    ("op_art_circles", "Op Art Circles", "⭕", glitch_op_art_circles, [
        ("Frequenza",      0.0, 1.0, 0.5, 0.05, "oa_freq"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05, "oa_cont"),
        ("Blend",          0.0, 1.0, 0.5, 0.05, "oa_blend"),
    ]),
    ("halftone", "Halftone", "🔵", glitch_halftone, [
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05, "ht_size"),
        ("Sfondo bianco",  0.0, 1.0, 1.0, 1.0,  "ht_sfondo"),
        ("Colore",         0.0, 1.0, 0.7, 0.05, "ht_color"),
    ]),
    ("moire", "Moire Pattern", "🔲", glitch_moire, [
        ("Frequenza 1",    0.0, 1.0, 0.4, 0.05, "mo_f1"),
        ("Frequenza 2",    0.0, 1.0, 0.6, 0.05, "mo_f2"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05, "mo_ang"),
    ]),
    ("drip", "Drip Sort", "🌊💧", glitch_drip, [
        ("Soglia lum.",    0.0, 1.0, 0.3, 0.05, "drip_soglia"),
        ("Sep. RGB",       0.0, 1.0, 0.5, 0.05, "drip_rgb"),
        ("Asse (0=V 1=H)", 0.0, 1.0, 0.0, 1.0,  "drip_asse"),
    ]),
    ("oil_paint", "Oil Paint", "🖌️", glitch_oil_paint, [
        ("Raggio",         0.0, 1.0, 0.3, 0.05, "op_rad"),
        ("Livelli",        0.0, 1.0, 0.5, 0.05, "op_lev"),
        ("Blend",          0.0, 1.0, 0.7, 0.05, "op_blend"),
    ]),
    ("posterize", "Posterize", "🎨", glitch_posterize, [
        ("Livelli",        0.0, 1.0, 0.4, 0.05, "po_lev"),
        ("Dither",         0.0, 1.0, 0.4, 0.05, "po_dith"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05, "po_col"),
    ]),
    ("neon_glow", "Neon Glow", "💡", glitch_neon_glow, [
        ("Soglia bordi",   0.0, 1.0, 0.3, 0.05, "ng_thresh"),
        ("Ampiezza glow",  0.0, 1.0, 0.5, 0.05, "ng_width"),
        ("Colore (0-4)",   0.0, 1.0, 0.0, 0.25, "ng_color"),
    ]),
    ("duotone", "Duotone", "🎭", glitch_duotone, [
        ("Colore 1 (hue)", 0.0, 1.0, 0.1, 0.05, "dt_c1"),
        ("Colore 2 (hue)", 0.0, 1.0, 0.6, 0.05, "dt_c2"),
        ("Blend",          0.0, 1.0, 0.8, 0.05, "dt_blend"),
    ]),
    ("solarize", "Solarize", "☀️", glitch_solarize, [
        ("Soglia",         0.0, 1.0, 0.5, 0.05, "sol_thresh"),
        ("Forza",          0.0, 1.0, 0.8, 0.05, "sol_str"),
        ("Channel Split",  0.0, 1.0, 0.3, 0.05, "sol_ch"),
    ]),
    ("thermal", "Thermal Camera", "🌡️", glitch_thermal, [
        ("Palette (0-2)",  0.0, 1.0, 0.0, 0.5,  "th_pal"),
        ("Rumore",         0.0, 1.0, 0.2, 0.05, "th_noise"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05, "th_cont"),
    ]),
    ("polar", "Polar Coords", "🌀", glitch_polar, [
        ("Forza",          0.0, 1.0, 0.6, 0.05, "pol_str"),
        ("Rotazione",      0.0, 1.0, 0.0, 0.05, "pol_rot"),
        ("Zoom",           0.0, 1.0, 0.5, 0.05, "pol_zoom"),
    ]),
    ("tunnel_zoom", "Tunnel Zoom", "🔭", glitch_tunnel_zoom, [
        ("Strati",         0.0, 1.0, 0.5, 0.05, "tz_layers"),
        ("Velocità",       0.0, 1.0, 0.5, 0.05, "tz_speed"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05, "tz_col"),
    ]),
    ("mirror_kal", "Mirror Kaleido.", "🪞", glitch_mirror_kaleidoscope, [
        ("Specchi (4/6/8)", 0.0, 1.0, 0.3, 0.1,  "mk_mirrors"),
        ("Rotazione",       0.0, 1.0, 0.0, 0.05, "mk_rot"),
        ("Zoom",            0.0, 1.0, 0.5, 0.05, "mk_zoom"),
    ]),
    ("crosshatch", "Crosshatch", "✏️", glitch_crosshatch, [
        ("Densità",        0.0, 1.0, 0.5, 0.05, "ch_den"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05, "ch_ang"),
        ("Spessore",       0.0, 1.0, 0.3, 0.05, "ch_thick"),
    ]),
    ("stippling", "Stippling", "🔴", glitch_stippling, [
        ("Densità",        0.0, 1.0, 0.5, 0.05, "st_den"),
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05, "st_dot"),
        ("Colore",         0.0, 1.0, 0.6, 0.05, "st_col"),
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ══════════════════════════════════════════════════════════════════════════════

EFFECT_QUOTES = {
    "vhs":              "Il nastro ha consumato i colori. La memoria e' distorta.",
    "distruttivo":      "I blocchi si sono spostati. La struttura non esiste piu'.",
    "noise":            "Il segnale e' collassato. Il rumore ha preso il controllo.",
    "pixel_sort":       "La luce ha scelto il suo ordine. Il pixel ha obbedito.",
    "wave_warp":        "La materia e' diventata liquida. La forma e' un'illusione.",
    "chromatic":        "Il prisma ha spezzato la luce. I colori non tornano piu'.",
    "datamosh":         "Il frame e' rimasto bloccato. Il tempo non scorre piu'.",
    "scanline_burn":    "Il tubo e' bruciato. Il CRT ricorda ancora.",
    "psychedelic":      "L'hue ha ruotato oltre il visibile. La realta' e' soggettiva.",
    "channel_swap":     "I canali si sono scambiati. Il colore non riconosce se stesso.",
    "image_feedback":   "Lo schermo si e' guardato allo specchio. L'infinito e' iniziato.",
    "destruction_art":  "L'immagine e' stata tagliata. Il collage e' l'unica verita'.",
    "analogic":         "Il segnale ha perso il sincronismo. L'antenna non risponde.",
    "displacement_map": "Il pixel si e' spostato seguendo se stesso. Lo spazio e' curvo.",
    "op_art_circles":   "I cerchi hanno ipnotizzato la forma. L'occhio non trova pace.",
    "halftone":         "La stampa ha dissolto l'immagine. Il punto e' tutto cio' che resta.",
    "moire":            "Le griglie si sono scontrate. Il pattern e' nato dal conflitto.",
    "drip":             "La gravita' ha scelto i colori. Il pixel ha obbedito alla caduta.",
    "oil_paint":        "Il pennello ha ridisegnato la realta'. La texture ha vinto sul pixel.",
    "posterize":        "Il colore e' stato ridotto all'essenziale. La serigrafia non perdona.",
    "neon_glow":        "I bordi si sono accesi. Il buio esalta la luce.",
    "duotone":          "Due colori soltanto. La sintesi e' la forma piu' alta.",
    "solarize":         "La luce si e' invertita. La camera oscura ha tradito l'originale.",
    "thermal":          "Il calore ha riscritto i colori. La temperatura e' la nuova forma.",
    "polar":            "Lo spazio si e' avvolto su se stesso. Il centro non esiste piu'.",
    "tunnel_zoom":      "L'immagine e' collassata verso l'interno. Il tunnel non ha fondo.",
    "mirror_kal":       "Gli specchi si sono moltiplicati. La simmetria e' diventata religione.",
    "crosshatch":       "Il tratteggio ha sostituito il colore. L'incisione non mente.",
    "stippling":        "Il punto e' la minima unita' di verita'. Milioni di punti, una sola immagine.",
}

EFFECT_ENGINES = {
    "vhs":              "magnetic_tape_engine",
    "distruttivo":      "block_fragment_engine",
    "noise":            "entropy_noise_core",
    "pixel_sort":       "luminance_sort_engine",
    "wave_warp":        "sinusoidal_warp_engine",
    "chromatic":        "radial_aberration_core",
    "datamosh":         "frame_decay_engine",
    "scanline_burn":    "crt_burn_engine",
    "psychedelic":      "hue_rotation_core",
    "channel_swap":     "channel_matrix_engine",
    "image_feedback":   "recursive_zoom_engine",
    "destruction_art":  "strip_collage_engine",
    "analogic":         "analog_sync_engine",
    "displacement_map": "self_displacement_engine",
    "op_art_circles":   "concentric_wave_engine",
    "halftone":         "halftone_dot_engine",
    "moire":            "grid_interference_engine",
    "drip":             "directional_drip_sort_engine",
    "oil_paint":        "kuwahara_paint_engine",
    "posterize":        "color_quantize_engine",
    "neon_glow":        "edge_neon_engine",
    "duotone":          "dual_color_engine",
    "solarize":         "highlight_invert_engine",
    "thermal":          "false_color_engine",
    "polar":            "polar_coords_engine",
    "tunnel_zoom":      "tunnel_zoom_engine",
    "mirror_kal":       "radial_symmetry_engine",
    "crosshatch":       "hatch_render_engine",
    "stippling":        "pointillism_engine",
}


def make_report(effect_key, effect_label, img_size, param_vals, param_labels, ts):
    w, h = img_size
    mpx = w * h / 1_000_000
    date_str, time_str = ts.split(" ")
    engine = EFFECT_ENGINES.get(effect_key, "unknown_engine")
    quote  = EFFECT_QUOTES.get(effect_key, "Il glitch e' la verita'.")
    avg_pct = int(sum(param_vals) / len(param_vals) / 2.0 * 100) if param_vals else 0
    lines = [
        f"GLITCHLAB [IMAGE] // {effect_label.upper()} // 01 //",
        f":: MOTORE: {engine} [v3.0]",
        f":: PROCESSO: Corruzione Singolo Strato — {effect_label.upper()}",
        "",
        f'"{quote}"',
        "",
        "> TECHNICAL LOG SHEET:",
        f"* Asset: {w} x {h} px  ({mpx:.2f} Mpx)",
        f"* Data: {date_str}  //  {time_str}",
        f"* Effect Index: {avg_pct}%",
        "",
        f"> {effect_label.upper()} ENGINE:",
    ]
    for label, val in zip(param_labels, param_vals):
        lines.append(f"* {label:<22}: {val:.2f}")
    lines += [
        "",
        "> Regia e Algoritmo: Loop507",
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
        img = Image.open(uploaded_file).convert("RGB")
        st.image(img, caption="🖼️ Originale", use_container_width=True)
        st.info(f"Dimensioni: {img.size[0]} × {img.size[1]} px")

        st.markdown("### 🎛️ Controlli Effetti")
        st.markdown("---")
        live_mode = st.checkbox(
            "⚡ Modalità Live — l'anteprima si aggiorna ad ogni slider",
            value=False, key="live_mode"
        )
        should_process = live_mode
        if not live_mode:
            if st.button("✨ Genera tutti gli effetti"):
                should_process = True
        if live_mode:
            st.caption("💡 I download salvano l'ultimo frame generato.")
        st.markdown("---")

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for key, label, emoji, fn, sliders in EFFECTS:
            with st.expander(f"{emoji} {label}", expanded=False):
                sc = st.columns(len(sliders))
                vals = []
                for i, (slabel, smin, smax, sdef, sstep, skey) in enumerate(sliders):
                    v = sc[i].slider(slabel, smin, smax, sdef, sstep, key=skey)
                    vals.append(v)

                prev_vals = st.session_state.get(f"params_{key}")
                params_changed = (prev_vals != vals)
                needs_process = (
                    should_process
                    or (live_mode and params_changed)
                    or (not live_mode and params_changed and st.session_state.get(f"img_{key}") is not None)
                )

                if needs_process:
                    result_img = fn(img, *vals)
                    st.session_state[f"img_{key}"]    = img_to_bytes(result_img)
                    st.session_state[f"rep_{key}"]    = make_report(
                        key, label, img.size, vals, [s[0] for s in sliders], ts)
                    st.session_state[f"params_{key}"] = vals
                    st.session_state.processed        = True

                if st.session_state.get(f"img_{key}"):
                    img_bytes = st.session_state[f"img_{key}"]
                    rep_bytes = st.session_state[f"rep_{key}"]
                    st.image(img_bytes, caption=f"{emoji} {label}", use_container_width=True)
                    dl1, dl2 = st.columns(2)
                    dl1.download_button("⬇️ Immagine", img_bytes,
                                        f"{key}_glitch.png", "image/png",
                                        key=f"dl_img_{key}")
                    dl2.download_button("📄 Report", rep_bytes,
                                        f"{key}_report.txt", "text/plain",
                                        key=f"dl_rep_{key}")

    except Exception as e:
        st.error(f"Errore: {e}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")
else:
    st.info("📁 Carica un'immagine per iniziare!")

st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** — 29 effetti glitch per le tue foto")
st.markdown("*⚡ Live per lavorare in tempo reale · ✨ Genera per elaborare tutti gli effetti insieme*")
