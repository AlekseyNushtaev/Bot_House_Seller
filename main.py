import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TG_TOKEN, ADMIN_IDS
from db.models import create_tables
import datetime  # Добавляем импорт
from openpyxl import Workbook
from db.models import Session, User, Order


bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

TOTAL_PHOTOS = 117
PHOTO_DIR = "photo"
PHOTO_SECTIONS = {
    "fasad": {"name": "Фасад", "count": 21, "path": "photo/fasad_21"},
    "kitchen": {"name": "Кухня", "count": 7, "path": "photo/kitchen_7"},
    "bedroom1": {"name": "Спальня №1", "count": 6, "path": "photo/bedroom_6"},
    "bedroom2": {"name": "Спальня №2", "count": 4, "path": "photo/bedroom_4"},
    "biliard": {"name": "Бильярдная", "count": 4, "path": "photo/biliard_4"},
    "boiler": {"name": "Бойлерная", "count": 4, "path": "photo/boiler_4"},
    "cokol": {"name": "Цокольный этаж", "count": 9, "path": "photo/cokol_9"},
    "fligel": {"name": "Флигель", "count": 42, "path": "photo/fligel_42"},
    "master": {"name": "Мастерская", "count": 6, "path": "photo/master_6"},
    "football": {"name": "Футбольное поле", "count": 3, "path": "photo/football_3"},
    "oka": {"name": "Ока", "count": 2, "path": "photo/oka_2"},
    "forest": {"name": "Лес", "count": 2, "path": "photo/forest_2"},
    "rodnik": {"name": "Родник", "count": 6, "path": "photo/rodnik_6"},
}


class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


# ===== Генераторы клавиатур =====
def main_menu_kb():
    """Клавиатура главного меню с эмодзи"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="🏠 Узнать подробности о доме",
            callback_data="details"
        ),
        types.InlineKeyboardButton(
            text="📅 Записаться на просмотр",
            callback_data="appointment"
        ),
        types.InlineKeyboardButton(
            text="👤 Связаться с продавцом",
            url="https://t.me/Boris69m"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def details_menu_kb():
    """Клавиатура меню подробностей с эмодзи"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="📊 Основные характеристики",
            callback_data="features"
        ),
        types.InlineKeyboardButton(
            text="💰 Стоимость",
            callback_data="price"
        ),
        types.InlineKeyboardButton(
            text="📏 Площадь дома",
            callback_data="area"
        ),
        types.InlineKeyboardButton(
            text="📍 Местоположение",
            callback_data="location"
        ),
        types.InlineKeyboardButton(
            text="📋 План дома",
            callback_data="plan"
        ),
        types.InlineKeyboardButton(
            text="🖼️ Фото",
            callback_data="photos"
        ),
        types.InlineKeyboardButton(
            text="🎬 Видео",
            callback_data="videos"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_main"
        )
    )
    builder.adjust(1, 2, 2, 2, 1)
    return builder.as_markup()


def back_to_details_kb():
    """Клавиатура с кнопкой Назад"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_details"
        )
    )
    return builder.as_markup()


def features_menu_kb():
    """Клавиатура меню характеристик с эмодзи"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="🏡 Главный дом",
            callback_data="main_house"
        ),
        types.InlineKeyboardButton(
            text="🛖 Гостевой дом",
            callback_data="guest_house"
        ),
        types.InlineKeyboardButton(
            text="🌳 Приусадебная территория",
            callback_data="territory"
        ),
        types.InlineKeyboardButton(
            text="⭐ Дополнительные преимущества",
            callback_data="benefits"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_details"
        )
    )
    builder.adjust(1, 1, 1)
    return builder.as_markup()


def main_house_kb():
    """Клавиатура меню главного дома с эмодзи"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="🧱 Материалы",
            callback_data="materials"
        ),
        types.InlineKeyboardButton(
            text="1️⃣ Первый этаж",
            callback_data="first_floor"
        ),
        types.InlineKeyboardButton(
            text="2️⃣ Второй этаж",
            callback_data="second_floor"
        ),
        types.InlineKeyboardButton(
            text="🏢 Цокольный этаж",
            callback_data="basement"
        ),
        types.InlineKeyboardButton(
            text="🔼 Мансарда",
            callback_data="attic"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_features"
        )
    )
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def back_to_main_house_kb():
    """Кнопка назад в меню главного дома"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_main_house"
        )
    )
    return builder.as_markup()


