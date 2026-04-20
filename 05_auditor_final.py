import mysql.connector
import re

def conectar_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="14272916", 
        database="proyecto_ocr"
    )

def normalizar_texto(texto):
    """Limpia el texto para facilitar la comparación"""
    if not texto: return ""
    # Convertir a minúsculas
    texto = texto.lower()
    # Quitar saltos de línea y tabulaciones por espacios
    texto = re.sub(r'[\n\t\r]', ' ', texto)
    # Quitar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def auditar_avanzado():
    conn = conectar_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM registros_maestros WHERE estado = 'pendiente'")
    maestros = cursor.fetchall()

    cursor.execute("SELECT * FROM extracciones")
    extracciones = cursor.fetchall()

    print(f"--- Iniciando Auditoría de Frases/Párrafos ---")

    for m in maestros:
        match_encontrado = False
        # El bloque de texto que quieres buscar (puede ser una frase completa)
        bloque_esperado = normalizar_texto(m['referencia']) 

        for e in extracciones:
            texto_pdf = normalizar_texto(e['contenido_texto'])
            
            # Buscamos la frase completa dentro del texto del PDF
            if bloque_esperado in texto_pdf:
                print(f"✅ ¡COINCIDENCIA TOTAL! Se encontró el bloque: '{bloque_esperado[:30]}...'")
                
                cursor.execute(
                    "UPDATE registros_maestros SET estado = 'procesado' WHERE id = %s", 
                    (m['id'],)
                )
                match_encontrado = True
                break
        
        if not match_encontrado:
            print(f"❌ NO SE ENCONTRÓ: '{bloque_esperado[:30]}...'")

    conn.commit()
    conn.close()
    print("--- Auditoría Finalizada ---")

if __name__ == "__main__":
    auditar_avanzado()