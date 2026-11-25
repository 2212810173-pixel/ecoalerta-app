from __future__ import annotations

import time

import streamlit as st
from streamlit_folium import st_folium
from ecoalerta.drive_evidencias import subir_foto_drive
from ecoalerta import estado, evidencia, externos, geo, servicios
from ecoalerta.auth import es_staff
from ecoalerta.catalogos import AIRE, RUIDO, usa_aire, usa_ruido
from ecoalerta.config import (
    CONFIRM_HORAS, CONFIRM_RADIO_M, COOLDOWN_SEGUNDOS, DOM_INTEGRAL, DOMINIOS, EMOJI_NIVEL,
    MOMENTOS, NIVELES_EXPERIENCIA, PUNTOS_CONTROL, ROLES, TIPOS_REGISTRO, ahora,
)
from ecoalerta.scoring import evaluar
from ecoalerta.ui import components as ui
from ecoalerta.ui.captcha_widget import render_captcha
from ecoalerta.ui.maps import dentro_de_limites, mapa_registro
from ecoalerta.ui.sonometro import panel_sonometro

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

PUNTO_POR_CODIGO = {p["codigo"]: p for p in PUNTOS_CONTROL}
NINGUNO = "— Ninguno —"


def _aplicar_punto_control(n: int) -> None:
    p = PUNTO_POR_CODIGO.get(st.session_state.get(f"pc_{n}"))
    if p:
        estado.fijar_punto(p["lat"], p["lon"], precision=None, zoom=17)


def _sugerir_referencia(n: int) -> None:
    lat, lon = st.session_state.lat, st.session_state.lon
    if lat is None:
        st.toast("Primero marca un punto en el mapa.", icon="📍")
        return
    sug = externos.referencia_sugerida(lat, lon)
    if sug:
        st.session_state[f"ref_{n}"] = sug
    else:
        st.toast("No se pudo obtener una dirección; escríbela manualmente.", icon="ℹ️")


def _bloque(criterios, n: int, hint_viento: str | None) -> dict:
    resp = {}
    for c in criterios:
        resp[c.codigo] = st.selectbox(f"{c.codigo} · {c.etiqueta}", list(c.opciones), key=f"{c.codigo}_{n}")
        if c.codigo == "A4" and hint_viento:
            st.caption(hint_viento)
    return resp


def _formulario_criterios(dominio: str, n: int, hint_viento) -> dict:
    resp: dict = {}
    if dominio == DOM_INTEGRAL:
        t_aire, t_ruido = st.tabs(["💨 Calidad del Aire", "🔊 Ruido Ambiental"])
        with t_aire:
            resp.update(_bloque(AIRE, n, hint_viento))
        with t_ruido:
            resp.update(_bloque(RUIDO, n, None))
    else:
        criterios = AIRE if usa_aire(dominio) else RUIDO
        with st.container(border=True):
            st.markdown("**💨 Calidad del Aire**" if usa_aire(dominio) else "**🔊 Ruido Ambiental**")
            resp.update(_bloque(criterios, n, hint_viento if usa_aire(dominio) else None))
    return resp


def _lectura_sonora(n: int) -> str:
    with st.expander("🎙️ Medir ruido con el micrófono (opcional)"):
        panel_sonometro()
        lectura = st.text_input("Pega aquí el resultado", key=f"db_{n}", placeholder="Leq 68 dB ref (mín 55 / pico 80)…")
    return lectura.strip()


def _campos_tecnicos(dominio: str, n: int) -> list[str]:
    partes = []
    with st.expander("🔬 Campos técnicos (Monitor con experiencia)", expanded=True):
        c1, c2 = st.columns(2)
        if usa_aire(dominio):
            ring = c1.selectbox("Referencia Ringelmann",
                                ["No aplica", "N° 0 (<10%)", "N° 1 (~20%)", "N° 2 (~40%)",
                                 "N° 3 (~60%)", "N° 4 (~80%)", "N° 5 (100%)"], key=f"ring_{n}")
            viento = c2.text_input("Viento observado (velocidad / dirección)", key=f"vto_{n}",
                                   placeholder="Ej. Calma <2 km/h, NE")
            if ring != "No aplica":
                partes.append(f"Ringelmann:{ring}")
            if viento.strip():
                partes.append(f"Viento:{viento.strip()}")
        dist = c1.text_input("Distancia a la fuente (m)", key=f"dist_{n}", placeholder="Ej. 25")
        if dist.strip():
            partes.append(f"Dist_fuente:{dist.strip()} m")
    return partes


