# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import globalPluginHandler
import gui
import api
import ui
from scriptHandler import script
from winsound import PlaySound, SND_FILENAME, SND_ASYNC
import shellapi
import os
import subprocess
import ctypes
from threading import Thread
from re import search
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

class disable_file_system_redirection:

	_disable = ctypes.windll.kernel32.Wow64DisableWow64FsRedirection
	_revert = ctypes.windll.kernel32.Wow64RevertWow64FsRedirection

	def __enter__(self):
		self.old_value = ctypes.c_long()
		self.success = self._disable(ctypes.byref(self.old_value))

	def __exit__(self, type, value, traceback):
		if self.success:
			self._revert(self.old_value)

def getAppId():
	hide = subprocess.STARTUPINFO()
	hide.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	try:
		os.environ['PROGRAMFILES(X86)']
		with disable_file_system_redirection():
			content = subprocess.Popen(['PowerShell', 'Get-StartApps', 'unigram'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=hide, creationflags = 0x08000000, universal_newlines=True)
	except:
		content = subprocess.Popen(['PowerShell', 'Get-StartApps', 'unigram'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=hide, creationflags = 0x08000000, universal_newlines=True)
	return str(content.communicate()[0])

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Abre unigram, o lo enfoca si ya se encuentra abierto'),
		category="Unigram"
	)
	def script_open(self, gesture):
		try:
			PlaySound("C:/Windows/Media/Windows Battery Low.wav", SND_FILENAME | SND_ASYNC)
			content = getAppId()
			id = content.split(" ")
			shellapi.ShellExecute(None, 'open', "explorer.exe", "shell:appsfolder\{}".format(id[-1]), None, 10)
		except:
			#Translators: Mensaje que anuncia que no se ha encontrado la aplicación
			ui.message(_('No se encuentra la aplicación'))