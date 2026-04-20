import pytesseract
from PIL import Image
import PyPDF2
import io
import mysql.connector

# 1. CONFIGURACIÓN DE RUTAS
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\INVITAD\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def guardar_en_mysql(nombre, texto):
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="14272916", 
            database="proyecto_ocr"
        )
        cursor = conexion.cursor()
        sql = "INSERT INTO extracciones (nombre_archivo, contenido_texto) VALUES (%s, %s)"
        cursor.execute(sql, (nombre, texto))
        conexion.commit()
        print(f"✅ Datos de '{nombre}' guardados en MySQL.")
    except mysql.connector.Error as err:
        print(f"❌ Error de MySQL: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

def extraer_todo(ruta_archivo):
    texto_final = ""
    try:
        with open(ruta_archivo, 'rb') as archivo:
            lector = PyPDF2.PdfReader(archivo)
            for i, pagina in enumerate(lector.pages):
                # Extraer texto digital
                digital = pagina.extract_text()
                if digital: texto_final += digital + "\n"
                
                # Extraer texto de imágenes dentro del PDF
                if '/Resources' in pagina and '/XObject' in pagina['/Resources']:
                    xObject = pagina['/Resources']['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            data = xObject[obj].get_data()
                            img = Image.open(io.BytesIO(data))
                            texto_final += pytesseract.image_to_string(img, lang='spa') + "\n"
        return texto_final
    except Exception as e:
        return f"Error: {e}"

# --- EJECUCIÓN PRINCIPAL ---
nombre_del_pdf = r"C:\Users\INVITAD\Downloads\imagen de prueba.pdf"

print("Procesando archivo...")
resultado = extraer_todo(nombre_del_pdf)

if resultado.strip():
    guardar_en_mysql(nombre_del_pdf, resultado)
else:
    print("No se extrajo nada de texto.")

