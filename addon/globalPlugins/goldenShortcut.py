# -*- coding: utf-8 -*-
# golden shortcut
# Copyright (C) 2025
# Version 1.0
# License GNU GPL
# Date: 25/12/2025
# work: Anna Zych-Pawlewicz + the authors of Golden Cursor

# Define context sensitive keyboard shortcuts for Papenmeier braille terminals  

import threading
import os
from configobj import ConfigObj
import globalPluginHandler
import inputCore
import gui
import wx
import config
import globalVars
import scriptHandler
import ui
import api
import winUser
import versionInfo
import addonHandler

##tu wykomentujemy translatora na razie
#addonHandler.initTranslation()

# Each global constant is prefixed with "GS".

# Constants
GSProfiles = os.path.join(globalVars.appArgs.configPath, "addons", "goldenShortcut", "Profiles")
shotCut = "none"

#we are not using this at the moment, not sure why GC is using it
class EnterName(wx.TextEntryDialog):
	"""
	This subclass of the wx.TextEntryDialog class was created to
	prevent multiple instances of the dialog box that propose to give a name to the current mouse position.
	This dialog can be opened via the script_saveMousePosition accessible with the nvda+shift+l shortcut.
	"""
	# The following comes from exit dialog class from GUI package (credit: NV Access and Zahari from Bulgaria).
	_instance = None

	def __new__(cls, parent, *args, **kwargs):
		inst = cls._instance() if cls._instance else None
		if not inst:
			return super(cls, cls).__new__(cls, parent, *args, **kwargs)
		return inst

	def __init__(self, *args, **kwargs):
		inst = EnterName._instance() if EnterName._instance else None
		if inst:
			return
		# Use a weakref so the instance can die.
		import weakref
		EnterName._instance = weakref.ref(self)

		super(EnterName, self).__init__(*args, **kwargs)

