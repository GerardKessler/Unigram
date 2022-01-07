# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import wx
import gui
import winUser
from globalCommands import commands
import api
from scriptHandler import script, getLastScriptRepeatCount
import appModuleHandler
import controlTypes
from winsound import PlaySound, SND_FILENAME, SND_ASYNC
from ui import message
from threading import Thread
from time import sleep
from re import search
import speech
from globalVars import appArgs
from keyboardHandler import KeyboardInputGesture
from . import portapapeles as pt
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

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.listObj = None
		self.chatObj = None
		self.focusObj = None
		self.recordObj = None
		self.fgObject = None
		# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
		self.errorMessage = _('Solo disponible desde la lista de mensajes')
		self.recordConfig = None
		self.configFile()

	def configFile(self):
		try:
			with open(f"{appArgs.configPath}\\unigram.ini", "r") as f:
				self.recordConfig = f.read()
		except FileNotFoundError:
			with open(f"{appArgs.configPath}\\unigram.ini", "w") as f:
				f.write("activado")

	def searchList(self):
		self.fgObject = api.getForegroundObject()
		try:
			for obj in reversed(self.fgObject.children[1].children):
				if obj.role == getRole('LIST'):
					self.listObj = obj
					return obj
			# Translators: Mensaje que anuncia que no se ha encontrado nindgún chat abierto
			message(_('No se ha encontrado ningún chat abierto'))
		except:
			pass

	def event_valueChange(self, obj, nextHandler):
		return

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
			if obj.role == getRole('LISTITEM') and obj.parent.next.UIAAutomationId == 'Search':
				clsList.insert(0, ElementsList)
			elif obj.role == getRole('LISTITEM') and obj.parent.parent.lastChild.role == getRole('TABCONTROL'):
				clsList.insert(0, Messages)
			elif obj.role == getRole('LISTITEM') and obj.parent.parent.lastChild.role != getRole('TABCONTROL'):
				clsList.insert(0, Chats)
			elif obj.role == getRole('MENUITEM'):
				clsList.insert(0, ContextMenu)
			elif obj.UIAAutomationId == "TextField":
				clsList.insert(0, History)
		except:
			pass

	def event_NVDAObject_init(self, obj):
		if not self.fgObject:
			self.fgObject = api.getForegroundObject()
		try:
			if obj.role == getRole('LINK') and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
				obj.name = f"{obj.next.name} ({obj.next.next.name})"
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
		if self.recordConfig == "desactivado":
			gesture.send()
			return
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

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Conmuta entre el modo de grabación por defecto y el personalizado'),
		gesture="kb:control+shift+r"
	)
	def script_recordConfig(self, gesture):
		self.configFile()
		with open(f"{appArgs.configPath}\\unigram.ini", "w") as f:
			if self.recordConfig == "activado":
				f.write("desactivado")
				self.recordConfig = "desactivado"
				message(_('mensajes de voz por defecto'))
			else:
				f.write("activado")
				self.recordConfig = "activado"
				message(_('mensajes de voz del complemento'))

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
		if self.recordConfig == "desactivado":
			# Translators: Anuncia la disponibilidad del gesto solo con el modo de grabación del complemento
			message(_('Solo disponible en el modo de grabación de mensajes del complemento'))
			return
		try:
			if self.recordObj.next.UIAAutomationId == "ElapsedLabel":
				timeStr = search("\d{1,2}\:\d\d", self.recordObj.next.name)
				message(timeStr[0])
			else:
				message(_('No hay ninguna grabación en curso'))
		except AttributeError:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Anuncia la descripción o el texto del mensaje, y al pulsarlo 2 veces lo copia al portapapeles'),
		gesture="kb:control+shift+d"
	)
	def script_descriptionAnnounce(self, gesture):
		obj = api.getFocusObject()
		try:
			if getLastScriptRepeatCount() == 1:
				for child in obj.children:
					if child.UIAAutomationId == 'Message':
						api.copyToClip(child.name)
						# Translators: Anuncia que el mensaje ha sido copiado
						message(_('copiado'))
						return
			else:
				if obj.firstChild.UIAAutomationId == 'Message':
					message(obj.firstChild.name)
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Ingresa en el perfil del chat abierto, y pulsado dentro de este enfoca la lista de elementos a buscar'),
		gesture="kb:control+shift+p"
	)
	def script_profile(self, gesture):
		if not self.listObj: self.searchList()
		try:
			for obj in self.listObj.parent.children:
				try:
					if obj.UIAAutomationId == 'Profile':
						message(obj.name)
						obj.doAction()
						return
				except:
					pass
		except:
			pass
		try:
			for list in self.fgObject.children[1].children[-2].children:
				if list.role == getRole('LIST'):
					list.setFocus()
					PlaySound("C:/Windows/Media/Windows Feed Discovered.wav", SND_FILENAME | SND_ASYNC)
					break
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa un cuadro de edición para realizar una búsqueda entre los elementos de un perfil'),
		gesture="kb:NVDA+f"
	)
	def script_txtSearch(self, gesture):
		obj = api.getFocusObject()
		if obj.role == getRole('EDITABLETEXT') and obj.parent.role == getRole('LIST'):
			self.dlg = textDlg(gui.mainFrame, _("Cuadro de búsqueda"), _("Ingrese los términos de búsqueda y pulse intro:"), obj)
			gui.mainFrame.prePopup()
			self.dlg.Show()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la lista de mensajes fijados'),
		gesture="kb:alt+control+f")
	def script_pinnedChats(self, gesture):
		if self.listObj == None: self.searchList()
		for obj in self.listObj.parent.recursiveDescendants:
			try:
				if obj.UIAAutomationId == 'ListButton':
					message(obj.name)
					obj.doAction()
			except:
				pass

	@script(
		category = category,
		description= _('Abrir el menú de navegación'),
		gesture="kb:control+m"
	)
	def script_optionsMenu(self, gesture):
		obj = api.getForegroundObject().children[1].firstChild
		obj.doAction()
		message(obj.name)
		sleep(0.1)
		Thread(target=speak, args=(None, 0.4), daemon= True).start()
		Thread(target=self.tab, daemon=True).start()

	def tab(self):
		sleep(0.5)
		KeyboardInputGesture.fromName("tab").send()