def back_to_features_kb():
    """Кнопка назад в меню характеристик"""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_features"
        )
    )
    return builder.as_markup()


def photo_sections_kb():
    """Клавиатура выбора раздела фото"""
    builder = InlineKeyboardBuilder()

    sections = list(PHOTO_SECTIONS.items())
    for i in range(0, len(sections), 2):
        # Добавляем по 2 кнопки в ряд
        row = sections[i:i + 2]
        for section_key, section_data in row:
            builder.add(types.InlineKeyboardButton(
                text=section_data["name"],
                callback_data=f"open_section_{section_key}_1"
            ))

    # Кнопка "Назад"
    builder.add(types.InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_details"
    ))

    builder.adjust(2, 2, 2, 2, 2, 2, 2, 1)  # 2 кнопки в ряду, последний ряд - 1 кнопка
    return builder.as_markup()


def section_photo_navigation_kb(section: str, photo_index: int):
    """Клавиатура для навигации по фото в разделе"""
    section_data = PHOTO_SECTIONS.get(section)
    if not section_data:
        return None

    total_photos = section_data["count"]
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    if photo_index > 1:
        builder.add(types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"prev_sec_{section}_{photo_index - 1}"
        ))

    if photo_index < total_photos:
        builder.add(types.InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"next_sec_{section}_{photo_index + 1}"
        ))

    # Кнопки возврата
    builder.add(types.InlineKeyboardButton(
        text="Назад к разделам ◀️",
        callback_data="photo_sections"
    ))


    # Оптимальное расположение кнопок
    if photo_index > 1 and photo_index < total_photos:
        builder.adjust(2, 2)  # Две кнопки навигации в первом ряду, две кнопки возврата во втором
    else:
        builder.adjust(1, 2)  # Одна кнопка навигации, затем две кнопки возврата

    return builder.as_markup()


def plan_navigation_kb(photo_index: int):
    """Клавиатура для навигации по фото плана"""
    builder = InlineKeyboardBuilder()

    # Кнопка "Назад" (только если не первая фото)
    if photo_index > 1:
        builder.add(
            types.InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"prev_plan_{photo_index - 1}"
            )
        )

    # Кнопка "Вперед" (только если не последняя фото)
    if photo_index < 3:
        builder.add(
            types.InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"next_plan_{photo_index + 1}"
            )
        )

    # Кнопка возврата в меню
    builder.add(
        types.InlineKeyboardButton(
            text="Назад в меню ◀️",
            callback_data="back_details_from_photo"
        )
    )

    # Оптимальное расположение кнопок
    if photo_index > 1 and photo_index < 3:
        builder.adjust(2, 1)  # Две кнопки в первой строке, одна во второй
    else:
        builder.adjust(1)  # Все кнопки в один столбец

    return builder.as_markup()


# ===== Обработчики сообщений =====
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    # Сохраняем пользователя в БД
    with Session() as session:
        user = session.get(User, message.from_user.id)
        if not user:
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                time_start=datetime.datetime.now()
            )
            session.add(new_user)
            session.commit()

    await message.answer(
        "🏡 Продается уникальная усадьба в живописном уголке Калужской области "
        "на высоком правом берегу Оки в 160 км от МКАД.",
        reply_markup=main_menu_kb()
    )


# ===== Обработчики колбэков =====
@dp.callback_query(F.data == "details")
async def details_handler(callback: types.CallbackQuery):
    """Обработчик кнопки подробностей"""
    await callback.message.edit_text(
        "🌳 Эта впечатляющая усадьба площадью 1,6 гектара расположена на "
        "живописной территории в окружении вековых лесов и сказочных оврагов, "
        "всего в 8 км от центра города Калуги.\n\n"
        "✅ Идеальное место для ценителей природы и уединения, "
        "а также для тех, кто ищет вдохновения вдали от городской суеты.",
        reply_markup=details_menu_kb()
    )
    await callback.answer()


