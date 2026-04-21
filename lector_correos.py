import imaplib
import email
import os
import streamlit as st  # Necesario para leer los secretos
from email.header import decode_header

def conectar_y_descargar():
    # --- CAMBIO CLAVE: LEER DESDE STREAMLIT SECRETS ---
    # Asegúrate de agregar estas variables en el panel de Secrets de Streamlit
    try:
        usuario = st.secrets["correo"]["usuario"]
        password = st.secrets["correo"]["password"]
    except Exception:
        # Esto permite que el código siga funcionando en tu PC local si usas variables de entorno
        usuario = "pipepruebas.001@gmail.com"
        password = "dixn huig gncl mjre" 

    servidor_imap = "imap.gmail.com"

    # Crear carpeta de descargas si no existe
    if not os.path.exists('descargas'):
        os.makedirs('descargas')

    try:
        # Conexión al servidor
        mail = imaplib.IMAP4_SSL(servidor_imap)
        mail.login(usuario, password)
        mail.select("inbox")

        # Buscamos correos (puedes cambiar 'ALL' por 'UNSEEN' para solo los nuevos)
        status, mensajes = mail.search(None, 'ALL')
        ids_correos = mensajes[0].split()
        
        descargados = 0
        st.info(f"📬 Analizando {len(ids_correos)} correos en la bandeja...")

        for i in ids_correos:
            res, datos = mail.fetch(i, "(RFC822)")
            for respuesta in datos:
                if isinstance(respuesta, tuple):
                    msg = email.message_from_bytes(respuesta[1])
                    
                    for parte in msg.walk():
                        if parte.get_content_maintype() == 'multipart': continue
                        if parte.get('Content-Disposition') is None: continue

                        nombre_sucio = parte.get_filename()
                        if nombre_sucio:
                            # Decodificación de caracteres especiales (ñ, tildes)
                            decoded_parts = decode_header(nombre_sucio)
                            nombre_archivo = ""
                            for content, charset in decoded_parts:
                                if isinstance(content, bytes):
                                    nombre_archivo += content.decode(charset or 'utf-8', errors='ignore')
                                else:
                                    nombre_archivo += content
                            
                            # Limpieza de nombre para evitar errores de sistema
                            nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in "._- ")
                            
                            ruta_archivo = os.path.join('descargas', nombre_archivo)
                            
                            # Guardar el archivo
                            with open(ruta_archivo, "wb") as f:
                                f.write(parte.get_payload(decode=True))
                            
                            descargados += 1
                            st.write(f"📥 Archivo guardado: {nombre_archivo}")

        mail.close()
        mail.logout()
        return descargados # Devolvemos el número para mostrarlo en el Dashboard

    except Exception as e:
        st.error(f"❌ Error en la conexión de correo: {e}")
        return 0

if __name__ == "__main__":
    conectar_y_descargar()