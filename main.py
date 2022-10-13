import asyncio
import logging
import datetime
from datetime import timedelta
import random
from sys import flags


#aiogram и всё утилиты для коректной работы с Telegram API
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.utils.emoji import emojize
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

#конфиг с настройками
import config
#кастомные ответы
import custom_answer as cus_ans
from database import dbworker
import os.path


#задаём логи
logging.basicConfig(level=logging.INFO)

chatID = 0
last_pers_id = 0


#инициализируем бота
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot,storage=MemoryStorage())

#инициализируем базу данных
db = dbworker('database.db')

#хендлер команды /start
@dp.message_handler(commands=['start'],state='*')
async def start(message : types.Message):
	#кнопки для волшебного входа
	button_start = KeyboardButton('Начать коллаборацию🌀')

	magic_start = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

	magic_start.add(button_start)
	await message.answer('Привет👋\n\nC вами CoLabBot🧑‍💻\nМы поможем вам найти интересных людей из различных сфер\n\nCoLabBot - это место для : \n 🕺💃🏼коллабораций\n 👨🏻‍🎨👩‍💻полезных знакомств\n 👩‍💼🧑‍💼общения\n и тд.',reply_markup=magic_start)
	await message.answer_sticker('CAACAgIAAxkBAAEGDOtjQ-dXYqyNC63YM4VHDdVZqcyw1wACIwADfoTDCB9Wh2bqIorCKgQ')
	chatID = message.chat.id
	print(message.chat.id)
	if(not db.user_exists(message.from_user.id)):
		#если юзера нет в базе добавляем его
		db.add_user(message.from_user.username,message.from_user.id,message.from_user.full_name)
		#await bot.send_message(-1001406772763,f'Новый пользователь!\nID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}')
#хендлер для команды Зайти в волшебный мир


@dp.message_handler(lambda message: message.text == 'Начать коллаборацию🌀' or message.text == '/magic_start',state='*')
async def magic_start(message : types.Message):
	'''Функция для меню самого бота'''
	#await send_log(message)
	#кнопки меню
	button_search = KeyboardButton('Поиск🔍')

	button_create_profile = KeyboardButton('Создать анкету📌')

	button_edit_profile = KeyboardButton('Редактировать анкету📝')

	button_remove_profile = KeyboardButton('Удалить🗑')

	button_admin = KeyboardButton('Админка⚙️')

	menu = ReplyKeyboardMarkup(resize_keyboard=True)

	if(not db.profile_exists(message.from_user.id)):
			menu.row(button_search,button_create_profile)
	elif(db.profile_exists(message.from_user.id)) :
		menu.row(button_search)
		menu.row(button_edit_profile)
		menu.row(button_remove_profile)
	#if message.from_user.id in config.ADMIN_LIST:
	#	menu.add(button_admin)
	await message.answer('Это центральный компьютер чат бота🤖\n\nТут ты можешь управлять всеми этими кнопками внизу⚙️',reply_markup=menu)


#хендлер для создания анкеты


class CreateProfile(StatesGroup):
	name = State()
	description = State()
	tags = State()
	city = State()
	photo = State()
	sex = State()
	age = State()
	social_link	 = State()
#хендлер старта для создания анкеты
@dp.message_handler(lambda message: message.text == 'Создать анкету📌',state='*')
async def create_profile(message : types.Message):
	#кнопки отмены
	button_exit = KeyboardButton('Выйти❌')

	menu_exit = ReplyKeyboardMarkup(resize_keyboard=True)

	menu_exit.add(button_exit)

	if message.from_user.username != None:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer("Для того что бы создать анкету нужно заполнить несколько пунктов\nДавайте начнём с имени, как тебя зовут?😉",reply_markup=menu_exit)
			await CreateProfile.name.set()
		elif(db.profile_exists(message.from_user.id)) :
			await message.answer('У тебя уже есть активная анкета\n\n')
	else:
		await message.answer('‼️У вас не заполнен username в телеграм!\n\nПожалуйста сделайте это для коректного функционирования бота\nДля этого зайдите в настройки -> Edit Profile(Изменить профиль) и нажмите add username\n\nТам введите желаемый никнейм')