@dp.callback_query(F.data == "back_details_from_photo")
async def details_handler_from_photo(callback: types.CallbackQuery):
    """Обработчик кнопки назад из фото/плана"""
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "🌳 Эта впечатляющая усадьба площадью 1,6 гектара расположена на "
        "живописной территории в окружении вековых лесов и сказочных оврагов, "
        "всего в 8 км от центра города Калуги.\n\n"
        "✅ Идеальное место для ценителей природы и уединения, "
        "а также для тех, кто ищет вдохновения вдали от городской суеты.",
        reply_markup=details_menu_kb()
    )
    await callback.answer()


@dp.callback_query(F.data == "features")
async def features_handler(callback: types.CallbackQuery):
    """Обработчик основных характеристик"""
    await callback.message.edit_text(
        "📊 Основные характеристики усадьбы:",
        reply_markup=features_menu_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "main_house")
async def main_house_handler(callback: types.CallbackQuery):
    """Обработчик главного дома"""
    await callback.message.edit_text(
        "🏡 <b>Главный дом</b>:\n"
        "• Площадь: 1000 кв.м\n"
        "• Этажи: 3 этажа + мансарда\n"
        "• Спальни: 7\n"
        "• Санузлы: 7\n"
        "• Кухни: 2\n"
        "• Камины: 2 + русская печь\n\n"
        "⚙️ <b>Коммуникации</b>:\n"
        "• Магистральный газ + 2 газгольдера (10м³)\n"
        "• Скважина 80м\n"
        "• Септик 10м³\n"
        "• Газовый электрогенератор 15 кВт\n"
        "• Электричество: 35 кВт",
        parse_mode="HTML",
        reply_markup=main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "materials")
async def materials_handler(callback: types.CallbackQuery):
    """Обработчик материалов"""
    await callback.message.edit_text(
        "🧱 <b>Материалы и конструкции</b>:\n"
        "• Фундамент: бетонная монолитная плита\n"
        "• Гидроизоляция: внешняя (гидроизол) + внутренняя (Пенетрон)\n"
        "• Стены: красный кирпич + облицовочный кирпич\n"
        "• Стропильная система: металл (швеллер, балки)\n"
        "• Коммуникации: медные трубы (водоснабжение и отопление)\n\n"
        "✅ Всё выполнено очень добротно, надёжно и качественно!",
        parse_mode="HTML",
        reply_markup=back_to_main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "first_floor")
async def first_floor_handler(callback: types.CallbackQuery):
    """Обработчик первого этажа"""
    await callback.message.edit_text(
        "1️⃣ <b>Первый этаж</b> включает:\n"
        "• Просторная кухня-гостиная с русской печью\n"
        "• Большая спальня с кабинетом, санузлом и камином\n"
        "• 2 уютные спальни\n"
        "• Комната свободного назначения\n"
        "• Бытовая комната\n"
        "• 2 отдельных санузла\n"
        "• Большой холл\n"
        "• Гараж на 2 машины",
        parse_mode="HTML",
        reply_markup=back_to_main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "second_floor")
async def second_floor_handler(callback: types.CallbackQuery):
    """Обработчик второго этажа"""
    await callback.message.edit_text(
        "2️⃣ <b>Второй этаж</b> включает:\n"
        "• Кухня-гостиная с восточным камином\n"
        "• 3 спальни с индивидуальными санузлами\n"
        "• Гостевой санузел\n"
        "• Просторная библиотека (можно организовать музыкальный салон)\n"
        "• Помещение с барной зоной и высокими потолками (идеально для бильярда)",
        parse_mode="HTML",
        reply_markup=back_to_main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "basement")
async def basement_handler(callback: types.CallbackQuery):
    """Обработчик цокольного этажа"""
    await callback.message.edit_text(
        "🏢 <b>Цокольный этаж</b> включает:\n"
        "• Бойлерная (4 котла, 112кВт)\n"
        "• Овощехранилище с вентиляцией\n"
        "• Спортивный зал\n"
        "• Помещения свободного назначения (мастерская, хранилище)",
        parse_mode="HTML",
        reply_markup=back_to_main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "attic")
