import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Si cambias los permisos, elimina el archivo token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def obtener_servicio_drive():
    creds = None
    # El archivo token.json guarda los permisos de acceso del usuario.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas, deja que el usuario inicie sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guarda las credenciales para la próxima vez
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def buscar_y_descargar_por_cedula(cedula):
    service = obtener_servicio_drive()
    
    # MODIFICACIÓN: Ahora usa 'contains' en lugar de '=' para permitir nombres largos
    query = f"name contains '{cedula}' and mimeType = 'application/pdf' and trashed = false"
    
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            return None

        # Tomamos el primer archivo que coincida
        file_id = items[0]['id']
        file_name = items[0]['name']
        
        # Guardamos con un nombre temporal para procesar
        ruta_local = f"descargas/DRIVE_{cedula}.pdf"
        
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        with open(ruta_local, 'wb') as f:
            f.write(fh.getvalue())
            
        return ruta_local

    except Exception as e:
        print(f"❌ Error al conectar con Drive: {e}")
        return None