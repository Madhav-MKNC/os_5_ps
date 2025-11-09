from psd_tools import PSDImage
import os, uuid
from PIL import Image

def _normalize_color(vals):
    if vals is None: return [0,0,0]
    # PSD engine sometimes stores 0..1 floats or 0..255 ints
    out = []
    for v in vals[:3]:
        try:
            if 0 <= v <= 1:
                out.append(int(v*255))
            else:
                out.append(int(v))
        except:
            out.append(0)
    return out

def parse_psd_text_layers(psd_path):
    psd = PSDImage.open(psd_path)
    result = []
    for layer in psd.descendants():
        try:
            if not layer.visible:
                continue
            is_text = getattr(layer, "kind", None) == "type" or getattr(layer, "has_text", False)
            if not is_text: continue
            engine = layer.engine_dict or {}
            text = engine.get("Editor", {}).get("Text", "") or layer.name or ""
            sruns = engine.get("StyleRun", {}).get("RunArray", [])
            ssdata = {}
            if sruns:
                ssdata = sruns[0].get("StyleSheet", {}).get("StyleSheetData", {})
            font_post = ssdata.get("Font", "")
            font_size = int(ssdata.get("FontSize") or ssdata.get("FontSize", 24))
            color_vals = ssdata.get("FillColor", {}).get("Values") or ssdata.get("FillColor", {}).get("Values", None)
            color = _normalize_color(color_vals)
            left = getattr(layer, "left", 0)
            top = getattr(layer, "top", 0)
            width = getattr(layer, "width", 0)
            height = getattr(layer, "height", 0)
            result.append({
                "id": uuid.uuid4().hex,
                "name": layer.name or "text",
                "text": text,
                "font_postscript": font_post,
                "size": font_size,
                "color": color,
                "position": [left, top, width, height]
            })
        except Exception:
            continue
    return result

def export_flattened_preview(psd_path, out_dir):
    psd = PSDImage.open(psd_path)
    try:
        composite = psd.composite()
    except Exception:
        # fallback: combine topil of layers
        layers = [lay.topil() for lay in psd if getattr(lay,"visible",True)]
        if layers:
            composite = layers[0].convert("RGBA")
            for im in layers[1:]:
                composite.alpha_composite(im.convert("RGBA"))
        else:
            composite = Image.new("RGBA", (1200,800), (255,255,255,255))
    outname = f"preview_{uuid.uuid4().hex}.png"
    outpath = os.path.join(out_dir, outname)
    composite.save(outpath, "PNG")
    return outpath
