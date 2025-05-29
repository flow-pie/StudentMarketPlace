import os
import socket
import uuid
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse

import requests
from flask import current_app
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from werkzeug.utils import secure_filename

from .. import config
from ..config import Config
from ..extensions import db
from ..models import ItemImage


class ImageService:
    @staticmethod
    def generate_unique_filename(original_filename):
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4().hex}{ext}"

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @staticmethod
    def save_image(file, item_id):
        try:
            if not file or not ImageService.allowed_file(file.filename):
                raise ValueError("Invalid file type")

            unique_filename = ImageService.generate_unique_filename(file.filename)
            filepath = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                unique_filename
            )

            # Create image record first
            image = ItemImage(
                item_id=item_id,
                image_url=f"{current_app.config['MEDIA_URL']}{unique_filename}",
                is_primary=False
            )

            # Validate uniqueness before saving file
            if ItemImage.query.filter_by(image_url=image.image_url).first():
                raise ValueError("Image URL already exists")

            # Save file only after DB validation
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)

            return image
        except Exception as err:
            current_app.logger.error(f"Image save failed: {str(err)}")
            raise ValueError(f"Could not save image: {str(err)}") from err
    @staticmethod
    def delete_image(image):
        # Remove from filesystem
        filename = image.image_url.replace(Config.MEDIA_URL, "")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Remove from database
        db.session.delete(image)

    @staticmethod
    def get_full_path(image_url):
        relative_path = image_url.replace(current_app.config['MEDIA_URL'], '')
        return os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)

    # @staticmethod
    # def download_from_url(url):
    #     """Complete robust image download handler with:
    #     - DNS verification
    #     - Retry logic
    #     - Proper timeout handling
    #     - Image validation
    #     - Clean error reporting
    #     """
    #     try:
    #         #URL Validation ---
    #         parsed = urlparse(url)
    #         if not all([parsed.scheme, parsed.netloc]):
    #             raise ValueError("Invalid URL format")
    #
    #         domain = parsed.netloc
    #         if domain not in current_app.config['ALLOWED_IMAGE_DOMAINS']:
    #             raise ValueError(f"Downloads from {domain} are not allowed")
    #
    #         # Pre-Check ---
    #         try:
    #             socket.gethostbyname(domain)
    #         except socket.gaierror as e:
    #             raise ValueError(f"Cannot resolve domain '{domain}': {str(e)}")
    #
    #         # Retry
    #         retry_strategy = Retry(
    #             total=3,
    #             backoff_factor=1,
    #             status_forcelist=[500, 502, 503, 504],
    #             allowed_methods=["GET"]
    #         )
    #         adapter = HTTPAdapter(max_retries=retry_strategy)
    #         session = requests.Session()
    #         session.mount("https://", adapter)
    #         session.mount("http://", adapter)
    #
    #         # --- 4. Download Image ---
    #         response = session.get(
    #             url,
    #             stream=True,
    #             timeout=(10, 30),  # 10s connect, 30s read
    #             headers={
    #                 'User-Agent': 'Mozilla/5.0',
    #                 'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
    #             }
    #         )
    #         response.raise_for_status()
    #
    #         # Validate Content ---
    #         content_type = response.headers.get('content-type', '')
    #         if not content_type.startswith('image/'):
    #             raise ValueError("URL does not point to a valid image")
    #
    #         # Process File ---
    #         ext = content_type.split('/')[-1].lower()
    #         if ext not in current_app.config['ALLOWED_EXTENSIONS']:
    #             ext = 'jpg'  #fallback
    #
    #         filename = f"{uuid.uuid4().hex}.{ext}"
    #         filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    #
    #         #Stream Download ---
    #         try:
    #             with open(filepath, 'wb') as f:
    #                 for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
    #                     if chunk:  # Filter out keep-alive chunks
    #                         f.write(chunk)
    #
    #             with Image.open(filepath) as img:
    #                 img.verify()  # Verify without loading
    #
    #                 # Convert problematic modes
    #                 if img.mode in ('RGBA', 'P'):
    #                     img = img.convert('RGB')
    #
    #                 # Re-save in standard format
    #                 img.save(filepath, quality=95)
    #
    #             return filename
    #
    #         except Exception as img_error:
    #             # Clean up if image validation fails
    #             if os.path.exists(filepath):
    #                 os.remove(filepath)
    #             raise ValueError(f"Invalid image content: {str(img_error)}")
    #
    #     except requests.exceptions.SSLError:
    #         raise ValueError("SSL verification failed - potentially unsafe connection")
    #     except requests.exceptions.Timeout:
    #         raise ValueError("Connection timed out - server took too long to respond")
    #     except requests.exceptions.TooManyRedirects:
    #         raise ValueError("Too many redirects - URL might be broken")
    #     except requests.exceptions.RequestException as e:
    #         raise ValueError(f"Download failed: {str(e)}")
    #     except Exception as e:
    #         # Generic fallback
    #         raise ValueError(f"Image processing error: {str(e)}")
