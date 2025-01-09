from ninja import NinjaAPI
from .models import Product, Order, OrderItem
from typing import List
from .schemas import (
    ProductSchema,
    ProductCreateSchema,
    UserRegistrationSchema,
    TokenSchema,
    MessageSchema,
    LoginSchema,
    OrderCreateSchema,
    OrderSchema
)
from ninja.security import HttpBearer
import jwt
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from decimal import Decimal
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            user = User.objects.get(id=payload["user_id"])
            if user:
                request.user = user
            return user
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None


api = NinjaAPI(auth=[AuthBearer()], urls_namespace="api_v1")
auth_router = NinjaAPI(urls_namespace="api_v1_auth")


@auth_router.post("/auth/register", response={201: TokenSchema, 400: MessageSchema})
def register(request, payload: UserRegistrationSchema):
    if payload.password != payload.confirm_password:
        return 400, {"message": "Passwords do not match"}

    if User.objects.filter(username=payload.username).exists():
        return 400, {"message": "Username already exists"}

    if User.objects.filter(email=payload.email).exists():
        return 400, {"message": "Email already exists"}

    user = User.objects.create_user(
        username=payload.username, email=payload.email, password=payload.password
    )
    token = create_token(user)
    return 201, {"access_token": token}


@auth_router.post("auth/login", response={200: TokenSchema, 401: MessageSchema})
def login(request, payload: LoginSchema):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return 401, {"message": "Invalid credentials"}

    token = create_token(user)
    return 200, {"access_token": token}


def create_token(user):
    exp = datetime.now() + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS)
    payload = {"user_id": user.id, "exp": exp}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


@api.get("/products", response=List[ProductSchema])
@paginate
def list_products(request):
    return Product.objects.all()


@api.post("/products", response=ProductSchema)
def create_product(request, payload: ProductCreateSchema):
    product = Product.objects.create(**payload.dict())
    return product

@api.post("/orders", response=OrderSchema)
def create_order(request, payload: OrderCreateSchema):
    total = Decimal(0)
    order_items = []

    for item in payload.items:
        product = get_object_or_404(Product, id=item.product_id)
        if product.stock < item.quantity:
            return api.create_response(
                request,
                {"error": f"Insufficient stock for {product.name}"},
                status=400
            )
        total += product.price * item.quantity
        order_items.append((product, item.quantity))
    
    order = Order.objects.create(user=request.user, total=total)

    for product, quantity in order_items:
        OrderItem.objects.create(order=order, product=product, price=product.price)
        product.stock -= quantity
        product.save()
    
    return order

@api.get("/orders", response=List[OrderSchema])
@paginate
def list_orders(request):
    return Order.objects.filter(user=request.user)