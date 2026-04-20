import imaplib
import email
import os
from email.header import decode_header

def conectar_y_descargar():
    usuario = "pipepruebas.001@gmail.com"
    password = "dixn huig gncl mjre" 
    servidor_imap = "imap.gmail.com"

    if not os.path.exists('descargas'):
        os.makedirs('descargas')

    try:
        mail = imaplib.IMAP4_SSL(servidor_imap)
        mail.login(usuario, password)
        mail.select("inbox")

        # Buscamos todos los correos en la bandeja
        status, mensajes = mail.search(None, 'ALL')
        ids_correos = mensajes[0].split()
        
        descargados = 0
        print(f"📬 Analizando {len(ids_correos)} correos...")

        for i in ids_correos:
            res, datos = mail.fetch(i, "(RFC822)")
            for respuesta in datos:
                if isinstance(respuesta, tuple):
                    # Forzamos la lectura en UTF-8 para evitar errores de caracteres
                    msg = email.message_from_bytes(respuesta[1])
                    
                    for parte in msg.walk():
                        if parte.get_content_maintype() == 'multipart': continue
                        if parte.get('Content-Disposition') is None: continue

                        nombre_sucio = parte.get_filename()
                        if nombre_sucio:
                            # --- SOLUCIÓN AL ERROR DE CARACTERES (\xf1 / ñ) ---
                            decoded_parts = decode_header(nombre_sucio)
                            nombre_archivo = ""
                            for content, charset in decoded_parts:
                                if isinstance(content, bytes):
                                    nombre_archivo += content.decode(charset or 'utf-8', errors='ignore')
                                else:
                                    nombre_archivo += content
                            
                            # Limpieza final para Windows
                            nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in "._- ")
                            
                            print(f"📥 Descargando: {nombre_archivo}")
                            ruta_archivo = os.path.join('descargas', nombre_archivo)
                            
                            with open(ruta_archivo, "wb") as f:
                                f.write(parte.get_payload(decode=True))
                            descargados += 1

        mail.close()
        mail.logout()
        print(f"✅ EXITO: Se bajaron {descargados} archivos.")

    except Exception as e:
        print(f"❌ Error en el proceso de correo: {e}")

if __name__ == "__main__":
    conectar_y_descargar()