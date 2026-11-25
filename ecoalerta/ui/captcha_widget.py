import streamlit.components.v1 as components

_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; font-family: Inter, system-ui, sans-serif; color: #e2e8f0; background: transparent; }
  .box { border: 1px solid rgba(45,212,191,.25); border-radius: 12px; padding: 10px 12px; background: #162232; }
  canvas { border-radius: 8px; border: 1px solid #334155; background: #0f172a; display: block; }
  .hint { font-size: 12px; color: #94a3b8; margin-top: 6px; }
</style>
</head>
<body>
<div class="box">
  <canvas id="capCanvas" width="190" height="44"></canvas>
  <div class="hint">Escribe los 5 caracteres del recuadro en el campo inferior.</div>
</div>
<script>
const code = "__CODE__";
const canvas = document.getElementById("capCanvas");
const ctx = canvas.getContext("2d");

for (let i = 0; i < 6; i++) {
  ctx.strokeStyle = i % 2 === 0 ? "rgba(45,212,191,0.35)" : "rgba(148,163,184,0.30)";
  ctx.beginPath();
  ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
  ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
  ctx.stroke();
}

for (let i = 0; i < code.length; i++) {
  ctx.save();
  ctx.translate(24 + i * 31, 29 + (Math.random() * 4 - 2));
  ctx.rotate((Math.random() * 0.32 - 0.16));
  ctx.font = "800 22px monospace";
  ctx.fillStyle = i % 2 === 0 ? "#f8fafc" : "#2dd4bf";
  ctx.fillText(code[i], 0, 0);
  ctx.restore();
}
</script>
</body>
</html>
"""


def render_captcha(codigo: str) -> None:
    components.html(_HTML.replace("__CODE__", codigo), height=88)