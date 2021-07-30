# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import globalPluginHandler
import api
from ui import message
from scriptHandler import script
from subprocess import run
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Abre unigram, o lo enfoca si ya se encuentra abierto'),
		category="Unigram"
	)
	def script_open(self, gesture):
		try:
			run("start shell:AppsFolder\\38833FF26BA1D.UnigramPreview_g9c9v27vpyspw!App", shell=True)
		except:
			#Translators: Mensaje que anuncia que no se ha encontrado la aplicación
			message(_('No se encuentra la aplicación'))
