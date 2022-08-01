# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import wx
import gui
import winUser
from globalCommands import commands
import api
from scriptHandler import script, getLastScriptRepeatCount
import config
from pickle import dump, load
import os
import appModuleHandler
import controlTypes
from nvwave import playWaveFile
from ui import message
from threading import Thread
from time import sleep
from re import search
import speech
from globalVars import appArgs
from keyboardHandler import KeyboardInputGesture
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

# Funciones de lectura y escritura de las configuraciones del complemento
def initConfiguration():
	confspec = {
		'AnnounceProgressBars': 'boolean(default=False)',
		'AudioRecords': 'boolean(default=True)'
	}
	config.conf.spec['unigram'] = confspec

def getConfig(key):
	return config.conf["unigram"][key]

def setConfig(key, value):
	try:
		config.conf.profiles[0]["unigram"][key] = value
	except:
		config.conf["unigram"][key] = value

initConfiguration()

getRole = lambda attr: getattr(controlTypes, f'ROLE_{attr}') if hasattr(controlTypes, 'ROLE_BUTTON') else getattr(controlTypes.Role, attr)

def speak(time, msg= False):
	if speech.getState().speechMode == speech.SpeechMode.off: return
	if msg:
		message(msg)
		sleep(0.1)
	Thread(target=killSpeak, args=(time,), daemon= True).start()

# Función para romper la cadena de verbalización y callar al sintetizador durante el tiempo especificado
def killSpeak(time):
	speech.setSpeechMode(speech.SpeechMode.off)
	sleep(time)
	speech.setSpeechMode(speech.SpeechMode.talk)

soundsPath = os.path.join(appArgs.configPath, 'addons', 'unigram', 'sounds')

