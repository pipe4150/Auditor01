import os
import re
import time
from lector_correos import conectar_y_descargar
from procesador_ia import procesar_y_guardar_pdf
from lector_drive import buscar_y_descargar_por_cedula

def ejecutar_auditoria_final():
    print("\n" + "="*60)
    print("🚀 INICIANDO AUDITORÍA MASIVA DE DOCUMENTOS")
    print("="*60)
    
    # 1. Intentar descargar todo lo nuevo
    conectar_y_descargar()
    
    # 2. Leer la carpeta de descargas
    if not os.path.exists('descargas'):
        print("📁 La carpeta de descargas no existe.")
        return

    archivos_locales = [f for f in os.listdir('descargas') 
                        if f.endswith('.pdf') and not f.startswith('DRIVE_')]
    
    total = len(archivos_locales)
    print(f"\n📋 TOTAL DE ARCHIVOS ENCONTRADOS: {total}")
    print("-" * 60)

    exitos = 0
    alertas = 0

    # 3. BUCLE PRINCIPAL DE PROCESAMIENTO
    for indice, nombre_archivo in enumerate(archivos_locales, 1):
        print(f"\n({indice}/{total}) 🔍 Procesando: {nombre_archivo}")
        ruta_pdf = os.path.join('descargas', nombre_archivo)
        
        # IA extrae texto del PDF del correo
        texto_correo = procesar_y_guardar_pdf(ruta_pdf) or ""
        
        # Regex para capturar la cédula
        match = re.search(r'(\d[\d\.]{6,12}\d)', texto_correo)
        
        if match:
            cedula = match.group(0).replace(".", "").replace(" ", "")
            print(f"   📌 Cédula detectada: {cedula}")
            
            # Buscar el archivo espejo en Drive
            ruta_drive = buscar_y_descargar_por_cedula(cedula)
            
            if ruta_drive:
                # IA extrae texto del PDF de Drive
                texto_drive = procesar_y_guardar_pdf(ruta_drive) or ""
                
                # Comparación de integridad
                if cedula in texto_drive.replace(".", ""):
                    print(f"   ✅ [VALIDADO] Coincide con respaldo en Drive.")
                    exitos += 1
                else:
                    print(f"   ⚠️ [ALERTA] La cédula no aparece dentro del PDF de Drive.")
                    alertas += 1
            else:
                print(f"   ❌ [ERROR] No existe archivo para {cedula} en Google Drive.")
                alertas += 1
        else:
            print(f"   ❓ [S/N] No se pudo leer un número de cédula en este archivo.")
            alertas += 1

        # Pausa de cortesía para las APIs
        time.sleep(0.5)

    # 4. Resumen Estadístico
    print("\n" + "="*60)
    print("📊 RESUMEN DE LA OPERACIÓN:")
    print(f"   ✔️ Documentos Validados: {exitos}")
    print(f"   🚩 Documentos con Alerta: {alertas}")
    print("="*60 + "\n")

if __name__ == "__main__":
    ejecutar_auditoria_final()