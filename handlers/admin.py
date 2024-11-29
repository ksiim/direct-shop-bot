import asyncio
from bot import dp, bot

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram import F

from config import CHANNEL_ID, CHANNEL_TYPE
from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *

from .user import *


@dp.message(Command('id'))
async def get_thread_id(message: Message):
    answer = await message.answer(
        text=f"ID чата: {message.chat.id}\n\nID темы: {message.reply_to_message.message_thread_id}"
    )
    await asyncio.sleep(10)
    await message.delete()
    await answer.delete()


@dp.message(Command('admin'))
async def admin_message_handler(message: Message, state: FSMContext):
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    if not user.admin:
        return

    await state.clear()

    await send_admin_panel(telegram_id=message.from_user.id)


async def send_admin_panel(telegram_id: int):
    await bot.send_message(
        chat_id=telegram_id,
        text=panel_title_text,
        reply_markup=admin_panel_markup
    )


@dp.callback_query(F.data == 'add_good')
async def add_good_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(request_product_name)

    await state.set_state(AddGoodState.waiting_for_name)


@dp.message(AddGoodState.waiting_for_name)
async def add_good_name_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(request_product_name)
        return

    await state.update_data(name=message.text)

    await message.answer(request_product_photo)

    await state.set_state(AddGoodState.waiting_for_photo)


@dp.message(AddGoodState.waiting_for_photo)
async def add_good_photo_handler(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(request_product_photo)
        return

    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)

    await message.answer(request_product_price)

    await state.set_state(AddGoodState.waiting_for_price)


@dp.message(AddGoodState.waiting_for_price)
async def add_good_price_handler(message: Message, state: FSMContext):
    try:
        price = int(message.text)
    except ValueError:
        await message.answer(price_input_error)
        return

    await state.update_data(price=price)

    await message.answer(request_product_description)

    await state.set_state(AddGoodState.waiting_for_description)


@dp.message(AddGoodState.waiting_for_description)
async def add_good_description_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(request_product_description)
        return

    await state.update_data(description=message.text)

    await state.set_state(AddGoodState.waiting_for_discount)

    await message.answer(
        text=request_discount_text,
        reply_markup=discount_markup
    )


@dp.callback_query(AddGoodState.waiting_for_discount)
async def discount_callback(callback: CallbackQuery, state: FSMContext):
    discount = callback.data == 'discount'

    await state.update_data(discount=discount)

    await callback.message.answer(
        text=request_delivery_points_text,
        reply_markup=await generate_delivery_points_markup()
    )

    await state.set_state(AddGoodState.waiting_for_delivery_points)


@dp.callback_query(AddGoodState.waiting_for_delivery_points)
async def delivery_point_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'next':
        await callback.message.answer(request_product_count)
        return await state.set_state(AddGoodState.waiting_for_count)

    data = await state.get_data()
    choosed_points = data.get('delivery_points', [])

    if callback.data in choosed_points:
        choosed_points.remove(callback.data)
    else:
        choosed_points.append(callback.data)

    await state.update_data(delivery_points=choosed_points)

    await callback.message.edit_reply_markup(
        reply_markup=await generate_delivery_points_markup(choosed_points)
    )


@dp.message(AddGoodState.waiting_for_count)
async def add_good_count_handler(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer(count_error_text)
        return

    await state.update_data(count=count)

    if CHANNEL_TYPE == 'channel':
        pass
    elif CHANNEL_TYPE == 'supergroup':
        return await message.answer(
            text=request_topic_text,
            reply_markup=await generate_choose_topics_markup()
        )

    await save_good_details_and_notify(message, state)
    
    
@dp.callback_query(lambda callback: callback.data.startswith('topic:'))
async def topic_callback(callback: CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split(':')[1])
    await state.update_data(topic_id=topic_id)

    await save_good_details_and_notify(callback, state)

async def save_good_details_and_notify(message: Message, state: FSMContext):
    data = await state.get_data()
    good = await Orm.create_good(
        name=data['name'],
        photo=data['photo'],
        price=data['price'],
        description=data['description'],
        count=data['count'],
        delivery_points_ids=data.get('delivery_points', []),
        pickup_points_ids=data.get('pickup_points', []),
        discount=data['discount']
    )

    caption = await generate_good_text(good)
    if len(caption) > 1020:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=too_long_description_text
        )
        await asyncio.sleep(3)
        return await send_admin_panel(telegram_id=message.from_user.id)
    
    if CHANNEL_TYPE == 'channel':
        good_message = await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=good.photo,
            caption=caption,
            reply_markup=await generate_buy_markup(good.id)
        )
    else:
        good_message = await bot.send_photo(
            chat_id=CHANNEL_ID,
            message_thread_id=data['topic_id'],
            photo=good.photo,
            caption=caption,
            reply_markup=await generate_buy_markup(good.id)
        )

    await Orm.update_good_message_id(good.id, good_message.message_id)

    await bot.send_message(
        chat_id=message.from_user.id,
        text=good_added_confirmation,
    )

    await state.clear()

    await send_admin_panel(telegram_id=message.from_user.id)


@dp.callback_query(F.data == 'delete_good')
async def delete_good_callback(callback: CallbackQuery, state: FSMContext):
    goods = await Orm.get_all_goods()
    if not goods:
        return await callback.answer(no_goods_message, show_alert=True)

    await callback.message.answer(
        text=choose_good_for_delete_text,
    )

    await state.set_state(DeleteGoodState.waiting_for_good_name)