class AppModule(appModuleHandler.AppModule):

	category = 'Unigram'

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.listObj = None
		self.chatObj = None
		self.focusObj = None
		self.recordObj = None
		self.fgObject = None
		self.slider = None
		self.audioRecords = getConfig('AudioRecords')
		self.item_name = None
		self.speak= True
		self.announceProgressBars = getConfig('AnnounceProgressBars')
		# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
		self.errorMessage = _('Solo disponible desde la lista de mensajes')

	def searchList(self):
		self.fgObject = api.getForegroundObject()
		try:
			for obj in self.fgObject.children[1].children:
				if obj.UIAAutomationId == 'Messages':
					self.listObj = obj
					return obj
			# Translators: Mensaje que anuncia que no se ha encontrado nindgún chat abierto
			message(_('No se ha encontrado ningún chat abierto'))
		except:
			pass

	def event_valueChange(self, obj, nextHandler):
		if self.announceProgressBars:
			nextHandler()
		else:
			return

	def event_gainFocus(self, obj, nextHandler):
		try:
			if obj.role != getRole('LISTITEM'): nextHandler()
			elif obj.firstChild.states == {1} and obj.parent.firstChild.UIAAutomationId == 'ArchivedChatsPanel':
				self.chatObj = obj
				nextHandler()
			else:
				nextHandler()
		except:
			nextHandler()
		try:
			if obj.role == getRole('MENUITEM') and self.item_name:
				for item in obj.parent.children:
					if item.firstChild.name == self.item_name:
						speak(0.2, item.name)
						item.doAction()
						self.item_name = None
						break
			self.speak= True
		except:
			nextHandler()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == getRole('CHECKBOX'):
				clsList.insert(0, Messages)
			elif obj.role == getRole('MENUITEM'):
				clsList.insert(0, ContextMenu)
			elif obj.role == getRole('SLIDER') and obj.UIAAutomationId == 'Slider':
				self.slider = obj
		except:
			pass

	def event_NVDAObject_init(self, obj):
		if not self.fgObject: self.fgObject = api.getForegroundObject()
		if not self.speak: speech.cancelSpeech()
		try:
			if obj.role == getRole('LINK') and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
				obj.name = f'{obj.next.name} ({obj.next.next.name})'
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Marca el chat como leído'),
		gesture="kb:alt+upArrow")
	def script_markAsMessagesRead(self, gesture):
		if api.getFocusObject().role == getRole('LISTITEM'):
			self.item_name = '\ue91d'
			KeyboardInputGesture.fromName('applications').send()
			self.speak= False
		else:
			gesture.send()

	@script(gesture="kb:upArrow")
	def script_chatUp(self, gesture):
		focus = api.getFocusObject()
		try:
			if focus.role == getRole('CHECKBOX') and focus.UIAAutomationId == '':
				KeyboardInputGesture.fromName('shift+upArrow').send()
			else:
				gesture.send()
		except:
			pass

	@script(gesture="kb:downArrow")
	def script_chatUp(self, gesture):
		focus = api.getFocusObject()
		try:
			if focus.role == getRole('CHECKBOX') and focus.UIAAutomationId == '':
				KeyboardInputGesture.fromName('shift+downArrow').send()
			else:
				gesture.send()
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de chats'),
		gesture='kb:alt+1'
	)
	def script_chatFocus(self, gesture):
		playWaveFile(os.path.join(soundsPath, 'click.wav'))
		if self.chatObj != None:
			self.chatObj.setFocus()
			Thread(target=speak, args=(0.1, self.chatObj.name), daemon=True).start()
		else:
			for obj in api.getForegroundObject().children[1].recursiveDescendants:
				try:
					if obj.UIAAutomationId == 'ArchivedChatsPanel':
						obj.next.setFocus()
						message(obj.next.name)
						sleep(0.1)
						Thread(target=speak, args=(0.1,), daemon=True).start()
						break
				except:
					pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de mensajes del chat abierto'),
		gesture='kb:alt+2'
	)
	def script_messagesFocus(self, gesture):
		try:
			playWaveFile(os.path.join(soundsPath, 'click.wav'))
			if self.listObj == None: self.searchList()
			focus = api.getFocusObject()
			fg = api.getForegroundObject()
			if focus.UIAAutomationId != 'TextField':
				for obj in fg.children[1].children:
					if obj.UIAAutomationId == 'TextField':
						obj.setFocus()
						return
		except:
			pass
		try:
			Thread(target=speak, args=(0.2, self.listObj.lastChild.name), daemon=True).start()
			self.listObj.lastChild.setFocus()
			KeyboardInputGesture.fromName('end').send()
			KeyboardInputGesture.fromName('end').send()
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca los mensajes no leídos del chat abierto'),
		gesture='kb:alt+3'
	)
	def script_unreadFocus(self, gesture):
		try:
			if not self.listObj:
				list = self.searchList()
			else:
				list = self.listObj
			unreadObj = False
			lastMessage = list.lastChild
			playWaveFile(os.path.join(soundsPath, 'click.wav'))
			while lastMessage:
				if lastMessage.firstChild.role== getRole('GROUPING'):
					unreadObj = lastMessage
					break
				else:
					lastMessage = lastMessage.previous
			if unreadObj:
				unreadObj.setFocus()
			else:
				message(_('No hay mensajes sin leer'))
		except AttributeError:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Descarga el archivo adjunto'),
		gesture='kb:alt+l'
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
		gesture='kb:alt+d'
	)
	def script_toggleButton(self, gesture):
		focus = api.getFocusObject()
		try:
			for obj in api.getForegroundObject().children[1].children:
				if obj.UIAAutomationId == 'RateButton':
					obj.doAction()
					focus.setFocus()
					if obj.states == {16777216, 16} or obj.states == {25, 5}:
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
		gesture='kb:control+shift+a'
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
		gesture='kb:control+shift+t'
	)
	def script_chatName(self, gesture):
		try:
			for obj in api.getForegroundObject().children[1].children:
				if obj.UIAAutomationId == 'Profile':
					message(obj.name)
					break
		except:
			message(self.errorMessage)

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón llamada de audio'),
		gesture='kb:alt+control+l'
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
		gesture='kb:alt+control+v'
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

	@script(gesture='kb:control+r')
	def script_voiceMessage(self, gesture):
		if not self.audioRecords:
			gesture.send()
			return
		self.focusObj = api.getFocusObject()
		self.searchList()
		try:
			for obj in reversed(api.getForegroundObject().children[1].children):
				if obj.UIAAutomationId == 'btnVoiceMessage':
					obj.doAction()
					self.recordObj = obj
					break
			self.focusObj.setFocus()
		except:
			pass
		try:
			if self.recordObj.next.UIAAutomationId != 'ElapsedLabel':
				# Translators: Mensaje que indica el comienzo de la grabación
				playWaveFile(os.path.join(soundsPath, 'start.wav'))
			elif self.recordObj.next.UIAAutomationId == 'ElapsedLabel':
				# Translators: Mensaje que indica el envío de la grabación
				playWaveFile(os.path.join(soundsPath, 'send.wav'))
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Conmuta entre el modo de grabación por defecto y el personalizado'),
		gesture='kb:control+shift+r'
	)
	def script_recordConfig(self, gesture):
		if self.audioRecords:
			setConfig('AudioRecords', False)
			self.audioRecords = False
			# Translators: Anuncia el tipo de grabación por defecto
			message(_('mensajes de voz por defecto'))
		else:
			setConfig('AudioRecords', True)
			self.audioRecords = True
			# Translators: Anuncia la grabación de mensajes del complemento
			message(_('mensajes de voz del complemento'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa y desactiva las barras de progreso en la aplicación'),
		gesture='kb:control+shift+b'
	)
	def script_progressConfig(self, gesture):
		if self.announceProgressBars:
			setConfig('AnnounceProgressBars', False)
			self.announceProgressBars = False
			# Translators: Anuncia la desactivación del anunciado de  las barras de progreso
			message(_('Barras de progreso desactivadas'))
		else:
			setConfig('AnnounceProgressBars', True)
			self.announceProgressBars = True
			# Translators: Anuncia la activación del anunciado de las barras de progreso
			message(_('Barras de progreso activadas'))

	@script(gesture='kb:control+d')
	def script_cancelVoiceMessage(self, gesture):
		gesture.send()
		try:
			if self.recordObj.next.UIAAutomationId == 'ElapsedLabel':
				self.focusObj.setFocus()
				playWaveFile(os.path.join(soundsPath, 'cancel.wav'))
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Verbaliza el tiempo actual de la grabación del mensaje de voz'),
		gesture='kb:control+t'
	)
	def script_recordTime(self, gesture):
		if not self.audioRecords:
			# Translators: Anuncia la disponibilidad del gesto solo con el modo de grabación del complemento
			message(_('Solo disponible en el modo de grabación de mensajes del complemento'))
			return
		try:
			if self.recordObj.next.UIAAutomationId == 'ElapsedLabel':
				timeStr = search('\d{1,2}\:\d\d', self.recordObj.next.name)
				message(timeStr[0])
			else:
				message(_('No hay ninguna grabación en curso'))
		except AttributeError:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description=_('Anuncia la descripción o el texto del mensaje, y al pulsarlo 2 veces lo copia al portapapeles'),
		gesture='kb:control+shift+d'
	)
	def script_descriptionAnnounce(self, gesture):
		obj = api.getFocusObject()
		try:
			if getLastScriptRepeatCount() == 1:
				for child in obj.firstChild.children:
					if child.UIAAutomationId == 'Message':
						api.copyToClip(child.name)
						# Translators: Anuncia que el mensaje ha sido copiado
						message(_('copiado'))
						return
			else:
				if obj.firstChild.firstChild.UIAAutomationId == 'Message':
					message(obj.firstChild.firstChild.name)
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Ingresa en el perfil del chat abierto, y pulsado dentro de este enfoca la lista de elementos a buscar'),
		gesture='kb:control+shift+p'
	)
	def script_profile(self, gesture):
		if not self.listObj: self.searchList()
		for obj in self.listObj.parent.children:
			try:
				if obj.UIAAutomationId == 'Profile':
					obj.doAction()
					Thread(target=self.listFocus, daemon= True).start()
			except:
				pass

	def listFocus(self):
		playWaveFile(os.path.join(soundsPath, 'profile.wav'))
		speech.setSpeechMode(speech.SpeechMode.off)
		sleep(0.8)
		speech.setSpeechMode(speech.SpeechMode.talk)
		for obj in api.getFocusObject().parent.children:
			if obj.role == getRole('LIST'):
				for obj_list in obj.children:
					if obj_list.role == getRole('LIST'):
						obj_list.firstChild.setFocus()
						break
				break

	@script(gesture='kb:alt+enter')
	def script_doubleClick(self, gesture):
		focus = api.getFocusObject()
		api.moveMouseToNVDAObject(focus)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		playWaveFile(os.path.join(soundsPath, 'play.wav'))


	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la lista de mensajes fijados'),
		gesture='kb:alt+control+f')
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
		gesture='kb:control+m'
	)
	def script_optionsMenu(self, gesture):
		for obj in reversed(api.getForegroundObject().children[1].children):
			if obj.UIAAutomationId == 'Photo' and obj.role == getRole('LINK'):
				obj.doAction()
				Thread(target=speak, args=(0.4, obj.name), daemon= True).start()
				Thread(target=self.tab, daemon=True).start()
				break

	def tab(self):
		sleep(0.5)
		KeyboardInputGesture.fromName('tab').send()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Retrocede el mensaje de audio en reproducción'),
		gesture="kb:alt+control+leftArrow"
	)
	def script_back(self, gesture):
		if not self.slider or self.slider.location.width == 0:
			# Translators: Anuncio de ninguna reproducción en curso
			message(_('Ninguna reproducción en curso'))
			return
		focus = api.getFocusObject()
		self.slider.setFocus()
		KeyboardInputGesture.fromName('leftArrow').send()
		focus.setFocus()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Avanza el mensaje de audio en reproducción'),
		gesture="kb:alt+control+rightArrow"
	)
	def script_advance(self, gesture):
		if not self.slider or self.slider.location.width == 0:
			message(_('Ninguna reproducción en curso'))
			return
		focus = api.getFocusObject()
		self.slider.setFocus()
		KeyboardInputGesture.fromName('rightArrow').send()
		focus.setFocus()

