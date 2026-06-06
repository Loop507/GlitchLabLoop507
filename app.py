import streamlit as st
from PIL import Image
import numpy as np
import io
import random
from datetime import datetime

st.set_page_config(page_title="GlitchLabLoop507", layout="wide")
st.title("🔥 GlitchLabLoop507")
st.write("Carica una foto e applica 14 effetti glitch — Live o Manuale.")


# ── Helper ────────────────────────────────────────────────────────────────────
def img_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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


def glitch_op_art_circles(img, frequency=1.0, contrast=1.0, blend=0.5):
    """Cerchi concentrici che distorcono l'immagine — Op Art ipnotica."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w]
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        freq = 0.05 + 0.15 * frequency
        wave = np.sin(dist * freq) * 0.5 + 0.5  # 0…1
        wave3 = wave[:, :, np.newaxis]
        contrast_arr = np.clip(arr * (0.5 + contrast), 0, 255)
        inverted = 255 - arr
        result = arr * (1 - blend * wave3) + inverted * (blend * wave3)
        result = np.clip(result * (0.7 + 0.6 * contrast_arr / 255), 0, 255)
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Op Art Circles: {e}"); return img


def glitch_halftone(img, dot_size=1.0, angle=0.3, color_mode=0.5):
    """Puntini tipografici — stampa offset anni '60."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        cell = max(4, int(4 + 16 * dot_size))
        out = np.zeros_like(arr)
        angle_rad = angle * np.pi

        for y in range(0, h, cell):
            for x in range(0, w, cell):
                patch = arr[y:y+cell, x:x+cell]
                if patch.size == 0:
                    continue
                avg = patch.mean(axis=(0, 1))
                lum = (avg[0]*0.299 + avg[1]*0.587 + avg[2]*0.114) / 255
                radius = int((cell / 2) * (1 - lum) * 1.5)
                cy_p, cx_p = y + cell // 2, x + cell // 2
                ys_p = np.arange(max(0, cy_p - cell), min(h, cy_p + cell))
                xs_p = np.arange(max(0, cx_p - cell), min(w, cx_p + cell))
                if len(ys_p) == 0 or len(xs_p) == 0:
                    continue
                yy, xx = np.meshgrid(ys_p, xs_p, indexing='ij')
                mask = (xx - cx_p)**2 + (yy - cy_p)**2 <= radius**2
                if color_mode > 0.5:
                    color = avg
                else:
                    color = np.array([0, 0, 0]) if lum < 0.5 else np.array([255, 255, 255])
                out[yy[mask], xx[mask]] = color

        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Halftone: {e}"); return img


def glitch_moire(img, freq1=1.0, freq2=1.0, angle=0.3):
    """Griglie sovrapposte — pattern ottico vibrante."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        a = angle * np.pi
        f1 = 0.05 + 0.15 * freq1
        f2 = 0.04 + 0.12 * freq2
        grid1 = np.sin(xs * f1 * np.cos(a) + ys * f1 * np.sin(a))
        grid2 = np.sin(xs * f2 * np.cos(a + 0.3) + ys * f2 * np.sin(a + 0.3))
        moire = ((grid1 * grid2) * 0.5 + 0.5)[:, :, np.newaxis]
        result = arr * moire + (255 - arr) * (1 - moire)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Moire: {e}"); return img


def glitch_kaleidoscope(img, segments=1.0, rotation=0.0, zoom=0.5):
    """Simmetria radiale — specchi geometrici."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        n_seg = max(2, int(2 + 10 * segments))
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        dy, dx = ys - cy, xs - cx
        angles = np.arctan2(dy, dx)
        radii  = np.sqrt(dx**2 + dy**2)
        seg_angle = np.pi / n_seg
        angles_mod = angles % (2 * seg_angle)
        angles_mod = np.where(angles_mod > seg_angle, 2 * seg_angle - angles_mod, angles_mod)
        angles_mod += rotation * np.pi
        scale = 0.5 + zoom
        src_x = np.clip((cx + radii * np.cos(angles_mod) * scale).astype(int), 0, w - 1)
        src_y = np.clip((cy + radii * np.sin(angles_mod) * scale).astype(int), 0, h - 1)
        return Image.fromarray(arr[src_y, src_x])
    except Exception as e:
        st.error(f"Kaleidoscope: {e}"); return img


