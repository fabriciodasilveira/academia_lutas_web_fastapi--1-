from PIL import Image
import io

def process_avatar_image(file_stream, max_size=(500, 500), quality=85):
    """
    Redimensiona e comprime uma imagem para ser usada como avatar.

    :param file_stream: O stream de bytes do arquivo de imagem.
    :param max_size: Uma tupla (width, height) com o tamanho máximo.
    :param quality: A qualidade da compressão JPEG (0-100).
    :return: Um objeto BytesIO com a imagem processada e seu content type.
    """
    try:
        # Abre a imagem usando a biblioteca Pillow
        img = Image.open(file_stream)

        # Converte imagens com paletas (como alguns GIFs) ou com canal alfa (PNG) para RGB
        if img.mode in ('P', 'RGBA'):
            img = img.convert('RGB')

        # Mantém a proporção da imagem, redimensionando para o tamanho máximo
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Salva a imagem otimizada em um buffer de memória
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        
        # Move o "cursor" de volta para o início do buffer para que o boto3 possa lê-lo
        img_byte_arr.seek(0)

        return img_byte_arr, 'image/jpeg'

    except Exception as e:
        # Se ocorrer um erro (ex: arquivo não é uma imagem), retorna None
        print(f"Erro ao processar imagem: {e}")
        return None, None