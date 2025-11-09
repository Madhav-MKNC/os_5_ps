from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor
import os, math
from datetime import datetime
import uuid

def _rgb(col):
    if isinstance(col, (list,tuple)): return tuple(col)
    return ImageColor.getrgb(col)

def _find_font_file(fonts_dir, ps_name_or_filename):
    if not ps_name_or_filename: return None
    # direct filename
    candidate = os.path.join(fonts_dir, ps_name_or_filename)
    if os.path.exists(candidate): return candidate
    # substring match
    key = ps_name_or_filename.lower()
    for fname in os.listdir(fonts_dir):
        if key in fname.lower() or fname.lower().split('.')[0] in key:
            return os.path.join(fonts_dir, fname)
    return None

def _draw_text_outline(draw, pos, text, font, fill, outline_width, outline_fill):
    x,y = pos
    # simple square outline
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx==0 and dy==0: continue
            draw.text((x+dx, y+dy), text, font=font, fill=outline_fill)
    draw.text((x,y), text, font=font, fill=fill)

def _create_gradient_image_for_text(text, font, size, gradient):
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.text((0,0), text, font=font, fill=255)
    top = ImageColor.getrgb(gradient[0])
    bottom = ImageColor.getrgb(gradient[1])
    grad = Image.new("RGBA", size)
    gd = ImageDraw.Draw(grad)
    w,h = size
    for i in range(h):
        r = int(top[0] + (bottom[0]-top[0]) * (i/(h-1 if h>1 else 1)))
        g = int(top[1] + (bottom[1]-top[1]) * (i/(h-1 if h>1 else 1)))
        b = int(top[2] + (bottom[2]-top[2]) * (i/(h-1 if h>1 else 1)))
        gd.line([(0,i),(w,i)], fill=(r,g,b))
    return grad, mask

def render_text_on_image(payload, output_dir, fonts_dir, previews_dir):
    width = int(payload.get("width", 1200))
    height = int(payload.get("height", 800))
    background_preview = payload.get("background_preview")  # filename in previews_dir
    if background_preview:
        bg_path = os.path.join(previews_dir, background_preview)
        if os.path.exists(bg_path):
            base = Image.open(bg_path).convert("RGBA").resize((width,height))
        else:
            base = Image.new("RGBA",(width,height),(255,255,255,255))
    else:
        base = Image.new("RGBA",(width,height),(255,255,255,255))

    entries = payload.get("text_entries", [])
    for e in entries:
        text = e.get("text","")
        x = int(e.get("x", width//2))
        y = int(e.get("y", height//2))
        size = int(e.get("size", 72))
        color = e.get("color", [0,0,0])
        effects = e.get("effects", {}) or {}
        font_file = None
        # check uploaded font name or postscript mapping
        if e.get("font") and os.path.exists(os.path.join(fonts_dir, e.get("font"))):
            font_file = os.path.join(fonts_dir, e.get("font"))
        else:
            font_file = _find_font_file(fonts_dir, e.get("font_postscript") or e.get("font",""))

        try:
            if font_file:
                font = ImageFont.truetype(font_file, size)
            else:
                font = ImageFont.truetype("arial.ttf", size)
        except Exception:
            font = ImageFont.load_default()

        # 3D depth
        depth = int(effects.get("3d_depth", 0))
        if depth > 0:
            depth_color = tuple(max(0, c-80) for c in _rgb(color))
            for i in range(depth,0,-1):
                tmp = Image.new("RGBA", base.size, (0,0,0,0))
                d = ImageDraw.Draw(tmp)
                d.text((x+i, y+i), text, font=font, fill=depth_color+(200,))
                base = Image.alpha_composite(base, tmp)

        # shadow
        if effects.get("shadow"):
            dx = int(effects.get("shadow_dx", 6))
            dy = int(effects.get("shadow_dy", 6))
            blur = int(effects.get("shadow_blur", 6))
            tmp = Image.new("RGBA", base.size, (0,0,0,0))
            d = ImageDraw.Draw(tmp)
            d.text((x+dx, y+dy), text, font=font, fill=(0,0,0,200))
            tmp = tmp.filter(ImageFilter.GaussianBlur(blur))
            base = Image.alpha_composite(base, tmp)

        # outline
        outline = int(effects.get("outline", 0))
        if outline > 0:
            tmp = Image.new("RGBA", base.size, (0,0,0,0))
            d = ImageDraw.Draw(tmp)
            _draw_text_outline(d, (x,y), text, font, fill=tuple(_rgb(color)), outline_width=outline, outline_fill=(0,0,0))
            base = Image.alpha_composite(base, tmp)
        else:
            # gradient or solid
            if effects.get("gradient") and effects["gradient"][0] and effects["gradient"][1]:
                # measure text bbox
                mask_all = Image.new("L", base.size, 0)
                md = ImageDraw.Draw(mask_all)
                md.text((x,y), text, font=font, fill=255)
                bbox = mask_all.getbbox() or (0,0,base.size[0], base.size[1])
                w = bbox[2]-bbox[0]; h = bbox[3]-bbox[1]
                grad_img, grad_mask = _create_gradient_image_for_text(text, font, (w,h), effects["gradient"])
                region = Image.new("RGBA", base.size, (0,0,0,0))
                region.paste(grad_img, box=(bbox[0], bbox[1]), mask=grad_mask)
                base = Image.alpha_composite(base, region)
            else:
                tmp = Image.new("RGBA", base.size, (0,0,0,0))
                d = ImageDraw.Draw(tmp)
                d.text((x,y), text, font=font, fill=tuple(_rgb(color)))
                base = Image.alpha_composite(base, tmp)

    os.makedirs(output_dir, exist_ok=True)
    outname = f"render_{uuid.uuid4().hex}.png"
    outpath = os.path.join(output_dir, outname)
    base.convert("RGB").save(outpath, "PNG")
    return outpath
