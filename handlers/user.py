from aiogram import F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, FSInputFile
)

from bot import dp, bot

from config import CHANNEL_ID
from models.dbs.orm import Orm
from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *


@dp.message(Command('start'))
async def start_message_handler(message: Message, state: FSMContext):
    await state.clear()

    await Orm.create_user(message)

    good_id = message.text[7:]

    if not good_id:
        return await message.answer(
            text='Обратитесь к администратору канала @Maestro_Michael'
        )

    await send_good_info(telegram_id=message.from_user.id, good_id=good_id)
    
@dp.callback_query(F.data == 'cancel')
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        text="Заказ успешно отменен\n\nДля оформления нового заказа перейдите в канал"
    )


async def send_good_info(telegram_id: int, good_id: int):
    good = await Orm.get_good_by_id(good_id)
    
    if not good:
        return await bot.send_message(
            chat_id=telegram_id,
            text=good_not_found_text
        )

    await bot.send_photo(
        chat_id=telegram_id,
        photo=good.photo,
        caption=good.name,
        reply_markup=await generate_choose_delivery_markup(good_id)
    )


@dp.callback_query(lambda callback: callback.data.split(':')[0] in ['delivery', 'pickup', 'delivery_to_addres'])
async def delivery_or_pickup_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    delivery_or_pickup, good_id = callback.data.split(':')
    await state.update_data(good_id=good_id)
    match delivery_or_pickup:
        case 'delivery':
            await state.update_data(delivery=True)
            
            delivery_points_markup = await generate_delivery_points_markup_client(good_id)
            if not delivery_points_markup:
                await Orm.clear_delivery_points(good_id)
                return await callback.message.answer(
                    text=an_error_occurred_text
                )
                
            await callback.message.answer(
                text=request_delivery_points_client_text,
                reply_markup=delivery_points_markup
            )
        case 'pickup':
            await state.update_data(pickup=True)
                
            await callback.message.answer(
                text=request_count_text_client
            )
            await state.set_state(BuyGoodState.waiting_for_count)


@dp.callback_query(lambda callback: callback.data.split(':')[0] in ['delivery_point'])
async def delivery_or_pickup_point_callback(callback: CallbackQuery, state: FSMContext):
    delivery_or_pickup_point, point_id = callback.data.split(':')
    match delivery_or_pickup_point:
        case 'delivery_point':
            await state.update_data(delivery_point_id=point_id)
    await callback.message.answer(
        text=request_count_text_client
    )
    await state.set_state(BuyGoodState.waiting_for_count)


@dp.message(BuyGoodState.waiting_for_count)
async def buy_good_count_handler(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer(count_error_text)
        return
    
    good_id = (await state.get_data())['good_id']
    good = await Orm.get_good_by_id(good_id)
    if count > good.count:
        return await message.answer(
            text=not_enough_goods_text + f'\n\nВ наличии: {good.count} шт.'
        )
    
    await state.update_data(count=count)
    
    await message.answer(
        text=request_name_text_client
    )
    await state.set_state(BuyGoodState.waiting_for_name)
    
@dp.message(BuyGoodState.waiting_for_name)
async def buy_good_name_handler(message: Message, state: FSMContext):
    
    await state.update_data(name=message.text)
    
    await message.answer(
        text=request_phone_number_text_client,
        reply_markup=phone_number_markup
    )

    await state.set_state(BuyGoodState.waiting_for_phone_number)
    
@dp.message(BuyGoodState.waiting_for_phone_number)
async def buy_good_phone_number_handler(message: Message, state: FSMContext):
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        if not message.text.isdigit() or len(message.text) <= 9 or len(message.text) >= 12:
            return await message.answer(
                text=phone_number_error_text
            )
        phone_number = message.text
    
    await state.update_data(phone_number=phone_number)
    

    data = await state.get_data()

    if 'delivery_point_id' in data:
        delivery_point_id = data['delivery_point_id']
        
    name = data['name']

    good_id = data['good_id']

    good = await Orm.get_good_by_id(good_id)
    
    count = data['count']
    
    discount_text = ''
    discount = 1
    
    if good.discount:
    
        if count > 10:
            discount = 0.9
        elif count < 5:
            discount = 1
            discount_text = ''
        else:
            discount = 1 - 0.01 * count
        
        discount_in_cents = int(discount * 100)
        discount_percentage = 100 - discount_in_cents
        discount_text = f'Скидка: {discount_percentage}%'


    if 'delivery' in data:
        price = good.price * count
    elif 'pickup' in data:
        discount -= 0.1
        price = good.price * count * discount
        discount_text += ' +10% за самовывоз со склада'
        
    await state.update_data(price=int(price))
    
    order = await Orm.create_order(
        good_id=good_id,
        count=count,
        price=price,
        phone_number=phone_number,
        name=name,
        delivery_point_id=delivery_point_id if 'delivery_point_id' in data else None,
        pickup=True if 'pickup' in data else False,
        discount_text=discount_text,
        telegram_id=message.from_user.id
    )

    await bot.send_message(
        chat_id=message.from_user.id,
        text=await generate_order_text(
            good=good,
            count=count,
            price=price,
            phone_number=phone_number,
            name=name,
            delivery_point_id=delivery_point_id if 'delivery_point_id' in data else None,
            discount_text=discount_text + '\n' if discount_text else ''
        ),
        reply_markup=await generate_payment_markup(order_id=order.id)
    )
    
    await state.clear()

@dp.callback_query(lambda callback: callback.data.startswith('pay'))
async def pay_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    order_id = int(callback.data.split(':')[1])
    order = await Orm.get_order_by_id(order_id)
    amount = order.price
    await callback.message.answer(
        text=await generate_reqs_text(amount=amount),
        reply_markup=await generate_check_payment_markup(order_id=order.id)
    )
    
    
@dp.callback_query(lambda callback: callback.data.startswith('check_payment'))
async def check_payment_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    order_id = int(callback.data.split(':')[1])
    order = await Orm.get_order_by_id(order_id)
    await callback.message.answer(
        text=wait_for_confirmation_text_client
    )
    
    admin = await Orm.get_admin()
    
    await bot.send_message(
        chat_id=admin.telegram_id,
        text=await generate_check_payment_text(order=order),
        reply_markup=await generate_confirm_payment_markup(order_id=order.id)
    )

async def send_start_message(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text=await generate_start_text(message),
    )
