# To change this template, choose Tools | Templates
# and open the template in the editor.

import wx
import sys
import queVars
import globalConf

import socket

import traceback

import cPickle

class MyFrame(wx.Frame):

	axis = 0


	def __init__(self, * args, ** kwds):



		# begin wxGlade: MyFrame.__init__
		kwds["style"] = wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, * args, ** kwds)


		#self.buttonBlank1 = wx.Panel(self, -1)


		self.__set_properties()
		self.__do_layout()


		self.ipOK = False


		try:
			pikFile = open("targetip.pik", "r")

			targetip = cPickle.load(pikFile)
			pikFile.close()

			#print "Target IP", targetip
			self.ipTextCtrl.SetValue(targetip)
		except:
			#traceback.print_exc(6)
			pass

		self.Bind(wx.EVT_CLOSE, self.quitApp)
		# end wxGlade

	def __set_properties(self):
		# begin wxGlade: MyFrame.__set_properties
		self.SetTitle("Controller IP Setup")
		self.SetSize((600, 110))
		self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE))
		# end wxGlade



	def __mainPanel(self):


		ipEntrySizer = wx.BoxSizer(wx.HORIZONTAL)

		self.ipWindowStaticText = wx.StaticText(self, -1, "Galil Controller IP: ")
		ipEntrySizer.Add(self.ipWindowStaticText, 0, wx.ALL, 5)

		self.ipTextCtrl = wx.TextCtrl(self, -1, "", style = wx.TE_PROCESS_ENTER)
		self.ipTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.evtIpEnter)

		self.TextCtrlFont = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
		self.ipTextCtrl.SetFont(self.TextCtrlFont)
		ipEntrySizer.Add(self.ipTextCtrl, 1, wx.ALL | wx.EXPAND, 3)

		self.selectIpButton = wx.Button(self, -1, "Ok")
		ipEntrySizer.Add(self.selectIpButton, 0, wx.ALL, 3)
		self.selectIpButton.Bind(wx.EVT_BUTTON, self.evtIpEnter)

		return ipEntrySizer
	def __subPanel(self):

		statusSizer = wx.BoxSizer(wx.HORIZONTAL)


		self.noticeText = wx.StaticText(self, -1, "Please Enter Galil Controller IP", name = "")
		statusSizer.Add(self.noticeText, 1, wx.ALL|wx.EXPAND, 5)

		self.fakeGalilCheckbox = wx.CheckBox(self, style = wx.ALIGN_CENTRE, label = "Fake Galil")
		self.fakeGalilCheckbox.Bind(wx.EVT_CHECKBOX, self.changeFakeGalilState)
		statusSizer.Add(self.fakeGalilCheckbox, 0, wx.ALL, 5)

		return statusSizer

	def __do_layout(self):
		# begin wxGlade: MyFrame.__do_layout


		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainSizer.Add(self.__mainPanel(), 0, wx.EXPAND, 0)


		mainSizer.Add(self.__subPanel(), 1, wx.EXPAND | wx.ALL, 5)

		self.SetSizer(mainSizer)

		self.Layout()
		# end wxGlade
	def changeFakeGalilState(self, event):
		globalConf.fakeGalil = self.fakeGalilCheckbox.IsChecked()
		if not self.fakeGalilCheckbox.IsChecked():
			self.ipOK = False
			self.evtIpEnter(None)

	def evtIpEnter(self, event):
		self.noticeText.SetLabel("Checking IP")
		wx.GetApp().Yield()
		ipAddress = self.ipTextCtrl.GetValue()

		if self.fakeGalilCheckbox.IsChecked():
			self.ipOK = True
			self.Destroy()
		elif len(ipAddress.split(".")) == 4:
			try:
				con = socket.create_connection((ipAddress, 501), 1)
				con.shutdown(socket.SHUT_RDWR)
				con.close()

				self.noticeText.SetLabel("IP Valid")
				self.ipOK = True

				pikFile = open("targetip.pik", "w")
				cPickle.dump(self.ipTextCtrl.GetValue(), pikFile)
				pikFile.close()

				self.Destroy()
			except:
				traceback.print_exc()
				self.noticeText.SetLabel("Failed to open connection. Are you sure the IP is correct?")
			queVars.galilIP = ipAddress


		else:
			self.noticeText.SetLabel("Error: Invalid IP")


	def quitApp(self, event): # wxGlade: MainFrame.<event_handler>
		print "Exiting"

		if self.ipOK:

			self.Destroy()
		else:
			sys.exit()



class IpChecker(wx.App):
	def OnInit(self):
		wx.InitAllImageHandlers()
		mainFrame = MyFrame(None, -1, "")
		self.SetTopWindow(mainFrame)
		mainFrame.Show()
		return 1

