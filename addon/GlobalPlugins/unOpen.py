# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Clases para abrir la aplicación por Héctor J. Benítez Corredera <xebolax@gmail.com>

import globalPluginHandler
import addonHandler
import gui
import api
import ui
from scriptHandler import script
from winUser import user32
from nvwave import playWaveFile
import shellapi
import globalVars
import os
import sys
import subprocess
import ctypes
from globalVars import appArgs
from threading import Thread

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

def obtenApps():
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	try:
		os.environ['PROGRAMFILES(X86)']
		with disable_file_system_redirection():
			p = subprocess.Popen('PowerShell get-StartApps'.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=si, creationflags = 0x08000000, universal_newlines=True)
	except:
		p = subprocess.Popen('PowerShell get-StartApps'.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='CP437', startupinfo=si, creationflags = 0x08000000, universal_newlines=True)
	result_string = str(p.communicate()[0])
	lines = [s.strip() for s in result_string.split('\n') if s]
	nuevo = lines[2:]
	lista_final = []
	for x in nuevo:
		y = ' '.join(x.split())
		z = y.rsplit(' ', 1)
		lista_final.append(z)
	return lista_final

def buscarApp(lista, valor):
	tempA = []
	tempB = []
	for i in range(0, len(lista)):
		tempA.append(lista[i][0])
		tempB.append(lista[i][1])
	filtro = [item for item in tempA if valor.lower() in item.lower()]
	return tempA, tempB, filtro

IS_WinON = False

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	sound= 'C:/Windows/Media/Ring02.wav'

	@script(
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Abre unigram, o lo enfoca si ya se encuentra abierto'),
		category="Unigram"
	)
	def script_open(self, gesture):
		if os.path.exists(self.sound): playWaveFile(self.sound)
		nombre, id, resultados = buscarApp(obtenApps(), "Unigram")
		if len(resultados) == 1:
			shellapi.ShellExecute(None, 'open', "explorer.exe", "shell:appsfolder\{}".format(id[nombre.index(resultados[0])]), None, 10)
		else:
			# Translators: Mensaje de aviso de aplicación no encontrada
			ui.message(_('No se ha encontrado la aplicación de WhatsApp'))
