import os, uuid, shutil, pathlib, magic
from flask import Flask, request, jsonify, send_file, render_template, abort
from werkzeug.utils import secure_filename
from config import UPLOAD_DIR, PREVIEW_DIR, OUTPUT_DIR, FONTS_DIR, ALLOWED_PSD_EXT, ALLOWED_FONT_EXT, MAX_CONTENT_LENGTH
from utils.psd_parser import parse_psd_text_layers, export_flattened_preview
from utils.render_engine import render_text_on_image

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# near top after app creation:
app.static_folder = "static"
# expose previews and fonts via simple routes (for dev)
from flask import send_from_directory
@app.route("/previews/<path:fn>") 
def previews(fn): return send_from_directory(PREVIEW_DIR, fn)
@app.route("/fonts/<path:fn>") 
def fonts(fn): return send_from_directory(FONTS_DIR, fn)



def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".",1)[1].lower() in allowed_set

def safe_save(fileobj, dest_dir, allowed_set):
    filename = secure_filename(fileobj.filename)
    if not allowed_file(filename, allowed_set):
        abort(400, "invalid file type")
    uid = uuid.uuid4().hex
    outname = f"{uid}_{filename}"
    path = os.path.join(dest_dir, outname)
    fileobj.save(path)
    # basic magic check
    try:
        m = magic.from_file(path, mime=True)
        # skip strict checks to allow PSD/PSB detection by extension but could add more checks
    except Exception:
        pass
    return outname, path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_psd", methods=["POST"])
def upload_psd():
    f = request.files.get("psd")
    if not f: return jsonify({"error":"no file"}), 400
    name, path = safe_save(f, UPLOAD_DIR, ALLOWED_PSD_EXT)
    # parse layers
    layers = parse_psd_text_layers(path)
    # export flattened preview image for background composition
    preview_path = export_flattened_preview(path, PREVIEW_DIR)
    return jsonify({
        "psd_filename": name,
        "psd_path": os.path.basename(path),
        "preview": os.path.basename(preview_path),
        "layers": layers
    })

@app.route("/upload_font", methods=["POST"])
def upload_font():
    f = request.files.get("font")
    if not f: return jsonify({"error":"no file"}), 400
    name, path = safe_save(f, FONTS_DIR, ALLOWED_FONT_EXT)
    return jsonify({"font": name})

@app.route("/list_fonts")
def list_fonts():
    files = [fn for fn in os.listdir(FONTS_DIR) if allowed_file(fn, ALLOWED_FONT_EXT)]
    return jsonify({"fonts": files})

@app.route("/render", methods=["POST"])
def render_route():
    payload = request.get_json()
    if not payload: return jsonify({"error":"no payload"}), 400
    outpath = render_text_on_image(payload,
                                  output_dir=OUTPUT_DIR,
                                  fonts_dir=FONTS_DIR,
                                  previews_dir=PREVIEW_DIR)
    return send_file(outpath, mimetype="image/png")

@app.route("/download/<path:filename>")
def download(filename):
    safe = secure_filename(filename)
    fp = os.path.join(OUTPUT_DIR, safe)
    if not os.path.exists(fp): abort(404)
    return send_file(fp, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
