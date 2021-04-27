# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import api
from scriptHandler import script
import appModuleHandler
import controlTypes
from NVDAObjects.UIA import UIA

class AppModule(appModuleHandler.AppModule):
	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if not isinstance(obj, UIA): return
		if '\r\nMensaje de voz' in obj.name:
			clsList.insert(0, UnigramMessage)

	@script(
		category="Unigram",
		description="Enfoca la lista de mensajes o de chats, según el contexto",
		gesture="kb:control+c"
	)
	def script_chatFocus(self, gesture):
		obj = api.getForegroundObject()
		for hs in obj.recursiveDescendants:
			if hs.role == controlTypes.ROLE_LISTITEM:
				if hs.parent.parent.name == 'Chats' and hs.parent.parent.role == controlTypes.ROLE_TAB:
					hs.setFocus()
					break
				else:
					hs.parent.lastChild.setFocus()
					break


	@script(
		category="Unigram",
		description="Abre el link del mensaje",
		gesture="kb:control+l"
	)
	def script_link(self, gesture):
		focus = api.getFocusObject()
		for hs in focus.recursiveDescendants:
			if "http" in hs.name and hs.role == controlTypes.ROLE_LINK:
				hs.doAction()
				break

	@script(
		category="Unigram",
		description="Activa y desactiva la velocidad doble de un mensaje de voz",
		gesture="kb:control+d"
	)
	def script_toggleButton(self, gesture):
		fc = api.getFocusObject()
		fg = api.getForegroundObject()
		for hs in fg.recursiveDescendants:
			if hs.name == 'Velocidad doble' and hs.role == controlTypes.ROLE_TOGGLEBUTTON:
				hs.doAction()
				fc.setFocus()
				break

class UnigramMessage(UIA):
	def initOverlayClass(self):
		self.bindGesture("kb:space", "playMessage")
	@script(
		category="Unigram",
		description="Comienza y detiene la reproducción el mensaje de voz",
	)
	def script_playMessage(self, gesture):
		fc = api.getFocusObject()
		for hijo in fc.children:
			if hijo.role == controlTypes.ROLE_LINK:
				if hijo.name == "Reproducir" or hijo.name == "Pausar":
					hijo.doAction()
					fc.setFocus()
					break