class Messages():

	def initOverlayClass(self):
		self.bindGesture('kb:rightArrow', 'contextMenu')
		try:
			if self.UIAAutomationId == '':
				self.bindGestures({'kb:space':'playPause', 'kb:alt+p':'player', 'kb:alt+q': 'close'})
				self = self.parent
		except:
			pass

	def script_contextMenu(self, gesture):
		KeyboardInputGesture.fromName('applications').send()

	def script_playPause(self, gesture):
		for h in self.recursiveDescendants:
			try:
				if h.UIAAutomationId == 'Button' and h.role == getRole('LINK'):
					h.doAction()
					playWaveFile(os.path.join(soundsPath, 'play.wav'))
					self.setFocus()
					Thread(target=speak, args=(0.3,), daemon=True).start()
					break
			except:
				pass

	def script_player(self, gesture):
		for obj in api.getForegroundObject().children[1].children:
			if obj.UIAAutomationId == 'VolumeButton':
				obj.setFocus()
				break

	def script_close(self, gesture):
		for obj in api.getForegroundObject().children[1].children:
			if obj.UIAAutomationId == 'ShuffleButton':
				message(obj.next.name)
				obj.next.doAction()
				self.setFocus()
				break

class ContextMenu():
	def initOverlayClass(self):
		self.bindGesture('kb:leftArrow', 'close')

	def script_close(self, gesture):
		KeyboardInputGesture.fromName('escape').send()

class ElementsList():
	def initOverlayClass(self):
		self.bindGestures({'kb:rightArrow':'nextItem', 'kb:leftArrow':'previousItem', 'kb:enter':'pressItem'})

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