def _boton_gps() -> None:
    if streamlit_geolocation is None:
        return
    loc = streamlit_geolocation()
    if not loc or loc.get("latitude") is None:
        return
    clave = (round(loc["latitude"], 6), round(loc["longitude"], 6))
    if clave == st.session_state.gps_aplicado:
        return
    st.session_state.gps_aplicado = clave
    estado.fijar_punto(clave[0], clave[1], precision=loc.get("accuracy"), zoom=17)


def _bloque_cercanos(df, lat, lon) -> None:
    if lat is None or df.empty:
        return
    cer = geo.cercanos(df, lat, lon)
    if cer.empty:
        return
    with st.container(border=True):
        st.markdown(f"**🤝 Hay {len(cer)} alerta(s) activa(s) a menos de {CONFIRM_RADIO_M} m**")
        st.caption("Si es el mismo problema, confírmalo con un toque: varios reportes independientes "
                   "pesan más que uno aislado. Si es distinto, continúa con tu registro.")
        ahora_n = ahora().replace(tzinfo=None)
        for r in cer.head(3).itertuples():
            hace = (ahora_n - r.Fecha).total_seconds() / 3600
            hace_txt = f"{hace * 60:.0f} min" if hace < 1 else f"{hace:.0f} h"
            c1, c2 = st.columns([2.2, 1.3])
            c1.markdown(f"`{r.ID_Reporte}` · {r.Referencia_Lugar}  \n"
                        f"{EMOJI_NIVEL.get(r.Nivel_Riesgo, '')} {r.Nivel_Riesgo} · hace {hace_txt} · "
                        f"{r.Distancia_m:.0f} m · 👥 {int(r.Confirmaciones or 0)}")
            ya = r.ID_Reporte in st.session_state.confirmados
            if c2.button("✔ Confirmado" if ya else "👋 Yo también", key=f"conf_{r.ID_Reporte}",
                         disabled=ya, use_container_width=True):
                try:
                    servicios.confirmar(r.ID_Reporte)
                    st.session_state.confirmados.add(r.ID_Reporte)
                    st.toast("¡Gracias! Tu confirmación fortalece la alerta.", icon="🤝")
                except Exception as e:
                    st.error(f"No se pudo confirmar: {e}")


def _mostrar_ultimo_resultado() -> None:
    r = st.session_state.ultimo_resultado
    if not r:
        return
    ui.tarjeta_resultado(r["ticket"], r["res"], r["tipo"], r["dominio"])
    c1, c2 = st.columns([3, 1])
    c1.caption("Guarda tu código para consultar el seguimiento en la pestaña 🎫:")
    c1.code(r["ticket"], language=None)
    if r.get("foto"):
        c1.download_button("⬇️ Descargar evidencia sellada", r["foto"], f"{r['ticket']}.jpg", "image/jpeg")
    if c2.button("Cerrar resumen", use_container_width=True):
        st.session_state.ultimo_resultado = None
    st.divider()