def glitch_oil_paint(img, radius=1.0, levels=1.0, blend=0.5):
    """Pennellate di olio — algoritmo di Kuwahara semplificato."""
    try:
        from PIL import ImageFilter
        img = img.convert("RGB")
        r = max(2, int(2 + 6 * radius))
        lev = max(2, int(2 + 6 * levels))
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        out = arr.copy()
        # Kuwahara: per ogni pixel sceglie il quadrante con varianza minima
        step = max(1, r // 2)
        for dy_off, dx_off in [(-r, -r), (-r, 0), (0, -r), (0, 0)]:
            y0 = max(0, -dy_off); y1 = min(h, h - dy_off)
            x0 = max(0, -dx_off); x1 = min(w, w - dx_off)
            patch = arr[y0:y1, x0:x1]
            var = patch.var(axis=2)
            mean = patch.mean(axis=2, keepdims=True)
        # Semplificato: blur progressivo + posterizzazione
        blurred = np.array(
            Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)),
            dtype=np.float32
        )
        # Posterize
        step_size = 256 / lev
        posterized = (np.floor(blurred / step_size) * step_size).clip(0, 255)
        result = arr * (1 - blend) + posterized * blend
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Oil Paint: {e}"); return img


def glitch_posterize(img, levels=1.0, dither=0.5, color_shift=0.3):
    """Colori ridotti a fasce piatte — poster serigrafico."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lev = max(2, int(2 + 6 * levels))
        step = 256.0 / lev
        # Dithering con rumore prima della posterizzazione
        if dither > 0.05:
            noise = np.random.uniform(-step * dither * 0.5, step * dither * 0.5, arr.shape)
            arr = np.clip(arr + noise, 0, 255)
        posterized = (np.floor(arr / step) * step).clip(0, 255)
        # Shift colore per canale
        if color_shift > 0.05:
            shifts = [int(color_shift * random.uniform(-20, 20)) for _ in range(3)]
            for ch, s in enumerate(shifts):
                posterized[:, :, ch] = np.roll(posterized[:, :, ch], s, axis=1)
        return Image.fromarray(posterized.astype(np.uint8))
    except Exception as e:
        st.error(f"Posterize: {e}"); return img


def glitch_neon_glow(img, threshold=0.5, glow_width=1.0, color_mode=0.5):
    """Bordi luminosi neon su nero — estetica cyberpunk."""
    try:
        from PIL import ImageFilter
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        # Estrai bordi con differenza di blur
        blur_small = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)), dtype=np.float32)
        blur_large = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(2, int(2 + 6 * glow_width)))), dtype=np.float32)
        edges = np.abs(blur_small - blur_large).mean(axis=2)
        edges = edges / (edges.max() + 1e-8)
        mask = (edges > threshold * 0.3)[:, :, np.newaxis]
        # Colore neon
        if color_mode < 0.25:
            neon = np.array([0, 255, 255], dtype=np.float32)   # ciano
        elif color_mode < 0.5:
            neon = np.array([255, 0, 255], dtype=np.float32)   # magenta
        elif color_mode < 0.75:
            neon = np.array([0, 255, 0], dtype=np.float32)     # verde
        else:
            neon = np.array([255, 200, 0], dtype=np.float32)   # giallo
        bg = np.zeros_like(arr)
        glow_layer = bg + neon
        intensity = np.clip(edges * 3, 0, 1)[:, :, np.newaxis]
        result = arr * (1 - intensity * 0.8) + glow_layer * intensity * 0.8
        result = np.clip(result, 0, 255)
        return Image.fromarray(result.astype(np.uint8))
    except Exception as e:
        st.error(f"Neon Glow: {e}"); return img


def glitch_duotone(img, color1=0.1, color2=0.7, blend=0.8):
    """Due colori soli — grafica contemporanea."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255
        # Genera due colori da hue
        def hue_to_rgb(h):
            h = h % 1.0
            r = abs(h * 6 - 3) - 1
            g = 2 - abs(h * 6 - 2)
            b = 2 - abs(h * 6 - 4)
            return np.clip([r, g, b], 0, 1) * 255
        c1 = hue_to_rgb(color1)
        c2 = hue_to_rgb(color2)
        t = lum[:, :, np.newaxis]
        result = c1 * (1 - t) + c2 * t
        result = arr * (1 - blend) + result * blend
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Duotone: {e}"); return img


