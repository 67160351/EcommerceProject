from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False); password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True); name = Column(String, unique=True, nullable=False)
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True); category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String, nullable=False); description = Column(String, default="")
    price = Column(Float, nullable=False); stock = Column(Integer, default=0)
    rating = Column(Float, default=4.0); popularity = Column(Float, default=0.5); active = Column(Boolean, default=True)
    category = relationship("Category")
class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    id = Column(Integer, primary_key=True); product_id = Column(Integer, ForeignKey("products.id"))
    key = Column(String); value = Column(String)
class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True); name = Column(String, unique=True); description = Column(String, default="")
class GoalRequirement(Base):
    __tablename__ = "goal_requirements"
    id = Column(Integer, primary_key=True); goal_id = Column(Integer, ForeignKey("goals.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    priority = Column(String)  # essential | recommended | optional
    reason = Column(String, default="")
class Bundle(Base):
    __tablename__ = "bundles"
    id = Column(Integer, primary_key=True); user_id = Column(Integer, ForeignKey("users.id"))
    goal_id = Column(Integer, ForeignKey("goals.id")); budget = Column(Float); total = Column(Float, default=0)
    items = relationship("BundleItem", cascade="all, delete-orphan")
class BundleItem(Base):
    __tablename__ = "bundle_items"
    id = Column(Integer, primary_key=True); bundle_id = Column(Integer, ForeignKey("bundles.id"))
    product_id = Column(Integer, ForeignKey("products.id")); role = Column(String); reason = Column(String, default="")
    product = relationship("Product")
class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True); user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True); budget = Column(Float, nullable=True)  # Cart Doctor context
    goal = relationship("Goal")
    items = relationship("CartItem", cascade="all, delete-orphan")
class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True); cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(Integer, ForeignKey("products.id")); quantity = Column(Integer, default=1)
    product = relationship("Product")
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True); user_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float); status = Column(String, default="confirmed"); address = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
    items = relationship("OrderItem", cascade="all, delete-orphan")
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True); order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id")); quantity = Column(Integer); price = Column(Float)  # price at purchase
    product = relationship("Product")