class Messages():

	def initOverlayClass(self):
		self.bindGesture("kb:rightArrow", "contextMenu")
		try:
			if self.parent.parent.lastChild.role == getRole('TABCONTROL'):
				self.bindGestures({"kb:space":"playPause", "kb:alt+t":"time", "kb:alt+p":"player", "kb:alt+q": "close"})
		except:
			pass

	def script_contextMenu(self, gesture):
		KeyboardInputGesture.fromName("applications").send()

	def script_playPause(self, gesture):
		for h in self.children:
			try:
				if h.UIAAutomationId == "Button":
					h.doAction()
					self.setFocus()
					Thread(target=speak, args=(None, 0.3), daemon=True).start()
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

class Chats():
	def initOverlayClass(self):
		self.bindGestures({"kb:rightArrow":"markAsRead", "kb:leftArrow":"selectMessages"})

	def script_markAsRead(self, gesture):
		Thread(target=speak, args=(None, 0.2), daemon= True).start()
		KeyboardInputGesture.fromName("applications").send()
		Thread(target=self.getMenuItems, args=(3,), daemon= True).start()

	def script_selectMessages(self, item):
		Thread(target=speak, args=(None, 0.2), daemon= True).start()
		KeyboardInputGesture.fromName("applications").send()
		Thread(target=self.getMenuItems, args=(2,), daemon= True).start()

	def getMenuItems(self, item):
		sleep(0.2)
		focus = api.getFocusObject()
		message(focus.parent.children[item].name)
		sleep(0.1)
		Thread(target=speak, args=(None, 0.2), daemon= True).start()
		focus.parent.children[item].doAction()

class ContextMenu():
	def initOverlayClass(self):
		self.bindGesture("kb:leftArrow", "close")

	def script_close(self, gesture):
		KeyboardInputGesture.fromName("escape").send()

class ElementsList():
	def initOverlayClass(self):
		self.bindGestures({"kb:rightArrow":"nextItem", "kb:leftArrow":"previousItem", "kb:enter":"pressItem"})

	def script_nextItem(self, gesture):
		commands.script_navigatorObject_next(gesture)

	def script_previousItem(self, gesture):
		commands.script_navigatorObject_previous(gesture)

	def script_pressItem(self, gesture):
		nav = api.getNavigatorObject()
		api.moveMouseToNVDAObject(nav)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)

class textDlg(wx.Dialog):
	def __init__(self, parent, title, message, obj):
		# Translators: Título de la ventana
		super(textDlg, self).__init__(parent, -1, title=title, size=(550, 350))

		self.obj = obj

		self.Panel = wx.Panel(self)

		label = wx.StaticText(self.Panel, wx.ID_ANY, message)
		self.search = wx.TextCtrl(self.Panel,wx.ID_ANY,style=wx.TE_PROCESS_ENTER)

		self.searchBTN = wx.Button(self.Panel, wx.ID_ANY, _("&Buscar"))
		self.closeBTN = wx.Button(self.Panel, wx.ID_CANCEL, _("&Cerrar"))

		sizerV = wx.BoxSizer(wx.VERTICAL)
		sizerH = wx.BoxSizer(wx.HORIZONTAL)

		sizerV.Add(label, 0, wx.EXPAND)
		sizerV.Add(self.search, 0, wx.EXPAND)

		sizerH.Add(self.searchBTN, 2, wx.CENTER)
		sizerH.Add(self.closeBTN, 2, wx.CENTER)

		sizerV.Add(sizerH, 0, wx.CENTER)

		self.Panel.SetSizer(sizerV)

		self.search.Bind(wx.EVT_CONTEXT_MENU, self.onPass)
		self.search.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
		self.searchBTN.Bind(wx.EVT_BUTTON, self.onSearch)
		self.Bind(wx.EVT_ACTIVATE, self.onClose)
		self.Bind(wx.EVT_BUTTON, self.onClose, id=wx.ID_CANCEL)

		self.CenterOnScreen()

	def onPass(self, event):
		pass

	def onSearch(self, event):
		text = self.search.GetValue()
		pt.put(text)
		self.Close()
		Thread(target=self.paste, daemon= True).start()
		self.Destroy()
		gui.mainFrame.postPopup()

	def paste(self):
		sleep(0.1)
		KeyboardInputGesture.fromName("control+v").send()
		sleep(0.5)
		self.obj.setFocus()
		pt.clean()

	def onClose(self, event):
		if event.GetEventType() == 10012:
			self.Destroy()
			gui.mainFrame.postPopup()
		elif event.GetActive() == False:
			self.Destroy()
			gui.mainFrame.postPopup()
		event.Skip()
