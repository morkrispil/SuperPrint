# https://github.com/morkrispil/SuperPrint
# https://code.activestate.com/recipes/tags/meta:license=mit

from time import time
import psutil
import threading
from subprocess import check_output, call, CalledProcessError
from datetime import datetime


class Highlighter(object):
	def __init__(self):
		self.header = '\033[95m'
		self.blue = '\033[94m'
		self.warning = '\033[93m'
		self.fail = '\033[91m'
		self.bold = '\033[1m'
		self.underline = '\033[4m'
		self.green = '\033[92m'
		self.end = '\033[0m'
	
	def wrap_green(self, s):
		return '{0}{1}{2}'.format(self.green, s, self.end)
	
	def wrap_blue(self, s):
		return '{0}{1}{2}'.format(self.blue, s, self.end)
	
	def wrap_red(self, s):
		return '{0}{1}{2}'.format(self.fail, s, self.end)
	
	def clear_string(self, s):
		clear_s = s
		for v in self.__dict__.itervalues():
			clear_s = clear_s.replace(v, '')
		return clear_s


class SuperPrint(object):
	def __init__(self, print_elapsed=False, print_memory=False, print_thread_id=False, print_buffer=False, start_message=None):
		self.timestamp = time()
		self.init_timestamp = self.timestamp
		self.print_elapsed = print_elapsed
		self.print_memory = print_memory
		self.print_thread_id = print_thread_id
		
		self.memory_free = psutil.virtual_memory().free
		self.init_memory_free = self.memory_free
		
		self.print_buffer = None
		if print_buffer:
			self.print_buffer = []
		
		call('clear', shell=True)
		try:
			cosole_rows, cosole_columns = [int(res) for res in check_output(['stty', 'size']).split()]
		except CalledProcessError:
			cosole_rows, cosole_columns = 60, 20
		self.cosole_columns = cosole_columns
		
		# TODO: override built-in print
		# print = self.p
		self.highlighter = Highlighter()
		
		if start_message is None:
			start_message = 'started'
		self.ps(start_message)
		
	def bytes2human(self, n):
		# http://code.activestate.com/recipes/578019
		# https://code.activestate.com/recipes/tags/meta:license=mit/
		signed = ''
		if n < 0:
			signed = '-'
			n = abs(n)
			
		symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
		prefix = {}
		for i, s in enumerate(symbols):
			prefix[s] = 1 << (i + 1) * 10
		for s in reversed(symbols):
			if n >= prefix[s]:
				value = float(n) / prefix[s]
				return '%.1f%s' % (value, s)
		return signed + ("%sB" % n)
	
	def p(self, message, print_time=True, print_buffer_curr=False):
		timestamp = time()
		elapsed_s = self.calc_elapsed_s(timestamp, self.timestamp)
		self.timestamp = timestamp
		
		d_s = ''
		if print_time:
			d = datetime.fromtimestamp(timestamp)
			d_s = self.highlighter.wrap_blue(d.strftime("%H:%M:%S"))
			
		elapsed_message = ''
		if self.print_elapsed:
			elapsed_message = '[{0} / {1}] '.format(self.highlighter.wrap_blue(elapsed_s), self.highlighter.wrap_blue(self.calc_total_elapsed_s()))
			
		memory_message = ''
		if self.print_memory:
			memory_free = self.calc_free_mem()
			used_s = self.calc_mem_used_s(self.memory_free, memory_free)		
			self.memory_free = memory_free
			memory_message = '[{0} / {1}] '.format(self.highlighter.wrap_blue(used_s), self.highlighter.wrap_blue(self.calc_total_mem_used_s()))
			
		thread_id = ''
		if self.print_thread_id:
			thread_id = '[{0}] '.format(threading.current_thread().name)
		
		formated_message = '{0}{1} {2}{3}{4}'.format(
			thread_id,
			d_s,
			elapsed_message,
			memory_message,
			message)
		print(formated_message)
		if self.print_buffer is not None and print_buffer_curr:
			self.print_buffer.append(self.highlighter.clear_string(formated_message))

	def e(self, message):
		self.p(self.highlighter.wrap_red(message))
	
	def ps(self, message, print_buffer_curr=False):
		sep = '-' * self.cosole_columns
		print(sep)
		if self.print_buffer is not None and print_buffer_curr:
			self.print_buffer.append(sep)
		self.p(message=message, print_buffer_curr=print_buffer_curr)
		print(sep)
		if self.print_buffer is not None and print_buffer_curr:
			self.print_buffer.append(sep)
	
	def calc_elapsed_s(self, from_t, to_t):
		elapsed = from_t - to_t
		return '{0}s'.format(round(elapsed, 2))
		
	def calc_total_elapsed_s(self):
		return self.calc_elapsed_s(time(), self.init_timestamp)

	def calc_free_mem(self):
		return psutil.virtual_memory().free
		
	def calc_mem_used_s(self, from_m, to_m):
		# free memory diff
		used = from_m - to_m
		return self.bytes2human(used)
	
	def calc_total_mem_used_s(self):
		return self.calc_mem_used_s(self.init_memory_free, self.calc_free_mem())
		
	def done(self, message=None):
		if message is None:
			message = 'done'
		self.ps(message)
		
		elapsed_s = self.calc_total_elapsed_s()
		used_s = self.calc_total_mem_used_s()
		
		print('total: elapsed {0}, in use {1}\n'.format(self.highlighter.wrap_green(elapsed_s), self.highlighter.wrap_green(used_s)))


def print_time(message):
	print('{0} - {1}'.format(datetime.now().strftime("%H:%M:%S"), message))


def print_console(console_stdout, message):
	# force output to console
	# resume output to what it was
	curr_stdout = sys.stdout
	sys.stdout = console_stdout
	print_time(message)
	sys.stdout = curr_stdout