#хендлер для заполнения имя
@dp.message_handler(state=CreateProfile.name)
async def create_profile_name(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(str(message.text)) < 35:
		await state.update_data(profile_name=message.text.lower())
		await message.reply(message.text.title() + ' - прекрасное имя)\n\nТеперь заполни описание своей личности что бы все поняли кто же ты')
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('У тебя какое-то больно длинное имя, попробуй по другому')
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return

#хендлер для заполнение описания

@dp.message_handler(state=CreateProfile.description)
async def create_profile_description(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(message.text) < 235 and (not str(message.text) in cus_ans.ban_symvols):
		await state.update_data(profile_description=message.text)
		#keyboard = types.InlineKeyboardMarkup(row_width=1)
		#keyboard.add(types.InlineKeyboardButton(text="Ссылка на соц.сети", )
		await message.answer('Неплохо,неплохо\n\nТеперь через пробел укажи теги, оисывающие твой род деятельности\nНапример: #театртабакова #lambprod #актер')
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('Слишком длинное описание')
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return


#хендлер для заполнение тегов

@dp.message_handler(state=CreateProfile.tags)
async def create_profile_tags(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	tags_for_check = message.text.split(" #")
	flag = True
	if len(tags_for_check) > 0 and tags_for_check[0].find("#") == 0:
		tags_for_check[0] = tags_for_check[0].replace("#", "")
	else:
		flag = False
		await message.answer('Теги заполнены неправильно\nПопробуй еще раз и обрати внимание на пример #театртабакова #lambprod #актер')
	if flag == True:
		print(tags_for_check)
		for i in range(len(tags_for_check)):
			if (tags_for_check[i].find('#') != -1 or tags_for_check[i].find(' ') != -1):
				flag = False
				await message.answer('Теги заполнены неправильно\nПример: #театртабакова #lambprod #актер')
				break
		if (flag):
			if len(message.text) < 35 and (not str(message.text) in cus_ans.ban_symvols):
				res = '#' + ' #'.join(tags_for_check)
				
				await state.update_data(profile_tags=res)
				await message.answer('Неплохо,неплохо\n\nТеперь введите ваш город')
				await CreateProfile.next()
			elif str(message.text) in cus_ans.ban_symvols:
				await message.answer('У тебя в сообщении запрещённые символы(\nЗапятая к примеру')
			else:
				await message.answer(cus_ans.random_reapeat_list())
				#прерывание функции
				return

#хендлер для заполнения города
@dp.message_handler(state=CreateProfile.city)
async def create_profile_city(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(message.text) < 35 and (not str(message.text) in cus_ans.ban_symvols):
		await state.update_data(profile_city=message.text.lower())
		await message.answer('Прелестно, теперь давай добавим фото🖼')
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('У тебя в сообщении запрещённые символы(\nЗапятая к примеру')
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return
#хендлер для заполнения фотографии
@dp.message_handler(state=CreateProfile.photo,content_types=['photo'])
async def create_profile_photo(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)

	#кнопки выбора пола
	button_male = KeyboardButton('Мужчина')

	button_wooman = KeyboardButton('Женщина')

	sex_input = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
	sex_input.add(button_male,button_wooman)

	await message.photo[-1].download('photo_user/' + str(message.from_user.id) + '.jpg')
	await message.answer('Замечательно)\n\nОсталось совсем немного,укажи свой пол',reply_markup=sex_input)
	await CreateProfile.next()
#хендлер для заполнения пола
@dp.message_handler(state=CreateProfile.sex)
async def create_profile_sex(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if message.text == 'Мужчина' or message.text == 'Женщина':
		await state.update_data(profile_sex=message.text.lower())
		await message.answer('Замечательно!\nОсталось совсем чуть-чуть\n\nДавай же узнаем твой возвраст')
		await CreateProfile.next()
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции 
		return

#хендлер для заполнения возвраста
@dp.message_handler(state=CreateProfile.age)
async def create_profile_age(message: types.Message, state: FSMContext):
	try:
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return
		if int(message.text) < 12:
			await message.answer('ой🤭\nЧто-то ты маловат...')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 90:
			await message.answer('Ничего себе, не врете?👨‍')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 12 and int(message.text) < 90:
			await state.update_data(profile_age=message.text)
			#кнопки меню
			button_skip = KeyboardButton('Пропустить')

			skip_input = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
			skip_input.add(button_skip)
			await message.answer('Отлично!\nПоследний шаг - указать ссылку на любую свою социальную сеть\nЕсли нет желания - можно пропустить➡🔜',reply_markup=skip_input)
			await CreateProfile.next()
		else:
			#await answer.message('Укажи правильный возраст, только цифры')
			return
	except:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return
#хендлер для заполнения ссылки на социальную сеть
@dp.message_handler(state=CreateProfile.social_link)
async def create_profile_social_link(message: types.Message, state: FSMContext):
	try:
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return
		if str(message.text) == 'Пропустить':
			await message.answer('Анкета успешно создана!')
			user_data = await state.get_data()
			db.create_profile(message.from_user.id,message.from_user.username,str(user_data['profile_name']),str(user_data['profile_description']),str(user_data['profile_city']),'photo/' + str(message.from_user.id) + '.jpg',str(user_data['profile_sex']),str(user_data['profile_age']),None, str(user_data['profile_tags'])) #self,telegram_id,telegram_username,name,description,city,photo,sex,age,social_link
			await state.finish()
			await magic_start(message)
		elif str(message.text).startswith('https://'):
			await state.update_data(profile_link=message.text)
			await message.answer('Анкета успешно создана!')
			user_data = await state.get_data()
			db.create_profile(message.from_user.id,message.from_user.username,str(user_data['profile_name']),str(user_data['profile_description']),str(user_data['profile_city']),'photo/' + str(message.from_user.id) + '.jpg',str(user_data['profile_sex']),str(user_data['profile_age']),str(user_data['profile_link']), str(user_data['profile_tags'])) #self,telegram_id,telegram_username,name,description,city,photo,sex,age,social_link
			await state.finish()
			await magic_start(message)
		else :
			await message.answer('Ссылка не корректна!\n\nОна должна начинаться с https://\n\nК примеру - https://www.instagram.com/chepush1nka/')
			return


	except:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return

#хендлер для удаления анкеты
@dp.message_handler(lambda message: message.text == 'Удалить🗑')
async def delete_profile(message : types.Message):
	'''Функция для удаления анкеты'''
	#await send_log(message)
	try:
		db.delete_profile(message.from_user.id)
		await message.answer('Анкета успешно удалена!')
		await magic_start(message)
	except:
		await message.answer(cus_ans.random_reapeat_list())
		return

#хендлер для редактирования анкеты
@dp.message_handler(lambda message: message.text == 'Редактировать анкету📝')
async def edit_profile(message : types.Message):
	'''Функция для меню редактирования анкеты'''
	#await send_log(message)
	try:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer('У тебя нет анкеты!')
		elif(db.profile_exists(message.from_user.id)) :
			photo = open('photo_user/' + str(message.from_user.id) + '.jpg','rb')
			#кнопки выбора пола
			button_again = KeyboardButton('Заполнить анкету заново')

			button_edit_photo = KeyboardButton('Изменить фото')

			button_edit_description = KeyboardButton('Изменить описание анкеты')

			button_edit_age = KeyboardButton('Изменить возраст')

			button_edit_tags = KeyboardButton('Изменить теги')

			button_cancel = KeyboardButton('Выйти')

			edit_profile = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
			edit_profile.row(button_again)
			edit_profile.row(button_edit_photo)
			edit_profile.row(button_edit_description)
			edit_profile.row(button_edit_age)
			edit_profile.row(button_edit_tags)
			edit_profile.row(button_cancel)
			#print(db.all_profile(str(message.from_user.id))[0])
			tg_id, tg_username, name, description, city, ph, sex, age, social_link, rating, tags = db.all_profile(str(message.from_user.id))[0]
			caption = str(tags) + '\n' + str(name).title() + ', ' + str(age) + ', ' + str(city).title() +'\n\n' + str(description)
			await message.answer_photo(photo,caption=caption,reply_markup=edit_profile)
			await message.answer('Твоя анкета',reply_markup=edit_profile)
			photo.close()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

#хендлер для заполнения анкеты заново
@dp.message_handler(lambda message: message.text == 'Заполнить анкету заново')
async def edit_profile_again(message : types.Message):
	'''Функция для заполнения анкеты заново'''
	#await send_log(message)
	try:
		db.delete_profile(message.from_user.id)
		await create_profile(message)

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

#класс машины состояний FSM
class EditProfile(StatesGroup):
	description_edit = State()
	age_edit = State()
	tags_edit = State()
	photo_edit = State()

#хендлеры для изменение возвраста и описания анкеты

@dp.message_handler(lambda message: message.text == 'Изменить возраст' or message.text == 'Изменить описание анкеты' or message.text == 'Изменить теги' or message.text == 'Изменить фото')
async def edit_profile_age(message : types.Message):
	try:
		#кнопки для отмены
		button_cancel = KeyboardButton('Отменить')

		button_cancel_menu = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

		button_cancel_menu.add(button_cancel)

		if message.text == 'Изменить возраст':
			await message.answer('Введи свой новый возвраст',reply_markup=button_cancel_menu)
			await EditProfile.age_edit.set()
		elif message.text == 'Изменить описание анкеты':
			await message.answer('Введи новое описание своей анкеты!',reply_markup=button_cancel_menu)
			await EditProfile.description_edit.set()
		elif message.text == 'Изменить теги':
			await message.answer('Введи новые теги',reply_markup=button_cancel_menu)
			await EditProfile.tags_edit.set()
		elif message.text == 'Изменить фото':
			await message.answer('Пришли новое фото',reply_markup=button_cancel_menu)
			await EditProfile.photo_edit.set()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return
@dp.message_handler(state=EditProfile.age_edit)
async def edit_profile_age_step2(message: types.Message, state: FSMContext):
	'''Функция для обновления возвраста в бд'''
	#await send_log(message)
	try:
		if str(message.text) == 'Отменить':
			await state.finish()
			await magic_start(message)

			return
		elif int(message.text) < 12:
			await message.answer('ой🤭\nТы чёт маловат...')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 90:
			await message.answer('Больно вы взрослый человек👨‍')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 12 and int(message.text) < 90:
			await message.answer('Бом Бом🤗\n\nВозвраст успешно измененён!')
			await state.update_data(edit_profile_age=message.text)
			user_data = await state.get_data()

			db.edit_age(user_data['edit_profile_age'],str(message.from_user.id))
			await state.finish()
			await edit_profile(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return
@dp.message_handler(state=EditProfile.description_edit)
async def edit_profile_description(message: types.Message, state: FSMContext):
	'''Функция для обновления описания в бд'''
	#await send_log(message)
	try:
		if str(message.text) == 'Отменить':
			await state.finish()
			await magic_start(message)
			return
		if len(message.text) < 235 and (not str(message.text) in cus_ans.ban_symvols):
			await state.update_data(edit_profile_description=message.text)
		elif str(message.text) in cus_ans.ban_symvols:
			await message.answer('Слишком длинное описание')
		else:
			await message.answer(cus_ans.random_reapeat_list())
			#прерывание функции
			await state.finish()
			await magic_start(message)
			return
		await message.answer('Прекрасное описание\n\nОписание успешно изменено!')
		user_data = await state.get_data()

		db.edit_description(user_data['edit_profile_description'],str(message.from_user.id))
		await state.finish()
		await edit_profile(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await magic_start(message)
		print(e)
		return

@dp.message_handler(state=EditProfile.tags_edit)
async def edit_profile_description(message: types.Message, state: FSMContext):
	'''Функция для обновления описания в бд'''
	#await send_log(message)
	try:
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return
		tags_for_check = message.text.split(" #")
		flag = True
		res = ""
		if len(tags_for_check) > 0 and tags_for_check[0].find("#") == 0:
			tags_for_check[0] = tags_for_check[0].replace("#", "")
		else:
			flag = False
			await message.answer('Теги заполнены неправильно\nПопробуй еще раз и обрати внимание на пример #театртабакова #lambprod #актер')
		if flag == True:
			print(tags_for_check)
			for i in range(len(tags_for_check)):
				if (tags_for_check[i].find('#') != -1 or tags_for_check[i].find(' ') != -1):
					flag = False
					await message.answer('Теги заполнены неправильно\nПример: #театртабакова #lambprod #актер')
					break
			if (flag):
				if len(message.text) < 35 and (not str(message.text) in cus_ans.ban_symvols):
					res = '#' + ' #'.join(tags_for_check)
				
				elif str(message.text) in cus_ans.ban_symvols:
					await message.answer('У тебя в сообщении запрещённые символы(\nЗапятая к примеру')
				else:
					await message.answer(cus_ans.random_reapeat_list())
					#прерывание функции
					return
			db.edit_tags(res,str(message.from_user.id))
			await state.finish()
			await edit_profile(message)

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await magic_start(message)
		print(e)
		return

@dp.message_handler(state=EditProfile.photo_edit, content_types=['photo'])
async def edit_profile_photo(message: types.Message, state: FSMContext):
	'''Функция для обновления описания в бд'''
	#await send_log(message)
	try:
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return

		await message.photo[-1].download('photo_user/' + str(message.from_user.id) + '.jpg')
		res = 'photo/' + str(message.from_user.id) + '.jpg'		
		db.edit_photo(res,str(message.from_user.id))
		await state.finish()
		await edit_profile(message)

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await magic_start(message)
		print(e)
		return

@dp.message_handler(lambda message: message.text == 'Выйти')
async def exit(message : types.Message):
	await magic_start(message)



#класс машины состояний FSM
class SearchProfile(StatesGroup):
	"""City Choose"""
	city_choose = State()
	"""City Choose"""
	city_search = State()
	in_doing = State()

#хендлеры для поиска по анкетам
@dp.message_handler(lambda message: message.text == 'Поиск🔍')
async def search_profile(message : types.Message):
	'''Функция для ввода пользователя своего города,последующей записи в бд'''
	#await send_log(message)
	try:
		if db.profile_exists(message.from_user.id) == False:
			await message.answer('У тебя нет анкеты, заполни её и переходи к поиску')
		elif db.get_info_user(str(message.from_user.id))[3] != "None":
			button_city = KeyboardButton(str(db.get_info_user(str(message.from_user.id))[3]).title())
			button_another_city = KeyboardButton('Выбрать другой город')
			button_exit = KeyboardButton('Главное меню')
			
			mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)

			mark_menu.row(button_city, button_another_city)
			mark_menu.row(button_exit)

			await message.answer('Выбери город для поиска:', reply_markup=mark_menu)
			await SearchProfile.city_search.set()
		else:
			await message.answer('Введи название города:')
			#print(db.set_city_search_slava("москва")[1])
			await SearchProfile.city_search.set()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		#await state.finish()
		print(e)
		return


@dp.message_handler(state=SearchProfile.city_search)
async def seach_profile_step2(message: types.Message, state: FSMContext):
	'''Функция поиска анкет после отправки пользователя своего города'''
	#await send_log(message)
	try:
		if message.text == 'Выбрать другой город':
			await message.answer('Введи название города:')
			return
		if message.text == 'Главное меню':
			await magic_start(message)
			await state.finish()
			return
		await state.update_data(search_profile_city=message.text.lower())
		await state.update_data(last_profile_id="1")

		user_data = await state.get_data()
		print(user_data)

		db.set_city_search(str(user_data['search_profile_city']),str(message.from_user.id))
		search_users_count = len(db.search_profile(str(db.get_info_user(str(message.from_user.id))[3])))
		if (bool(search_users_count)):
			profile_id = message.from_user.id
			count = 0
			while profile_id == message.from_user.id or db.add_like_exists(str(message.from_user.id),profile_id) == True or db.add_dislike_exists(str(message.from_user.id), profile_id) == True or db.report_exists(str(message.from_user.id), profile_id) == True:
				try:
					pr = db.search_profile(str(db.get_info_user(str(message.from_user.id))[3]))
					profile_id = pr[db.search_profile_status(str(message.from_user.id))[0]][0]
				except:
					db.edit_zero_profile_status(message.from_user.id)
					profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[3]))[db.search_profile_status(str(message.from_user.id))[0]][0]
				await state.update_data(last_profile_id=profile_id)
				print(db.search_profile_status(str(message.from_user.id)))
				db.edit_profile_status(str(message.from_user.id),db.search_profile_status(str(message.from_user.id))[0])
				print(len(db.search_profile(str(db.get_info_user(str(message.from_user.id))[3]))))
				if len(pr) < count:
					await message.answer('В этом городе закончились анкеты(')
					await magic_start(message)
					await state.finish()
					return
				count += 1
			print(db.add_like_exists(str(message.from_user.id),profile_id))
			print('up')
			#кнопки для оценки
			button_like = KeyboardButton('👍')

			button_dislike = KeyboardButton('👎')

			button_other = KeyboardButton('Откат действий◀️')

			button_exit = KeyboardButton('Выход')

			button_report = KeyboardButton('Репорт👺')

			mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)

			mark_menu.add(button_dislike,button_like,button_report,button_other, button_exit)

			city = str(user_data['search_profile_city']).title()

			keyboard = types.InlineKeyboardMarkup(row_width=1)
			final_text_profile, keyboard = profileGen(message, profile_id, keyboard)

			photo_profile = open('photo_user/' + str(profile_id) + '.jpg','rb')
			await message.answer_photo(photo_profile,caption=final_text_profile,reply_markup=mark_menu)


			await SearchProfile.next()
		else:
			await message.answer('Такого города нет или там нет анкет :(')
	except Exception as e:
		print('mama')
		await message.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)

def profileGen(message: types.Message, profile_id: str, keyboard: types.InlineKeyboardMarkup):
	try:
		x, y, name_profile, description_profile, city_profile, photo_profile, sex_profile, age_profile, social_link_profile, rating_oc_profile, tags_profile = db.get_info(profile_id)
		if str(social_link_profile) != "None":
			keyboard.add(types.InlineKeyboardButton(text="Ссылка на соц.сети", url=str(social_link_profile)))
		photo_profile = open('photo_user/' + str(profile_id) + '.jpg','rb')
		final_text_profile = str(tags_profile)  + '\n' + str(name_profile ).title() + ', ' + str(age_profile ) + ', ' + str(city_profile).title() +'\n\n' + str(description_profile)

		return final_text_profile, keyboard
	except Exception as e:
		message.answer(cus_ans.random_reapeat_list())
		magic_start(message)
		print(e)


@dp.message_handler(state=SearchProfile.in_doing)
async def seach_profile_step3(message: types.Message, state: FSMContext):
	'''Функция поиска анкет после отправки пользователя своей оценки(лайк,дизлайк,репорт)'''
	#await send_log(message)
	global last_pers_id
	try:
		user_data = await state.get_data()
		print(user_data)
		if str(message.text) == '👍':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)
			db.add_like(str(message.from_user.id),user_data['last_profile_id'])
			last_pers_id = user_data['last_profile_id']

			if db.add_like_exists(user_data['last_profile_id'], str(message.from_user.id)) == True:
				x, y, name_profile_self, description_profile_self, city_profile, photo_profile, sex_profile, age_profile_self, social_link_profile_self, rating_oc_profile, tags_profile  = db.get_info(str(message.from_user.id))
				keyboard_self = types.InlineKeyboardMarkup(row_width=1)
				if str(social_link_profile_self) != "None":
					keyboard_self.add(types.InlineKeyboardButton(text="Ссылка на соц.сети", url=str(social_link_profile_self)))
				photo_profile_self = open('photo_user/' + str(message.from_user.id) + '.jpg','rb')
				final_text_profile_self = f'Тобой кто то заинтересовался!{tags_profile}\n{name_profile_self}, {age_profile_self}, {city_profile}\n\n{description_profile_self}\n\nЧего ты ждёшь,беги знакомиться - @{str(message.from_user.username)}'
				await bot.send_photo(user_data['last_profile_id'],photo_profile_self,caption=final_text_profile_self, reply_markup=keyboard_self)

				xq, yq, name_profile_selfq, description_profile_selfq, city_profileq, photo_profileq, sex_profileq, age_profile_selfq, social_link_profile_selfq, rating_oc_profileq, tags_profileq  = db.get_info(str(user_data['last_profile_id']))
				keyboard_selfq = types.InlineKeyboardMarkup(row_width=1)
				last_pr = str(user_data['last_profile_id'])
				if str(social_link_profile_selfq) != "None":
					keyboard_selfq.add(types.InlineKeyboardButton(text="Ссылка на соц.сети", url=str(social_link_profile_selfq)))
				photo_profile_selfq = open('photo_user/' + last_pr + '.jpg','rb')
				final_text_profile_selfq = f'Тобой кто то заинтересовался!{tags_profileq}\n{name_profile_selfq}, {age_profile_selfq}, {city_profileq}\n\n{description_profile_selfq}\n\nЧего ты ждёшь,беги знакомиться - @{yq}'
				await bot.send_photo(message.from_user.id,photo_profile_selfq,caption=final_text_profile_selfq, reply_markup=keyboard_selfq)

			#return
			#await state.finish()
		elif str(message.text) == '👎':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)
			db.add_dislike(str(message.from_user.id),user_data['last_profile_id'])
			last_pers_id = user_data['last_profile_id']


		elif str(message.text) == 'Репорт👺':

			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)
			last_pers_id = user_data['last_profile_id']

			user_data = await state.get_data()

			if(db.report_exists(str(message.from_user.id),user_data['last_profile_id']) == False):
				db.throw_report(str(message.from_user.id),user_data['last_profile_id'])
				await message.answer('Репорт отправлен!\nСпасибо за улучшение комьюнити🥰')
			else:
				await message.answer('У вас уже есть репорт на данную анкету!\nЧёж вы его так хейтите..😦')

		elif str(message.text) == 'Выход':
			await magic_start(message)
			await state.finish()
			return
		elif str(message.text) == 'Откат действий◀️':
			print(last_pers_id)
			button_backup1 = KeyboardButton('Репорт👺')
			button_backup2 = KeyboardButton('Репорт👺')

			if db.add_like_exists(str(message.from_user.id), last_pers_id) == True:
				button_backup1 = KeyboardButton('Поставить 👎 последней анкете')
				button_backup2 = KeyboardButton('Отправить жалобу на последнюю анкету')
			elif db.add_dislike_exists(str(message.from_user.id), last_pers_id) == True:
				button_backup1 = KeyboardButton('Поставить 👍 последней анкете')
				button_backup2 = KeyboardButton('Отправить жалобу на последнюю анкету')
			elif db.report_exists(str(message.from_user.id), last_pers_id) == True:
				button_backup1 = KeyboardButton('Поставить 👍 последней анкете')
				button_backup2 = KeyboardButton('Поставить 👎 последней анкете')
			else:
				await message.answer('Что-то пошло не так, вы точно уже ставили оценки в режиме поиска?')
				await magic_start(message)
				return

			mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)

			mark_menu.row(button_backup1)
			mark_menu.row(button_backup2)
			await message.answer('Часто бывает, что в потоке скучных анкет натыкаешься на “самородок”, но случайно нажимаешь не туда.\n\nС помощью этой функции ты сможешь изменить выбор для последней анкеты\nВыбери действие ниже:', reply_markup=mark_menu)
			await message.answer_sticker('CAACAgIAAxkBAAEGDY9jREiXfhy8Rrqi3DJOdCq07TsUDQACDAADfoTDCI2t04V9AQSVKgQ')
			await state.finish()
			await Backup.step1.set()
			return
		else:
			await state.finish()
			await magic_start(message)

		profile_id = message.from_user.id
		count = 0
		while profile_id == message.from_user.id or db.add_like_exists(str(message.from_user.id), profile_id) == True or db.add_dislike_exists(str(message.from_user.id), profile_id) == True or db.report_exists(str(message.from_user.id), profile_id) == True:
			pr = []
			try:
				pr = db.search_profile(str(db.get_info_user(str(message.from_user.id))[3]))
				profile_id = pr[db.search_profile_status(str(message.from_user.id))[0]][0]
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[3]))[db.search_profile_status(str(message.from_user.id))[0]][0]
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)
			await state.update_data(last_profile_id=profile_id)
			db.edit_profile_status(str(message.from_user.id),db.search_profile_status(str(message.from_user.id))[0])
			if (count > len(pr) + 1):
				await message.answer('В этом городе закончились анкеты((')
				await magic_start(message)
				await state.finish()
				return
			count += 1

		city = str(user_data['search_profile_city']).title()

		keyboard = types.InlineKeyboardMarkup(row_width=1)
		final_text_profile, keyboard = profileGen(message, profile_id, keyboard)
		photo_profile = open('photo_user/' + str(profile_id) + '.jpg','rb')
		await message.answer_photo(photo_profile,caption=final_text_profile, reply_markup=keyboard)	

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return

