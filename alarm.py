#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import MySQLdb
import time
import threading
from datetime import datetime

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(filename)s:%(lineno)d %(message)s', level = logging.INFO, filename = u'/home/pi/alarm.log')
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
	    db = MySQLdb.connect(host="localhost", user="****", passwd="****", db="****", charset='utf8')
    
	    # формируем курсор, с помощью которого можно исполнять SQL-запросы
	    cursor = db.cursor()
    
	    
	    # Ждем отработку датчика движения
	    while (counter <= 60):
		msg = "mw_wait %s" % str(mw_wait)
		logging.debug(msg)
		# Проверяем флаг датчика движения
		if (mw_wait == 1):
		    # Если да, шлем СМС
		    # Сначала прочитаем полученный баланс
		    sql = u"select ID,TextDecoded from inbox where TextDecoded like '%баланс:%' order by 1 DESC;"
		    cursor.execute(sql)
		    row = cursor.fetchone()

		    cursor.close()
		    cursor = db.cursor()

		    balance =  row[1].split(' ')[2]
		    log_msg = u'Движение через %s сек.' % counter
		    logging.info(log_msg)    		    
		    log_msg = u'Баланс: %s руб.' % balance
		    logging.info(log_msg)    		    
		    # Отправим аларм и баланс
		    sql = u"INSERT INTO outbox ( DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport) \
			    VALUES ( '+7**********', '%s Открыта дверь\nДвижение через %s сек.\n%sруб.', 'Program', 'Unicode_No_Compression', 'yes');" % (str(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M")),counter, balance)
		    cursor.execute(sql)
		    db.commit()
		    # Заодно запросим баланс
		    sql = u"INSERT INTO outbox ( DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport) \
			    VALUES ( '111', '11','Program', 'Unicode_No_Compression', 'yes');"

		    cursor.execute(sql)
		    db.commit()

		    mw_wait = 0
		    msg = "mw_wait %s" % str(mw_wait)
		    logging.debug(msg)
		    break
		#logging.debug(str(counter))
		time.sleep(1)
		counter += 1
	
	    # Если движения не было (для тестов все равно шлем СМСку)
	    if (counter >= 60):
		print counter, "Timeout"
		sql = "INSERT INTO outbox ( DestinationNumber, TextDecoded, CreatorID, Coding, DeliveryReport) \
		    VALUES ( '+7**********', 'Открыта дверь!', 'Program', 'Unicode_No_Compression', 'yes');"
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
