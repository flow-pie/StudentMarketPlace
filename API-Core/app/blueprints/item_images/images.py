import os
from http import HTTPStatus

from flask import request, jsonify, current_app
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ...errors import APIError
from ...config import Config
from ...models import Item, ItemImage
from ...schemas.auth import MessageSchema
from ...schemas.item import ImageResponseSchema, ImageSchema
from ...services.item_images import ImageService
from ...extensions import db

images_crud_bp = Blueprint('Item Images', __name__, description="Upload/delete images for your items")

@images_crud_bp.route('/<int:item_id>/images', methods=['POST'])
@images_crud_bp.doc(
    description="Upload an image file for a specific item. Only the item's seller can upload.",
    tags=["Item Images"]
)
@images_crud_bp.arguments(ImageSchema, location="files")
@images_crud_bp.response(201, ImageResponseSchema)
@images_crud_bp.response(400, MessageSchema)
@images_crud_bp.response(403, MessageSchema)
@images_crud_bp.response(404, MessageSchema)
@jwt_required()
@images_crud_bp.doc(security=[{"BearerAuth": []}])
def upload_image(data, item_id):
    """
    Upload an image file for the given item.

    Path parameters:
    - item_id (int): ID of the item to attach the image to.

    Form-data:
    - image (file): The image file to upload.
    """
    item = Item.query.get(item_id)
    if not item:
        raise APIError(
            message="Item not found",
            code="ITEM_NOT_FOUND",
            status_code=404
        )

    if item.seller_id != current_user.user_id:
        raise APIError(
            message="Unauthorized: cannot upload image for this item",
            code="PERMISSION_DENIED",
            status_code=403
        )

    image_file = data["image"]
    if not image_file:
        raise APIError(
            message="No image file provided",
            code="NO_IMAGE_PROVIDED",
            status_code=400
        )

    filepath = None

    try:
        filepath = ImageService.save_image(image_file, item_id)

        is_primary = not bool(item.images)  # True if there are no existing image

        new_image = ItemImage(item_id=item.item_id, image_url=filepath, is_primary=is_primary)
        db.session.add(new_image)
        db.session.commit()
        return new_image.to_dict(), 201

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error saving image for item {item_id}: {e}")
        try:
            db.session.rollback()
        except SQLAlchemyError as rollback_err:
            current_app.logger.error(f"Error during rollback: {rollback_err}")

        if filepath:
            try:
                os.remove(filepath)
            except OSError as cleanup_err:
                current_app.logger.error(f"Failed to delete image file '{filepath}': {cleanup_err}")
        return {"error": "Failed to save image due to a database error"}, 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error uploading image for item {item_id}: {e}")
        if filepath:
            try:
                os.remove(filepath)
            except OSError as cleanup_err:
                current_app.logger.error(f"Failed to delete image file '{filepath}': {cleanup_err}")
        return {"error": "Image upload failed due to an internal error"}, 500


@images_crud_bp.route('/images/<int:image_id>', methods=['DELETE'])
@images_crud_bp.doc(
    description="Delete an image by its ID. Only the item's seller can delete.",
    tags=["Item Images"]
)
@images_crud_bp.response(200, MessageSchema)
@images_crud_bp.response(403, MessageSchema)
@images_crud_bp.response(404, MessageSchema)
@jwt_required()
@images_crud_bp.doc(security=[{"BearerAuth": []}])
def delete_image(image_id):
    """
    Delete an image by its ID.

    Path parameters:
    - image_id (int): ID of the image to delete.
    """
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