# beda potrzebne dwie takie klasy - jedna do trybu a druga do wprowadzania skrotow
class ProfileList(wx.Dialog):
	"""
	This dialog is for listing the profiles saved for the current application
    For now, it is accesible via script script_ProfileList activated by nvda+control+p shortcut
	"""
	# The following comes from exit dialog class from GUI package (credit: NV Access and Zahari from Bulgaria).
	_instance = None

	def __new__(cls, parent, *args, **kwargs):
		inst = cls._instance() if cls._instance else None
		if not inst:
			return super(cls, cls).__new__(cls, parent, *args, **kwargs)
		return inst

	def __init__(self, parent, appName=None):
		inst = PositionsList._instance() if PositionsList._instance else None
		if inst:
			return
		# Use a weakref so the instance can die.
		import weakref
		PositionsList._instance = weakref.ref(self)

		if appName:
			super(PositionsList, self).__init__(parent, title=_("Profile selector for %s") % (appName), size=(420, 300))
			self.ListProfileList(appName=appName)
		else:
    #       TU JAKIS KoMUNIKAT BLEDU
            gui.messageBox(
				# Translators: An error displayed when the application on focus was not found.
				_("Sorry, something went terribly wrong."),
				_("Error"), wx.OK | wx.ICON_ERROR, self
			)

	def ListProfileList(self, appName):
		self.appName = appName
        # If the files path does not exist, create it now.
		if not os.path.exists(GSProfiles):
            os.mkdir(GSProfiles)
		self.profiles = ConfigObj(os.path.join(GSProfiles, f"{appName}.gs"), encoding="UTF-8")
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: The label for the list view of the profiles in the current application.
		profilesText = _("&Saved profiles")
		self.ListProfileList = sHelper.addLabeledControl(
			profilesText, wx.ListCtrl, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(550, 350)
		)
        self.listItems()
        if(self.ListProfileList.GetItemCount()>0)
            self.ListProfileList.Select(0, on=1)
            self.ListProfileList.SetItemState(0, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
		
		bHelper = gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL)

		activateButtonID = wx.NewIdRef()
		# Translators: the button to activate a profile position.
		bHelper.addButton(self, activateButtonID, _("&Activate"), wx.DefaultPosition)

		defineButtonID = wx.NewIdRef()
		# Translators: the button to define the shortcuts for this profile.
		bHelper.addButton(self, defineButtonID, _("&Define"), wx.DefaultPosition)

		renameButtonID = wx.NewIdRef()
		# Translators: the button to rename a profile name.
		bHelper.addButton(self, renameButtonID, _("&Rename"), wx.DefaultPosition)

		deleteButtonID = wx.NewIdRef()
		# Translators: the button to delete the profile.
		bHelper.addButton(self, deleteButtonID, _("&Delete"), wx.DefaultPosition)

		newButtonID = wx.NewIdRef()
		# Translators: the button to create a new profile for this app.
		bHelper.addButton(self, newButtonID, _("&New"), wx.DefaultPosition)

		# Translators: The label of a button to close the profile listing dialog.
		bHelper.addButton(self, wx.ID_CLOSE, _("&Close"), wx.DefaultPosition)

		sHelper.addItem(bHelper)

		self.Bind(wx.EVT_BUTTON, self.onActivate, id=activateButtonID)
		self.Bind(wx.EVT_BUTTON, self.onDefine, id=defineButtonID)
        self.Bind(wx.EVT_BUTTON, self.onRename, id=renameButtonID)
		self.Bind(wx.EVT_BUTTON, self.onDelete, id=deleteButtonID)
		self.Bind(wx.EVT_BUTTON, self.onNew, id=newButtonID)
		self.Bind(wx.EVT_BUTTON, lambda evt: self.Close(), id=wx.ID_CLOSE)

		# Borrowed from NVDA Core (add-ons manager).
		# To allow the dialog to be closed with the escape key.
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.EscapeId = wx.ID_CLOSE

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Sizer = mainSizer
		mainSizer.Fit(self)
		self.ListProfileList.SetFocus()
		self.CenterOnScreen()
        
    def listItems(self):
        # Translators: the column in profile list to identify the profile name.
		self.ListProfileList.InsertColumn(0, _("Name"), width=150)
		self.ListProfileList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onActivate)
		
        if len(self.profiles):
            for entry in sorted(self.profiles.keys()):
                self.ListProfileList.Append((entry))

	def onRename(self, event):
		if self.ListProfileList.GetItemCount() == 0:
            return;
        index = self.ListProfileList.GetFirstSelected()
		oldName = self.ListProfileList.GetItemText(index)
		name = wx.GetTextFromUser(
			# Translators: The label of a field to enter a new name for a profile.
			_("New name"),
			# Translators: The title of the dialog to rename a profile.
			_("Rename"), oldName
		)
		# When escape is pressed, an empty string is returned.
		if name in ("", oldName):
			return
		if name in self.positions:
			gui.messageBox(
				# Translators: An error displayed when renaming a profile
				# with the new name already exists.
				_("Another profile has the same name as the entered name. Please choose a different name."),
				_("Error"), wx.OK | wx.ICON_ERROR, self
			)
			return
		self.ListProfileList.SetItemText(index, name)
		self.ListProfileList.SetFocus()
		self.profiles[name] = self.profiles[oldName]
		del self.profiles[oldName]
        
    def onNew(self,event):
        name = wx.GetTextFromUser(
			# Translators: The label of a field to enter a new name for a mouse position/tag.
			_("Profile name"),
            # Translators: The title of the dialog to rename a mouse position.
            _("New profile")
		)
		# When escape is pressed, an empty string is returned.
		if name in (""):
			return
		if name in self.positions:
			gui.messageBox(
				# Translators: An error displayed when renaming a mouse position
				# and a tag with the new name already exists.
				_("Another profile has the same name as the entered name. Please choose a different name."),
				_("Error"), wx.OK | wx.ICON_ERROR, self
			)
			return
        self.ListProfileList.InsertItem(self.ListProfileList.GetItemCount(),name)
        self.profiles[name]=""
        
        if(self.ListProfileList.GetItemCount()==1):
            self.ListProfileList.Select(0, on=1)
            self.ListProfileList.SetItemState(0, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
        self.ListProfileList.SetFocus()

    def onDelete(self,event):
        if self.ListProfileList.GetItemCount() == 0:
            return;
        message, title = "", ""
        entry = self.ListProfileList.GetFirstSelected()
        name = self.ListProfileList.GetItemText(entry)
        message = _(
				# Translators: The confirmation prompt displayed when the user requests to delete the selected tag.
				"Are you sure you want to delete the position named {name}? This cannot be undone."
			).format(name=name)
        # Translators: The title of the confirmation dialog for deletion of selected position.
		title = _("Delete position")
        if gui.messageBox(
			message, title, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self
		) == wx.NO:
			return
		
		del self.profiles[name]
		self.ListProfileList.DeleteItem(entry)
		if self.ListProfileList.GetItemCount() > 0:
			self.ListProfileList.Select(0, on=1)
        self.ListProfileList.SetFocus()

	def onActivate(self, event):
        return


    def onDefine(self,event):
        return

	def onClose(self, evt):
		self.Destroy()
		if len(self.positions):
			self.positions.write()
        else:
            os.remove(self.profiles.filename)
		self.positions = None


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Golden Cursor")

	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.getAppRestriction = None
		self.restriction = False
		self.mouseArrows = False
#		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(GoldenCursorSettings)
#
#	def terminate(self):
#		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(GoldenCursorSettings)

	@scriptHandler.script(
		# Translators: input help message for a Golden Cursor command.
		description=_("Opens a dialog listing profiles for the current application"),
		gesture="kb:nvda+control+p"
	)
	def script_ProfileList(self, gesture):
		appName = api.getForegroundObject().appModule.appName
#		if not os.path.exists(os.path.join(GCMousePositions, f"{appName}.gc")):
#			# Translators: message presented when no mouse positions are available for the focused app.
#			ui.message(_("No mouse positions for %s.") % appName)
#		else:
		try:
			d = ProfileList(parent=gui.mainFrame, appName=appName)
			gui.mainFrame.prePopup()
			d.Raise()
			d.Show()
			gui.mainFrame.postPopup()
		except RuntimeError:
			pass

	#@scriptHandler.script(
	#	# Translators: Input help message for a Golden Cursor command.
	#	description=_("Opens a dialog to label the current mouse position and saves it"),
	#	gesture="kb:nvda+shift+l"
	#)
    #
	#def script_saveMousePosition(self, gesture):
	#	x, y = winUser.getCursorPos()
	#	# Stringify coordinates early.
	#	x, y = str(x), str(y)
	#	d = EnterPositionName(
	#		# Translators: edit field label for new mouse position.
	#		gui.mainFrame, _("Enter the name for the current mouse position (x: {positionX}, Y: {positionY}").format(
	#			positionX=x, positionY=y
	#		),
	#		# Translators: title for save mouse position dialog.
	#		_("Save mouse position")
	#	)
#
	#	def callback(result):
	#		if result == wx.ID_OK:
	#			name = d.GetValue().rstrip()
	#			if name == "":
	#				return
	#			appName = self.getMouse().appModule.appName
	#			# If the files path does not exist, create it now.
	#			if not os.path.exists(GCMousePositions):
	#				os.mkdir(GCMousePositions)
	#			position = ConfigObj(os.path.join(GCMousePositions, f"{appName}.gc"), encoding="UTF-8")
	#			position[name] = ",".join([x, y])
	#			position.write()
	#			# Translators: presented when position (tag) has been saved.
	#			ui.message(_("Position saved in %s.") % position.filename)
	#	gui.runScriptModalDialog(d, callback)
#
#	@scriptHandler.script(
#		# Translators: input help message for a Golden Cursor command.
#		description=_("Changes mouse movement unit"),
#		gesture="kb:nvda+windows+c"
#	)
#	def script_mouseMovementChange(self, gesture):
#		pixelUnits = (1, 5, 10, 20, 50, 100)
#		movementUnit = config.conf["goldenCursor"]["mouseMovementUnit"]
#		pixelUnitChoices = len(pixelUnits)
#		try:
#			index = pixelUnits.index(movementUnit)
#			movementUnit = pixelUnits[(index + 1) % pixelUnitChoices]
#		except ValueError:
#			for unit in pixelUnits:
#				# No need to check for equality because the try block does this already.
#				if movementUnit < unit:
#					movementUnit = unit
#					break
#		config.conf["goldenCursor"]["mouseMovementUnit"] = movementUnit
#		ui.message(str(movementUnit))
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor add-on command.
#		description=_("toggles reporting of mouse coordinates in pixels when mouse moves"),
#		gesture="kb:nvda+windows+s"
#	)
#	def script_toggleSpeakPixels(self, gesture):
#		sayPixel = config.conf["goldenCursor"]["reportNewMouseCoordinates"]
#		sayPixel = not sayPixel
#		if sayPixel:
#			# Translators: reported when new mouse coordinate announcement is on.
#			ui.message(_("Report new mouse coordinates on"))
#		else:
#			# Translators: reported when new mouse coordinate announcement is on.
#			ui.message(_("Report new mouse coordinates off"))
#		config.conf["goldenCursor"]["reportNewMouseCoordinates"] = sayPixel
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Reports current X and Y mouse position"),
#		gesture="kb:nvda+windows+p"
#	)
#	def script_sayPosition(self, gesture):
#		reportMousePosition()
#
#	@scriptHandler.script(
#		# Translators: input help mode message for a Golden Cursor add-on command.
#		description=_("Toggles mouse arrows to move the mouse with the arrow keys"),
#		gesture="kb:nvda+windows+m"
#	)
#	def script_toggleMouseArrows(self, gesture):
#		self.mouseArrows = not self.mouseArrows
#		if self.mouseArrows:
#			self.bindGesture("kb:rightArrow", "moveMouseRight")
#			self.bindGesture("kb:leftArrow", "moveMouseLeft")
#			self.bindGesture("kb:downArrow", "moveMouseDown")
#			self.bindGesture("kb:upArrow", "moveMouseUp")
#			# Translators: presented when toggling mouse arrows feature.
#			ui.message(_("Mouse arrows on"))
#		else:
#			self.clearGestureBindings()
#			self.bindGestures(self.__gestures)
#			# Translators: presented when toggling mouse arrows feature.
#			ui.message(_("Mouse arrows off"))
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Moves the Mouse pointer to the right"),
#		gesture="kb:nvda+windows+rightArrow"
#	)
#	def script_moveMouseRight(self, gesture):
#		self.moveMouse(GCMouseRight)
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Moves the Mouse pointer to the left"),
#		gesture="kb:nvda+windows+leftArrow"
#	)
#	def script_moveMouseLeft(self, gesture):
#		self.moveMouse(GCMouseLeft)
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Moves the Mouse pointer down"),
#		gesture="kb:nvda+windows+downArrow"
#	)
#	def script_moveMouseDown(self, gesture):
#		self.moveMouse(GCMouseDown)
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Moves the Mouse pointer up"),
#		gesture="kb:nvda+windows+upArrow"
#	)
#	def script_moveMouseUp(self, gesture):
#		self.moveMouse(GCMouseUp)
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Opens a dialog to enter the X and Y coordinates for the mouse to move to"),
#		gesture="kb:nvda+windows+j"
#	)
#	def script_goToPosition(self, gesture):
#		try:
#			d = PositionsList(parent=gui.mainFrame, goto=True)
#			gui.mainFrame.prePopup()
#			d.Raise()
#			d.Show()
#			gui.mainFrame.postPopup()
#		except RuntimeError:
#			pass
#
#	@scriptHandler.script(
#		# Translators: Input help message for a Golden Cursor command.
#		description=_("Toggles mouse movement restriction between current application and unrestricted"),
#		gesture="kb:nvda+windows+r"
#	)
#	def script_toggleMouseRestriction(self, gesture):
#		self.getAppRestriction = self.getMouse()
#		self.restriction = not self.restriction
#		if self.restriction:
#			# Translators: presented when mouse movement is restricted to current application.
#			ui.message(_("Mouse movement restricted to current application"))
#		else:
#			# Translators: presented when mouse movement is unrestricted.
#			ui.message(_("Mouse movement unrestricted"))
#
#	def moveMouse(self, direction):
#		w, h = api.getDesktopObject().location[2:]
#		x, y = winUser.getCursorPos()
#		oldX, oldY = x, y
#		pixelMoving = config.conf["goldenCursor"]["mouseMovementUnit"]
#		if direction == GCMouseRight:
#			x += pixelMoving
#		elif direction == GCMouseLeft:
#			x -= pixelMoving
#		elif direction == GCMouseDown:
#			y += pixelMoving
#		elif direction == GCMouseUp:
#			y -= pixelMoving
#		# Just do a chain comparison, as it is a lot faster.
#		if 0 <= x < w and 0 <= y < h:
#			setMousePosition(x, y)
#		else:
#			wx.Bell()
#			return
#		if self.restriction and self.getAppRestriction.appModule.appName != self.getMouse().appModule.appName:
#			wx.Bell()
#			setMousePosition(oldX, oldY)
#			if self.getAppRestriction.appModule.appName != self.getMouse().appModule.appName:
#				x, y, w, h = self.getAppRestriction.location
#				setMousePosition(x, y)
#			return
#		if config.conf["goldenCursor"]["reportNewMouseCoordinates"]:
#			ui.message(str(x if direction in (GCMouseRight, GCMouseLeft) else y))
#
#	def getMouse(self):
#		return api.getDesktopObject().objectFromPoint(*winUser.getCursorPos())
#
#
## Add-on config database
## Borrowed from Enhanced Touch Gestures by Joseph Lee
#confspec = {
#	"reportNewMouseCoordinates": "boolean(default=true)",
#	"mouseMovementUnit": "integer(min=1, max=100, default=5)",
#}
#config.conf.spec["goldenCursor"] = confspec
#
## this we will not need at all (for now) - soon to be commented out
#class GoldenCursorSettings(gui.settingsDialogs.SettingsPanel):
#	# Translators: This is the label for the Golden Cursor settings category in NVDA Settings screen.
#	title = _("Golden Cursor")
#
#	def makeSettings(self, settingsSizer):
#		gcHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
#		self.mouseCoordinatesCheckBox = gcHelper.addItem(
#			# Translators: This is the label for a checkbox in the
#			# Golden Cursor settings dialog.
#			wx.CheckBox(self, label=_("&Announce new mouse coordinates when mouse moves"))
#		)
#		self.mouseCoordinatesCheckBox.SetValue(config.conf["goldenCursor"]["reportNewMouseCoordinates"])
#		self.mouseMovementUnit = gcHelper.addLabeledControl(
#			# Translators: The label for a setting in Golden Cursor settings dialog to change mouse movement units.
#			_("Mouse movement &unit (in pixels)"), gui.nvdaControls.SelectOnFocusSpinCtrl,
#			min=1, max=100, initial=config.conf["goldenCursor"]["mouseMovementUnit"]
#		)
#
#	def onSave(self):
#		config.conf["goldenCursor"]["reportNewMouseCoordinates"] = self.mouseCoordinatesCheckBox.IsChecked()
#		config.conf["goldenCursor"]["mouseMovementUnit"] = self.mouseMovementUnit.Value
#