#хендлер для рейтинга анкет

@dp.message_handler(lambda message: message.text == 'Рейтинг анкет⭐️',state='*')
async def rating_profile(message : types.Message):
	'''Возвращает рейтинг анкет'''
	#await send_log(message)
	try:
		final_top = ''
		top_count = 0
		for i in db.top_rating():
			for d in i:
				top_count +=1
				rofl_list = ['\#ь ты жёсткий😳','\nвасап👋','\nбро полегче там😮','\nгений🧠','\nреспект🤟']
				final_top = final_top + str(top_count) + ' место - ' + str(db.get_info(str(d))[3]).title() + ' из города ' + str(db.get_info(str(d))[5]).title() +  rofl_list[top_count-1] + '\n'
		await message.answer(f'Рейтинг самых популярных в этом чат боте😎\nОчки рейтинга получаются с помощью активностей\n\n{final_top}')
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)

#админка
@dp.message_handler(lambda message: message.text == 'Админка⚙️')
async def admin(message : types.Message):
	if message.from_user.id in config.ADMIN_LIST:

		await message.answer('Для отправки сообщений нужно написать /sendmsg_admin,user_id,msg')
	else:
		await message.answer('Отказано в доступе')

@dp.message_handler(lambda message: message.text.startswith('/sendmsg_admin'),state='*')
async def admin_send_msg(message : types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		msg = message.text.split(',')
		await bot.send_message(msg[1],msg[2])
		await message.answer('')
	else:
		await message.answer('Отказано в доступе')

#хендлер всячины
@dp.message_handler(lambda message: message.text == 'Другое')
async def other(message : types.Message):
	'''Функция срабатывает при нажатии на кнопку всячина'''
	#await send_log(message)
	#кнопки для всякой всячины

	button_backup = KeyboardButton('Откат действия◀️')

	button_exit = KeyboardButton('Выйти')

	menu_other = ReplyKeyboardMarkup(resize_keyboard=True)

	menu_other.add(button_exit,button_backup)
	await message.answer('Тут так же можно выполнить несколько хитрых и не очень махинаций',reply_markup=menu_other)


#класс машины состояний FSM для отката действий
class Backup(StatesGroup):
	step1 = State()

#хендлер отката действий
@dp.message_handler(lambda message: message.text == 'Откат действия◀️')
async def backup(message : types.Message):
	print(last_pers_id)
	#await send_log(message)
	print('PHD')
	button_backup1 = KeyboardButton('Репорт👺')
	button_backup2 = KeyboardButton('Репорт👺')

	if db.add_like_exists(str(message.from_user.id), last_pers_id) == True:
		button_backup1 = KeyboardButton('Поставить дизлайк последней анкете')
		button_backup2 = KeyboardButton('Отправить жалобу на последнюю анкету')
	elif db.add_dislike_exists(str(message.from_user.id), last_pers_id) == True:
		button_backup1 = KeyboardButton('Поставить лайк последней анкете')
		button_backup2 = KeyboardButton('Отправить жалобу на последнюю анкету')
	elif db.report_exists(str(message.from_user.id), last_pers_id) == True:
		button_backup1 = KeyboardButton('Поставить лайк последней анкете')
		button_backup2 = KeyboardButton('Поставить дизлайк последней анкете')
	else:
		await message.answer('Что-то пошло не так, вы точно уже ставили оценки при поиске?')
		await magic_start(message)
		return

	mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)

	mark_menu.add(button_backup1, button_backup2)

	await message.answer('Часто бывает, что в потоке скучных анкет натыкаешься на “самородок”, но случайно нажимаешь не туда.\n\nС помощью этой функции ты сможешь изменить выбор для последней анкеты\nВыбери действие ниже:')
	await message.answer_sticker('CAACAgIAAxkBAAEGDY9jREiXfhy8Rrqi3DJOdCq07TsUDQACDAADfoTDCI2t04V9AQSVKgQ')
	await Backup.step1.set()

