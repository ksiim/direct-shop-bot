import asyncio

from models.databases import Session
from models.dbs.models import *

from sqlalchemy import insert, inspect, or_, select, text, update


class Orm:
    
    @staticmethod
    async def update_good_count(good_id, count):
        async with Session() as session:
            query = update(Good).where(Good.id == good_id).values(count=count)
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def delete_topic_by_id(topic_id):
        async with Session() as session:
            query = select(Topic).where(Topic.id == topic_id)
            topic = (await session.execute(query)).scalar_one_or_none()
            await session.delete(topic)
            await session.commit()
    
    @staticmethod
    async def get_all_topics():
        async with Session() as session:
            query = select(Topic)
            topics = (await session.execute(query)).scalars().all()
            return topics
    
    @staticmethod
    async def create_topic(name, thread_id):
        async with Session() as session:
            topic = Topic(
                name=name,
                thread_id=thread_id
            )
            session.add(topic)
            await session.commit()
            await session.refresh(topic)
            return topic
    
    @staticmethod
    async def get_admin():
        async with Session() as session:
            query = select(User).where(User.admin == True)
            admin = (await session.execute(query)).scalar_one_or_none()
            return admin
    
    @staticmethod
    async def get_order_by_id(order_id) -> Order:
        async with Session() as session:
            order = await session.get(Order, order_id)
            return order
    
    @staticmethod
    async def create_order(good_id, count, price, phone_number, name, pickup, discount_text, telegram_id, delivery_point_id=None) -> Order:
        async with Session() as session:
            order = Order(
                good_id=good_id,
                count=count,
                price=price,
                phone_number=phone_number,
                name=name,
                pickup=pickup,
                discount_text=discount_text,
                delivery_point_id=delivery_point_id,
                telegram_id=telegram_id
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order
    
    @staticmethod
    async def update_delivery_point_address(point_id, address):
        async with Session() as session:
            query = update(DeliveryPoint).where(DeliveryPoint.id == point_id).values(address=address)
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def get_all_goods():
        async with Session() as session:
            query = select(Good)
            goods = (await session.execute(query)).scalars().all()
            return goods
    
    @staticmethod
    async def clear_delivery_points(good_id):
        async with Session() as session:
            query = update(Good).where(Good.id == good_id).values(delivery_points_ids='[]')
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def clear_pickup_points(good_id):
        async with Session() as session:
            query = update(Good).where(Good.id == good_id).values(pickup_points_ids='[]')
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def update_good_message_id(good_id, message_id):
        async with Session() as session:
            query = update(Good).where(Good.id == good_id).values(message_id=message_id)
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def delete_delivery_point_by_id(point_id):
        async with Session() as session:
            query = select(DeliveryPoint).where(DeliveryPoint.id == point_id)
            point = (await session.execute(query)).scalar_one_or_none()
            await session.delete(point)
            await session.commit()
    
    @staticmethod
    async def create_delivery_point(address, phone_number, name):
        async with Session() as session:
            delivery_point = DeliveryPoint(
                address=address,
                phone_number=phone_number,
                name=name
            )
            session.add(delivery_point)
            await session.commit()
            await session.refresh(delivery_point)
            return delivery_point
    
    @staticmethod
    async def delete_good_by_id(good_id):
        async with Session() as session:
            query = select(Good).where(Good.id == good_id)
            good = (await session.execute(query)).scalar_one_or_none()
            await session.delete(good)
            await session.commit()
    
    @staticmethod
    async def get_good_by_name(name):
        async with Session() as session:
            query = select(Good).where(Good.name == name)
            good = (await session.execute(query)).scalar_one_or_none()
            return good
    
    @staticmethod
    async def get_delivery_point_by_id(point_id: int) -> DeliveryPoint:
        async with Session() as session:
            query = select(DeliveryPoint).where(DeliveryPoint.id == point_id)
            point = (await session.execute(query)).scalar_one_or_none()
            return point

    @staticmethod
    async def get_admin_telegram_ids():
        async with Session() as session:
            query = select(User.telegram_id).where(User.admin == True)
            admin_ids = (await session.execute(query)).scalars().all()
            return admin_ids

    @staticmethod
    async def get_delivery_points_by_ids(ids):
        async with Session() as session:
            query = select(DeliveryPoint).where(DeliveryPoint.id.in_(ids))
            delivery_points = (await session.execute(query)).scalars().all()
            return delivery_points


    @staticmethod
    async def get_all_delivery_points():
        async with Session() as session:
            query = select(DeliveryPoint)
            delivery_points = (await session.execute(query)).scalars().all()
            return delivery_points

    @staticmethod
    async def create_good(name, photo, price, description, count, discount, delivery_points_ids=[], pickup_points_ids=[]):
        async with Session() as session:
            good = Good(
                name=name,
                photo=photo,
                price=price,
                description=description,
                count=count,
                delivery_points_ids=json.dumps(delivery_points_ids),
                pickup_points_ids=json.dumps(pickup_points_ids),
                discount=discount
            )
            session.add(good)
            await session.commit()
            await session.refresh(good)
            return good

    @staticmethod
    async def get_good_by_id(good_id: int):
        async with Session() as session:
            query = select(Good).where(Good.id == good_id)
            good = (await session.execute(query)).scalar_one_or_none()
            return good

    @staticmethod
    async def create_user(message):
        if await Orm.get_user_by_telegram_id(message.from_user.id) is None:
            async with Session() as session:
                user = User(
                    full_name=message.from_user.full_name,
                    telegram_id=message.from_user.id,
                    username=message.from_user.username
                )
                session.add(user)
                await session.commit()

    @staticmethod
    async def get_user_by_telegram_id(telegram_id):
        async with Session() as session:
            query = select(User).where(User.telegram_id == telegram_id)
            user = (await session.execute(query)).scalar_one_or_none()
            return user

    @staticmethod
    async def get_all_users():
        async with Session() as session:
            query = select(User)
            users = (await session.execute(query)).scalars().all()
            return users
