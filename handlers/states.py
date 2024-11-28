from aiogram.fsm.state import State, StatesGroup


class AddGoodState(StatesGroup):
    waiting_for_name = State()
    waiting_for_photo = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_count = State()
    waiting_for_delivery_points = State()
    waiting_for_pickup_points = State()
    waiting_for_discount = State()
    
class BuyGoodState(StatesGroup):
    waiting_for_count = State()
    waiting_for_delivery_address = State()
    waiting_for_phone_number = State()
    waiting_for_name = State()
    
class DeleteGoodState(StatesGroup):
    waiting_for_good_name = State()
    
class AddDeliveryPointState(StatesGroup):
    waiting_for_delivery_point_address = State()
    waiting_for_delivery_point_name = State()
    waiting_for_delivery_point_phone_number = State()
    
class AddPickupPointState(StatesGroup):
    waiting_for_pickup_point_address = State()
    
class ChangeDeliveryPointState(StatesGroup):
    waiting_for_delivery_point_address = State()
    
class AddTopicState(StatesGroup):
    waiting_for_topic_name = State()
    waiting_for_thread_id = State()