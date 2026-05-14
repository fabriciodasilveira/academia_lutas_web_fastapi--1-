# src/image_utils.py
from PIL import Image, ImageOps # <--- ADICIONEI ImageOps
import io
import os
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
import uuid

# Configurações do Cloudflare R2 (certifique-se de ter essas variáveis no seu .env)
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
# URL pública do bucket ou do custom domain
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-seu-hash.r2.dev") 

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto" # R2 não usa região, mas boto3 exige
    )

def process_avatar_image(file_stream, max_size=(800, 800), quality=70):
    """
    Redimensiona e comprime, CORRIGINDO A ROTAÇÃO (EXIF).
    """
    try:
        img = Image.open(file_stream)

        # --- CORREÇÃO DE ROTAÇÃO (O PULO DO GATO) ---
        # Verifica a orientação EXIF e aplica a rotação física na imagem
        img = ImageOps.exif_transpose(img)
        # ---------------------------------------------
        
        if img.mode in ('P', 'RGBA'):
            img = img.convert('RGB')
            
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        img_byte_arr.seek(0)
        
        return img_byte_arr, 'image/jpeg'
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        return None, None

def salvar_imagem_cloudflare(file_bytes, filename, content_type='image/jpeg'):
    """
    Envia os bytes da imagem para o Cloudflare R2 e retorna a URL pública.
    """
    s3 = get_s3_client()
    
    # Gera um nome único para evitar sobrescrita
    ext = filename.split('.')[-1]
    novo_nome = f"financeiro/{datetime.now().strftime('%Y%m')}/{uuid.uuid4()}.{ext}"

    try:
        s3.upload_fileobj(
            file_bytes,
            R2_BUCKET_NAME,
            novo_nome,
            ExtraArgs={'ContentType': content_type}
        )
        # Retorna a URL completa
        return f"{R2_PUBLIC_URL}/{novo_nome}"
    except Exception as e:
        print(f"Erro no upload para Cloudflare: {e}")
        return None