def glitch_solarize(img, threshold=0.5, strength=1.0, channel_split=0.3):
    """Inversione alte luci — camera oscura anni '70."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        thresh = threshold * 255
        mask = arr > thresh
        inverted = arr.copy()
        inverted[mask] = 255 - arr[mask]
        result = arr * (1 - strength) + inverted * strength
        if channel_split > 0.05:
            s = int(channel_split * 20)
            result[:, :, 0] = np.roll(result[:, :, 0], s, axis=1)
            result[:, :, 2] = np.roll(result[:, :, 2], -s, axis=0)
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Solarize: {e}"); return img


def glitch_thermal(img, palette=0.5, noise=0.2, contrast=1.0):
    """Falsi colori termografici."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114)
        lum = lum / 255.0
        if noise > 0.01:
            lum = np.clip(lum + np.random.uniform(-noise*0.1, noise*0.1, lum.shape), 0, 1)
        # Contrasto
        lum = np.clip((lum - 0.5) * (1 + contrast) + 0.5, 0, 1)
        # Palette termica: freddo(viola) → blu → ciano → verde → giallo → rosso → bianco
        palettes = [
            [(0.05,0,0.2),(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0,0),(1,1,1)],
            [(0,0,0.5),(0,0.5,1),(0,1,0.5),(0.5,1,0),(1,0.5,0),(1,0,0),(1,1,1)],
        ]
        pal = palettes[int(palette > 0.5)]
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


