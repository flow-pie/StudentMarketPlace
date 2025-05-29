import os
from http import HTTPStatus

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ...errors import APIError
from ...config import Config
from ...models import Item, ItemImage
from ...services.item_images import ImageService
from ...extensions import db

images_crud_bp = Blueprint('item_images', __name__)


@images_crud_bp.route('/<int:item_id>/images', methods=['POST'])
@jwt_required()
def upload_image(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            raise APIError("Item not found", "ITEM_NOT_FOUND", HTTPStatus.NOT_FOUND.value)

        if item.seller_id != current_user.user_id:
            raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)

        if 'image' not in request.files:
            raise APIError("No image provided", "MISSING_IMAGE", HTTPStatus.BAD_REQUEST.value)

        file = request.files['image']
        image = ImageService.save_image(file, item_id)
        filepath = ImageService.get_full_path(image.image_url)

        db.session.add(image)

        if not item.images.count():
            with db.session.begin_nested():
                item.images.update({'is_primary': False})
                image.is_primary = True

        db.session.commit()

        return image.to_dict(), HTTPStatus.CREATED.value

    except ValueError:
        db.session.rollback()
        raise APIError(
            message="Invalid image file",
            code="INVALID_IMAGE",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except IntegrityError as err:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        db.session.rollback()
        if "unique constraint" in str(err).lower():
            raise APIError(
                message="Image URL conflict",
                code="IMAGE_CONFLICT",
                status_code=HTTPStatus.CONFLICT
            )
        raise APIError(
            message="Database integrity error",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )
    except SQLAlchemyError as err:
        db.session.rollback()
        current_app.logger.error(f"Database error uploading image: {str(err)}")
        raise APIError(
            message="Failed to save image",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
    except Exception as err:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        item = Item.query.get(item_id)
        db.session.rollback()
        current_app.logger.error(f"Unexpected error uploading image: {str(err)}")
        if item.seller_id != current_user.user_id:
            raise APIError("Sorry you dont have permission to edit item you dont own", "PERMISSION_DENIED",
                           HTTPStatus.FORBIDDEN.value)
        elif not item:
            raise APIError("Item not found", "ITEM_NOT_FOUND", HTTPStatus.NOT_FOUND.value)
        else:
            raise APIError(
                message="Image upload failed",
                code="UPLOAD_FAILED",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
            )


@images_crud_bp.route('/images/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    try:
        image = ItemImage.query.get_or_404(image_id)

        if not image:
            raise APIError("Image not found", "IMAGE_NOT_FOUND", HTTPStatus.NOT_FOUND.value)

        if image.item.seller_id != current_user.user_id:
            raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)

        ImageService.delete_image(image)
        db.session.commit()

        return {"message": "Image deleted successfully"}, HTTPStatus.OK.value


    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Error deleting image {image_id}: {str(err)}")
        if image.item.seller_id != current_user.user_id:
            raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)
        raise APIError(
            message="Failed to delete image",
            code="DELETE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value

        )

# @images_crud_bp.route('/<int:item_id>/images/remote', methods=['POST'])
# @jwt_required()
# def upload_from_url(item_id):
#     try:
#         data = request.get_json()
#         if not data or 'url' not in data:
#             raise APIError("URL parameter is required", "MISSING_URL", HTTPStatus.BAD_REQUEST.value)
#
#         item = Item.query.get(item_id)
#         if not item:
#             raise APIError("Item not found", "ITEM_NOT_FOUND", HTTPStatus.NOT_FOUND.value)
#
#         if item.seller_id != current_user.user_id:
#             raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)
#
#         filename = ImageService.download_from_url(data['url'])
#         image = ItemImage(
#             item_id=item_id,
#             image_url=f"{Config.MEDIA_URL}{filename}",
#             is_primary=False
#         )
#         db.session.add(image)
#         db.session.commit()
#
#         return {
#             "success": True,
#             "image": image.to_dict()
#         }, HTTPStatus.CREATED.value
#
#
#     except ValueError as err:
#         raise APIError(
#             message="Invalid image URL",
#             code="INVALID_URL",
#             status_code=HTTPStatus.BAD_REQUEST.value
#         )
#     except Exception as err:
#         db.session.rollback()
#         current_app.logger.error(f"Error uploading from URL: {str(err)}")
#         raise APIError(
#             message="Failed to upload image from URL",
#             code="REMOTE_UPLOAD_FAILED",
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
#         )
