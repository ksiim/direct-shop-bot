from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from bot import bot
from models.dbs.models import Good, Order
from models.dbs.orm import Orm
from config import REQS, BASE_PHONE_NUMBER, BASE_NAME

from .callbacks import *


prices_per_days = {
    2: 500,
    7: 200,
    10: 0
}

pickup_address = 'Б-Исток'


async def generate_start_text(message):
    return f"Привет, {message.from_user.full_name}! Я - бот"


async def generate_good_text(good: Good):
    return f"{good.name}\n\n{good.description}\n\nЦена: {good.price} руб."


async def generate_good_client_text(good: Good, count: int, type_: str, point_id_or_address: int):
    match type_:
        case 'delivery':
            delivery = await Orm.get_delivery_point_by_id(point_id_or_address)
            return f"Заказ {good.name} в количестве {count} шт. с доставкой на пункт {delivery.address}"
        case 'pickup':
            return f"Заказ {good.name} в количестве {count} шт. на складе"


async def generate_delivery_points_markup(choosed_points: list[int] = []):
    delivery_points = await Orm.get_all_delivery_points()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{delivery_point.address} " + '✅' if str(
                    delivery_point.id) in choosed_points else f"{delivery_point.address}",
                callback_data=str(delivery_point.id)
            )] for delivery_point in delivery_points
        ] + [[
            InlineKeyboardButton(text='Далее', callback_data='next')
        ]]
    )
    return keyboard


async def generate_delivery_points_markup_client(good_id: int):
    good = await Orm.get_good_by_id(good_id)
    delivery_points = await Orm.get_delivery_points_by_ids(good.delivery_points)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{delivery_point.address}",
                callback_data=f'delivery_point:{delivery_point.id}'
            )] for delivery_point in delivery_points
        ]
    )
    return keyboard if delivery_points else None


async def generate_choose_delivery_markup(good_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'Самовывоз со склада(-10%) {pickup_address}', callback_data=f'pickup:{good_id}')
            ],
            [
                InlineKeyboardButton(
                    text='Самовывоз из пункта выдачи', callback_data=f'delivery:{good_id}')
            ]
        ]
    )


async def generate_confirmation_of_address_text(message):
    return f"Вы указали адрес: {message.text}. Подтвердить?"


async def generate_confirmation_of_address_markup(message):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Подтвердить',
                    callback_data='confirm_address')
            ],
            [
                InlineKeyboardButton(
                    text='Изменить',
                    callback_data='rewrite_address')
            ]
        ]
    )


async def generate_delivery_points_to_prefix_markup_admin(prefix='delivery_point_delete'):
    delivery_points = await Orm.get_all_delivery_points()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=delivery_point.address,
                callback_data=f'{prefix}:{delivery_point.id}'
            )] for delivery_point in delivery_points
        ]
    )
    return keyboard


async def generate_order_text(good: Good, count: int, price: float, phone_number, name, delivery_point_id=None, discount_text=''):
    delivery_point = await Orm.get_delivery_point_by_id(delivery_point_id) if delivery_point_id else None
    return f"""Вы заказали: {good.name} {count} шт.
На сумму {price} руб. {discount_text}
Место получения - {delivery_point.address if delivery_point else pickup_address}
"""


async def generate_check_payment_text(order: Order):
    good = await Orm.get_good_by_id(order.good_id)
    delivery_point = await Orm.get_delivery_point_by_id(order.delivery_point_id) if order.delivery_point_id else None
    return f"""{order.name} должен(а) перевести вам {order.price} руб. ({order.discount_text if order.discount_text else ''})
Номер телефона: {order.phone_number}

Заказ: {good.name} {order.count} шт.
Место получения: {delivery_point.address if delivery_point else pickup_address}
"""


async def generate_confirm_payment_markup(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Подтвердить оплату',
                    callback_data=f'confirm_payment:{order_id}'
                )
            ]
        ]
    )


async def generate_buy_markup(good_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Купить', url=f't.me/{(await bot.me()).username}?start={good_id}')
            ]
        ]
    )


async def generate_payment_keyboard(payment_link: str, payment_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить",
                    url=payment_link,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"check_payment:{payment_id}"
                )
            ]
        ]
    )


async def generate_payment_markup(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Оплатить',
                    callback_data=f'pay:{order_id}'
                ),
                InlineKeyboardButton(
                    text='Отменить заказ',
                    callback_data='cancel'
                )
            ]
        ]
    )


async def generate_check_payment_markup(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Проверить оплату',
                    callback_data=f'check_payment:{order_id}'
                )
            ]
        ]
    )


async def generate_reqs_text(amount: int):
    return REQS + str(amount) + ' руб.'

async def generate_bought_good_text(order: Order):
    phone_number = BASE_PHONE_NUMBER
    name = BASE_NAME
    delivery_point = await Orm.get_delivery_point_by_id(order.delivery_point_id)
    if delivery_point:
        phone_number = delivery_point.phone_number
        name = delivery_point.name
    good = await Orm.get_good_by_id(order.good_id)
    return f"""Вы купили {good.name} в количестве {order.count} шт.
На сумму {order.price} руб. {order.discount_text if order.discount_text else ''}
Место получения - {delivery_point.address if delivery_point else pickup_address}
Контактный телефон для получения заказа {phone_number} Зовут {name}
"""

