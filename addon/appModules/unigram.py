# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Función ProgressBar basada en  el complemento unigramAccess

import api
from scriptHandler import script
import appModuleHandler
import controlTypes
from winsound import PlaySound, SND_FILENAME, SND_ASYNC
from ui import message
from threading import Thread
from time import sleep
from NVDAObjects.behaviors import ProgressBar
from NVDAObjects.UIA import UIA
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	category = 'Unigram'
	# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
	errorMessage = _('Solo disponible desde la lista de mensajes')

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == controlTypes.ROLE_LISTITEM:
				clsList.insert(0, Messages)
			elif obj.UIAElement.CachedClassName == 'ProgressBar':
				clsList.remove(ProgressBar)
			elif obj.UIAAutomationId == "btnVoiceMessage":
				clsList.insert(0, Rec)
			elif obj.UIAAutomationId == "TextField":
				clsList.insert(0, History)
		except:
			pass

	def event_NVDAObject_init(self, obj):
		try:
			if obj.role == controlTypes.ROLE_LINK and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
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
			if obj.role == controlTypes.ROLE_BUTTON and obj.next.UIAAutomationId == 'PlaceholderTextBlock':
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
		for obj in api.getForegroundObject().children[1].lastChild.children[0].recursiveDescendants:
			if obj.UIAAutomationId == 'ArchivedChatsPanel':
				obj.next.setFocus()
				break

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de mensajes del chat abierto'),
		gesture="kb:alt+2"
	)
	def script_messagesFocus(self, gesture):
		PlaySound("C:/Windows/Media/Speech Disambiguation.wav", SND_FILENAME | SND_ASYNC)
		for obj in reversed(api.getForegroundObject().children[1].children):
			if obj.role == controlTypes.ROLE_LIST:
				obj.lastChild.setFocus()
				return
		message(_('No se ha encontrado ningún chat abierto'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca los mensajes no leídos del chat abierto'),
		gesture="kb:alt+3"
	)
	def script_unreadFocus(self, gesture):
		PlaySound("C:/Windows/Media/Speech Disambiguation.wav", SND_FILENAME | SND_ASYNC)
		for obj in reversed(api.getForegroundObject().children[1].children):
			if obj.role == controlTypes.ROLE_LIST:
				break
		for h in reversed(obj.children):
			if h.firstChild.role == controlTypes.ROLE_GROUPING:
				h.setFocus()
				return
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
		if obj.role == controlTypes.ROLE_WINDOW:
			for h in obj.children:
				if h.UIAAutomationId == 'ButtonAttach':
					message(h.name)
					h.doAction()
					self.itemObj.setFocus()
					break
		elif obj.role == controlTypes.ROLE_LIST:
			for h in obj.parent.children:
				if h.name == 'Adjuntar multimedia':
					message(h.name)
					h.doAction()
					self.itemObj.setFocus()
					break

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
					Thread(target=self.finish).start()
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
					Thread(target=self.finish).start()
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

class Messages():

	def initOverlayClass(self):
		if self.parent.parent.lastChild.role == controlTypes.ROLE_TABCONTROL:
			self.bindGestures({"kb:space":"playPause", "kb:alt+t":"time", "kb:alt+p":"player", "kb:alt+q": "close"})

	def script_playPause(self, gesture):
		for h in self.children:
			if h.role == controlTypes.ROLE_PROGRESSBAR:
				h.previous.doAction()
				self.setFocus()
				break

	def script_time(self, gesture):
		try:
			for h in self.children:
				if h.role == controlTypes.ROLE_PROGRESSBAR:
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
				break

class Rec():

	def initOverlayClass(self):
		if self.UIAAutomationId == "btnVoiceMessage":
			self.bindGesture("kb:control+t", "recordTime")

	def script_recordTime(self, gesture):
		message(self.next.name)

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
		obj = self.listObj
		x = int(gesture.mainKeyName)
		PlaySound("C:/Windows/Media/Windows Startup.wav", SND_FILENAME | SND_ASYNC)
		if x == 1: message(obj.lastChild.name)
		elif x == 2: message(obj.lastChild.previous.name)
		elif x == 3: message(obj.lastChild.previous.previous.name)
		elif x == 4: message(obj.lastChild.previous.previous.previous.name)
		elif x == 5: message(obj.lastChild.previous.previous.previous.previous.name)
		elif x == 6: message(obj.lastChild.previous.previous.previous.previous.previous.name)
		elif x == 7: message(obj.lastChild.previous.previous.previous.previous.previous.previous.name)
		elif x == 8: message(obj.lastChild.previous.previous.previous.previous.previous.previous.previous.name)
		elif x == 9: message(obj.lastChild.previous.previous.previous.previous.previous.previous.previous.previous.name)