def glitch_polar(img, strength=1.0, rotation=0.0, zoom=0.5):
    """Coordinate polari — immagine avvolta su se stessa."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        # Mappa polare → cartesiana
        norm_x = (xs / w - 0.5) * 2
        norm_y = (ys / h - 0.5) * 2
        radius = np.sqrt(norm_x**2 + norm_y**2)
        angle  = np.arctan2(norm_y, norm_x) + rotation * np.pi
        # Coordinate sorgente in spazio polare
        scale = 0.3 + 0.7 * zoom
        src_x = np.clip(((angle / (2 * np.pi) + 0.5) * w * scale).astype(int) % w, 0, w - 1)
        src_y = np.clip((radius * h * strength * 0.6).astype(int), 0, h - 1)
        warped = arr[src_y, src_x]
        # Blend con originale ai bordi
        blend = np.clip(radius, 0, 1)[:, :, np.newaxis]
        result = (arr * (1 - blend * strength) + warped * blend * strength).astype(np.uint8)
        return Image.fromarray(result)
    except Exception as e:
        st.error(f"Polar: {e}"); return img


def glitch_tunnel_zoom(img, layers=1.0, speed=0.5, color_shift=0.3):
    """Zoom concentrico infinito — tunnel visivo."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        n_layers = int(3 + 7 * layers)
        accumulated = np.zeros_like(arr)
        total_weight = 0
        for i in range(n_layers):
            scale = 1.0 / (1.3 + i * 0.4 * speed)
            new_h = max(4, int(h * scale))
            new_w = max(4, int(w * scale))
            small = np.array(
                Image.fromarray(arr.astype(np.uint8)).resize((new_w, new_h), Image.BILINEAR),
                dtype=np.float32
            )
            # Centra
            pad_y = (h - new_h) // 2
            pad_x = (w - new_w) // 2
            layer = np.zeros_like(arr)
            layer[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = small
            # Color shift per strato
            if color_shift > 0.05:
                s = int(i * color_shift * 5)
                layer[:, :, 0] = np.roll(layer[:, :, 0], s, axis=1)
                layer[:, :, 2] = np.roll(layer[:, :, 2], -s, axis=1)
            w_layer = 1.0 / (i + 1)
            accumulated += layer * w_layer
            total_weight += w_layer
        result = accumulated / total_weight
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    except Exception as e:
        st.error(f"Tunnel Zoom: {e}"); return img


def glitch_mirror_kaleidoscope(img, mirrors=0.5, rotation=0.0, zoom=0.5):
    """4/6/8 specchi radiali — simmetria perfetta."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        h, w, _ = arr.shape
        n_mirrors = 4 if mirrors < 0.33 else (6 if mirrors < 0.66 else 8)
        cy, cx = h / 2, w / 2
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        dy, dx = ys - cy, xs - cx
        angles = np.arctan2(dy, dx) + rotation * np.pi
        radii  = np.sqrt(dx**2 + dy**2)
        seg = np.pi / n_mirrors
        angles_mod = angles % (2 * seg)
        angles_mod = np.where(angles_mod > seg, 2 * seg - angles_mod, angles_mod)
        scale = 0.4 + 0.8 * zoom
        src_x = np.clip((cx + radii * np.cos(angles_mod) * scale).astype(int), 0, w - 1)
        src_y = np.clip((cy + radii * np.sin(angles_mod) * scale).astype(int), 0, h - 1)
        return Image.fromarray(arr[src_y, src_x])
    except Exception as e:
        st.error(f"Mirror Kaleidoscope: {e}"); return img


def glitch_crosshatch(img, density=0.5, angle=0.3, thickness=0.3):
    """Tratteggi incrociati — incisione su rame."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255
        spacing = max(2, int(3 + 10 * (1 - density)))
        thick = max(1, int(1 + 2 * thickness))
        a = angle * np.pi * 0.5
        out = np.ones((h, w, 3), dtype=np.float32) * 255
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        # Primo set di linee
        line1 = (xs * np.cos(a) + ys * np.sin(a)) % spacing
        # Secondo set perpendicolare
        line2 = (xs * np.cos(a + np.pi/2) + ys * np.sin(a + np.pi/2)) % spacing
        dark = lum < 0.5
        medium = (lum >= 0.5) & (lum < 0.75)
        hatch1 = line1 < thick
        hatch2 = line2 < thick
        # Zone scure: doppio tratteggio
        mask_dark = dark & (hatch1 | hatch2)
        # Zone medie: tratteggio singolo
        mask_med = medium & hatch1
        out[mask_dark] = arr[mask_dark] * 0.1
        out[mask_med]  = arr[mask_med] * 0.3
        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Crosshatch: {e}"); return img


def glitch_stippling(img, density=0.5, dot_size=0.5, color_mode=0.5):
    """Puntinismo digitale — nuvole di punti."""
    try:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        lum = (arr[:, :, 0]*0.299 + arr[:, :, 1]*0.587 + arr[:, :, 2]*0.114) / 255
        out = np.ones((h, w, 3), dtype=np.float32) * 255
        # Numero di punti proporzionale alla densità e alle zone scure
        n_dots = int(w * h * 0.02 * density)
        max_r = max(1, int(1 + 3 * dot_size))
        # Campionamento pesato per luminosità (zone scure = più punti)
        prob = 1 - lum
        prob = prob / prob.sum()
        flat_idx = np.random.choice(h * w, size=min(n_dots, h * w), replace=False, p=prob.ravel())
        ys_dots = flat_idx // w
        xs_dots = flat_idx % w
        for i in range(len(ys_dots)):
            y, x = ys_dots[i], xs_dots[i]
            r = random.randint(1, max_r)
            y0, y1 = max(0, y-r), min(h, y+r+1)
            x0, x1 = max(0, x-r), min(w, x+r+1)
            color = arr[y, x] if color_mode > 0.5 else np.array([0, 0, 0])
            out[y0:y1, x0:x1] = color
        return Image.fromarray(out.astype(np.uint8))
    except Exception as e:
        st.error(f"Stippling: {e}"); return img


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
    ("op_art_circles", "Op Art Circles", "⭕", glitch_op_art_circles, [
        ("Frequenza",      0.0, 1.0, 0.5, 0.05,"oa_freq"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05,"oa_cont"),
        ("Blend",          0.0, 1.0, 0.5, 0.05,"oa_blend"),
    ]),
    ("halftone", "Halftone", "🔵", glitch_halftone, [
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05,"ht_size"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05,"ht_angle"),
        ("Colore",         0.0, 1.0, 0.7, 0.05,"ht_color"),
    ]),
    ("moire", "Moire Pattern", "🔲", glitch_moire, [
        ("Frequenza 1",    0.0, 1.0, 0.4, 0.05,"mo_f1"),
        ("Frequenza 2",    0.0, 1.0, 0.6, 0.05,"mo_f2"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05,"mo_ang"),
    ]),
    ("kaleidoscope", "Kaleidoscope", "💎", glitch_kaleidoscope, [
        ("Segmenti",       0.0, 1.0, 0.4, 0.05,"kal_seg"),
        ("Rotazione",      0.0, 1.0, 0.0, 0.05,"kal_rot"),
        ("Zoom",           0.0, 1.0, 0.5, 0.05,"kal_zoom"),
    ]),
    ("oil_paint", "Oil Paint", "🖌️", glitch_oil_paint, [
        ("Raggio",         0.0, 1.0, 0.4, 0.05,"op_rad"),
        ("Livelli",        0.0, 1.0, 0.5, 0.05,"op_lev"),
        ("Blend",          0.0, 1.0, 0.7, 0.05,"op_blend"),
    ]),
    ("posterize", "Posterize", "🎨", glitch_posterize, [
        ("Livelli",        0.0, 1.0, 0.4, 0.05,"po_lev"),
        ("Dither",         0.0, 1.0, 0.4, 0.05,"po_dith"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05,"po_col"),
    ]),
    ("neon_glow", "Neon Glow", "💡", glitch_neon_glow, [
        ("Soglia",         0.0, 1.0, 0.5, 0.05,"ng_thresh"),
        ("Ampiezza",       0.0, 1.0, 0.5, 0.05,"ng_width"),
        ("Colore",         0.0, 1.0, 0.2, 0.05,"ng_color"),
    ]),
    ("duotone", "Duotone", "🎭", glitch_duotone, [
        ("Colore 1",       0.0, 1.0, 0.1, 0.05,"dt_c1"),
        ("Colore 2",       0.0, 1.0, 0.6, 0.05,"dt_c2"),
        ("Blend",          0.0, 1.0, 0.8, 0.05,"dt_blend"),
    ]),
    ("solarize", "Solarize", "☀️", glitch_solarize, [
        ("Soglia",         0.0, 1.0, 0.5, 0.05,"sol_thresh"),
        ("Forza",          0.0, 1.0, 0.8, 0.05,"sol_str"),
        ("Channel Split",  0.0, 1.0, 0.3, 0.05,"sol_ch"),
    ]),
    ("thermal", "Thermal Camera", "🌡️", glitch_thermal, [
        ("Palette",        0.0, 1.0, 0.3, 0.05,"th_pal"),
        ("Rumore",         0.0, 1.0, 0.2, 0.05,"th_noise"),
        ("Contrasto",      0.0, 1.0, 0.6, 0.05,"th_cont"),
    ]),
    ("polar", "Polar Coords", "🌀", glitch_polar, [
        ("Forza",          0.0, 1.0, 0.6, 0.05,"pol_str"),
        ("Rotazione",      0.0, 1.0, 0.0, 0.05,"pol_rot"),
        ("Zoom",           0.0, 1.0, 0.5, 0.05,"pol_zoom"),
    ]),
    ("tunnel_zoom", "Tunnel Zoom", "🔭", glitch_tunnel_zoom, [
        ("Strati",         0.0, 1.0, 0.5, 0.05,"tz_layers"),
        ("Velocità",       0.0, 1.0, 0.5, 0.05,"tz_speed"),
        ("Color Shift",    0.0, 1.0, 0.3, 0.05,"tz_col"),
    ]),
    ("mirror_kal", "Mirror Kaleido.", "🪞", glitch_mirror_kaleidoscope, [
        ("Specchi",        0.0, 1.0, 0.3, 0.1, "mk_mirrors"),
        ("Rotazione",      0.0, 1.0, 0.0, 0.05,"mk_rot"),
        ("Zoom",           0.0, 1.0, 0.5, 0.05,"mk_zoom"),
    ]),
    ("crosshatch", "Crosshatch", "✏️", glitch_crosshatch, [
        ("Densità",        0.0, 1.0, 0.5, 0.05,"ch_den"),
        ("Angolo",         0.0, 1.0, 0.3, 0.05,"ch_ang"),
        ("Spessore",       0.0, 1.0, 0.3, 0.05,"ch_thick"),
    ]),
    ("stippling", "Stippling", "🔴", glitch_stippling, [
        ("Densità",        0.0, 1.0, 0.5, 0.05,"st_den"),
        ("Dim. Punto",     0.0, 1.0, 0.4, 0.05,"st_dot"),
        ("Colore",         0.0, 1.0, 0.6, 0.05,"st_col"),
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
    "displacement_map": "Il pixel si e' spostato seguendo se stesso. Lo spazio e' curvo.",
    "op_art_circles":   "I cerchi hanno ipnotizzato la forma. L'occhio non trova pace.",
    "halftone":         "La stampa ha dissolto l'immagine. Il punto e' tutto cio' che resta.",
    "moire":            "Le griglie si sono scontrate. Il pattern e' nato dal conflitto.",
    "kaleidoscope":     "Lo specchio si e' moltiplicato. La simmetria e' diventata caos.",
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
    "displacement_map": "self_displacement_engine",
    "op_art_circles":   "concentric_wave_engine",
    "halftone":         "halftone_dot_engine",
    "moire":            "grid_interference_engine",
    "kaleidoscope":     "radial_mirror_engine",
    "oil_paint":        "kuwahara_paint_engine",
    "posterize":        "color_quantize_engine",
    "neon_glow":        "edge_neon_engine",
    "duotone":          "dual_color_engine",
    "solarize":         "highlight_invert_engine",
    "thermal":          "false_color_engine",
    "polar":            "polar_coords_engine",
    "tunnel_zoom":      "recursive_zoom_engine",
    "mirror_kal":       "radial_symmetry_engine",
    "crosshatch":       "hatch_render_engine",
    "stippling":        "pointillism_engine",
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

ss_keys = ["processed"] + [f"img_{e[0]}" for e in EFFECTS] + [f"rep_{e[0]}" for e in EFFECTS] + [f"params_{e[0]}" for e in EFFECTS]
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

        # ── Modalità Live / Manuale ────────────────────────────────────────────
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

        # ── Expander per ogni effetto: slider + anteprima + download ──────────
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_params = {}

        for key, label, emoji, fn, sliders in EFFECTS:
            with st.expander(f"{emoji} {label}", expanded=False):

                # Slider
                sc = st.columns(len(sliders))
                vals = []
                for i, (slabel, smin, smax, sdef, sstep, skey) in enumerate(sliders):
                    v = sc[i].slider(slabel, smin, smax, sdef, sstep, key=skey)
                    vals.append(v)
                all_params[key] = vals

                # Rileva se i parametri sono cambiati rispetto all'ultimo calcolo
                prev_vals = st.session_state.get(f"params_{key}")
                params_changed = (prev_vals != vals)

                # Elabora se: Genera premuto, oppure slider cambiato (in Live sempre; in Manuale solo se gia' calcolato)
                needs_process = (
                    should_process
                    or (live_mode and params_changed)
                    or (not live_mode and params_changed and st.session_state.get(f"img_{key}") is not None)
                )

                if needs_process:
                    result_img = fn(img, *vals)
                    st.session_state[f"img_{key}"] = img_to_bytes(result_img)
                    param_labels = [s[0] for s in sliders]
                    st.session_state[f"rep_{key}"] = make_report(
                        key, label, img.size, vals, param_labels, ts
                    )
                    st.session_state[f"params_{key}"] = vals
                    st.session_state.processed = True

                # Anteprima + download dentro l'expander
                if st.session_state.get(f"img_{key}"):
                    img_bytes = st.session_state[f"img_{key}"]
                    rep_bytes = st.session_state[f"rep_{key}"]
                    st.image(img_bytes, caption=f"{emoji} {label}", use_container_width=True)
                    dl1, dl2 = st.columns(2)
                    dl1.download_button(
                        "⬇️ Immagine", img_bytes,
                        f"{key}_glitch.png", "image/png",
                        key=f"dl_img_{key}"
                    )
                    dl2.download_button(
                        "📄 Report", rep_bytes,
                        f"{key}_report.txt", "text/plain",
                        key=f"dl_rep_{key}"
                    )


    except Exception as e:
        st.error(f"Errore: {e}")
        st.info("Assicurati che il file sia un'immagine valida (JPG, JPEG, PNG)")
else:
    st.info("📁 Carica un'immagine per iniziare!")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("🔥 **GlitchLabLoop507** — 13 effetti glitch per le tue foto")
st.markdown("*⚡ Live per lavorare in tempo reale · ✨ Genera per elaborare tutti gli effetti insieme*")