async def generate_topics_markup_admin():
    topics = await Orm.get_all_topics()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=topic.name,
                callback_data=f'topic_delete:{topic.id}'
            )] for topic in topics
        ]
    )
    return keyboard

async def generate_choose_topics_markup():
    topics = await Orm.get_all_topics()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=topic.name,
                callback_data=f'topic:{topic.thread_id}'
            )] for topic in topics
        ]
    )
    return keyboard

admin_panel_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Добавить товар',
                callback_data='add_good'),
            InlineKeyboardButton(
                text='Удалить товар',
                callback_data='delete_good')
        ],
        [
            InlineKeyboardButton(
                text='Добавить пункт доставки',
                callback_data='add_delivery_point'),
        ],
        [
            InlineKeyboardButton(
                text='Удалить пункт доставки',
                callback_data='delete_delivery_point'),
        ],
        [
            InlineKeyboardButton(
                text='Изменить адрес пункта доставки',
                callback_data='change_delivery_point_address')
        ],
        [
            InlineKeyboardButton(
                text='Добавить тему',
                callback_data='add_topic'),
            InlineKeyboardButton(
                text='Удалить тему',
                callback_data='delete_topic')
        ]
    ]
)

phone_number_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Отправить номер телефона',
                           request_contact=True)
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

discount_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='discount'),
            InlineKeyboardButton(text='Нет', callback_data='no_discount')
        ]
    ]
)

request_product_name = 'Введите название товара'
request_product_photo = 'Отправьте фото товара'
request_product_price = 'Введите цену за единицу товара'
request_product_description = 'Введите описание товара'
request_product_count = 'Введите доступное для продажи количество товара'
request_delivery_points_text = 'Выберите пункты, доступные для выдачи'
request_pickup_points_text = 'Выберите пункты, доступные для самовывоза'
request_topic_text = 'Выберите тему, куда выложить товар'
request_discount_text = 'Предоставить систему скидок?'
good_added_confirmation = 'Товар успешно добавлен и выложен в канал!'

request_topic_name_text = 'Введите название темы'
request_thread_id_text = 'Введите id темы (напишите /id в вашей теме для того, чтобы получить ее id)'
topic_added_text = 'Тема успешно добавлена'

choose_topic_to_delete_text = 'Выберите тему для удаления'
topic_deleted_text = 'Тема удалена'

good_not_found_text = 'Товар не найден'
good_deleted_text = 'Товар удален'
no_goods_message = 'Товаров нет'
not_enough_goods_text = 'Вы хотите купить больше товаров, чем есть в наличии'
phone_number_error_text = 'Номер телефона должен состоять из цифр без знака +'
count_error_text = 'Количество должно быть целым числом'
price_input_error = 'Цена должна быть целым числом'
an_error_occurred_text = 'Произошла ошибка, обратитесь к администратору'
thread_id_error_text = 'ID темы должен быть целым числом'

no_topics_text = 'Тем нет'

panel_title_text = 'Админ-панель'

choose_good_for_delete_text = 'Введите название товара для удаления'

waiting_for_address_delivery_point_text = 'Введите адрес пункта доставки'
waiting_for_price_delivery_point_text = 'Введите цену доставки'
request_for_delivery_point_name_text = 'Введите имя контактного лица пункта доставки'
request_for_delivery_point_phone_number_text = 'Введите номер телефона контактного лица пункта доставки'
delivery_point_confirmation_text = 'Пункт доставки добавлен'

waiting_for_address_pickup_point_text = 'Введите адрес пункта самовывоза'
pickup_point_confirmation_text = 'Пункт самовывоза добавлен'

wait_for_confirmation_text_client = 'Дождитесь подтверждения оплаты...'
payment_confirmed_text = 'Оплата подтверждена'

choose_address_of_delivery_point_to_delete = 'Выберите пункт доставки для удаления'
choose_delivery_point_to_change_text = 'Выберите пункт выдачи для изменения адреса'
request_new_address_text = 'Введите новый адрес пункта выдачи'
delivery_point_deleted_text = 'Пункт доставки удален'
delivery_point_address_changed_text = 'Адрес пункта выдачи изменен'
no_delivery_points_text = 'Пунктов доставки нет'

choose_address_of_pickup_point_to_delete = 'Выберите пункт самовывоза для удаления'
pickup_point_deleted_text = 'Пункт самовывоза удален'
no_pickup_points_text = 'Пунктов самовывоза нет'


request_delivery_points_client_text = 'Выберите пункт выдачи, где вы заберете товар'
request_pickup_points_client_text = 'Выберите пункт, где вы заберете товар'
request_count_text_client = 'Введите количество товара целым числом'
request_delivery_address_text_client = 'Введите адрес доставки'
request_dates_for_delivery_text_client = 'Выберите сроки доставки'
request_phone_number_text_client = 'Отправьте ваш номер телефона'
request_name_text_client = 'Как к вам обращаться?'
order_accepted_text = 'Ваш заказ принят'
