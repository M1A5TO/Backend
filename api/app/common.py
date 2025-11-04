from PIL import Image
from loguru import logger
import os


logger.remove()
logger.add("logs/image_optimizer.log", 
           rotation="5 MB", 
           retention="7 days", 
           compression="zip",
           level="INFO",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")



def optimize_image_to_webp(image_path, width=1231, height=872, quality=80):
    """
    Optymalizuje obraz i zapisuje jako WebP:
    - przeskalowuje do width×height
    - usuwa metadane
    - ustawia jakość (default 80)
    - zapisuje z tą samą nazwą, ale rozszerzeniem .webp
    - jeśli zmieni rozszerzenie, usuwa oryginalny plik
    - zwraca ścieżkę do nowego pliku .webp
    """
    if not os.path.isfile(image_path):
        logger.error(f"Plik nie istnieje: {image_path}")
        return None

    try:
        with Image.open(image_path) as img:
            img_resized = img.resize((width, height), Image.LANCZOS)

            base, _ = os.path.splitext(image_path)
            output_path = base + ".webp"

            img_resized.save(output_path, "webp", quality=quality, method=6, lossless=False)

        # Usuń oryginał, jeśli miał inne rozszerzenie
        if image_path.lower() != output_path.lower():
            os.remove(image_path)
            logger.debug(f"Usunięto oryginalny plik: {image_path}")

        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"Zapisano: {output_path} ({size_kb:.2f} KB)")
        return output_path

    except Exception as e:
        logger.exception(f"Błąd podczas przetwarzania {image_path}: {e}")
        return None