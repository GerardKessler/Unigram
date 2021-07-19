# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import api
from scriptHandler import script
import appModuleHandler
import controlTypes
from ui import message
from threading import Thread
from time import sleep
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

class AppModule(appModuleHandler.AppModule):

	itemObj = ''
	category = 'Unigram'
	# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
	errorMessage = _('Solo disponible desde la lista de mensajes')
	
	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == controlTypes.ROLE_LISTITEM:
				clsList.insert(0, PlayPause)
		except:
			pass

	def event_NVDAObject_init(self, obj):
		try:
			if obj.role == controlTypes.ROLE_LINK and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
				obj.name = obj.next.name
		except:
			pass

	def event_gainFocus(self, obj, nextHandler):
		try:
			if obj.role == controlTypes.ROLE_LISTITEM:
				self.itemObj = obj
				nextHandler()
			else:
				nextHandler()
		except TypeError:
			nextHandler()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Pulsa el botón compartir'),
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
		description=_('Enfoca la lista de chats'),
		gesture="kb:alt+rightArrow"
	)
	def script_chatFocus(self, gesture):
		try:
			for obj in api.getForegroundObject().children[1].lastChild.children[0].recursiveDescendants:
				if obj.UIAAutomationId == 'ArchivedChatsPanel':
					obj.next.setFocus()
					break
		except:
			pass

	@script(	
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Descarga el archivo adjunto'),
		gesture="kb:control+l"
	)
	def script_link(self, gesture):
		for obj in api.getFocusObject().recursiveDescendants:
			if obj.UIAAutomationId == 'Button':
				obj.doAction()
				break

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Activa y desactiva la velocidad doble de un mensaje de voz'),
		gesture="kb:control+d"
	)
	def script_toggleButton(self, gesture):
		try:
			for obj in api.getFocusObject().parent.parent.children:
				if obj.UIAAUtomationId == 'RateButton':
					message(obj.name)
					obj.doAction()
					break
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Pulsa el botón adjuntar'),
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
		description=_('Enfoca el último elemento de lista que tuvo el foco'),
		gesture="kb:alt+upArrow"
	)
	def script_itemFocus(self, gesture):
		try:
			self.itemObj.setFocus()
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Verbaliza el nombre del chat actual'),
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
		description=_('Pulsa el botón llamada de audio'),
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
		description=_('Pulsa el botón llamada de video'),
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

class PlayPause():

	def initOverlayClass(self):
		if self.parent.parent.lastChild.role == controlTypes.ROLE_TABCONTROL:
			self.bindGestures({"kb:space":"playPause", "kb:control+t":"time", "kb:control+p":"player"})

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
