#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import MySQLdb
import time
import threading
from datetime import datetimefrom datetime import datetime

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s', level = logging.INFO, filename = u'/home/pi/alarm.log')
import RPIO # Импортируем библиотеку RPIO
import serial

# Глобальная переменная: флаг отработки датчика движения
mw_wait = 0

def send_sms(gpio_id, value):
    global mw_wait
    mw_wait = 0
    counter = 0
    if (value == 0):
	logging.info(u'Открыта входная дверь!')
	try:
	    # подключаемся к базе данных (не забываем указать кодировку, а то в базу запишутся иероглифы)
	    db = MySQLdb.connect(host="localhost", user="***", passwd="***", db="smsd", charset='utf8')
    
	    # формируем курсор, с помощью которого можно исполнять SQL-запросы
	    cursor = db.cursor()
    
	    
	    # Ждем отработку датчика движения
	    while (counter <= 60):
		msg = "mw_wait %s" % str(mw_wait)
		logging.debug(msg)
		# Проверяем флаг датчика движения
		if (mw_wait == 1):
		    # Если да, шлем СМС
		    sql = "INSERT INTO outbox ( DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport) \
			    VALUES ( '+79049155555', '%s Открыта входная дверь!\nЗафиксированно движение через %s сек.', 'Program', 'Unicode_No_Compression', 'yes');" % (str(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")),counter)
		    
		    cursor.execute(sql)
		    db.commit()
		    mw_wait = 0
		    log_msg = u'Движение зафиксированно через %s секунд!' % counter
		    logging.info(log_msg)
		    msg = "mw_wait %s" % str(mw_wait)
		    logging.debug(msg)
		    break
		logging.debug(str(counter))
		time.sleep(1)
		counter += 1
	
	    # Если движения не было (для тестов все равно шлем СМСку)
	    if (counter >= 60):
		print counter, "Timeout"
		sql = "INSERT INTO outbox ( DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport) \
		    VALUES ( '+79049155555', 'Открыта входная дверь!', 'Program', 'Unicode_No_Compression', 'yes');"
		# cursor.execute(sql)
		# db.commit()

	    # применяем изменения к базе данных
	    #db.commit()

	    # закрываем соединение с базой данных
	    db.close()
	except Exception, e:
	    db.close()
	    logging.error(str(e))


def send_mwave(gpio_id, value):
    global mw_wait
    try:
	if (value == 0):
	    mw_wait = 1
	    log_msg = u'Microwave sensor gpio_id: %s, value: %s' % (gpio_id, value)
	    logging.debug(log_msg)
	return True
    except Exception, e:
	logging.error(str(e))
	return False

RPIO.setup(23, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)
RPIO.setup(24, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)
RPIO.setup(25, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)
#send_text()

RPIO.add_interrupt_callback(24, send_sms,pull_up_down=RPIO.PUD_DOWN, threaded_callback=True, debounce_timeout_ms=500) #Добавляем прерывание, с подтяжкой к земле и подавлением дребезга контактов
RPIO.add_interrupt_callback(25, send_mwave,pull_up_down=RPIO.PUD_DOWN,threaded_callback=True, debounce_timeout_ms=500) #Добавляем прерывание, с подтяжкой к земле и подавлением дребезга контактов

RPIO.wait_for_interrupts() # Запускаем ожидание прерываний
