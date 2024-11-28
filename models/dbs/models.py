import json
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.databases import Base

    
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    full_name: Mapped[str]
    username: Mapped[str] = mapped_column(nullable=True)
    admin: Mapped[bool] = mapped_column(default=False)
    
class Good(Base):
    __tablename__ = 'goods'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    photo: Mapped[str]
    price: Mapped[int]
    description: Mapped[str]
    count: Mapped[int]
    delivery_points_ids: Mapped[str] = mapped_column(nullable=True)
    pickup_points_ids: Mapped[str] = mapped_column(nullable=True)
    discount: Mapped[bool] = mapped_column(nullable=True)
    message_id: Mapped[int] = mapped_column(nullable=True)

    @property
    def delivery_points(self):
        return json.loads(self.delivery_points_ids) if self.delivery_points_ids else []

    @delivery_points.setter
    def delivery_points(self, value):
        self.delivery_points_ids = json.dumps(value)

    @property
    def pickup_points(self):
        return json.loads(self.pickup_points_ids) if self.pickup_points_ids else []

    @pickup_points.setter
    def pickup_points(self, value):
        self.pickup_points_ids = json.dumps(value)
    
    
class DeliveryPoint(Base):
    __tablename__ = 'delivery_points'

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str]
    phone_number: Mapped[str]
    name: Mapped[str]
    
class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    good_id: Mapped[int] = mapped_column(ForeignKey('goods.id'))
    count: Mapped[int]
    delivery_point_id: Mapped[int] = mapped_column(ForeignKey('delivery_points.id'), nullable=True)
    phone_number: Mapped[str]
    name: Mapped[str]
    pickup: Mapped[bool]
    discount_text: Mapped[str] = mapped_column(nullable=True)
    telegram_id: Mapped[int]
    price: Mapped[float]
    
class Topic(Base):
    __tablename__ = 'topics'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    thread_id: Mapped[int] = mapped_column(nullable=True)

    