def render(df) -> None:
    n = st.session_state.form_n
    staff = es_staff()
    _mostrar_ultimo_resultado()
    ui.como_funciona()

    lat, lon = st.session_state.lat, st.session_state.lon
    clima = externos.clima_actual(lat, lon) if lat is not None else None

    ui.paso(1, "¿Qué vas a registrar?", f"Hora de Lima: {ahora():%H:%M} · cobertura nacional Perú")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Finalidad")
            tipo = st.segmented_control("Finalidad", TIPOS_REGISTRO, default=TIPOS_REGISTRO[0],
                                        key=f"cfg_tipo_{n}", label_visibility="collapsed") or TIPOS_REGISTRO[0]
        with c2:
            st.caption("Dominio")
            dominio = st.segmented_control("Dominio", DOMINIOS, default=DOMINIOS[0],
                                           key=f"cfg_dom_{n}", label_visibility="collapsed") or DOMINIOS[0]
        c3, c4 = st.columns(2)
        with c3:
            st.caption("Nivel de detalle")
            experiencia = st.segmented_control("Nivel", NIVELES_EXPERIENCIA, default=NIVELES_EXPERIENCIA[0],
                                               key=f"cfg_exp_{n}", label_visibility="collapsed") or NIVELES_EXPERIENCIA[0]
        with c4:
            momento = st.selectbox("¿Cuándo lo observaste?", MOMENTOS, key=f"mom_{n}",
                                   help="Reportar en el momento mejora la precisión de la hora y la meteorología asociada.")
        es_monitoreo = tipo.startswith("Monitoreo")
        sin_emision = False
        if es_monitoreo:
            sin_emision = st.toggle("✅ Todo normal: no percibo emisión ni ruido molesto", key=f"sin_{n}",
                                    help="Registra una línea base limpia. Es tan útil como una alerta: permite comparar.")

    izq, der = st.columns([1.15, 0.85], gap="large")

    with izq:
        ui.paso(2, "Lugar y reportante")
        with st.container(border=True):
            referencia = st.text_input("Referencia del lugar *", key=f"ref_{n}",
                                       placeholder="Ej. Villa El Salvador / Av. Revolución / Plaza de Huanta")
            st.button("✨ Sugerir referencia con el punto marcado", on_click=_sugerir_referencia, args=(n,))
            a, b = st.columns(2)
            rol = a.selectbox("Rol", ROLES, key=f"rol_{n}")
            etiqueta_alias = "Nombre o alias del monitor *" if es_monitoreo else "Nombre o alias"
            alias = b.text_input(etiqueta_alias, key=f"alias_{n}", placeholder="Ej. André Cabezas / Monitor UNAH")

            if es_monitoreo:
                anonimo = False
                st.caption("🔒 En **Monitoreo / Línea Base** se requiere nombre o alias para trazabilidad.")
            else:
                anonimo = st.checkbox("Reportar de forma anónima (no se guardará mi alias)", key=f"anon_{n}")

            observaciones = st.text_area("Observación breve", key=f"obs_{n}", height=80, max_chars=300,
                                         placeholder="Describe brevemente lo que observas o mides...")
            punto_control = None
            if es_monitoreo or experiencia == NIVELES_EXPERIENCIA[1]:
                sel = st.selectbox(
                    "Punto de control de la ronda (opcional)", [NINGUNO, *PUNTO_POR_CODIGO], key=f"pc_{n}",
                    format_func=lambda c: c if c == NINGUNO else f"{c} · {PUNTO_POR_CODIGO[c]['nombre']}",
                    on_change=_aplicar_punto_control, args=(n,),
                    help="Al elegirlo, el mapa se ubica en el punto. Permite comparar el mismo sitio en el tiempo.")
                punto_control = None if sel == NINGUNO else sel

        ui.paso(3, "Observaciones del entorno", "Responde según lo que ves, hueles o escuchas")
        hint_viento = (externos.sugerencia_viento(clima)
                       if (clima and momento == MOMENTOS[0] and usa_aire(dominio)) else None)
        respuestas: dict = {}
        if sin_emision:
            st.success("Se registrará como **línea base limpia** (0 % de riesgo) en el punto que marques. "
                       "No necesitas responder las preguntas.", icon="✅")
        else:
            respuestas = _formulario_criterios(dominio, n, hint_viento)

        partes_tec: list[str] = []
        if usa_ruido(dominio):
            lectura = _lectura_sonora(n)
            if lectura:
                partes_tec.append(f"Ruido:{lectura}")
        if experiencia == NIVELES_EXPERIENCIA[1]:
            partes_tec += _campos_tecnicos(dominio, n)
        datos_tecnicos = " | ".join(partes_tec) if partes_tec else "Estándar ciudadano"

        foto = st.file_uploader("📷 Fotografía de evidencia (opcional · se comprime y se elimina su EXIF)",
                                type=["jpg", "jpeg", "png"], key=f"foto_{n}")
        if foto:
            st.image(foto, caption=foto.name, width=220)

    with der:
        ui.paso(4, "Ubicación", "Usa tu GPS, un punto de control o haz clic en el mapa")
        with st.container(border=True):
            _boton_gps()
            rec = geo.publicar(geo.recientes(df, CONFIRM_HORAS), staff)
            mapa, grupo = mapa_registro(st.session_state.lat, st.session_state.lon, rec, st.session_state.centro)
            datos = st_folium(
                mapa,
                feature_group_to_add=grupo,
                height=400,
                use_container_width=True,
                key=f"mapa_reg_{n}_{st.session_state.map_n}",
                returned_objects=["last_clicked"],
            )
            click = (datos or {}).get("last_clicked")
            if click and (click["lat"], click["lng"]) != (st.session_state.lat, st.session_state.lon):
                st.session_state.lat, st.session_state.lon = click["lat"], click["lng"]
                st.session_state.gps_precision = None

            lat, lon = st.session_state.lat, st.session_state.lon
            if lat is None:
                st.info("Aún no seleccionaste un punto.")
            elif dentro_de_limites(lat, lon):
                st.success(f"📍 `{lat:.6f}`, `{lon:.6f}`")
                ui.precision_gps(st.session_state.gps_precision)
                if clima and momento == MOMENTOS[0]:
                    st.caption(f"🌤 {externos.texto_clima(clima)}")
            else:
                st.warning("El punto está fuera del territorio peruano. Verifica la ubicación.")

        _bloque_cercanos(df, lat, lon)

        ui.paso(5, "Vista previa y envío", "El riesgo se actualiza mientras respondes")
        res_prev = evaluar(tipo, dominio, respuestas, sin_emision=sin_emision)
        ui.medidor(res_prev)

        with st.container(border=True):
            render_captcha(st.session_state.captcha_codigo)
            cap_txt = st.text_input(
                "Código de verificación",
                value="",
                max_chars=6,
                key=f"cap_{n}",
                placeholder="Ej. K7M4P",
            ).strip().upper()
            cap_ok = cap_txt == str(st.session_state.captcha_codigo).upper()
            alias_ok = (not es_monitoreo) or bool(alias.strip())
            ui.checklist([
                (lat is not None and dentro_de_limites(lat, lon), "Punto en Perú"),
                (bool(referencia.strip()), "Referencia del lugar"),
                (alias_ok, "Identificación del monitor" if es_monitoreo else "Reportante listo"),
                (cap_ok, "Verificación"),
            ])
            guardar = st.button("Guardar registro y generar ticket", type="primary", use_container_width=True)

    if not guardar:
        return

    errores = []
    if es_monitoreo and not alias.strip():
        errores.append("En Monitoreo / Línea Base debes ingresar tu nombre o alias.")
    if lat is None:
        errores.append("Marca un punto en el mapa.")
    elif not dentro_de_limites(lat, lon):
        errores.append("La ubicación está fuera del territorio peruano.")
    if not referencia.strip():
        errores.append("Ingresa una referencia del lugar.")
    if not cap_ok:
        errores.append("Ingresa el código de 5 caracteres que aparece en el recuadro de verificación.")
    espera = COOLDOWN_SEGUNDOS - (time.time() - st.session_state.ultimo_envio)
    if espera > 0:
        errores.append(f"Espera {int(espera) + 1} s antes de enviar otro registro.")
    if errores:
        for e in errores:
            st.error(e)
        return

    foto_bytes, evidencia_txt = None, "Sin foto"
    if foto:
        try:
            sello = f"{ahora():%Y-%m-%d %H:%M} · {lat:.5f}, {lon:.5f} · EcoAlerta UNAH"
            foto_bytes, evidencia_txt = evidencia.procesar(foto.getvalue(), sello)
        except Exception:
            evidencia_txt = f"{foto.name} (no se pudo procesar)"

    meteo = externos.texto_clima(clima) if (clima and momento == MOMENTOS[0]) else "No disponible"
    solicitud = servicios.SolicitudRegistro(
        tipo_registro=tipo, dominio=dominio, nivel_experiencia=experiencia, rol=rol, alias=alias,
        anonimo=anonimo, referencia=referencia, observaciones=observaciones, respuestas=respuestas,
        datos_tecnicos=datos_tecnicos, lat=lat, lon=lon, evidencia=evidencia_txt,
        sin_emision=sin_emision, momento=momento, punto_control=punto_control,
        precision_gps=st.session_state.gps_precision, meteo=meteo,
    )
    try:
        with st.spinner("Guardando registro..."):
            ticket, res = servicios.registrar(solicitud)
    except Exception as e:
        st.error(f"No se pudo guardar el registro (no se modificó ningún dato): {e}")
        return

    evidencia_final = evidencia_txt
    url_drive = ""
    if foto_bytes:
        try:
            url_drive = subir_foto_drive(ticket, foto_bytes)
            if url_drive:
                evidencia_final = f"{evidencia_txt} · Drive: {url_drive}"
        except Exception as e:
            st.toast(f"Ticket guardado, pero no se pudo subir la foto a Drive: {e}", icon="⚠️")

    st.session_state.ultimo_ticket = ticket
    st.session_state.ultimo_resultado = {
        "ticket": ticket,
        "res": res,
        "tipo": tipo,
        "dominio": dominio,
        "foto": foto_bytes,
        "evidencia": evidencia_final,
        "url_drive": url_drive,
    }
    st.session_state.ultimo_envio = time.time()
    estado.nuevo_formulario()
    st.success(f"Registro guardado con éxito. Ticket generado: {ticket}")
    st.session_state.ultimo_ticket = ticket
    st.session_state.ultimo_resultado = {
        "ticket": ticket, "res": res, "tipo": tipo, "dominio": dominio, "foto": foto_bytes
    }