async def attic_handler(callback: types.CallbackQuery):
    """Обработчик мансарды"""
    await callback.message.edit_text(
        "🔼 <b>Мансарда</b>:\n"
        "• Просторное помещение свободного назначения\n"
        "• Идеально для детской/игровой комнаты\n"
        "• Возможность организации спальных мест, рабочей зоны и систем хранения",
        parse_mode="HTML",
        reply_markup=back_to_main_house_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_main_house")
async def back_main_house_handler(callback: types.CallbackQuery):
    """Возврат в меню главного дома"""
    await main_house_handler(callback)

@dp.callback_query(F.data == "back_features")
async def back_features_handler(callback: types.CallbackQuery):
    """Возврат в меню характеристик"""
    await features_handler(callback)

@dp.callback_query(F.data == "back_details")
async def back_details_handler(callback: types.CallbackQuery):
    """Возврат в меню подробностей"""
    await details_handler(callback)

@dp.callback_query(F.data == "back_main")
async def back_main_handler(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏡 Продается уникальная усадьба в живописном уголке Калужской области "
        "на высоком правом берегу Оки в 160 км от МКАД.",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

# ===== Новые обработчики колбэков =====
@dp.callback_query(F.data == "guest_house")
async def guest_house_handler(callback: types.CallbackQuery):
    """Обработчик гостевого дома"""
    await callback.message.edit_text(
        "🛖 <b>Гостевой дом</b>:\n"
        "• Площадь: 300 кв.м\n"
        "• Этажи: 2\n"
        "• Спальни: 4\n"
        "• Санузлы: 2\n"
        "• Кухня-гостиная\n"
        "• Отделка в охотничьем стиле\n\n"
        "⚙️ <b>Дополнительно</b>:\n"
        "• Мастерская\n"
        "• Гараж на 2 машины\n"
        "• Хозяйственный бокс",
        parse_mode="HTML",
        reply_markup=back_to_features_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "territory")
async def territory_handler(callback: types.CallbackQuery):
    """Обработчик приусадебной территории"""
    await callback.message.edit_text(
        "🌳 <b>Приусадебная территория</b> (1.6 га):\n"
        "• Ухоженный сад с беседкой\n"
        "• Зона барбекю\n"
        "• Огород и теплица\n"
        "• Спортивный комплекс\n"
        "• Лесной массив",
        parse_mode="HTML",
        reply_markup=back_to_features_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "benefits")
async def benefits_handler(callback: types.CallbackQuery):
    """Обработчик дополнительных преимуществ"""
    await callback.message.edit_text(
        "⭐ <b>Преимущества усадьбы</b>:\n"
        "• Идеально для агротуризма или бизнеса (отель, ресторан, мероприятия)\n"
        "• Отличная транспортная доступность\n"
        "• Магазины и аптеки в 3 км\n"
        "• Рыбалка на Оке 🎣\n"
        "• Чистый родник с вкусной водой\n"
        "• Лесные трассы для квадроциклов\n\n"
        "🌄 <b>Окрестности</b>:\n"
        "• Оптина Пустынь (1 час езды)\n"
        "• Шамординский монастырь\n"
        "• Горнолыжный спуск, парки, театры и музеи Калуги",
        parse_mode="HTML",
        reply_markup=back_to_features_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "price")
async def price_handler(callback: types.CallbackQuery):
    """Обработчик стоимости"""
    await callback.message.edit_text(
        "💰 <b>Стоимость</b>: 145 млн.руб.\n"
        "Цена обсуждается при осмотре объекта.",
        parse_mode="HTML",
        reply_markup=back_to_details_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "area")
async def area_handler(callback: types.CallbackQuery):
    """Обработчик площади дома"""
    await callback.message.edit_text(
        "📏 <b>Площади объектов</b>:\n"
        "• Главный дом: 1000 кв.м\n"
        "• Гостевой дом: 300 кв.м\n"
        "• Земельный участок: 1.6 га",
        parse_mode="HTML",
        reply_markup=back_to_details_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "location")
async def location_handler(callback: types.CallbackQuery):
    """Обработчик местоположения"""
    await callback.message.edit_text(
        "📍 <b>Местоположение</b>:\n"
        "Калужская область, правый берег Оки\n"
        "• 160 км от МКАД\n"
        "• 8 км от центра Калуги",
        parse_mode="HTML",
        reply_markup=back_to_details_kb()
    )
    await callback.answer()


@dp.callback_query(F.data == "appointment")
async def start_appointment(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса записи на просмотр"""
    await callback.message.edit_text(
        "📝 Запись на просмотр\n\nПожалуйста, введите Ваше имя:",
        reply_markup=None  # Убираем клавиатуру
    )
    await state.set_state(AppointmentStates.waiting_for_name)
    await callback.answer()


# Обработчик состояния "ожидание имени"
@dp.message(AppointmentStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка введенного имени"""
    await state.update_data(name=message.text)
    await message.answer("Теперь введите Ваш телефон:")
    await state.set_state(AppointmentStates.waiting_for_phone)


# Обработчик состояния "ожидание телефона"
@dp.message(AppointmentStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка введенного телефона и завершение записи"""
    user_data = await state.get_data()
    name = user_data.get('name', 'не указано')
    phone = message.text

    # Сохраняем заказ в БД
    with Session() as session:
        new_order = Order(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            phone=phone,
            fio=name,
            time_order=datetime.datetime.now()
        )
        session.add(new_order)
        session.commit()


    # Отправляем данные администратору
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"📋 Новая запись на просмотр:\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n↗️ TG: @{message.from_user.username}"
            )
        except:
            pass

    # Сбрасываем состояние
    await state.clear()

    # Благодарим пользователя и возвращаем в главное меню
    await message.answer(
        "✅ Спасибо за предоставленную информацию, в ближайшее время мы с Вами свяжемся!",
        reply_markup=main_menu_kb()
    )


# Обновляем заглушку для нереализованных разделов (убираем 'appointment' из списка)
@dp.callback_query(F.data.in_(["videos"]))
async def not_implemented_handler(callback: types.CallbackQuery):
    """Заглушка для нереализованных разделов"""
    await callback.answer("⏳ Раздел в разработке", show_alert=True)


@dp.callback_query(F.data == "plan")
async def plan_handler(callback: types.CallbackQuery):
    """Обработчик кнопки План дома"""
    try:
        await callback.message.delete()
    except:
        pass

    # Отправляем первое фото плана
    photo_index = 1
    photo_path = os.path.join("plan", f"{photo_index}.jpg")

    if os.path.exists(photo_path):
        with open(photo_path, "rb") as photo_file:
            await callback.message.answer_photo(
                photo=types.FSInputFile(photo_path),
                caption=f"План дома ({photo_index}/3)",
                reply_markup=plan_navigation_kb(photo_index)
            )
    else:
        await callback.message.answer("Фото плана временно недоступны")

    await callback.answer()


@dp.callback_query(F.data.startswith("prev_plan_"))
async def prev_plan_handler(callback: types.CallbackQuery):
    """Обработчик кнопки Назад для плана"""
    photo_index = int(callback.data.split("_")[-1])
    photo_path = os.path.join("plan", f"{photo_index}.jpg")

    if os.path.exists(photo_path):
        media = InputMediaPhoto(
            media=types.FSInputFile(photo_path),
            caption=f"План дома ({photo_index}/3)"
        )
        await callback.message.edit_media(
            media=media,
            reply_markup=plan_navigation_kb(photo_index)
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("next_plan_"))
async def next_plan_handler(callback: types.CallbackQuery):
    """Обработчик кнопки Вперед для плана"""
    photo_index = int(callback.data.split("_")[-1])
    photo_path = os.path.join("plan", f"{photo_index}.jpg")

    if os.path.exists(photo_path):
        media = InputMediaPhoto(
            media=types.FSInputFile(photo_path),
            caption=f"План дома ({photo_index}/3)"
        )
        await callback.message.edit_media(
            media=media,
            reply_markup=plan_navigation_kb(photo_index)
        )
    await callback.answer()


@dp.message(Command("export"))
async def export_command(message: types.Message):
    """Экспорт данных в Excel файл"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для выполнения этой команды")
        return

    # Создаем новую книгу Excel
    wb = Workbook()

    # Лист для заказов (Order)
    orders_sheet = wb.active
    orders_sheet.title = "Orders"

    # Заголовки для заказов
    orders_headers = [
        "ID", "User ID", "Username", "First Name",
        "Last Name", "Phone", "FIO", "Time Order"
    ]
    orders_sheet.append(orders_headers)

    # Лист для пользователей (User)
    users_sheet = wb.create_sheet(title="Users")

    # Заголовки для пользователей
    users_headers = [
        "User ID", "Username", "First Name",
        "Last Name", "Time Start"
    ]
    users_sheet.append(users_headers)

    # Получаем данные из БД
    with Session() as session:
        # Заполняем данные заказов
        orders = session.query(Order).all()
        for order in orders:
            orders_sheet.append([
                order.id,
                order.user_id,
                order.username,
                order.first_name,
                order.last_name,
                order.phone,
                order.fio,
                order.time_order.strftime("%Y-%m-%d %H:%M:%S") if order.time_order else ""
            ])

        # Заполняем данные пользователей
        users = session.query(User).all()
        for user in users:
            users_sheet.append([
                user.user_id,
                user.username,
                user.first_name,
                user.last_name,
                user.time_start.strftime("%Y-%m-%d %H:%M:%S") if user.time_start else ""
            ])

    # Настраиваем ширину столбцов
    for col in orders_sheet.columns:
        orders_sheet.column_dimensions[col[0].column_letter].width = 20

    for col in users_sheet.columns:
        users_sheet.column_dimensions[col[0].column_letter].width = 20

    # Сохраняем временный файл
    filename = "export.xlsx"
    wb.save(filename)

    # Отправляем файл пользователю
    with open(filename, "rb") as file:
        await message.answer_document(
            document=types.FSInputFile(filename),
            caption="📊 Экспорт данных из базы"
        )

    # Удаляем временный файл
    import os
    os.remove(filename)


@dp.callback_query(F.data == "photos")
async def photos_handler(callback: types.CallbackQuery):
    """Обработчик кнопки Фото"""
    try:
        await callback.message.edit_text(
            "Выберите раздел фото:",
            reply_markup=photo_sections_kb()
        )
    except:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите раздел фото:",
            reply_markup=photo_sections_kb()
        )
    await callback.answer()


@dp.callback_query(F.data == "photo_sections")
async def photo_sections_handler(callback: types.CallbackQuery):
    """Обработчик возврата к разделам фото"""
    await photos_handler(callback)


@dp.callback_query(F.data.startswith("open_section_"))
async def open_section_handler(callback: types.CallbackQuery):
    """Обработчик открытия раздела фото"""
    data = callback.data.split("_")
    section = data[2]
    photo_index = int(data[3])

    section_data = PHOTO_SECTIONS.get(section)
    if not section_data:
        await callback.answer("Раздел не найден")
        return

    photo_path = os.path.join(section_data["path"], f"{photo_index}.jpg")

    if os.path.exists(photo_path):
        try:
            await callback.message.delete()
        except:
            pass

        with open(photo_path, "rb") as photo_file:
            await callback.message.answer_photo(
                photo=types.FSInputFile(photo_path),
                caption=f"{section_data['name']} ({photo_index}/{section_data['count']})",
                reply_markup=section_photo_navigation_kb(section, photo_index)
            )
    else:
        await callback.answer("Фото не найдено")

    await callback.answer()


@dp.callback_query(F.data.startswith("prev_sec_"))
async def prev_sec_handler(callback: types.CallbackQuery):
    """Обработчик кнопки Назад в разделе фото"""
    data = callback.data.split("_")
    section = data[2]
    photo_index = int(data[3])

    await open_photo_in_section(callback, section, photo_index)


@dp.callback_query(F.data.startswith("next_sec_"))
async def next_sec_handler(callback: types.CallbackQuery):
    """Обработчик кнопки Вперед в разделе фото"""
    data = callback.data.split("_")
    section = data[2]
    photo_index = int(data[3])

    await open_photo_in_section(callback, section, photo_index)


async def open_photo_in_section(callback: types.CallbackQuery, section: str, photo_index: int):
    """Открывает фото в указанном разделе"""
    section_data = PHOTO_SECTIONS.get(section)
    if not section_data:
        await callback.answer("Раздел не найден")
        return

    photo_path = os.path.join(section_data["path"], f"{photo_index}.jpg")

    if os.path.exists(photo_path):
        media = InputMediaPhoto(
            media=types.FSInputFile(photo_path),
            caption=f"{section_data['name']} ({photo_index}/{section_data['count']})"
        )
        await callback.message.edit_media(
            media=media,
            reply_markup=section_photo_navigation_kb(section, photo_index)
        )
    else:
        await callback.answer("Фото не найдено")

    await callback.answer()


async def main() -> None:
    create_tables()
    logging.basicConfig(level=logging.INFO, format='%(filename)s:%(lineno)d %(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')
    logging.info('Starting bot')

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())