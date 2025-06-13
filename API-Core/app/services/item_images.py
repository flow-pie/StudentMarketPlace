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
    def generate_unique_filename(filename):
        """Generates a safe, unique filename."""
        safe_name = secure_filename(filename)  # Sanitize
        return f"{uuid.uuid4().hex}_{safe_name}"

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

            # Prevent path traversal
            filepath = os.path.abspath(filepath)
            upload_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
            if not filepath.startswith(upload_dir):
                raise ValueError("Invalid file path (directory traversal detected)")

            image = ItemImage(
                item_id=item_id,
                image_url=f"{current_app.config['MEDIA_URL']}{unique_filename}",
                is_primary=False
            )

            if ItemImage.query.filter_by(image_url=image.image_url).first():
                raise ValueError("Image URL already exists")

            os.makedirs(upload_dir, exist_ok=True)
            file.save(filepath)
            return f"{current_app.config['MEDIA_URL']}{unique_filename}"

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
