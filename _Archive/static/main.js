const uploadPsdBtn = document.getElementById("uploadPsdBtn");
const psdfile = document.getElementById("psdfile");
const psdStatus = document.getElementById("psdStatus");
const previewCard = document.getElementById("previewCard");
const previewImg = document.getElementById("previewImg");
const layersCard = document.getElementById("layersCard");
const layerSelect = document.getElementById("layerSelect");
const editorCard = document.getElementById("editorCard");
const textInput = document.getElementById("textInput");
const sizeInput = document.getElementById("sizeInput");
const colorInput = document.getElementById("colorInput");
const fontFileInput = document.getElementById("fontFileInput");
const shadowChk = document.getElementById("shadowChk");
const shadowBlur = document.getElementById("shadowBlur");
const depthChk = document.getElementById("depthChk");
const outlineInput = document.getElementById("outlineInput");
const g1 = document.getElementById("g1");
const g2 = document.getElementById("g2");
const renderBtn = document.getElementById("renderBtn");
const outputCard = document.getElementById("outputCard");
const outputImg = document.getElementById("outputImg");
const downloadLink = document.getElementById("downloadLink");
const fontsSelect = document.getElementById("fontsSelect");
const refreshFontsBtn = document.getElementById("refreshFontsBtn");
const uploadFontBtn = document.getElementById("uploadFontBtn");
const fontUpload = document.getElementById("fontUpload");
const fontMsg = document.getElementById("fontMsg");

let current = { psd_filename:null, preview:null, layers:[] };

uploadPsdBtn.onclick = async () => {
  if (!psdfile.files.length) return alert("choose psd");
  const f = psdfile.files[0];
  const fd = new FormData();
  fd.append("psd", f);
  psdStatus.innerText = "uploading...";
  const res = await fetch("/upload_psd", { method:"POST", body: fd });
  const j = await res.json();
  if (j.error) { psdStatus.innerText = j.error; return; }
  current.psd_filename = j.psd_filename;
  current.preview = j.preview;
  current.layers = j.layers || [];
  psdStatus.innerText = "uploaded";
  if (current.preview) {
    previewImg.src = `/previews/${current.preview}`;
    previewCard.style.display = "block";
  }
  populateLayers();
  await fetchFonts();
};

function populateLayers(){
  layerSelect.innerHTML = "";
  current.layers.forEach((l,i) => {
    const opt = document.createElement("option");
    opt.value = i; opt.text = `${l.name} — "${(l.text||"").slice(0,40)}"`;
    layerSelect.appendChild(opt);
  });
  if (current.layers.length){
    layersCard.style.display = "block";
    editorCard.style.display = "block";
    selectLayer(0);
  }
}

function selectLayer(i){ const l=current.layers[i]; textInput.value=l.text||""; sizeInput.value=l.size||72; colorInput.value=rgbToHex(l.color||[0,0,0]); fontFileInput.value=""; }

layerSelect.onchange = () => selectLayer(Number(layerSelect.value));

async function fetchFonts(){
  const r = await fetch("/list_fonts");
  const j = await r.json();
  fontsSelect.innerHTML = '<option value="">(choose uploaded font)</option>';
  j.fonts.forEach(fn => {
    const o = document.createElement("option"); o.value=fn; o.text=fn; fontsSelect.appendChild(o);
  });
}

refreshFontsBtn.onclick = fetchFonts;

renderBtn.onclick = async () => {
  const idx = Number(layerSelect.value);
  const l = current.layers[idx];
  const entry = {
    text: textInput.value,
    x: l.position[0]||100,
    y: l.position[1]||100,
    size: Number(sizeInput.value),
    color: hexToRgbArr(colorInput.value),
    font: fontsSelect.value || fontFileInput.value.trim(),
    font_postscript: l.font_postscript||"",
    effects: {
      "shadow": shadowChk.checked,
      "shadow_blur": Number(shadowBlur.value)||6,
      "3d_depth": depthChk.checked?6:0,
      "outline": Number(outlineInput.value)||0,
      "gradient": [g1.value, g2.value]
    }
  };
  const payload = {
    width: previewImg.naturalWidth || 1200,
    height: previewImg.naturalHeight || 800,
    background_preview: current.preview,
    text_entries: [entry]
  };
  renderBtn.disabled = true;
  const res = await fetch("/render", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload) });
  if (!res.ok){ alert("render failed"); renderBtn.disabled = false; return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  outputImg.src = url;
  outputCard.style.display = "block";
  downloadLink.style.display = "inline-block";
  downloadLink.href = url;
  downloadLink.download = `render_${Date.now()}.png`;
  renderBtn.disabled = false;
};

uploadFontBtn.onclick = async () => {
  if (!fontUpload.files.length) return alert("choose font file");
  const fd = new FormData();
  fd.append("font", fontUpload.files[0]);
  const res = await fetch("/upload_font", { method:"POST", body: fd });
  const j = await res.json();
  if (j.font){ fontMsg.innerText = "uploaded "+j.font; await fetchFonts(); } else fontMsg.innerText = "upload failed";
};

function hexToRgbArr(hex){ const bigint = parseInt(hex.replace("#",""),16); return [(bigint>>16)&255,(bigint>>8)&255, bigint&255]; }
function rgbToHex(rgb){ if(!rgb) return "#000000"; return "#" + rgb.map(c => c.toString(16).padStart(2,"0")).join(""); }
