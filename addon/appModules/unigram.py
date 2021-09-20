# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Función ProgressBar basada en  el complemento unigramAccess

import api
from scriptHandler import script, getLastScriptRepeatCount
import appModuleHandler
import controlTypes
from winsound import PlaySound, SND_FILENAME, SND_ASYNC
from ui import message
from threading import Thread
from time import sleep
from NVDAObjects.behaviors import ProgressBar
from re import search
import speech
from NVDAObjects.UIA import UIA
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

def getRole(attr):
	if hasattr(controlTypes, 'ROLE_BUTTON'):
		return getattr(controlTypes, f'ROLE_{attr}')
	else:
		return getattr(controlTypes, f'Role.{attr}')

def speak(str, time):
	if hasattr(speech, "SpeechMode"):
		speech.setSpeechMode(speech.SpeechMode.off)
		sleep(time)
		speech.setSpeechMode(speech.SpeechMode.talk)
	else:
		speech.speechMode = speech.speechMode_off
		sleep(time)
		speech.speechMode = speech.speechMode_talk
	if str != None:
		sleep(0.1)
		message(str)

class AppModule(appModuleHandler.AppModule):

	category = 'Unigram'
	listObj = None
	chatObj = None
	focusObj = None
	recordObj = None
	fgObject = None
	# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
	errorMessage = _('Solo disponible desde la lista de mensajes')

	def searchList(self):
		for obj in reversed(self.fgObject.children[1].children):
			if obj.role == getRole('LIST'):
				self.listObj = obj
				return obj
		# Translators: Mensaje que anuncia que no se ha encontrado nindgún chat abierto
		message(_('No se ha encontrado ningún chat abierto'))

	def event_gainFocus(self, obj, nextHandler):
		try:
			if obj.role != getRole('LISTITEM'):
				nextHandler()
				return
			if obj.firstChild.states == {1} and obj.parent.firstChild.UIAAutomationId == 'ArchivedChatsPanel':
				self.chatObj = obj
				nextHandler()
			else:
				nextHandler()
		except:
			nextHandler()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == getRole('LISTITEM'):
				clsList.insert(0, Messages)
			elif obj.UIAElement.CachedClassName == 'ProgressBar':
				clsList.remove(ProgressBar)
			elif obj.UIAAutomationId == "TextField":
				clsList.insert(0, History)
		except:
			pass

	def event_NVDAObject_init(self, obj):
		if not self.fgObject:
			self.fgObject = api.getForegroundObject()
		try:
			if obj.role == getRole('LINK') and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
				obj.name = obj.next.name
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón compartir'),
		gesture="kb:control+shift+c"
	)
	def script_share(self, gesture):
		for obj in api.getFocusObject().children:
			if obj.role == getRole('BUTTON') and obj.next.UIAAutomationId == 'PlaceholderTextBlock':
				message(obj.name)
				obj.doAction()
				break

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de chats'),
		gesture="kb:alt+1"
	)
	def script_chatFocus(self, gesture):
		PlaySound("C:/Windows/Media/Windows Feed Discovered.wav", SND_FILENAME | SND_ASYNC)
		if self.chatObj != None:
			self.chatObj.setFocus()
			message(self.chatObj.name)
			sleep(0.1)
			Thread(target=speak, args=(None, 0.1), daemon=True).start()
		else:
			try:
				for obj in api.getForegroundObject().children[1].lastChild.children[0].recursiveDescendants:
					if obj.UIAAutomationId == 'ArchivedChatsPanel':
						obj.next.setFocus()
						message(obj.next.name)
						sleep(0.1)
						Thread(target=speak, args=(None, 0.1), daemon=True).start()
						break
			except:
				pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de mensajes del chat abierto'),
		gesture="kb:alt+2"
	)
	def script_messagesFocus(self, gesture):
		PlaySound("C:/Windows/Media/Windows Feed Discovered.wav", SND_FILENAME | SND_ASYNC)
		if self.listObj == None: self.searchList()
		try:
			message(self.listObj.lastChild.name)
			sleep(0.1)
			Thread(target=speak, args=(None, 0.2), daemon=True).start()
			self.listObj.lastChild.setFocus()
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca los mensajes no leídos del chat abierto'),
		gesture="kb:alt+3"
	)
	def script_unreadFocus(self, gesture):
		if not self.listObj:
			list = self.searchList()
		else:
			list = self.listObj
		lastMessage = list.lastChild
		PlaySound("C:/Windows/Media/Windows Feed Discovered.wav", SND_FILENAME | SND_ASYNC)
		while True:
			if not lastMessage.previous: break
			if lastMessage.firstChild.role == getRole('GROUPING'):
				lastMessage.setFocus()
				return
			else:
				lastMessage = lastMessage.previous
		message(_('No se han encontrado mensajes no leídos'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Descarga el archivo adjunto'),
		gesture="kb:alt+l"
	)
	def script_link(self, gesture):
		for obj in api.getFocusObject().recursiveDescendants:
			if obj.UIAAutomationId == 'Button':
				message(obj.name)
				obj.doAction()
				break

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa y desactiva la velocidad doble de un mensaje de voz'),
		gesture="kb:alt+d"
	)
	def script_toggleButton(self, gesture):
		focus = api.getFocusObject()
		try:
			for obj in focus.parent.parent.children:
				if obj.UIAAutomationId == 'RateButton':
					obj.doAction()
					focus.setFocus()
					if obj.states == {16777216, 16}:
						message(_('Velocidad doble'))
					else:
						message(_('velocidad normal'))
					break
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón adjuntar'),
		gesture="kb:control+shift+a"
	)
	def script_toAttach(self, gesture):
		obj = api.getFocusObject().parent
		try:
			if obj.role == getRole('WINDOW'):
				for h in obj.children:
					if h.UIAAutomationId == 'ButtonAttach':
						h.doAction()
						obj.setFocus()
						break
			elif obj.role == getRole('LIST'):
				for h in obj.parent.children:
					if h.UIAAutomationId == 'ButtonAttach':
						h.doAction()
						obj.setFocus()
						break
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Verbaliza el nombre y estado del chat actual'),
		gesture="kb:control+shift+t"
	)
	def script_chatName(self, gesture):
		try:
			for obj in api.getFocusObject().parent.parent.children:
				if obj.UIAAutomationId == 'Profile':
					message(obj.name)
					break
		except:
			message(self.errorMessage)

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón llamada de audio'),
		gesture="kb:alt+control+l"
	)
	def script_audioCall(self, gesture):
		focus = api.getFocusObject()
		try:
			for obj in api.getFocusObject().parent.parent.children:
				if obj.UIAAutomationId == 'Call':
					message(obj.name)
					obj.doAction()
					Thread(target=self.finish, daemon= True).start()
					break
		except:
			message(self.errorMessage)

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón llamada de video'),
		gesture="kb:alt+control+v"
	)
	def script_videoCall(self, gesture):
		try:
			for obj in api.getFocusObject().parent.parent.children:
				if obj.UIAAutomationId == 'VideoCall':
					message(obj.name)
					obj.doAction()
					Thread(target=self.finish, daemon= True).start()
					break
		except:
			message(self.errorMessage)

	def finish(self):
		sleep(0.3)
		focus = api.getFocusObject()
		for obj in focus.parent.children:
			if obj.UIAAutomationId == 'Accept':
				obj.setFocus()
				break

	@script(gesture="kb:control+r")
	def script_voiceMessage(self, gesture):
		self.focusObj = api.getFocusObject()
		self.searchList()
		try:
			for obj in reversed(api.getForegroundObject().children[1].children):
				if obj.UIAAutomationId == "btnVoiceMessage":
					obj.doAction()
					self.recordObj = obj
					PlaySound("C:/Windows/Media/Windows Startup.wav", SND_FILENAME | SND_ASYNC)
					break
			self.focusObj.setFocus()
		except:
			pass
		try:
			if self.recordObj.next.UIAAutomationId != "ElapsedLabel":
				# Translators: Mensaje que indica el comienzo de la grabación
				message(_('grabando'))
			elif self.recordObj.next.UIAAutomationId == "ElapsedLabel":
				# Translators: Mensaje que indica el envío de la grabación
				message(_('Enviado'))
		except:
			pass

	@script(gesture="kb:control+d")
	def script_cancelVoiceMessage(self, gesture):
		gesture.send()
		try:
			if self.recordObj.next.UIAAutomationId == "ElapsedLabel":
				self.focusObj.setFocus()
				message(_('Grabación cancelada'))
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Verbaliza el tiempo actual de la grabación del mensaje de voz'),
		gesture="kb:control+t"
	)
	def script_recordTime(self, gesture):
		try:
			if self.recordObj.next.UIAAutomationId == "ElapsedLabel":
				timeStr = search("\d{1,2}\:\d\d", self.recordObj.next.name)
				message(timeStr[0])
			else:
				message(_('No hay ninguna grabación en curso'))
		except AttributeError:
			pass

