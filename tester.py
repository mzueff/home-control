#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Импорт необходимых библиотек
#

import ConfigParser	# Библиотека для работы с файлами конфигурации
import logging		# Библиотека для логирования
import RPIO		# Библиотека RPIO
import os
import sys
from datetime import datetime
import __main__

#
# Пути к необходимым файлам
#

path = os.path.dirname(sys.argv[0])	# Абсолютный путь к корню скрипта
if (path == '.' or path == ''):
    path = os.getcwd()

cfg_path = path+"/conf/"	# Путь к конфигам
log_path = path+"/log/"		# Путь к логам
lib_path = path+"/lib/"		# Путь к собственным библиотекам

cfg_file = cfg_path+"main.conf"	# Основной файл конфигурации

#
# Импорт собственных библиотек
#

sys.path.append(lib_path)	# Включаем в список поиска модулей путь к собственным библиотекам
import gsm			# Библиотека для работы с GSM USB устройством


#
# Читаем конфиг
#

try:
    config = ConfigParser.RawConfigParser()
    config.read(cfg_file)

    cfg = {}

    for section in  config.sections():
	cfg[section] = {}
	for cfg_line in config.items(section):
	    (key,val) = cfg_line
	    if (key.find('_list') >= 0 and val.find(',') >= 0):
		val = val.split(',')
	    cfg[section][key] = val
except Exception, e:
    print "ERROR in cfg %s" %str(e)
    sys.exit()

sms = gsm.sms() # Экземпляр класса работы с SMS
		# Методы: Отправка - sms.send(<phone>,<text>), Прочитать все - sms.recv(), Получить баланс - get_balance()
		# Удалить все: del_all()
# Получаем баланс
#
# Если пришло: -99999
# Значит ошибка при работе с модемом.
#
msgs = sms.recv()

for num, data in msgs[1].items():
    print num, data['text']

balance = sms.get_balance()

if (balance[0] is True and balance[1] != -99999):
    print "%s - %sруб." % (str(balance[2]),str(balance[1]))
else:
    print "Error",balance