@dp.message(DeleteGoodState.waiting_for_good_name)
async def delete_good_name_handler(message: Message, state: FSMContext):
    good = await Orm.get_good_by_name(message.text)
    if not good:
        await message.answer(good_not_found_text)
        return

    await bot.delete_message(chat_id=CHANNEL_ID, message_id=good.message_id)
    await Orm.delete_good_by_id(good.id)

    await message.answer(good_deleted_text)

    await state.clear()

    await send_admin_panel(telegram_id=message.from_user.id)


@dp.callback_query(F.data == 'add_delivery_point')
async def add_delivery_point_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=waiting_for_address_delivery_point_text
    )

    await state.set_state(AddDeliveryPointState.waiting_for_delivery_point_address)


@dp.message(AddDeliveryPointState.waiting_for_delivery_point_address)
async def add_delivery_point_address_handler(message: Message, state: FSMContext):

    address = message.text
    
    await state.update_data(address=address)
    
    await message.answer(
        text=request_for_delivery_point_phone_number_text
    )
    
    await state.set_state(AddDeliveryPointState.waiting_for_delivery_point_phone_number)
    
@dp.message(AddDeliveryPointState.waiting_for_delivery_point_phone_number)
async def add_delivery_point_phone_number_handler(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer(
        text=request_for_delivery_point_name_text
    )
    
    await state.set_state(AddDeliveryPointState.waiting_for_delivery_point_name)
    
@dp.message(AddDeliveryPointState.waiting_for_delivery_point_name)
async def add_delivery_point_name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    address = data['address']
    phone_number = data['phone_number']
    name = message.text

    await Orm.create_delivery_point(address, phone_number, name)

    await message.answer(delivery_point_confirmation_text)

    await state.clear()

    await send_admin_panel(telegram_id=message.from_user.id)


@dp.callback_query(F.data == 'delete_delivery_point')
async def delete_delivery_point_callback(callback: CallbackQuery, state: FSMContext):
    points = await Orm.get_all_delivery_points()
    if not points:
        return await callback.answer(no_delivery_points_text, show_alert=True)

    await callback.message.answer(
        text=choose_address_of_delivery_point_to_delete,
        reply_markup=await generate_delivery_points_to_prefix_markup_admin()
    )


@dp.callback_query(lambda callback: callback.data.startswith('delivery_point_delete:'))
async def delete_delivery_point_callback(callback: CallbackQuery, state: FSMContext):
    point_id = int(callback.data.split(':')[1])
    await Orm.delete_delivery_point_by_id(point_id)

    await callback.message.answer(delivery_point_deleted_text)

    await send_admin_panel(telegram_id=callback.from_user.id)


@dp.callback_query(F.data == 'change_delivery_point_address')
async def change_delivery_point_address_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=choose_delivery_point_to_change_text,
        reply_markup=await generate_delivery_points_to_prefix_markup_admin(prefix='delivery_point_change')
    )


@dp.callback_query(lambda callback: callback.data.startswith('delivery_point_change:'))
async def change_delivery_point_address_callback(callback: CallbackQuery, state: FSMContext):
    point_id = int(callback.data.split(':')[1])
    await state.update_data(point_id=point_id)

    await callback.message.answer(
        text=request_new_address_text
    )

    await state.set_state(ChangeDeliveryPointState.waiting_for_delivery_point_address)


@dp.message(ChangeDeliveryPointState.waiting_for_delivery_point_address)
async def change_delivery_point_address_handler(message: Message, state: FSMContext):
    point_id = (await state.get_data())['point_id']
    await Orm.update_delivery_point_address(point_id, message.text)

    await message.answer(delivery_point_address_changed_text)

    await state.clear()

    await send_admin_panel(telegram_id=message.from_user.id)


@dp.callback_query(lambda callback: callback.data.startswith('confirm_payment'))
async def confirm_payment_callback(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(':')[1])
    order = await Orm.get_order_by_id(order_id)

    await callback.message.delete_reply_markup()
    await callback.message.answer(
        text=payment_confirmed_text
    )

    client_text = await generate_bought_good_text(order)

    await bot.send_message(
        chat_id=order.telegram_id,
        text=client_text
    )


@dp.callback_query(F.data == "add_topic")
async def add_topic_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=request_topic_name_text
    )

    await state.set_state(AddTopicState.waiting_for_topic_name)


@dp.message(AddTopicState.waiting_for_topic_name)
async def add_topic_name_handler(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(
        text=request_thread_id_text
    )

    await state.set_state(AddTopicState.waiting_for_thread_id)


@dp.message(AddTopicState.waiting_for_thread_id)
async def add_thread_id_handler(message: Message, state: FSMContext):
    try:
        thread_id = int(message.text)
    except Exception as e:
        return await message.answer(thread_id_error_text)
    
    await state.update_data(thread_id=thread_id)
    
    data = await state.get_data()
    await Orm.create_topic(data['name'], data['thread_id'])
    
    await message.answer(
        text=topic_added_text
    )
    
    await state.clear()
    
    await send_admin_panel(telegram_id=message.from_user.id)
    

@dp.callback_query(F.data == 'delete_topic')
async def delete_topic_callback(callback: CallbackQuery, state: FSMContext):
    topics = await Orm.get_all_topics()
    if not topics:
        return await callback.answer(no_topics_text, show_alert=True)
    
    await callback.message.answer(
        text=choose_topic_to_delete_text,
        reply_markup=await generate_topics_markup_admin()
    )
    
@dp.callback_query(lambda callback: callback.data.startswith('topic_delete:'))
async def topic_delete_callback(callback: CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split(':')[1])
    await Orm.delete_topic_by_id(topic_id)
    
    await callback.message.answer(
        text=topic_deleted_text
    )
    
    await send_admin_panel(telegram_id=callback.from_user.id)