class Messages():

	def initOverlayClass(self):
		try:
			if self.parent.parent.lastChild.role == getRole('TABCONTROL'):
				self.bindGestures({"kb:space":"playPause", "kb:alt+t":"time", "kb:alt+p":"player", "kb:alt+q": "close"})
		except:
			pass

	def script_playPause(self, gesture):
		for h in self.children:
			try:
				if h.UIAAutomationId == "Button":
					h.doAction()
					self.setFocus()
					Thread(target=speak, args=(None, 0.2), daemon=True).start()
					break
			except:
				pass

	def script_time(self, gesture):
		try:
			for h in self.children:
				if h.role == getRole('PROGRESSBAR'):
					message(h.value)
					break
		except:
			pass

	def script_player(self, gesture):
		fc = api.getFocusObject()
		for obj in fc.parent.parent.children:
			if obj.UIAAutomationId == 'VolumeButton':
				obj.setFocus()
				break

	def script_close(self, gesture):
		for obj in self.parent.parent.children:
			if obj.UIAAutomationId == "ShuffleButton":
				message(obj.next.name)
				obj.next.doAction()
				self.setFocus()
				break

class History():

	listObj = None
	switch = True

	def initOverlayClass(self):
		self.bindGestures(
			{"kb:control+1": "history",
			"kb:control+2": "history",
			"kb:control+3": "history",
			"kb:control+4": "history",
			"kb:control+5": "history",
			"kb:control+6": "history",
			"kb:control+7": "history",
			"kb:control+8": "history",
			"kb:control+9": "history"}
		)

	def createList(self):
		self.switch = False
		for obj in self.parent.children:
			if obj.UIAAutomationId == "Messages":
				self.listObj = obj
				break

	def script_history(self, gesture):
		if self.switch == True: self.createList()
		x = int(gesture.mainKeyName)
		obj = self.listObj.lastChild
		try:
			for k in range(x-1):
				obj = obj.previous
			if getLastScriptRepeatCount() == 1:
				for child in obj.children:
					if child.UIAAutomationId == "Message":
						api.copyToClip(child.name)
						PlaySound("C:/Windows/Media/recycle.wav", SND_FILENAME | SND_ASYNC)
			else:
				message(obj.name)
		except:
			pass
