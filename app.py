import streamlit as st
from PIL import Image
import numpy as np
import io
import random
from datetime import datetime

st.set_page_config(page_title="GlitchLabLoop507", layout="wide")
st.title("🔥 GlitchLabLoop507")
st.write("Carica una foto e applica 13 effetti glitch — Live o Manuale.")


# ══════════════════════════════════════════════════════════════════════════════
#  EFFETTI
# ══════════════════════════════════════════════════════════════════════════════

def glitch_vhs(img, intensity=1.0, scanline_freq=1.0, color_shift=1.0):
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
        noise_prob = 0.2 + 0.2 * intensity
        noise_mask = np.random.random(h) < noise_prob
        noise_int = int(10 + 20 * intensity)
        noise = np.random.randint(-noise_int, noise_int, (h, w, 3), dtype=np.int16)
        arr[noise_mask] = np.clip(arr[noise_mask] + noise[noise_mask], 0, 255)
        sm = color_shift
        r_shift = int(15 * sm + random.randint(0, max(1, int(20 * sm))))
        b_shift = int(-15 * sm + random.randint(max(-1, int(-20 * sm)), 0))
        g_shift = int(random.randint(max(-1, int(-10 * sm)), max(1, int(10 * sm))))
        r = np.clip(np.roll(arr[:, :, 0], r_shift, axis=1) * (1.0 + random.uniform(0, 0.3 * sm)), 0, 255)
        g = np.clip(np.roll(arr[:, :, 1], g_shift, axis=0) * (1.0 - random.uniform(0, 0.24 * sm)), 0, 255)
        b = np.clip(np.roll(arr[:, :, 2], b_shift, axis=1) * (1.0 + random.uniform(-0.15 * sm, 0.3 * sm)), 0, 255)
        return Image.fromarray(np.stack([r, g, b], axis=2).astype(np.uint8))
    except Exception as e:
        st.error(f"VHS: {e}"); return img


