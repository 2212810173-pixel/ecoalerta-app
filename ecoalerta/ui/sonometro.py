"""Medición sonora referencial con el micrófono del celular (Web Audio API)."""
import streamlit.components.v1 as components

from ecoalerta.config import CAL_MIC_DB

_HTML = """
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Inter,system-ui,sans-serif;color:#e2e8f0;background:transparent}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:12px}
.t{background:rgba(15,118,110,.16);border:1px solid rgba(45,212,191,.25);border-radius:12px;padding:10px;font-size:12px;line-height:1.4}
.t b{display:block;font-size:13px;margin-bottom:2px;color:#99f6e4}.ic{font-size:20px}
button{border:0;border-radius:10px;padding:10px 16px;font-weight:700;cursor:pointer;background:#0d9488;color:#f8fafc;font-size:14px}
button:hover{background:#0f766e}
button:disabled{opacity:.5;cursor:default}
#big{font-size:44px;font-weight:800;color:#2dd4bf;line-height:1;margin-top:10px}
#big small{font-size:15px;font-weight:600;color:#94a3b8}
.bar{height:8px;background:#1e293b;border-radius:99px;overflow:hidden;margin:10px 0}
#pg{height:100%;width:0;background:linear-gradient(90deg,#14b8a6,#2dd4bf);transition:width .15s}
.st{display:flex;gap:18px;font-size:13px;margin-bottom:8px;color:#cbd5e1}
.st b{display:block;font-size:18px;color:#f8fafc}
input{width:100%;padding:8px 10px;border:1px solid #334155;background:#0f172a;color:#f1f5f9;border-radius:8px;font-size:13px;margin:6px 0}
.ok{color:#5eead4;font-size:12px;font-weight:600;margin-top:4px}
.n{font-size:11px;color:#94a3b8;line-height:1.4;margin-top:8px}
</style>
<div class="g">
 <div class="t"><span class="ic">📏</span><b>Distancia y altura</b>~1 m del pecho, a 1,2–1,5 m del suelo. No tapes el micrófono.</div>
 <div class="t"><span class="ic">🧍</span><b>Quieto y orientado</b>Mantén el equipo estable hacia la fuente sonora.</div>
 <div class="t"><span class="ic">🤫</span><b>Sin interferencias</b>Evita hablar o soplar encima del micrófono.</div>
</div>
<button id="go">🎙️ Medir durante 15 s</button>
<div id="big">-- <small>dB ref.</small></div>
<div class="bar"><div id="pg"></div></div>
<div class="st"><div>Mínimo<b id="mn">--</b></div><div>Promedio (Leq)<b id="lq">--</b></div><div>Pico<b id="mx">--</b></div></div>
<input id="res" readonly placeholder="Se llenará automáticamente al terminar los 15 s">
<div id="autoStatus" class="ok"></div>
<div class="n">Lectura referencial de tamizaje (sin ponderación A). Referencia ECA residencial (D.S. 085-2003-PCM): 60 dBA día / 50 dBA noche.</div>
<script>
const DUR=15, CAL=__CAL__;
const go=document.getElementById('go'), big=document.getElementById('big'), pg=document.getElementById('pg');
const mn=document.getElementById('mn'), lq=document.getElementById('lq'), mx=document.getElementById('mx');
const res=document.getElementById('res'), st=document.getElementById('autoStatus');

function rellenarCampoStreamlit(texto) {
  try {
    const doc = window.parent.document;
    const inputs = Array.from(doc.querySelectorAll('input[type="text"]'));
    const target = inputs.find(el => (el.placeholder || '').includes('Leq 68 dB ref'));
    if (target) {
      const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
      setter.call(target, texto);
      target.dispatchEvent(new Event('input', { bubbles: true }));
      target.dispatchEvent(new Event('change', { bubbles: true }));
      st.textContent = "✔ Registrado automáticamente en el campo de lectura sonora.";
      return true;
    }
  } catch (err) {}
  st.textContent = "ℹ Si el navegador bloquea el autocompletado entre marcos, selecciona y copia el texto de arriba.";
  return false;
}

go.onclick=async()=>{
  if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){
    res.value="Tu navegador no permite usar el micrófono aquí.";return;
  }
  let stream;
  try{
    stream=await navigator.mediaDevices.getUserMedia({
      audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}
    });
  }catch(e){
    res.value="No se pudo acceder al micrófono: "+e.message;return;
  }
  go.disabled=true; res.value="Midiendo…"; st.textContent="";
  const ctx=new (window.AudioContext||window.webkitAudioContext)();
  const src=ctx.createMediaStreamSource(stream), an=ctx.createAnalyser();
  an.fftSize=2048; src.connect(an);
  const buf=new Float32Array(an.fftSize), vals=[], t0=performance.now();
  const timer=setInterval(()=>{
    an.getFloatTimeDomainData(buf);
    let s=0; for(let i=0;i<buf.length;i++) s+=buf[i]*buf[i];
    const db=20*Math.log10(Math.sqrt(s/buf.length)||1e-8)+CAL;
    const el=performance.now()-t0;
    if(el>500) vals.push(db);
    big.innerHTML=Math.round(db)+' <small>dB ref.</small>';
    pg.style.width=Math.min(100,el/(DUR*10))+'%';
    if(el>=DUR*1000){
      clearInterval(timer); stream.getTracks().forEach(t=>t.stop()); ctx.close();
      const leq=10*Math.log10(vals.reduce((a,v)=>a+Math.pow(10,v/10),0)/Math.max(vals.length,1));
      const a=Math.min(...vals), b=Math.max(...vals);
      const resumen="Leq "+Math.round(leq)+" dB ref (mín "+Math.round(a)+" / pico "+Math.round(b)+") · 15 s · celular";
      big.innerHTML=Math.round(leq)+' <small>dB ref. (Leq)</small>';
      mn.textContent=Math.round(a); lq.textContent=Math.round(leq); mx.textContent=Math.round(b);
      res.value=resumen;
      rellenarCampoStreamlit(resumen);
      go.disabled=false; go.textContent="🔁 Repetir medición";
    }
  },125);
};
</script>
"""


def panel_sonometro() -> None:
    components.html(_HTML.replace("__CAL__", str(CAL_MIC_DB)), height=450)