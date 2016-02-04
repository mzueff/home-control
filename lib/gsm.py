#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Импорт необходимых библиотек
#
from datetime import datetime
import re
import serial		# Библиотека для работы с компортами
import binascii		# Библиотека для кодировки/раскодировки текстов смс в/из UCS2 кодировки
import __main__		# Импортируем пространство имен из основного скрипта

class sms:
    def __init__(self):
	self.device =  __main__.cfg['devices']['gsm_dongle']
	self.d = re.compile('[^-\d]')

    def send(self, num = None, text = None):
	if (num is None):
	    num = __main__.cfg['contacts']['alarm_sms']
	
	try:
	    ser = serial.Serial(self.device, timeout=1)
	except Exception, e:
	    log_msg = "ERROR open port: %s. MSG: %s" % (str(self.device), str(e))
	    return False, log_msg
	try:
	    # Переведем модем в режим СМС
	    ser.write('AT+CMGF=%d\r' % 1)
	
	    # Установим номер для отсылки
	    ser.write('AT+CMGS="%s"\r' % num)

	    # Отправим сообщение
    	    ser.write('%s\x1a' % text)

	    log_msg = ' '.join(' '.join(ser.readlines()).split())
	    #logging.debug(log_msg)
	
	    ser.close()
	    return True, log_msg

	except Exception, e:
	    log_msg = "ERROR write to port: %s. MSG: %s" % (str(self.device), str(' '.join(' '.join(e).split())))
	    ser.close()
	    return False, log_msg

    def recv(self):
	try:
	    ser = serial.Serial(self.device, timeout=1)
	except Exception, e:
	    log_msg = "ERROR open port: %s. MSG: %s" % (str(self.device), str(e))
	    return False, log_msg
	
	try:
	    # Переведем модем в режим СМС
	    ser.write('AT+CMGF=%d\r' % 1)
	    
	    # Прочитаем все пришедшие сообщения
	    ser.write('AT+CMGL="ALL"\r')
	    
	    all_msgs =  ser.readlines()
	    decode_msgs = []
	    for s in all_msgs:
		hexapattern = r'([0-9a-fA-F]+)(?:--)?'
		m = re.search(hexapattern, s)
		if m and len(m.group(1)) > 1:
		    s =  binascii.unhexlify(m.group(1)).decode('utf-16-be')
		msg = ' '.join(s.split())
		if (msg.find('AT+') < 0 or msg.find('AT+') is None):
		    decode_msgs.append(msg)
	    msg_arr = {}
	    for line in decode_msgs:
		if (line == 'OK'):
		    continue
		if (line.find('+CMGL:') == 0):
		    line = line.split(',')
		    msg_num = self.d.sub('',line[0])
		    msg_date= "%s %s" % (str(line[4]), str(line[5]))
		    msg_from= str(line[2])
		    line=''
		if (len(line) > 0):
		    msg_arr[msg_num] = {'date' : msg_date, 'phone' : msg_from, 'text' : line}
	    
	    return True, msg_arr
	
	except Exception, e:
	    print e
	    log_msg = "ERROR read from port: %s. MSG: %s" % (str(self.device), str(' '.join(' '.join(e).split())))
	    ser.close()
	    return False, log_msg
    
    def del_all(self):
	msgs = self.recv()	    	
	if (msgs[0] is True):
	    for num,msg in msgs[1].items():
		try:
		    ser = serial.Serial(self.device, timeout=1)
	    	    # Переведем модем в режим СМС
		    ser.write('AT+CMGF=%d\r' % 1)

		except Exception, e:
	    	    log_msg = "ERROR open port: %s. MSG: %s" % (str(self.device), str(e))
	    	    return False, log_msg
		
	        try:
		    # Удалим текущее сообщение
		    ser.write('AT+CMGD=%d\r\n\r\n' % int(num))
		
		except Exception, e:
		    log_msg = "ERROR read from port: %s. MSG: %s" % (str(self.device), str(' '.join(' '.join(e).split())))
		    ser.close()
		    return False, log_msg
		print "DEBUG:",ser.readlines()
		ser.close()
	return True
	
    def get_balance(self):
	try:
	    self.del_all()
	except:
	    log_msg = "Error del all sms"
	    return False, log_msg
	try:
	    if (self.send(__main__.cfg['contacts']['get_balance'],__main__.cfg['text']['get_balance'])[0] is False):
		raise
	except Exception, e:
	    return False, "Error Send sms: %s" % str(e)
	balance_arr = {}
	balance = -99999
	try:
	    msgs = self.recv()
	    if (msgs[0] is True):
		for num,msg in msgs[1].items():
		    if (msg['text'].find(u'аланс') >= 0):
			msg_tmp =  msg['text'].split('.')
			for msg_part in msg_tmp:
			    if (msg_part.find(u'руб') >= 0):
				balance= "%s.%s" % (self.d.sub('',msg_part.split(',')[0]),self.d.sub('',msg_part.split(',')[1]))
				date = datetime.strptime(msg['date'].replace('"','')[:-3], '%y/%m/%d %H:%M:%S')
				balance_arr[num] = {'date':date, 'balance':balance}
	    mix_date = 0
	    try:
		for num,data in balance_arr.items():
		    if (mix_date == 0):
			max_date = data['date']
		    if (data['date'] > max_date):
    			max_date = data['date']
			balance = data['balance']
		return True, balance, max_date
	    except Exception, e:
		log_msg = "ERROR parse SMS: %s" %str(e)	
		return False, log_msg

	except Exception,e:
	    return False, str(e)

    