def glitch_distruttivo(img, block_size=1.0, num_blocks=1.0, displacement=1.0):
    try:
        img = img.convert("RGB")
        arr = np.array(img)
        h, w, _ = arr.shape
        if w < 60 or h < 60:
            return img
        base_blocks = min(80, w * h // 1500)
        total_blocks = int(base_blocks * (0.5 + 1.5 * num_blocks))
        base_max_w = min(60, w // 4)
        base_max_h = min(60, h // 4)
        max_bw = max(5, int(base_max_w * (0.3 + 1.4 * block_size)))
        max_bh = max(5, int(base_max_h * (0.3 + 1.4 * block_size)))
        max_disp = max(1, int(min(w // 6, h // 6) * displacement))
        for _ in range(total_blocks):
            bw = random.randint(max(5, max_bw // 3), max_bw)
            bh = random.randint(max(5, max_bh // 3), max_bh)
            x = random.randint(0, max(0, w - bw))
            y = random.randint(0, max(0, h - bh))
            if y + bh > h or x + bw > w:
                continue
            block = arr[y:y + bh, x:x + bw].copy()
            if random.random() < (0.1 + 0.4 * displacement):
                block = np.roll(block, random.randint(-int(5 + 10 * displacement), int(5 + 10 * displacement)), axis=1)
            x_new = int(np.clip(x + random.randint(-max_disp, max_disp), 0, w - bw))
            y_new = int(np.clip(y + random.randint(-max_disp, max_disp), 0, h - bh))
            arr[y_new:y_new + bh, x_new:x_new + bw] = block
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Distruttivo: {e}"); return img


def glitch_noise(img, noise_intensity=1.0, coverage=1.0, chaos=1.0):
    try:
        img = img.convert("RGB")
        arr = np.array(img).astype(np.int32)
        h, w, _ = arr.shape
        base_intensity = int(30 + 90 * noise_intensity)
        coverage_factor = 0.3 + 0.7 * coverage
        if chaos < 0.3:   noise_type = "bands"
        elif chaos < 0.6: noise_type = "pixels"
        elif chaos < 0.8: noise_type = "waves"
        else:              noise_type = "mixed"
        if noise_type == "bands":
            for _ in range(int(5 + 15 * coverage)):
                sy = random.randint(0, h - 1)
                ey = min(sy + int(3 + 27 * noise_intensity), h)
                arr[sy:ey] += np.random.randint(-base_intensity, base_intensity, (ey - sy, w, 3))
        elif noise_type == "pixels":
            num_pix = int(w * h / 30 * coverage * (1 + chaos))
            xs = np.random.randint(0, w, num_pix)
            ys = np.random.randint(0, h, num_pix)
            pn = np.random.randint(-base_intensity, base_intensity, (num_pix, 3))
            for i in range(num_pix):
                arr[ys[i], xs[i]] += pn[i]
        elif noise_type == "waves":
            wave_freq = 0.1 + 0.4 * chaos
            for y in np.arange(0, h, max(1, int(h * (1 - coverage_factor) + 1))):
                ws = int(base_intensity * 0.7 * np.sin(y * wave_freq))
                arr[y:y + 1] += np.random.randint(-base_intensity // 2, base_intensity // 2, (1, w, 3))
                if ws:
                    arr[y:y + 1] = np.roll(arr[y:y + 1], ws, axis=1)
        else:
            arr += np.random.randint(-base_intensity // 2, base_intensity // 2, arr.shape)
            for _ in range(int(3 + 5 * coverage)):
                sy = random.randint(0, max(1, h - 10))
                ey = min(sy + random.randint(2, int(10 + 5 * noise_intensity)), h)
                arr[sy:ey] += np.random.randint(-base_intensity, base_intensity, (ey - sy, w, 3))
        if chaos > 0.4:
            for ch in random.sample([0, 1, 2], min(3, int(1 + 2 * chaos))):
                m = 0.5 + 1.5 * chaos
                arr[:, :, ch] = np.clip(arr[:, :, ch] * random.uniform(1 / m, m), 0, 255)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Noise: {e}"); return img


def glitch_pixel_sort(img, threshold=0.5, direction=0.5, strength=1.0):
    """Ordina pixel per luminosità — effetto colatura."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        thresh_val = threshold * 255
        vertical = direction > 0.5

        if not vertical:
            # Sort orizzontale
            coverage = int(h * (0.3 + 0.7 * strength))
            rows = random.sample(range(h), min(coverage, h))
            for y in rows:
                mask = lum[y] > thresh_val
                if mask.sum() > 2:
                    indices = np.where(mask)[0]
                    segment = arr[y, indices]
                    sort_key = 0.299 * segment[:, 0] + 0.587 * segment[:, 1] + 0.114 * segment[:, 2]
                    arr[y, indices] = segment[np.argsort(sort_key)]
        else:
            # Sort verticale
            coverage = int(w * (0.3 + 0.7 * strength))
            cols = random.sample(range(w), min(coverage, w))
            for x in cols:
                mask = lum[:, x] > thresh_val
                if mask.sum() > 2:
                    indices = np.where(mask)[0]
                    segment = arr[indices, x]
                    sort_key = 0.299 * segment[:, 0] + 0.587 * segment[:, 1] + 0.114 * segment[:, 2]
                    arr[indices, x] = segment[np.argsort(sort_key)]
        return Image.fromarray(arr)
    except Exception as e:
        st.error(f"Pixel Sort: {e}"); return img


def glitch_wave_warp(img, amplitude=1.0, frequency=1.0, axis=0.5):
    """Deformazione sinusoidale — effetto liquido."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = np.zeros_like(arr)
        amp_x = int(20 + 40 * amplitude)
        amp_y = int(15 + 30 * amplitude)
        freq_x = 0.02 + 0.08 * frequency
        freq_y = 0.015 + 0.06 * frequency

        ys = np.arange(h)
        xs = np.arange(w)
        # Warp orizzontale
        dx = (amp_x * np.sin(ys * freq_x)).astype(int)
        for y in range(h):
            src_x = np.clip(xs + dx[y], 0, w - 1)
            out[y] = arr[y, src_x]
        arr2 = out.copy()
        # Warp verticale
        dy = (amp_y * np.sin(xs * freq_y)).astype(int)
        for x in range(w):
            src_y = np.clip(ys + dy[x], 0, h - 1)
            out[:, x] = arr2[src_y, x]
        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Wave Warp: {e}"); return img


def glitch_chromatic(img, radius=1.0, angle=0.5, strength=1.0):
    """Aberrazione cromatica radiale dal centro."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = arr.copy().astype(np.float32)
        cy, cx = h / 2, w / 2
        max_shift = int(10 + 30 * strength)
        angle_rad = angle * 2 * np.pi

        for ch, ch_angle in enumerate([angle_rad, angle_rad + 2.094, angle_rad + 4.189]):
            shift_x = int(max_shift * radius * np.cos(ch_angle))
            shift_y = int(max_shift * radius * np.sin(ch_angle))
            out[:, :, ch] = np.roll(np.roll(arr[:, :, ch], shift_x, axis=1), shift_y, axis=0)

        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Chromatic: {e}"); return img


def glitch_datamosh(img, block_size=1.0, decay=1.0, num_frames=1.0):
    """Simula corruzione video — blocchi congelati sovrapposti."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_blocks = int(20 + 60 * num_frames)
        bw = max(8, int((w // 8) * (0.3 + 1.4 * block_size)))
        bh = max(8, int((h // 8) * (0.3 + 1.4 * block_size)))
        alpha = 0.3 + 0.6 * decay  # quanto il blocco sovrascrive

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


def glitch_scanline_burn(img, intensity=1.0, density=1.0, color_bleed=1.0):
    """Brucia righe — estetica CRT morto."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_burns = int(5 + 40 * density)

        for _ in range(n_burns):
            y = random.randint(0, h - 1)
            bh = random.randint(1, max(1, int(8 * intensity)))
            ey = min(y + bh, h)
            mode = random.random()
            if mode < 0.3:
                arr[y:ey] = 255  # bianco
            elif mode < 0.6:
                arr[y:ey] = 0    # nero
            else:
                # banda RGB pura
                ch = random.randint(0, 2)
                band = np.zeros((ey - y, w, 3))
                band[:, :, ch] = 255 * (0.5 + 0.5 * color_bleed)
                arr[y:ey] = arr[y:ey] * (1 - color_bleed * 0.8) + band * color_bleed * 0.8

        # Aggiunge RGB bleeding orizzontale
        if color_bleed > 0.3:
            bleed_px = int(3 + 12 * color_bleed)
            arr[:, :, 0] = np.roll(arr[:, :, 0], bleed_px, axis=1)
            arr[:, :, 2] = np.roll(arr[:, :, 2], -bleed_px, axis=1)

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Scanline Burn: {e}"); return img


def glitch_psychedelic(img, hue_shift=1.0, saturation=1.0, invert=0.0):
    """Rotazione hue estrema + saturazione psichedelica."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        h, w, _ = arr.shape

        # Hue rotation via matrix
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
        flat = arr.reshape(-1, 3)
        rotated = flat @ hue_matrix.T
        arr = np.clip(rotated, 0, 1).reshape(h, w, 3)

        # Saturazione: allontana dal grigio
        gray = arr.mean(axis=2, keepdims=True)
        arr = np.clip(gray + (arr - gray) * (1.0 + saturation * 3.0), 0, 1)

        # Inversione parziale per canale
        if invert > 0.1:
            for ch in range(3):
                if random.random() < invert:
                    arr[:, :, ch] = 1.0 - arr[:, :, ch]

        return Image.fromarray((arr * 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Psychedelic: {e}"); return img


def glitch_channel_swap(img, mode=0.5, intensity=1.0, blend=0.5):
    """Mescola canali RGB in combinazioni insolite."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8).astype(np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # Scegli combinazione in base al mode
        combos = [
            (g, b, r),   # GBR
            (b, r, g),   # BRG
            (r, b, g),   # RBG
            (b, g, r),   # BGR (complementare)
            (g, r, b),   # GRB
            (255 - r, g, 255 - b),  # inversione parziale
        ]
        idx = int(mode * (len(combos) - 0.01))
        nr, ng, nb = combos[idx]

        # Blend con originale
        result = np.stack([
            r * (1 - blend) + nr * blend,
            g * (1 - blend) + ng * blend,
            b * (1 - blend) + nb * blend,
        ], axis=2)

        # Shift aggiuntivo per intensità
        if intensity > 0.5:
            shift = int((intensity - 0.5) * 40)
            result[:, :, 0] = np.roll(result[:, :, 0], shift, axis=1)
            result[:, :, 2] = np.roll(result[:, :, 2], -shift, axis=1)

        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Channel Swap: {e}"); return img


def glitch_image_feedback(img, zoom=1.0, iterations=1.0, decay=1.0):
    """Simula feedback telecamera — zoom ricorsivo con dissolvenza."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_iters = int(3 + 7 * iterations)
        zoom_factor = 1.02 + 0.08 * zoom
        fade = 0.3 + 0.5 * decay

        accumulated = arr.copy()

        for i in range(n_iters):
            scale = zoom_factor ** (i + 1)
            new_h = int(h / scale)
            new_w = int(w / scale)
            if new_h < 4 or new_w < 4:
                break
            # Crop centro
            y0 = (h - new_h) // 2
            x0 = (w - new_w) // 2
            cropped = arr[y0:y0 + new_h, x0:x0 + new_w]
            # Ridimensiona al frame originale
            layer = np.array(
                Image.fromarray(cropped.astype(np.uint8)).resize((w, h), Image.BILINEAR),
                dtype=np.float32
            )
            weight = fade ** (i + 1)
            accumulated = accumulated * (1 - weight * 0.3) + layer * weight * 0.3

        return Image.fromarray(np.clip(accumulated, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Image Feedback: {e}"); return img


def glitch_destruction_art(img, cuts=1.0, scatter=1.0, color_shift=1.0):
    """Taglia l'immagine in strisce e le ricompone caoticamente."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        out = arr.copy()
        n_cuts = int(8 + 40 * cuts)
        vertical = random.random() > 0.5

        if vertical:
            indices = sorted(random.sample(range(w), min(n_cuts, w)))
            strips = []
            prev = 0
            for idx in indices:
                if idx > prev:
                    strips.append(arr[:, prev:idx].copy())
                prev = idx
            if prev < w:
                strips.append(arr[:, prev:].copy())
            random.shuffle(strips)
            x = 0
            for strip in strips:
                sw = strip.shape[1]
                if x + sw <= w:
                    if color_shift > 0.3 and random.random() < color_shift * 0.5:
                        strip = strip[:, :, ::-1]  # invert channels
                    dx = random.randint(-int(scatter * 20), int(scatter * 20))
                    src_x = np.clip(np.arange(sw) + dx, 0, sw - 1)
                    out[:, x:x + sw] = strip[:, src_x]
                    x += sw
        else:
            indices = sorted(random.sample(range(h), min(n_cuts, h)))
            strips = []
            prev = 0
            for idx in indices:
                if idx > prev:
                    strips.append(arr[prev:idx, :].copy())
                prev = idx
            if prev < h:
                strips.append(arr[prev:, :].copy())
            random.shuffle(strips)
            y = 0
            for strip in strips:
                sh = strip.shape[0]
                if y + sh <= h:
                    if color_shift > 0.3 and random.random() < color_shift * 0.5:
                        strip = np.roll(strip, random.randint(-30, 30), axis=1)
                    out[y:y + sh, :] = strip
                    y += sh

        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Destruction Art: {e}"); return img


def glitch_analogic(img, sync_loss=1.0, color_bleed=1.0, static=1.0):
    """Segnale analogico che perde sincronismo — TV mal sintonizzato."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape

        # Perdita di sincronismo: righe che scivolano lateralmente
        n_desync = int(h * (0.1 + 0.5 * sync_loss))
        desync_rows = np.random.choice(h, n_desync, replace=False)
        for y in desync_rows:
            shift = int(random.gauss(0, 30 * sync_loss))
            arr[y] = np.roll(arr[y], shift, axis=0)

        # Color bleed verticale (i colori "colano" verso il basso)
        if color_bleed > 0.1:
            bleed_strength = color_bleed * 0.3
            for ch in range(3):
                arr[:, :, ch] = (
                    arr[:, :, ch] * (1 - bleed_strength)
                    + np.roll(arr[:, :, ch], int(3 + 8 * color_bleed), axis=0) * bleed_strength
                )

        # Static: rumore bianco sparso
        if static > 0.1:
            n_static = int(w * h * 0.01 * static)
            xs = np.random.randint(0, w, n_static)
            ys = np.random.randint(0, h, n_static)
            vals = np.random.choice([0, 255], n_static)
            for i in range(n_static):
                arr[ys[i], xs[i]] = vals[i]

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Analogic: {e}"); return img


def glitch_displacement_map(img, strength=1.0, scale=0.5, channel=0.5):
    """Usa l'immagine stessa come mappa di spostamento — effetto liquido/glitch organico."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape

        # Blur della mappa per evitare rumore puro (simulato con media locale)
        blur_radius = max(1, int(3 + 12 * scale))
        from PIL import ImageFilter
        map_img = Image.fromarray(arr.astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )
        disp_map = np.array(map_img, dtype=np.float32)

        # Sceglie quale canale usare come mappa X e quale come Y
        ch_idx = int(channel * 2.99)          # 0=R, 1=G, 2=B
        ch_y   = (ch_idx + 1) % 3
        map_x  = (disp_map[:, :, ch_idx] / 255.0 - 0.5) * 2  # -1 … +1
        map_y  = (disp_map[:, :, ch_y]   / 255.0 - 0.5) * 2

        max_disp = int(20 + 80 * strength)
        dx = (map_x * max_disp).astype(int)
        dy = (map_y * max_disp).astype(int)

        # Griglia coordinate sorgente
        ys_grid, xs_grid = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        src_x = np.clip(xs_grid + dx, 0, w - 1)
        src_y = np.clip(ys_grid + dy, 0, h - 1)

        out = arr[src_y, src_x].astype(np.uint8)
        return Image.fromarray(out)
    except Exception as e:
        st.error(f"Displacement Map: {e}"); return img


# ══════════════════════════════════════════════════════════════════════════════
#  CATALOGO EFFETTI
#  Ogni entry: (chiave, label_ui, emoji, funzione, [(label_slider, min, max, default, step, key)])
# ══════════════════════════════════════════════════════════════════════════════

EFFECTS = [
    ("vhs", "VHS", "📺", glitch_vhs, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "vhs_int"),
        ("Scanlines",      0.0, 2.0, 1.0, 0.1, "vhs_scan"),
        ("Color Split",    0.0, 2.0, 1.0, 0.1, "vhs_col"),
    ]),
    ("distruttivo", "Distruttivo", "💥", glitch_distruttivo, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1, "dest_size"),
        ("Num. Blocchi",   0.0, 2.0, 1.0, 0.1, "dest_num"),
        ("Spostamento",    0.0, 2.0, 1.0, 0.1, "dest_disp"),
    ]),
    ("noise", "Noise", "🌀", glitch_noise, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "noise_int"),
        ("Copertura",      0.0, 2.0, 1.0, 0.1, "noise_cov"),
        ("Caos",           0.0, 1.0, 0.5, 0.1, "noise_chaos"),
    ]),
    ("pixel_sort", "Pixel Sort", "🔀", glitch_pixel_sort, [
        ("Soglia",         0.0, 1.0, 0.5, 0.05, "ps_thresh"),
        ("Direzione",      0.0, 1.0, 0.3, 0.1,  "ps_dir"),
        ("Forza",          0.0, 1.0, 0.7, 0.05, "ps_strength"),
    ]),
    ("wave_warp", "Wave Warp", "〰️", glitch_wave_warp, [
        ("Ampiezza",       0.0, 2.0, 1.0, 0.1, "ww_amp"),
        ("Frequenza",      0.0, 2.0, 1.0, 0.1, "ww_freq"),
        ("Asse",           0.0, 1.0, 0.5, 0.1, "ww_axis"),
    ]),
    ("chromatic", "Chromatic Ab.", "🌈", glitch_chromatic, [
        ("Raggio",         0.0, 2.0, 1.0, 0.1, "chr_rad"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05,"chr_ang"),
        ("Forza",          0.0, 2.0, 1.0, 0.1, "chr_str"),
    ]),
    ("datamosh", "Datamosh", "📼", glitch_datamosh, [
        ("Dim. Blocchi",   0.0, 2.0, 1.0, 0.1, "dm_block"),
        ("Decay",          0.0, 1.0, 0.5, 0.05,"dm_decay"),
        ("N. Frame",       0.0, 1.0, 0.5, 0.05,"dm_frames"),
    ]),
    ("scanline_burn", "Scanline Burn", "📟", glitch_scanline_burn, [
        ("Intensità",      0.0, 2.0, 1.0, 0.1, "sb_int"),
        ("Densità",        0.0, 1.0, 0.4, 0.05,"sb_den"),
        ("Color Bleed",    0.0, 1.0, 0.5, 0.05,"sb_bleed"),
    ]),
    ("psychedelic", "Psychedelic", "🔮", glitch_psychedelic, [
        ("Hue Shift",      0.0, 1.0, 0.3, 0.05,"psy_hue"),
        ("Saturazione",    0.0, 1.0, 0.5, 0.05,"psy_sat"),
        ("Inversione",     0.0, 1.0, 0.0, 0.1, "psy_inv"),
    ]),
    ("channel_swap", "Channel Swap", "🔁", glitch_channel_swap, [
        ("Modalità",       0.0, 1.0, 0.3, 0.1, "cs_mode"),
        ("Intensità",      0.0, 1.0, 0.7, 0.05,"cs_int"),
        ("Blend",          0.0, 1.0, 0.6, 0.05,"cs_blend"),
    ]),
    ("image_feedback", "Image Feedback", "🔁🔁", glitch_image_feedback, [
        ("Zoom",           0.0, 1.0, 0.5, 0.05,"fb_zoom"),
        ("Iterazioni",     0.0, 1.0, 0.4, 0.05,"fb_iter"),
        ("Decay",          0.0, 1.0, 0.5, 0.05,"fb_decay"),
    ]),
    ("destruction_art", "Destruction Art", "✂️", glitch_destruction_art, [
        ("Tagli",          0.0, 1.0, 0.5, 0.05,"da_cuts"),
        ("Scatter",        0.0, 1.0, 0.4, 0.05,"da_scatter"),
        ("Color Shift",    0.0, 1.0, 0.5, 0.05,"da_color"),
    ]),
    ("analogic", "Glitch Analogic", "📡", glitch_analogic, [
        ("Sync Loss",      0.0, 1.0, 0.5, 0.05,"ag_sync"),
        ("Color Bleed",    0.0, 1.0, 0.4, 0.05,"ag_bleed"),
        ("Static",         0.0, 1.0, 0.3, 0.05,"ag_static"),
    ]),
    ("displacement_map", "Displacement Map", "🌊", glitch_displacement_map, [
        ("Forza",          0.0, 1.0, 0.5, 0.05,"dsp_strength"),
        ("Scala Blur",     0.0, 1.0, 0.4, 0.05,"dsp_scale"),
        ("Canale Mappa",   0.0, 1.0, 0.3, 0.05,"dsp_channel"),
    ]),
]


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ══════════════════════════════════════════════════════════════════════════════

EFFECT_QUOTES = {
    "vhs":            "Il nastro ha consumato i colori. La memoria e' distorta.",
    "distruttivo":    "I blocchi si sono spostati. La struttura non esiste piu'.",
    "noise":          "Il segnale e' collassato. Il rumore ha preso il controllo.",
    "pixel_sort":     "La luce ha scelto il suo ordine. Il pixel ha obbedito.",
    "wave_warp":      "La materia e' diventata liquida. La forma e' un'illusione.",
    "chromatic":      "Il prisma ha spezzato la luce. I colori non tornano piu'.",
    "datamosh":       "Il frame e' rimasto bloccato. Il tempo non scorre piu'.",
    "scanline_burn":  "Il tubo e' bruciato. Il CRT ricorda ancora.",
    "psychedelic":    "L'hue ha ruotato oltre il visibile. La realta' e' soggettiva.",
    "channel_swap":   "I canali si sono scambiati. Il colore non riconosce se stesso.",
    "image_feedback": "Lo schermo si e' guardato allo specchio. L'infinito e' iniziato.",
    "destruction_art":"L'immagine e' stata tagliata. Il collage e' l'unica verita'.",
    "analogic":       "Il segnale ha perso il sincronismo. L'antenna non risponde.",
    "displacement_map":"Il pixel si e' spostato seguendo se stesso. Lo spazio e' curvo.",
}

EFFECT_ENGINES = {
    "vhs":            "magnetic_tape_engine",
    "distruttivo":    "block_fragment_engine",
    "noise":          "entropy_noise_core",
    "pixel_sort":     "luminance_sort_engine",
    "wave_warp":      "sinusoidal_warp_engine",
    "chromatic":      "radial_aberration_core",
    "datamosh":       "frame_decay_engine",
    "scanline_burn":  "crt_burn_engine",
    "psychedelic":    "hue_rotation_core",
    "channel_swap":   "channel_matrix_engine",
    "image_feedback": "recursive_zoom_engine",
    "destruction_art":"strip_collage_engine",
    "analogic":       "analog_sync_engine",
    "displacement_map":"self_displacement_engine",
}


def make_report(effect_key: str, effect_label: str, img_size, param_vals: list, param_labels: list, ts: str) -> bytes:
    w, h = img_size
    mpx = w * h / 1_000_000
    date_str, time_str = ts.split(" ")
    engine = EFFECT_ENGINES.get(effect_key, "unknown_engine")
    quote  = EFFECT_QUOTES.get(effect_key, "Il glitch e' la verita'.")
    avg_pct = int(sum(param_vals) / len(param_vals) / 2.0 * 100) if param_vals else 0

    lines = [
        f"GLITCHLAB [IMAGE] // {effect_label.upper()} // 01 //",
        f":: MOTORE: {engine} [v2.0]",
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
        lines.append(f"* {label:<18}: {val:.2f}")
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

ss_keys = ["processed"] + [f"img_{e[0]}" for e in EFFECTS] + [f"rep_{e[0]}" for e in EFFECTS]
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

        # ── Controlli per ogni effetto ─────────────────────────────────────────
        st.markdown("### 🎛️ Controlli Effetti")
        all_params = {}  # {effect_key: [val1, val2, val3]}

        # Disponi expander in 2 colonne
        left_effects  = EFFECTS[:7]
        right_effects = EFFECTS[7:]
        col_l, col_r  = st.columns(2)

        for col, eff_list in [(col_l, left_effects), (col_r, right_effects)]:
            with col:
                for key, label, emoji, fn, sliders in eff_list:
                    with st.expander(f"{emoji} {label}", expanded=False):
                        vals = []
                        sc = st.columns(len(sliders))
                        for i, (slabel, smin, smax, sdef, sstep, skey) in enumerate(sliders):
                            v = sc[i].slider(slabel, smin, smax, sdef, sstep, key=skey)
                            vals.append(v)
                        all_params[key] = vals

        # ── Modalità Live / Manuale ────────────────────────────────────────────
        st.markdown("---")
        live_mode = st.checkbox(
            "⚡ Modalità Live — ogni slider aggiorna in tempo reale",
            value=False, key="live_mode"
        )
        should_process = live_mode
        if not live_mode:
            if st.button("✨ Genera tutti gli effetti"):
                should_process = True

        # ── Elaborazione ──────────────────────────────────────────────────────
        if should_process:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = "⚡ Live..." if live_mode else "🔥 Generazione in corso..."
            with st.spinner(msg):
                for key, label, emoji, fn, sliders in EFFECTS:
                    vals = all_params[key]
                    result_img = fn(img, *vals)
                    st.session_state[f"img_{key}"] = img_to_bytes(result_img)
                    param_labels = [s[0] for s in sliders]
                    st.session_state[f"rep_{key}"] = make_report(key, label, img.size, vals, param_labels, ts)
            st.session_state.processed = True

        # ── Risultati ─────────────────────────────────────────────────────────
        if st.session_state.processed:
            header = "⚡ Live — ultimo frame" if live_mode else "🔥 Risultati glitch"
            st.subheader(header)

            # Griglia 4 colonne
            for row_start in range(0, len(EFFECTS), 4):
                row_effects = EFFECTS[row_start:row_start + 4]
                cols = st.columns(len(row_effects))
                for col, (key, label, emoji, fn, sliders) in zip(cols, row_effects):
                    img_bytes = st.session_state[f"img_{key}"]
                    rep_bytes = st.session_state[f"rep_{key}"]
                    with col:
                        st.image(img_bytes, caption=f"{emoji} {label}", use_container_width=True)
                        st.download_button(
                            "⬇️ Immagine", img_bytes,
                            f"{key}_glitch.png", "image/png",
                            key=f"dl_img_{key}"
                        )
                        st.download_button(
                            "📄 Report", rep_bytes,
                            f"{key}_report.txt", "text/plain",
                            key=f"dl_rep_{key}"
                        )
                st.markdown("---")

        if live_mode and st.session_state.processed:
            st.caption("💡 I download salvano l'ultimo frame generato.")

    except Exception as e:
        st.error(f"Errore: {e}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")
else:
    st.info("📁 Carica un'immagine per iniziare!")


# ── Helpers ───────────────────────────────────────────────────────────────────
def img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** — 13 effetti glitch per le tue foto")
st.markdown("*⚡ Live per lavorare in tempo reale · ✨ Genera per elaborare tutti gli effetti insieme*")
