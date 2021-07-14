# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import api
from scriptHandler import script
import appModuleHandler
import controlTypes
from ui import message

class AppModule(appModuleHandler.AppModule):

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == controlTypes.ROLE_LISTITEM:
				clsList.insert(0, PlayPause)
		except:
			pass

	
	@script(
		category="Unigram",
		description="Enfoca la lista de chats",
		gesture="kb:alt+rightArrow"
	)
	def script_chatFocus(self, gesture):
		for h in api.getForegroundObject().children[1].children:
			if h.role == 23:
				h.children[0].children[0].children[1].setFocus()
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

	@script(
		category="Unigram",
		description="Pulsa el botón adjuntar",
		gesture="kb:control+j"
	)
	def script_toAttach(self, gesture):
		obj = api.getFocusObject().parent
		if obj.role == controlTypes.ROLE_WINDOW:
			for h in obj.children:
				if h.name == 'Adjuntar multimedia':
					h.doAction()
					break
		elif obj.role == controlTypes.ROLE_LIST:
			for h in obj.parent.children:
				if h.name == 'Adjuntar multimedia':
					h.doAction()
					break

class PlayPause():

	def initOverlayClass(self):
		if self.parent.parent.lastChild.role == controlTypes.ROLE_TABCONTROL:
			self.bindGestures({"kb:space":"playPause", "kb:control+t":"time"})

	def script_playPause(self, gesture):
		for h in self.children:
			if h.role == controlTypes.ROLE_LINK:
				if h.name == "Reproducir" or h.name == "Pausar":
					h.doAction()
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
