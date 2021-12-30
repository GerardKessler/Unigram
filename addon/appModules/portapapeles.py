﻿# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.

import ctypes
from ctypes.wintypes import BOOL, HWND, HANDLE, HGLOBAL, UINT, LPVOID
from ctypes import c_size_t as SIZE_T

# Solución extraida de https://stackoverflow.com/questions/579687/how-do-i-copy-a-string-to-the-clipboard

OpenClipboard = ctypes.windll.user32.OpenClipboard
OpenClipboard.argtypes = HWND,
OpenClipboard.restype = BOOL
EmptyClipboard = ctypes.windll.user32.EmptyClipboard
EmptyClipboard.restype = BOOL
GetClipboardData = ctypes.windll.user32.GetClipboardData
GetClipboardData.argtypes = UINT,
GetClipboardData.restype = HANDLE
SetClipboardData = ctypes.windll.user32.SetClipboardData
SetClipboardData.argtypes = UINT, HANDLE
SetClipboardData.restype = HANDLE
CloseClipboard = ctypes.windll.user32.CloseClipboard
CloseClipboard.restype = BOOL
CF_UNICODETEXT = 13

GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalAlloc.argtypes = UINT, SIZE_T
GlobalAlloc.restype = HGLOBAL
GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalLock.argtypes = HGLOBAL,
GlobalLock.restype = LPVOID
GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
GlobalUnlock.argtypes = HGLOBAL,
GlobalSize = ctypes.windll.kernel32.GlobalSize
GlobalSize.argtypes = HGLOBAL,
GlobalSize.restype = SIZE_T

GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

unicode_type = type(u'')

def clean():
	OpenClipboard(None)
	EmptyClipboard()
	CloseClipboard()

def get():
	text = None
	OpenClipboard(None)
	handle = GetClipboardData(CF_UNICODETEXT)
	pcontents = GlobalLock(handle)
	size = GlobalSize(handle)
	if pcontents and size:
		raw_data = ctypes.create_string_buffer(size)
		ctypes.memmove(raw_data, pcontents, size)
		text = raw_data.raw.decode('utf-16le').rstrip(u'\0')
	GlobalUnlock(handle)
	CloseClipboard()
	return text

def put(text):
	if not isinstance(text, unicode_type):
		text = text.decode('mbcs')
	data = text.encode('utf-16le')
	OpenClipboard(None)
	EmptyClipboard()
	handle = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data) + 2)
	pcontents = GlobalLock(handle)
	ctypes.memmove(pcontents, data, len(data))
	GlobalUnlock(handle)
	SetClipboardData(CF_UNICODETEXT, handle)
	CloseClipboard()
