# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import winUser
import api
from scriptHandler import script, getLastScriptRepeatCount
import config
import os
import appModuleHandler
import controlTypes
from nvwave import playWaveFile
from tones import beep
from ui import message
from threading import Thread
from time import sleep
from re import search
import speech
from . import keyFunc
from globalVars import appArgs
from keyboardHandler import KeyboardInputGesture
import UIAHandler
from NVDAObjects.UIA import UIA
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

# Funciones de lectura y escritura de las configuraciones del complemento
def initConfiguration():
	confspec= {
		'AnnounceProgressBars': 'boolean(default=False)',
		'sounds': 'boolean(default=False)',
		'AudioRecords': 'boolean(default=True)',
		'linkAnnounce': 'integer(default=0)'
	}
	config.conf.spec['unigram']= confspec

def getConfig(key):
	return config.conf["unigram"][key]

def setConfig(key, value):
	try:
		config.conf.profiles[0]["unigram"][key]= value
	except:
		config.conf["unigram"][key]= value

initConfiguration()

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

# constantes
ADDON_PATH= os.path.dirname(__file__)
SOUNDS_PATH= os.path.join(ADDON_PATH, 'sounds')
SOUNDS= getConfig('sounds')

class AppModule(appModuleHandler.AppModule):

	category= 'Unigram'

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		self.list_object= None
		self.chat_object= None
		self.focus_object= None
		self.record_object= None
		self.slider= None
		self.item_name= None
		self.audio_records= getConfig('AudioRecords')
		self.announce_progress_bars= getConfig('AnnounceProgressBars')
		self.link_announce= getConfig('linkAnnounce')
		self.speak= True
		self.messageList= None
		self.topic_list= None
		self.x= None
		# Translators: Mensaje que anuncia la disponibilidad solo desde la lista de mensajes
		self.error_message= _('Solo disponible desde la lista de mensajes')

	def event_gainFocus(self, obj, nextHandler):
		if obj.role == controlTypes.Role.CHECKBOX and self.link_announce != 0:
			link_child= obj.firstChild.firstChild
			if link_child and link_child.role == controlTypes.Role.LINK or search(r'https?://', obj.name):
				if self.link_announce == 2:
					# Translators: Mensaje que anuncia la existencia de un enlace
					message(_('Con Enlace;'))
				elif self.link_announce == 1:
						playWaveFile(os.path.join(SOUNDS_PATH, 'link.wav'))
		try:
			if obj.role == controlTypes.Role.MENUITEM and self.item_name:
				for item in obj.parent.children:
					if item.firstChild.name == self.item_name:
						speak(0.2, item.name)
						item.doAction()
						self.item_name= None
						break
			self.speak= True
		except:
			nextHandler()
		try:
			if obj.role == controlTypes.Role.LISTITEM and obj.simpleFirstChild.UIAAutomationId == 'TitleLabel':
				self.chat_object= obj
		except:
			pass
		nextHandler()

	# Función creada por Noelia Ruiz Martínez
	@staticmethod
	def getElement(value):
		try:
			clientObject= UIAHandler.handler.clientObject
			condition= clientObject.createPropertyCondition(UIAHandler.UIA_AutomationIdPropertyId, value)
			walker= clientObject.createTreeWalker(condition)
			unigramWindow= clientObject.elementFromHandle(api.getForegroundObject().windowHandle)
			element= walker.getFirstChildElement(unigramWindow)
			element= element.buildUpdatedCache(UIAHandler.handler.baseCacheRequest)
			return element
		except Exception as e:
			log.debugWarning(e)

	def searchList(self):
		fg= api.getForegroundObject()
		for obj in fg.children[1].recursiveDescendants:
			try:
				if obj.UIAAutomationId == 'Messages':
					self.list_object= obj
					return obj
			except:
				continue
		# Translators: Mensaje que anuncia que no se ha encontrado nindgún chat abierto
		message(_('No se ha encontrado ningún chat abierto'))

	def event_valueChange(self, obj, nextHandler):
		if self.announce_progress_bars:
			nextHandler()
		else:
			return

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		try:
			if obj.role == controlTypes.Role.CHECKBOX and obj.UIAAutomationId == '':
				clsList.insert(0, MessagesList)
			elif obj.role == controlTypes.Role.MENUITEM:
				clsList.insert(0, ContextMenu)
			elif obj.role == controlTypes.Role.SLIDER and obj.UIAAutomationId == 'Slider':
				self.slider= obj
		except:
			pass

	def event_NVDAObject_init(self, obj):
		if not self.speak: speech.cancelSpeech()
		try:
			if 'forumTopic ' in obj.name:
				obj.name= f'{obj.simpleFirstChild.name} ({obj.children[-1].name})'
		except:
			pass
		try:
			if obj.role == controlTypes.Role.LINK and obj.UIAAutomationId == 'Button' and obj.next.UIAAutomationId == 'Title':
				obj.name= f'{obj.next.name} ({obj.next.next.name})'
		except:
			pass

	@script(gestures=[f'kb:alt+{i}' for i in range(1,10)])
	def script_messageHistory(self, gesture):
		self.x= int(gesture.displayName[-1])*-1
		if not self.list_object: self.searchList()
		try:
			message(self.list_object.children[self.x].name)
		except:
			gesture.send()

	@script(gesture="kb:alt+enter")
	def script_focusMessage(self, gesture):
		if not self.list_object: return
		try:
			self.list_object.children[self.x].setFocus()
		except:
			gesture.send()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Marca el chat como leído'),
		gesture="kb:alt+upArrow")
	def script_markAsMessagesRead(self, gesture):
		if api.getFocusObject().role == controlTypes.Role.LISTITEM:
			self.item_name= '\ue91d'
			keyFunc.press_key(0x5D)
			self.speak= False
		else:
			gesture.send()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de chats'),
		gesture='kb:alt+rightArrow'
	)
	def script_chatFocus(self, gesture):
		if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'click.wav'))
		if self.chat_object != None:
			self.chat_object.setFocus()
			speak(0.1, self.chat_object.name)
		else:
			for obj in api.getForegroundObject().children[1].recursiveDescendants:
				try:
					if obj.UIAAutomationId == 'ArchivedChatsPanel':
						obj.next.setFocus()
						message(obj.next.name)
						speak(0.1)
						break
				except:
					pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de mensajes del chat abierto'),
		gesture='kb:alt+leftArrow'
	)
	def script_messagesFocus(self, gesture):
		if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'click.wav'))
		self.list_object= self.searchList()
		self.list_object.setFocus()
		sleep(0.1)
		KeyboardInputGesture.fromName('end').send()

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca los mensajes no leídos del chat abierto'),
		gesture='kb:alt+downArrow'
	)
	def script_unreadFocus(self, gesture):
		try:
			if not self.list_object:
				list= self.searchList()
			else:
				list= self.list_object
			unreadObj= False
			lastMessage= list.lastChild
			if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'click.wav'))
			while lastMessage:
				if lastMessage.firstChild.role== controlTypes.Role.GROUPING:
					unreadObj= lastMessage
					break
				else:
					lastMessage= lastMessage.previous
			if unreadObj:
				unreadObj.setFocus()
			else:
				message(_('No hay mensajes sin leer'))
		except AttributeError:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Enfoca la lista de temas'),
		gesture='kb:alt+t'
	)
	def script_viewTopics(self, gesture):
		fg= api.getForegroundObject()
		try:
			if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'click.wav'))
			if fg.children[1].lastChild.UIAAutomationId == 'Button':
				fg.children[1].lastChild.doAction()
		except:
			pass
		for obj in api.getForegroundObject().children[1].recursiveDescendants:
			try:
				if obj.UIAAutomationId == 'TopicList':
					obj.firstChild.setFocus()
					breack
			except:
				continue

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
		focus= api.getFocusObject()
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
		obj= api.getFocusObject().parent
		try:
			if obj.role == controlTypes.Role.WINDOW:
				for h in obj.children:
					if h.UIAAutomationId == 'ButtonAttach':
						h.doAction()
						obj.setFocus()
						break
			elif obj.role == controlTypes.Role.LIST:
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
		message(self.getElement('Title').CachedName)

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Pulsa el botón llamada de audio'),
		gesture='kb:alt+control+l'
	)
	def script_audioCall(self, gesture):
		focus= api.getFocusObject()
		try:
			for obj in api.getFocusObject().parent.parent.children:
				if obj.UIAAutomationId == 'Call':
					message(obj.name)
					obj.doAction()
					Thread(target=self.finish, daemon= True).start()
					break
		except:
			message(self.error_message)

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
			message(self.error_message)

	def finish(self):
		sleep(0.3)
		focus= api.getFocusObject()
		for obj in focus.parent.children:
			if obj.UIAAutomationId == 'Accept':
				obj.setFocus()
				break

	@script(gesture='kb:control+r')
	def script_voiceMessage(self, gesture):
		if not self.audio_records:
			gesture.send()
			return
		self.focus_object= api.getFocusObject()
		self.searchList()
		try:
			for obj in reversed(api.getForegroundObject().children[1].children):
				if obj.UIAAutomationId == 'btnVoiceMessage':
					obj.doAction()
					self.record_object= obj
					break
			self.focus_object.setFocus()
		except:
			pass
		try:
			if self.record_object.next.UIAAutomationId != 'ElapsedLabel':
				# Translators: Mensaje que indica el comienzo de la grabación
				if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'start.wav'))
			elif self.record_object.next.UIAAutomationId == 'ElapsedLabel':
				# Translators: Mensaje que indica el envío de la grabación
				if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'send.wav'))
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Conmuta entre el modo de grabación por defecto y el personalizado'),
		gesture='kb:control+shift+r'
	)
	def script_recordConfig(self, gesture):
		if self.audio_records:
			setConfig('AudioRecords', False)
			self.audio_records= False
			# Translators: Anuncia el tipo de grabación por defecto
			message(_('mensajes de voz por defecto'))
		else:
			setConfig('AudioRecords', True)
			self.audio_records= True
			# Translators: Anuncia la grabación de mensajes del complemento
			message(_('mensajes de voz del complemento'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa y desactiva el anuncio de enlaces en un link'),
		gesture='kb:control+shift+k'
	)
	def script_linksConfig(self, gesture):
		if self.link_announce == 0:
			setConfig('linkAnnounce', 1)
			self.link_announce= 1
			# Translators: Anuncia los enlaces de un mensaje con sonido
			message(_('Anuncio de enlaces: sonido'))
		elif self.link_announce == 1:
			setConfig('linkAnnounce', 2)
			self.link_announce= 2
			# Translators: Anuncia los enlaces de un mensaje con texto
			message(_('Anuncio de enlaces: mensaje'))
		elif self.link_announce == 2:
			setConfig('linkAnnounce', 0)
			self.link_announce= 0
			# Translators: Anuncia los enlaces de un mensaje en ninguno
			message(_('Anuncio de enlaces: ninguno'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa y desactiva los sonidos del complemento'),
		gesture='kb:control+shift+s'
	)
	def script_soundsConfig(self, gesture):
		global SOUNDS
		if SOUNDS:
			setConfig('sounds', False)
			SOUNDS= False
			# Translators: Anuncia la desactivación de los sonidos
			message(_('Sonidos del complemento desactivados'))
		else:
			setConfig('sounds', True)
			SOUNDS= True
			# Translators: Anuncia la activación de los sonidos del complemento
			message(_('Sonidos del complemento activados'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa y desactiva las barras de progreso en la aplicación'),
		gesture='kb:control+shift+b'
	)
	def script_progressConfig(self, gesture):
		if self.announce_progress_bars:
			setConfig('AnnounceProgressBars', False)
			self.announce_progress_bars= False
			# Translators: Anuncia la desactivación del anunciado de  las barras de progreso
			message(_('Barras de progreso desactivadas'))
		else:
			setConfig('AnnounceProgressBars', True)
			self.announce_progress_bars= True
			# Translators: Anuncia la activación del anunciado de las barras de progreso
			message(_('Barras de progreso activadas'))

	@script(gesture='kb:control+d')
	def script_cancelVoiceMessage(self, gesture):
		gesture.send()
		try:
			if self.record_object.next.UIAAutomationId == 'ElapsedLabel':
				self.focus_object.setFocus()
				if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'cancel.wav'))
		except:
			pass

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Verbaliza el tiempo actual de la grabación del mensaje de voz'),
		gesture='kb:control+t'
	)
	def script_recordTime(self, gesture):
		if not self.audio_records:
			# Translators: Anuncia la disponibilidad del gesto solo con el modo de grabación del complemento
			message(_('Solo disponible en el modo de grabación de mensajes del complemento'))
			return
		try:
			if self.record_object.next.UIAAutomationId == 'ElapsedLabel':
				timeStr= search('\d{1,2}\:\d\d', self.record_object.next.name)
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
		obj= api.getFocusObject()
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
		if not self.list_object: self.searchList()
		for obj in self.list_object.parent.children:
			try:
				if obj.UIAAutomationId == 'Profile':
					obj.doAction()
					Thread(target=self.listFocus, daemon= True).start()
			except:
				pass

	def listFocus(self):
		if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'profile.wav'))
		speech.setSpeechMode(speech.SpeechMode.off)
		sleep(1)
		speech.setSpeechMode(speech.SpeechMode.talk)
		for obj in api.getFocusObject().parent.children:
			if obj.role == controlTypes.Role.LIST:
				for obj_list in obj.children:
					if obj_list.role == controlTypes.Role.LIST:
						obj_list.firstChild.setFocus()
						break
				break

	@script(gesture='kb:control+enter')
	def script_doubleClick(self, gesture):
		focus= api.getFocusObject()
		api.moveMouseToNVDAObject(focus)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'play.wav'))

	@script(
		category=category,
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la lista de mensajes fijados'),
		gesture='kb:alt+control+f')
	def script_pinnedChats(self, gesture):
		if self.list_object == None: self.searchList()
		for obj in self.list_object.parent.recursiveDescendants:
			try:
				if obj.UIAAutomationId == 'ListButton':
					message(obj.name)
					obj.doAction()
			except:
				pass

	@script(
		category= category,
		description= _('Abrir el menú de navegación'),
		gesture='kb:control+m'
	)
	def script_optionsMenu(self, gesture):
		for obj in reversed(api.getForegroundObject().children[1].children):
			if obj.UIAAutomationId == 'Photo' and obj.role == controlTypes.Role.LINK:
				obj.doAction()
				speak(0.4, obj.name)
				Thread(target=self.tab, daemon=True).start()
				break

	def tab(self):
		sleep(0.5)
		keyFunc.press_key(0x09)

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
		focus= api.getFocusObject()
		self.slider.setFocus()
		keyFunc.press_key(0x25)
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
		focus= api.getFocusObject()
		self.slider.setFocus()
		keyFunc.press_key(0x27)
		focus.setFocus()

	@script(
		gestures=["kb:control+tab", "kb:control+shift+tab"]
	)
	def script_switchChat(self, gesture):
		gesture.send()
		focusObject= api.getFocusObject()
		speak(0.1, self.getElement('Title').CachedName)

class MessagesList():
	def initOverlayClass(self):
		self.bindGestures({
			'kb:rightArrow':'contextMenu',
			'kb:space':'playPause',
			'kb:alt+p':'player',
			'kb:alt+q':'close'
		})
		self= self.parent

	def script_contextMenu(self, gesture):
		keyFunc.press_key(0x5D)

	def script_playPause(self, gesture):
		for h in self.recursiveDescendants:
			try:
				if h.UIAAutomationId == 'Button' and h.role == controlTypes.Role.LINK:
					h.doAction()
					if SOUNDS: playWaveFile(os.path.join(SOUNDS_PATH, 'play.wav'))
					self.setFocus()
					speak(0.3)
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
		keyFunc.press_key(0x1B)

