from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from ...config import Config
from ...models import Item, ItemImage
from ...services.item_images import ImageService
from ...extensions import db

images_crud_bp = Blueprint('item_images', __name__)


@images_crud_bp.route('/<int:item_id>/images', methods=['POST'])
@jwt_required()
def upload_image(item_id):
    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    try:
        file = request.files['image']
        image = ImageService.save_image(file, item_id)  #creates but doesn't save to DB

        # Add to session and commit
        db.session.add(image)

        # Set primary if needed AFTER adding to session
        if not item.images.count():
            image.set_as_primary()

        db.session.commit()

        return jsonify(image.to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Upload failed"}), 500


@images_crud_bp.route('/<int:item_id>/images/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(item_id, image_id):
    image = ItemImage.query.get_or_404(image_id)

    if image.item.seller_id != current_user.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        ImageService.delete_image(image)
        db.session.commit()
        return jsonify({"message": "Image deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@images_crud_bp.route('/<int:item_id>/images/remote', methods=['POST'])
@jwt_required()
def upload_from_url(item_id):
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        filename = ImageService.download_from_url(data['url'])
        image = ItemImage(
            item_id=item_id,
            image_url=f"{Config.MEDIA_URL}{filename}",
            is_primary=False
        )
        db.session.add(image)
        db.session.commit()

        return jsonify({
            "success": True,
            "image": image.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500