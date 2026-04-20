import pytesseract
from pdf2image import convert_from_path
import mysql.connector
import os


pytesseract.pytesseract.tesseract_cmd = r"C:\Users\INVITAD\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def conectar_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="14272916",
        database="proyecto_ocr"
    )

def procesar_y_guardar_pdf(ruta_pdf):
    nombre_archivo = os.path.basename(ruta_pdf)
    print(f"Leyendo: {nombre_archivo}...")
    texto_extraido = ""

    # ✅ BUG #2 CORREGIDO: El bloque OCR ahora está dentro de try/except
    try:
        # 1. Convertir PDF a imágenes
        paginas = convert_from_path(
            ruta_pdf,
            300,
            poppler_path=r"D:\PROYECTO PERSONAL\POPPLER\poppler-25.12.0\Library\bin"
        )

        for pagina in paginas:
            # 2. IA de Reconocimiento de Caracteres
            texto_extraido += pytesseract.image_to_string(pagina, lang='spa')

    except Exception as e:
        print(f"❌ Error durante el OCR o conversión del PDF '{nombre_archivo}': {e}")
        # Retornamos cadena vacía para que main.py pueda manejarlo sin explotar
        return ""

    # 3. Guardar en la tabla 'extracciones'
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        sql = "INSERT INTO extracciones (nombre_archivo, contenido_texto) VALUES (%s, %s)"
        cursor.execute(sql, (nombre_archivo, texto_extraido))
        conn.commit()
        conn.close()
        print("✅ Texto guardado en MySQL con éxito.")
    except Exception as e:
        print(f"❌ Error al guardar en DB: {e}")

    # ✅ BUG #1 CORREGIDO: Ahora sí retornamos el texto para que main.py pueda usarlo
    return texto_extraido


# Prueba directa
if __name__ == "__main__":
    ruta_exacta = r"D:\PROYECTO PERSONAL\descargas\test.pdf.pdf"
    resultado = procesar_y_guardar_pdf(ruta_exacta)
    print(f"\n📄 Texto extraído ({len(resultado)} caracteres):")
    print(resultado[:500] if resultado else "[Sin texto]")
