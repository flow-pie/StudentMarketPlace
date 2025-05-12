from flask_bcrypt import generate_password_hash
from marshmallow import Schema, fields, validate, validates, ValidationError
from sqlalchemy.testing.pickleable import User


class RegistrationSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = fields.Email(required=True, validate=validate.Email())
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*',
                            error="Password must contain uppercase, lowercase, and numbers")
        ],
        load_only=True
    )
    institution = fields.Str()
    student_id = fields.Str()

    @validates('email')
    def validate_email(self, email):
        if User.query.filter_by(email=email).first():
            raise ValidationError('Email already registered.')

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True
    )