@dp.message_handler(state=Backup.step1)
async def backup_step1(message: types.Message, state: FSMContext):
	#await send_log(message)
	try:
		if  str(message.text) == 'Поставить 👍 последней анкете':
			if (db.add_dislike_exists(str(message.from_user.id), last_pers_id)):
				db.delete_dislike(str(message.from_user.id), last_pers_id)
			if db.report_exists(str(message.from_user.id), last_pers_id):
				db.delete_report(str(message.from_user.id), last_pers_id)
			db.add_like(str(message.from_user.id), last_pers_id)
		elif str(message.text) == 'Поставить 👎 последней анкете':
			if (db.add_like_exists(str(message.from_user.id), last_pers_id)):
				db.delete_like(str(message.from_user.id), last_pers_id)
			if db.report_exists(str(message.from_user.id), last_pers_id):
				db.delete_report(str(message.from_user.id), last_pers_id)
			db.add_dislike(str(message.from_user.id), last_pers_id)
		elif str(message.text) == 'Отправить жалобу на последнюю анкету':
			if (db.add_dislike_exists(str(message.from_user.id), last_pers_id)):
				db.delete_dislike(str(message.from_user.id), last_pers_id)
			if (db.add_like_exists(str(message.from_user.id), last_pers_id)):
				db.delete_like(str(message.from_user.id), last_pers_id)
			db.throw_report(str(message.from_user.id), last_pers_id)
		else:
			await message.answer('Что-то пошло не так, вы точно уже ставили оценки в режиме поиска??')
			await magic_start(message)
			await state.finish()
			return
		await message.answer('Готово!')
		await magic_start(message)
		await state.finish()
		return
	except Exception as e:
		await message.answer('Я не смогу обработать данную анкету')
		print(e)
		await state.finish()
		return


#хендлер который срабатывает при непредсказуемом запросе юзера
@dp.message_handler()
async def end(message : types.Message):
	'''Функция непредсказумогого ответа'''
	await message.answer('Я не знаю, что с этим делать 😲\nЯ просто напомню, что есть команда /start \nВсе твои данные сохранятся)',parse_mode=ParseMode.MARKDOWN)
	#await send_log(message)

#@dp.message_handler(state='*')
##async def send_log(message : types.Message):
	#await bot.send_message(-1001406772763,f'ID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')


executor.start_polling(dp, skip_updates=True)
