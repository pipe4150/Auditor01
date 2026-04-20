import streamlit as st
import os
import re
import pandas as pd
import json
from dotenv import load_dotenv
from lector_correos import conectar_y_descargar
from procesador_ia import procesar_y_guardar_pdf
from lector_drive import buscar_y_descargar_por_cedula

# ✅ Carga las variables del archivo .env (que NO está en GitHub)
load_dotenv()

# --- CREDENCIALES DESDE VARIABLES DE ENTORNO ---
TWILIO_SID    = os.getenv("TWILIO_SID")
TWILIO_TOKEN  = os.getenv("TWILIO_TOKEN")
NUMERO_TWILIO = os.getenv("NUMERO_TWILIO")
TU_NUMERO     = os.getenv("TU_NUMERO")

# --- FUNCIÓN DE BASE DE DATOS LOCAL ---
def gestionar_historico(exitos=0, fallos=0, modo="lectura"):
    archivo = "historico_auditoria.json"
    if not os.path.exists(archivo):
        with open(archivo, "w") as f:
            json.dump({"exitos": 0, "fallos": 0}, f)
    with open(archivo, "r") as f:
        datos = json.load(f)
    if modo == "escritura":
        datos["exitos"] += exitos
        datos["fallos"]  += fallos
        with open(archivo, "w") as f:
            json.dump(datos, f)
    return datos

# --- INTERFAZ VISUAL ---
st.set_page_config(page_title="Mi Auditor Asistente", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 ¡Hola! Soy tu Asistente de Auditoría")
st.markdown("---")

# --- BLOQUE 1: RESUMEN HISTÓRICO ---
datos_historicos = gestionar_historico()
st.subheader("📊 Mi Trabajo Acumulado (Histórico)")
col_hist1, col_hist2, col_hist3 = st.columns(3)

with col_hist1:
    st.metric("✅ Total Éxitos", datos_historicos["exitos"], delta_color="normal")
with col_hist2:
    st.metric("🚩 Total Alertas", datos_historicos["fallos"], delta_color="inverse")
with col_hist3:
    total_vida = datos_historicos["exitos"] + datos_historicos["fallos"]
    st.metric("📦 Documentos Procesados", total_vida)

st.markdown("---")

# --- BLOQUE 2: ACCIÓN DEL DÍA ---
st.subheader("📂 Control del Día de Hoy")
col_btn, col_info = st.columns([1, 3])

with col_btn:
    if st.button("🚀 EMPEZAR A REVISAR AHORA", use_container_width=True):
        if not os.path.exists('descargas'):
            os.makedirs('descargas')
        for f in os.listdir('descargas'):
            os.remove(os.path.join('descargas', f))

        with st.status("🔍 Buscando correos nuevos... un momento", expanded=True) as s:
            conectar_y_descargar()
            s.update(label="¡Listo! Encontré archivos nuevos.", state="complete")

        archivos = [f for f in os.listdir('descargas')
                    if f.endswith('.pdf') and not f.startswith('DRIVE_')]

        if len(archivos) == 0:
            st.warning("No hay nada nuevo por revisar hoy. ¡Tómate un café! ☕")
        else:
            progreso = st.progress(0)
            status_dinamico = st.empty()
            col_tabla, col_grafico = st.columns([2, 1])

            resultados_lista = []
            texto_whatsapp = ""
            c_exitos_hoy = 0
            c_fallos_hoy = 0

            for i, nombre in enumerate(archivos, 1):
                status_dinamico.info(f"Analizando documento {i} de {len(archivos)}...")
                ruta = os.path.join('descargas', nombre)

                texto_correo = procesar_y_guardar_pdf(ruta) or ""
                match = re.search(r'(\d[\d\.]{6,12}\d)', texto_correo)

                cedula  = match.group(0).replace(".", "").replace(" ", "") if match else "N/A"
                emoji   = "❓"
                veredicto = "No se leyó cédula"

                if cedula != "N/A":
                    ruta_drive = buscar_y_descargar_por_cedula(cedula)
                    if ruta_drive:
                        texto_drive = procesar_y_guardar_pdf(ruta_drive) or ""
                        if cedula in texto_drive.replace(".", ""):
                            veredicto = "✅ TODO PERFECTO"
                            emoji = "✅"
                            c_exitos_hoy += 1
                        else:
                            veredicto = "⚠️ DATOS NO COINCIDEN"
                            emoji = "⚠️"
                            c_fallos_hoy += 1
                    else:
                        veredicto = "🚫 NO ESTÁ EN DRIVE"
                        emoji = "🚫"
                        c_fallos_hoy += 1
                else:
                    c_fallos_hoy += 1

                resultados_lista.insert(0, {"Estatus": emoji, "Documento": nombre, "Resultado": veredicto})
                texto_whatsapp += f"{emoji} {nombre}: {veredicto}\n"

                progreso.progress(i / len(archivos))
                with col_tabla:
                    st.dataframe(pd.DataFrame(resultados_lista), use_container_width=True)
                with col_grafico:
                    st.write("Avance de hoy:")
                    df_graf = pd.DataFrame({"Tipo": ["Éxitos", "Alertas"], "Cant": [c_exitos_hoy, c_fallos_hoy]})
                    st.bar_chart(df_graf.set_index("Tipo"))

            # --- FINALIZACIÓN ---
            gestionar_historico(c_exitos_hoy, c_fallos_hoy, modo="escritura")
            st.balloons()
            st.success(f"¡Terminé! Revisé {len(archivos)} documentos.")

            # WhatsApp
            if TWILIO_SID and TWILIO_TOKEN:
                from twilio.rest import Client
                client = Client(TWILIO_SID, TWILIO_TOKEN)
                resumen = (f"🤖 *REPORTE DE AUDITORÍA*\n"
                           f"Hoy revisé {len(archivos)} archivos.\n"
                           f"✅ Bien: {c_exitos_hoy}\n"
                           f"🚩 Mal: {c_fallos_hoy}\n\n"
                           f"¡Ya puedes descansar! ❤️")
                client.messages.create(body=resumen, from_=NUMERO_TWILIO, to=TU_NUMERO)
                st.info("📲 Te envié un resumen por WhatsApp.")
            else:
                st.warning("⚠️ Twilio no configurado en .env — el WhatsApp no se envió.")

            if st.button("Ver histórico actualizado"):
                st.rerun()

with col_info:
    st.write("💡 **Instrucciones:**")
    st.write("1. Dale clic al botón azul de la izquierda.")
    st.write("2. Espera a que los globitos salgan en pantalla.")
    st.write("3. ¡Listo! El reporte llegará a tu celular automáticamente.")
