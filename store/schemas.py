from ninja import Schema
from decimal import Decimal
from datetime  import datetime

class ProductSchema(Schema):
    id: int
    name: str
    description: str
    price: Decimal
    stock: int

class ProductCreateSchema(Schema):
    name: str
    description: str
    price: Decimal
    stock: int

class OrderItemSchema(Schema):
    product_id: int
    quantity: int

class OrderCreateSchema(Schema):
    items: list[OrderItemSchema]

class OrderSchema(Schema):
    id: int
    total: Decimal
    status: str
    created_at: datetime

class UserRegistrationSchema(Schema):
    username: str
    email: str
    password: str
    confirm_password: str

class LoginSchema(Schema):
    username: str
    password: str

class TokenSchema(Schema):
    access_token: str
    token_type: str = "bearer"

class MessageSchema(Schema):
    message: str
