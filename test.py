import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import sys
import csv
import PyQt4
import plot
import ply.lex as lex
import ply.yacc as yacc
from sys import stdout
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore
import os

#matplotlib.use("QT4Agg")
	
fields = []														#stores the column(field) names
col_with_strings = []											#stores names of those columns which can have strings as values 
col_fil_list = {}												#stores the upper and lower limits(set by user) of each columns(used in column filtering)
cfg_file_name = "cfg.csv"										#the default "configure file"
lower_limit = {}												#stores the lower limit of each columns(from the file)
upper_limit = {}												#stores the upper limit of each columns(from the file)
lll = []														#temporary variable used to calculate lower limit (lll = lower limit list)
ull = []														#temporary variable used to calculate upper limit (ull = upper limit list)
out_list = []													#stores the items to be outputted in configure file
curr_filename = ""												#stores the current file name
change = 0														#used to sync the sliders and combo boxes
cons={}															#dictionary to store values of fields applied in generate constraints box		
final_constraints=[]											#list of all constraints to generate constraints file
undo_old = ""													#stores old configuration string which can be recovered on pressing undo		
undo_new = ""													#stores configuration string on update press
write = ""														#stores the string to be written in constraints.ecl
range_constraints_string =""									#hardcoded string (added for now for the tool)
class col_filtering_window(QWidget):							#defines the class for column filtering window
	def __init__(self):
		super(col_filtering_window,self).__init__()

		self.setWindowTitle("Column Filtering")

		lay_range = QVBoxLayout()
		lay_main = QHBoxLayout()
		lay_but = QHBoxLayout()
		lay_final = QVBoxLayout()
		lay_l = QHBoxLayout()
		lay_h = QHBoxLayout()

		self.low = QLabel("Lower Limit")
		self.low.setAlignment(Qt.AlignLeft)
		self.up = QLabel("Upper Limit")
		self.up.setAlignment(Qt.AlignLeft)
		
		self.cb = QComboBox()

		self.sl_l = QSlider(Qt.Horizontal)
		self.sl_l.setRange(0,100)

		self.sl_h = QSlider(Qt.Horizontal)
		self.sl_h.setRange(0,100)
		
		self.sp_l = QDoubleSpinBox()
		self.sp_l.valueChanged.connect(self.sp_l_valuechange)
		self.sp_l.setDecimals(6)

		self.sp_h = QDoubleSpinBox()
		self.sp_h.valueChanged.connect(self.sp_h_valuechange)
		self.sp_h.setDecimals(6)

		self.sl_l.valueChanged.connect(self.print_l)
		self.sl_h.valueChanged.connect(self.print_h)

		self.apply_but = QPushButton('&Apply')
		self.apply_but.setDefault(True)
		self.apply_but.clicked.connect(self.apply_func)

		self.cancel_but = QPushButton('&Reset')
		self.cancel_but.setDefault(True)
		self.cancel_but.clicked.connect(self.cancel_func)

		self.reset_all_but = QPushButton('&Reset All')
		self.reset_all_but.setDefault(True)
		self.reset_all_but.clicked.connect(self.reset_all_func)

		self.ok_but = QPushButton('&OK')
		self.ok_but.setDefault(True)
		self.ok_but.clicked.connect(self.ok_func)

		self.cb.currentIndexChanged.connect(self.selectionchange)

		lay_l.addWidget(self.sl_l)
		lay_l.addWidget(self.sp_l)
		lay_h.addWidget(self.sl_h)
		lay_h.addWidget(self.sp_h)

		lay_range.addWidget(self.low)
		lay_range.addLayout(lay_l)
		lay_range.addWidget(self.up)
		lay_range.addLayout(lay_h)

		lay_main.addWidget(self.cb)
		lay_main.addLayout(lay_range)

		lay_but.addWidget(self.ok_but,0,Qt.AlignLeft)
		lay_but.addWidget(self.apply_but,0,Qt.AlignRight)
		lay_but.addWidget(self.cancel_but,0,Qt.AlignRight)
		lay_but.addWidget(self.reset_all_but,0,Qt.AlignRight)

		lay_final.addLayout(lay_main)
		lay_final.addLayout(lay_but)	

		self.setLayout(lay_final)

	def sp_l_valuechange(self):									#changes value of lower slider based on value of lower spin box
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.sp_l.value())
			else:
				a = (int)(((self.sp_l.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.sp_l.value())
		self.sl_l.setValue(a)		

	def sp_h_valuechange(self):									#changes value of upper slider based on value of upper spin box
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b]==lower_limit[b]:
				a = (int)(self.sp_h.value())
			else:
				a = (int)(((self.sp_h.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.sp_h.value())
		self.sl_h.setValue(a)

	def print_l(self):											#changes value of lower spin box based on value of lower slider
		global change
		if change == 1:
			change = 0
		else :
			b = str(PyQt4.QtCore.QString(self.cb.currentText()))
			if b in lower_limit.keys():
				a = lower_limit[b] + (((float)(self.sl_l.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.sl_l.value())
			self.sp_l.setValue(a)      

	def print_h(self):											#changes value of upper spin box based on value of upper slider
		global change
		if change == 1:
			change = 0
		else :
			b = str(PyQt4.QtCore.QString(self.cb.currentText()))
			if b in lower_limit.keys():
				a = lower_limit[b] + (((float)(self.sl_h.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.sl_h.value())
			self.sp_h.setValue(a)      

	def selectionchange(self):									#changes values of both spin boxes and sliders based on the field
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		if(lower_limit):
			(temp_ll,temp_ul)=col_fil_list[b]
			self.sp_l.setRange(lower_limit[b],upper_limit[b])
			self.sp_h.setRange(lower_limit[b],upper_limit[b])
			self.sp_l.setValue(temp_ll)
			self.sp_h.setValue(temp_ul)
			if b in lower_limit.keys():
				if upper_limit[b] == lower_limit[b]:
					a = (int)(self.sp_l.value())
				else:
					a = (int)(((self.sp_l.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
			else:
				a = (int)(self.sp_l.value())
			self.sl_l.setValue(a)
			if b in lower_limit.keys():
				if upper_limit[b] == lower_limit[b]:
					a = (int)(self.sp_h.value())
				else:
					a = (int)(((self.sp_h.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
			else:
				a = (int)(self.sp_h.value())
			self.sl_h.setValue(a)

	def reset_all_func(self):									#Resets the sliders and spin boxes in column filtering window
		for b in col_fil_list.keys():
			col_fil_list[b]=(lower_limit[b],upper_limit[b])
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		self.sp_l.setValue(lower_limit[b])
		self.sp_h.setValue(upper_limit[b])
		self.sl_l.setValue(0)
		self.sl_h.setValue(100)

	def apply_func(self):										#stores the upper and lower limit of the current field(as set by user) in col_fill_list[]
		global col_fil_list
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		if self.sp_l.value()>self.sp_h.value():					
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Lower limit greater than upper limit for x-axis")
			msg.setWindowTitle("Error")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
		else:
			col_fil_list[b]=(self.sp_l.value(),self.sp_h.value())

	def cancel_func(self):										#resets the value of current field if previously stored(changess it back to the maximum upper limit and minimum lower limit as seen from file)
		global col_fil_list
		global lower_limit
		global upper_limit
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		col_fil_list[b]=(lower_limit[b],upper_limit[b])
		self.sp_l.setValue(lower_limit[b])
		self.sp_h.setValue(upper_limit[b])
		self.sl_l.setValue(0)
		self.sl_h.setValue(100)

	def ok_func(self):											#same as apply, but closes the column filtering window afterwards
		global col_fil_list
		b = str(PyQt4.QtCore.QString(self.cb.currentText()))
		if self.sp_l.value()>self.sp_h.value():
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Lower limit greater than upper limit for x-axis")
			msg.setWindowTitle("Error")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
		else:
			col_fil_list[b]=(self.sp_l.value(),self.sp_h.value())
		self.close()



	
class update_constraints_window(QWidget):			# WINDOW TO GENERATE CONSTRAINTS FILE
	def __init__(self):
		super(update_constraints_window,self).__init__()
		self.setWindowTitle(" Setting constraints ")


		self.cb = QComboBox()
		self.cb.clear()
		

		# LOWER
		self.lower_limit_label = QLabel("Lower limit: ")
		self.lower_limit = QLineEdit()
		self.lower_limit_label.setEnabled(False)
		self.lower_limit.setEnabled(False)

		lay_lower_limit = QHBoxLayout();
		lay_lower_limit.addWidget(self.lower_limit_label)
		lay_lower_limit.addWidget(self.lower_limit)

		self.enable_lower_limit = QCheckBox("Enable lower limit")
		self.enable_lower_limit.setChecked(False)
		self.enable_lower_limit.stateChanged.connect(self.lower_limit_func)

		lower_limitf = QVBoxLayout();
		lower_limitf.addWidget(self.enable_lower_limit)
		lower_limitf.addLayout(lay_lower_limit)


		#	UPPER
		self.upper_limit_label = QLabel("Upper Limit: ")
		self.upper_limit = QLineEdit()
		self.upper_limit_label.setEnabled(False)
		self.upper_limit.setEnabled(False)

		lay_upper_limit = QHBoxLayout();
		lay_upper_limit.addWidget(self.upper_limit_label)
		lay_upper_limit.addWidget(self.upper_limit)

		self.enable_upper_limit = QCheckBox("Enable upper limit")
		self.enable_upper_limit.setChecked(False)
		self.enable_upper_limit.stateChanged.connect(self.upper_limit_func)

		upper_limitf = QVBoxLayout();
		upper_limitf.addWidget(self.enable_upper_limit)
		upper_limitf.addLayout(lay_upper_limit)


		# DISCRETE VALUES
		self.allowed_values_label = QLabel("List of allowed values: ")
		self.allowed_values = QLineEdit()
		self.allowed_values_label.setEnabled(False)
		self.allowed_values.setEnabled(False)

		lay_allowed_values = QHBoxLayout();
		lay_allowed_values.addWidget(self.allowed_values_label)
		lay_allowed_values.addWidget(self.allowed_values)

		self.enable_allowed_values = QCheckBox("Enable values insertion")
		self.enable_allowed_values.setChecked(False)
		self.enable_allowed_values.stateChanged.connect(self.discrete_values_func)

		allowed_valuesf = QVBoxLayout();
		allowed_valuesf.addWidget(self.enable_allowed_values)
		allowed_valuesf.addLayout(lay_allowed_values)

		
		choose = QVBoxLayout();
		choose.addLayout(lower_limitf)
		choose.addLayout(upper_limitf)
		choose.addLayout(allowed_valuesf)

		
		lay_constraints = QHBoxLayout()
		lay_constraints.addWidget(self.cb)
		lay_constraints.addLayout(choose)


		self.apply_but = QPushButton('&Apply')
		self.apply_but.setDefault(True)
		self.apply_but.clicked.connect(self.apply_func)

		self.generate_but = QPushButton('&Generate')
		self.generate_but.setDefault(True)
		self.generate_but.clicked.connect(self.generate_func)

		self.cancel_but = QPushButton('&Cancel')
		self.cancel_but.setDefault(True)
		self.cancel_but.clicked.connect(self.cancel_func)

		lay_buttons = QHBoxLayout()
		lay_buttons.addWidget(self.apply_but)
		lay_buttons.addWidget(self.generate_but)
		lay_buttons.addWidget(self.cancel_but)


		layout_final = QVBoxLayout()                          #final layout of window
		layout_final.addLayout(lay_constraints)
		layout_final.addLayout(lay_buttons)
		

		self.setLayout(layout_final)

	def lower_limit_func(self):								#to enable/disable lower limit bar
		if self.enable_lower_limit.isChecked():
			self.lower_limit_label.setEnabled(True)
			self.lower_limit.setEnabled(True)

			self.enable_allowed_values.setEnabled (False)
		else:
			self.lower_limit_label.setEnabled(False)
			self.lower_limit.setEnabled(False)

			self.enable_allowed_values.setEnabled (True)
			

	def upper_limit_func(self):								#to enable/disable upper limit bar
		if self.enable_upper_limit.isChecked():
			self.upper_limit_label.setEnabled(True)
			self.upper_limit.setEnabled(True)

			self.enable_allowed_values.setEnabled (False)
		else:
			self.upper_limit_label.setEnabled(False)
			self.upper_limit.setEnabled(False)

			self.enable_allowed_values.setEnabled (True)
			

	def discrete_values_func(self):								#to enable/disable discrete values bar
		if self.enable_allowed_values.isChecked():
			self.allowed_values_label.setEnabled(True)
			self.allowed_values.setEnabled(True)

			self.enable_lower_limit.setEnabled (False)
			self.enable_upper_limit.setEnabled (False)

		else:
			self.allowed_values_label.setEnabled(False)
			self.allowed_values.setEnabled(False)

			self.enable_lower_limit.setEnabled (True)
			self.enable_upper_limit.setEnabled (True)



	def apply_func(self):										#stores the upper and lower limit of the current field(as set by user) in cons{}
		
		global cons
		b=str(PyQt4.QtCore.QString(self.cb.currentText()))
		if (self.enable_allowed_values.isChecked()):
			values = (self.allowed_values.text())
			cons[b]=[3,str(values)]
			#print cons[b]
		elif (self.enable_lower_limit.isChecked() and self.enable_upper_limit.isChecked()):
			ll = float(self.lower_limit.text())
			ul = float(self.upper_limit.text())
			if (ll>ul):
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Lower limit greater than upper limit")
				msg.setWindowTitle("Error")
				msg.setStandardButtons(QMessageBox.Ok)
				msg.exec_()
			else:
				cons[b]=[2,ll,ul]
		elif (self.enable_lower_limit.isChecked()):
			ll=float(self.lower_limit.text())
			cons[b]=[0,ll]
		elif (self.enable_upper_limit.isChecked()):
			ul = float(self.upper_limit.text())
			cons[b]=[1,ul]

		self.lower_limit.setText('')
		self.upper_limit.setText('')
		self.allowed_values.setText('')
		self.lower_limit_label.setEnabled(False)
		self.lower_limit.setEnabled(False)
		self.upper_limit_label.setEnabled(False)
		self.upper_limit.setEnabled(False)
		self.enable_lower_limit.setChecked(False)
		self.enable_upper_limit.setChecked(False)
		self.enable_allowed_values.setChecked(False)	




	def generate_func(self):						

		global cons 									# dictionary to store the final constraints
		global final_constraints						
		global undo_old
		global undo_new
		global write
		global range_constraints_string
		b=str(PyQt4.QtCore.QString(self.cb.currentText()))
		if (self.enable_allowed_values.isChecked()):
			values = (self.allowed_values.text())
			cons[b]=[3,str(values)]									# 3 denotes insertion of discrete values
			#print cons[b]
		elif (self.enable_lower_limit.isChecked() and self.enable_upper_limit.isChecked()):
			ll = float(self.lower_limit.text())
			ul = float(self.upper_limit.text())
			if (ll>ul):
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Lower limit greater than upper limit")
				msg.setWindowTitle("Error")
				msg.setStandardButtons(QMessageBox.Ok)
				msg.exec_()
			else:
				cons[b]=[2,ll,ul]									# 2 implies both upper and lower limits have been specified
		elif (self.enable_lower_limit.isChecked()):
			ll=float(self.lower_limit.text())
			cons[b]=[0,ll]											# 0 if only the lower limit specified
		elif (self.enable_upper_limit.isChecked()):
			ul = float(self.upper_limit.text())
			cons[b]=[1,ul]											# 1 if only the upper limit is specified

		#final_constraints list created from the dictionary cons to be written in to the contrainsts file
		if (len(cons)==0):
			final_constraints.append(-1)
			
		else:	
			for field in cons:
				final_constraints.append(field)
				for values in cons[field]:
					final_constraints.append(values)
		f = open("constraints.ecl","w+")
		write = ""
		a = final_constraints[:-1]
		# The list is parsed and the string to be written into the file is created
		i = 0
		while i < len(a):
			if final_constraints[i+1] == 0:
				write += '\n\t'+final_constraints[i].strip()+' $>= '+str(int(final_constraints[i+2]))+','
				i += 3
			elif final_constraints[i+1] == 1:
				write += '\n\t'+final_constraints[i].strip()+' $=< '+str(int(final_constraints[i+2]))+','
				i += 3
			elif final_constraints[i+1] == 2:
				write += '\n\t'+final_constraints[i].strip()+' $>= '+str(int(final_constraints[i+2]))+','
				write += '\n\t'+final_constraints[i].strip()+' $=< '+str(int(final_constraints[i+3]))+','
				i += 4
			else:
				write += '\n\t'+final_constraints[i].strip()+' :: '+str(map(int,final_constraints[i+2].split(" ")))+','
				i += 3
		if len(write)>0:
			write = write[:-1] + '.'; 
		range_constraints_string = "range_constraints("
		for i in fields[:-1]:
			range_constraints_string += i.strip()+", ";
		if (len(fields)>0):
			range_constraints_string += fields[-1].strip()
		range_constraints_string += ") :-"
		range_constraints_string = "range_constraints(Ncore, Battery, MinFrames, WS, Atotal, Blife, Weight) :-" #These fields have been hardcoded for now as it was found some of these fields are necessary for tool to run
		# Remove the above line to make the constraints file according to the fields of the currently open file
		# range_constraints_string += "\t\nNcore :: [1,2,4,8],\n"
		# range_constraints_string += "\tBattery :: [1,2,3,4],\n"
		# range_constraints_string += "\tMinFrames :: [3],\n"
		# range_constraints_string += "\tWS :: [25,50,75,100,125,150],"
		# These are the fields that were present in the original test file
		undo_old = undo_new
		undo_new = write
		f.write(range_constraints_string)
		f.write(write);
		f.close() #constraints file updated
		self.close()
		os.system("../eclipse/bin/x86_64_linux/eclipse -f ../eclipse/tmp/test.ecl -f constraints.ecl -e main,fail") #tool called
		file_change = open("file.txt","r")
		newfile = open("generated.csv","w") #generated.csv removes the leading and trailing brackets present in each line of file.txt
		x = file_change.readlines()
		for i in x:
			newfile.write(i[1:-2]+'\n')
		file_change.close()
		newfile.close()

	def cancel_func(self):										#resets all the constraints set after opening this window
		global final_constraints
		del final_constraints[:]
		global cons
		cons.clear()
	def addItemsinCB(self):   									#adds fields to the combo box with stripped spaces
		self.cb.clear()
		self.cb.addItems([i.strip() for i in fields])    
	

		
		


class sub_window(QWidget):										#class defining the sub windows(as they appear in tabs)

	subwindow_id = 0
	def __init__(self):
		super(sub_window, self).__init__()

		group_box_x = QGroupBox('&X-Axis')
		group_box_y = QGroupBox('&Y-Axis')
		group_box_z = QGroupBox('&Z-Axis/Secondary Y-Axis')
		group_box_3 = QGroupBox('&Third Parameter(Shape)')
		group_box_4 = QGroupBox('&Fourth Parameter(Color)')
		group_box_pareto = QGroupBox('&Pareto Parameters')
		group_box_type_of_graph = QGroupBox('&Type of Graph')
		group_box_curve_fitting = QGroupBox('&Curve Fitting')

		lay_3_4 = QVBoxLayout()
		lay_3_4.addWidget(group_box_3)
		lay_3_4.addWidget(group_box_4)

		self.graph_type = QLabel("Select Type:")									#Adding things in graph_type combo box
		self.graph_type_cb = QComboBox()
		self.graph_type_cb.addItem("scatter")
		self.graph_type_cb.addItem("line")
		self.graph_type_cb.addItem("histogram")
		self.graph_type_cb.addItem("bar-graph")


		lay_graph_type = QVBoxLayout()

		lay_graph_type.addWidget(self.graph_type)
		lay_graph_type.addWidget(self.graph_type_cb)		
		group_box_type_of_graph.setLayout(lay_graph_type)		

		self.degree_label = QLabel("Enter degree:")									
		self.curve_fitting_sb = QSpinBox()
		self.curve_fitting_sb.setMaximum(100)
		self.degree_label.setEnabled(False)
		self.curve_fitting_sb.setEnabled(False)
		self.enable_curve_fitting = QCheckBox("Enable curve fitting")
		self.enable_curve_fitting.setChecked(False)
		self.enable_curve_fitting.stateChanged.connect(self.curve_fitting_func)


		self.graph_type_cb.currentIndexChanged.connect(self.selectionchangetype)


		lay_curve_fitting_h = QHBoxLayout()
		lay_curve_fitting_v = QVBoxLayout()
		lay_curve_fitting_h.addWidget(self.degree_label)
		lay_curve_fitting_h.addWidget(self.curve_fitting_sb)
		lay_curve_fitting_v.addLayout(lay_curve_fitting_h)
		lay_curve_fitting_v.addWidget(self.enable_curve_fitting)
		group_box_curve_fitting.setLayout(lay_curve_fitting_v)		

		lay_curve_fit_graph_type = QVBoxLayout()
		lay_curve_fit_graph_type.addWidget(group_box_type_of_graph)
		lay_curve_fit_graph_type.addWidget(group_box_curve_fitting)

		self.title_label = QLabel("Title:")
		self.title_name = QLineEdit()
		self.title_label.setEnabled(False)
		self.title_name.setEnabled(False)

		self.pareto_x = QLabel("X-axis:")
		self.pareto_y = QLabel("Y-Axis:")
		self.pareto_x.setEnabled(False)
		self.pareto_y.setEnabled(False)
		self.pareto_cbx = QComboBox()
		self.pareto_cby = QComboBox()
		self.pareto_cbx.setEnabled(False)
		self.pareto_cby.setEnabled(False)
		self.pareto_cbx.addItem("Maximize")
		self.pareto_cbx.addItem("Minimize")
		self.pareto_cby.addItem("Maximize")
		self.pareto_cby.addItem("Minimize")

		lay_pareto_x = QHBoxLayout()
		lay_pareto_y = QHBoxLayout()
		lay_pareto_main = QVBoxLayout()
		lay_pareto_final = QVBoxLayout()

		self.enable_plot_pareto = QCheckBox("Plot Pareto Curve")
		self.enable_plot_pareto.setChecked(False)
		self.enable_plot_pareto.stateChanged.connect(self.pareto_func)

		lay_pareto_x.addWidget(self.pareto_x)
		lay_pareto_x.addWidget(self.pareto_cbx)
		lay_pareto_y.addWidget(self.pareto_y)
		lay_pareto_y.addWidget(self.pareto_cby)
		lay_pareto_main.addLayout(lay_pareto_x)
		lay_pareto_main.addLayout(lay_pareto_y)
		lay_pareto_final.addLayout(lay_pareto_main)
		lay_pareto_final.addWidget(self.enable_plot_pareto)

		group_box_pareto.setLayout(lay_pareto_final)

		final_layout = QHBoxLayout()     #final layout including graphic view
		layout = QVBoxLayout()           #main layout
		layout_az = QHBoxLayout()		 #layout for third and fourth parameters group box

		lay_title = QHBoxLayout()        #title layout

		title_f = QVBoxLayout()

		lay_xx = QHBoxLayout()           #layout containins lay_x_s and drop down box for x-axis
		lay_yy = QHBoxLayout()           #layout containing lay_y_s and drop down box for y-axis
		lay_33 = QVBoxLayout()
		lay_44 = QVBoxLayout()
		lay_zz = QVBoxLayout()

		lay_y_custom = QVBoxLayout()
		lay_custom = QHBoxLayout()

		lay_x_s = QVBoxLayout()          #layout for slider x (contains slider and label)
		lay_y_s = QVBoxLayout()          #layout for slider y (contains slider and label)
		lay_z_s = QVBoxLayout()

		lay_z_field = QHBoxLayout()

		lay_xl_sp = QHBoxLayout()        #layouts joining sliders and spin boxes
		lay_xh_sp = QHBoxLayout()
		lay_yl_sp = QHBoxLayout()
		lay_yh_sp = QHBoxLayout()
		lay_zl_sp = QHBoxLayout()
		lay_zh_sp = QHBoxLayout()

		lay_gv = QVBoxLayout()

		lay_up_cb = QHBoxLayout()

		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)
		#self.canvas.setFixedSize(500,500)
		self.toolbar = NavigationToolbar(self.canvas,self)

		self.update_but = QPushButton('&Update')
		self.update_but.setDefault(True)
		self.update_but.clicked.connect(self.update_plot)

		self.column_filtering_but = QPushButton('&Column Filtering')
		self.column_filtering_but.setDefault(True)
		self.column_filtering_but.clicked.connect(self.column_filtering_func)

		
		self.swap_axis_but = QPushButton('&Swap Axis')
		self.swap_axis_but.setDefault(True)
		self.swap_axis_but.clicked.connect(self.swap_axis_func)

		self.update_constraints_but = QPushButton('&Generate constraints file')
		self.update_constraints_but.setDefault(True)
		self.update_constraints_but.clicked.connect(self.constraints_file_func)

		self.undo_but = QPushButton('&Undo')
		self.undo_but.setDefault(True)
		self.undo_but.clicked.connect(self.undo_func)

		self.enable_cb_3 = QCheckBox("Enable Third Parameter")
		self.enable_cb_3.setChecked(False)
		self.enable_cb_3.stateChanged.connect(self.enable_func_3)
		
		self.enable_cb_4 = QCheckBox("Enable Fourth Parameter")
		self.enable_cb_4.setChecked(False)
		self.enable_cb_4.stateChanged.connect(self.enable_func_4)

		self.enable_3d = QCheckBox("Enable 3D")
		self.enable_3d.setChecked(False)
		self.enable_3d.stateChanged.connect(self.enable_3d_func)

		self.enable_title = QCheckBox("Enable Title")
		self.enable_title.setChecked(False)
		self.enable_title.stateChanged.connect(self.title_func)

		self.enable_custom_formula = QCheckBox("Use Custom Formula for Y-Axis")
		self.enable_custom_formula.setChecked(False)
		self.enable_custom_formula.stateChanged.connect(self.enable_custom_formula_func)

		self.custom_formula_title = QLabel("Custom Formula:")
		self.custom_formula_title.setAlignment(Qt.AlignLeft)
		self.custom_formula_box = QLineEdit()
		self.custom_formula_title.setEnabled(False)
		self.custom_formula_box.setEnabled(False)

		self.xl = QLabel("Lower Limit")
		self.xl.setAlignment(Qt.AlignLeft)

		self.xh = QLabel("Upper Limit")
		self.xh.setAlignment(Qt.AlignLeft)

		self.yl = QLabel("Lower Limit")
		self.yl.setAlignment(Qt.AlignLeft)

		self.yh = QLabel("Upper Limit")
		self.yh.setAlignment(Qt.AlignLeft)

		self.zl = QLabel("Lower Limit")
		self.zl.setAlignment(Qt.AlignLeft)
		self.zl.setEnabled(False)

		self.zh = QLabel("Upper Limit")
		self.zh.setAlignment(Qt.AlignLeft)		
		self.zh.setEnabled(False)

		self.cbx = QComboBox()
		self.cby = QComboBox()
		self.cb3 = QComboBox()
		self.cb4 = QComboBox()
		self.cb4.setEnabled(False)
		self.cb3.setEnabled(False)
		self.cb_axes = QComboBox()
		self.cb_axes.setEnabled(False)
		self.cbz = QComboBox()
		self.cbz.setEnabled(False)
		self.cbz.currentIndexChanged.connect(self.selectionchangez)
		self.cbx.currentIndexChanged.connect(self.selectionchangex)
		self.cby.currentIndexChanged.connect(self.selectionchangey)      

		self.slzl = QSlider(Qt.Horizontal)
		self.slzl.setRange(0,100)
		self.slzl.setEnabled(False)

		self.slzh = QSlider(Qt.Horizontal)
		self.slzh.setRange(0,100)
		self.slzh.setEnabled(False)

		self.slxl = QSlider(Qt.Horizontal)
		self.slxl.setRange(0,100)

		self.slxh = QSlider(Qt.Horizontal)
		self.slxh.setRange(0,100)

		self.slyl = QSlider(Qt.Horizontal)
		self.slyl.setRange(0,100)

		self.slyh = QSlider(Qt.Horizontal)
		self.slyh.setRange(0,100)

		self.spzl = QDoubleSpinBox()
		self.spzl.valueChanged.connect(self.spzl_valuechange)
		self.spzl.setDecimals(6)
		self.spzl.setEnabled(False)

		self.spzh = QDoubleSpinBox()
		self.spzh.valueChanged.connect(self.spzh_valuechange)
		self.spzh.setDecimals(6)
		self.spzh.setEnabled(False)

		self.spxl = QDoubleSpinBox()
		self.spxl.valueChanged.connect(self.spxl_valuechange)
		self.spxl.setDecimals(6)

		self.spxh = QDoubleSpinBox()
		self.spxh.valueChanged.connect(self.spxh_valuechange)
		self.spxh.setDecimals(6)

		self.spyl = QDoubleSpinBox()
		self.spyl.valueChanged.connect(self.spyl_valuechange)
		self.spyl.setDecimals(6)

		self.spyh = QDoubleSpinBox()
		self.spyh.valueChanged.connect(self.spyh_valuechange)
		self.spyh.setDecimals(6)

		lay_custom.addWidget(self.custom_formula_title)
		lay_custom.addWidget(self.custom_formula_box)

		lay_xl_sp.addWidget(self.slxl)
		lay_xl_sp.addWidget(self.spxl)

		lay_xh_sp.addWidget(self.slxh)
		lay_xh_sp.addWidget(self.spxh)

		lay_yl_sp.addWidget(self.slyl)
		lay_yl_sp.addWidget(self.spyl)

		lay_yh_sp.addWidget(self.slyh)
		lay_yh_sp.addWidget(self.spyh)

		lay_zl_sp.addWidget(self.slzl)
		lay_zl_sp.addWidget(self.spzl)

		lay_zh_sp.addWidget(self.slzh)
		lay_zh_sp.addWidget(self.spzh)

		lay_x_s.addWidget(self.xl)
		lay_x_s.addLayout(lay_xl_sp)
		lay_x_s.addWidget(self.xh)
		lay_x_s.addLayout(lay_xh_sp)

		lay_y_s.addWidget(self.yl)
		lay_y_s.addLayout(lay_yl_sp)
		lay_y_s.addWidget(self.yh)
		lay_y_s.addLayout(lay_yh_sp)

		lay_z_s.addWidget(self.zl)
		lay_z_s.addLayout(lay_zl_sp)
		lay_z_s.addWidget(self.zh)
		lay_z_s.addLayout(lay_zh_sp)

		self.z_axis_label = QLabel("Axis:")
		self.z_axis_field = QLabel("Field:")
		self.z_axis_label.setEnabled(False)
		self.z_axis_field.setEnabled(False)
 
		lay_z_field.addWidget(self.z_axis_label)
		lay_z_field.addWidget(self.cb_axes)
		lay_z_field.addWidget(self.z_axis_field)
		lay_z_field.addWidget(self.cbz)

		lay_xx.addWidget(self.cbx)
		lay_xx.addLayout(lay_x_s)
		lay_yy.addWidget(self.cby)
		lay_yy.addLayout(lay_y_s)
		lay_33.addWidget(self.cb3)
		lay_33.addWidget(self.enable_cb_3)
		lay_44.addWidget(self.cb4)
		lay_44.addWidget(self.enable_cb_4)
		lay_zz.addLayout(lay_z_field)
		lay_zz.addLayout(lay_z_s)
		lay_zz.addWidget(self.enable_3d)

		lay_y_custom.addLayout(lay_yy)
		lay_y_custom.addLayout(lay_custom)
		lay_y_custom.addWidget(self.enable_custom_formula)

		group_box_x.setLayout(lay_xx)
		group_box_y.setLayout(lay_y_custom)
		group_box_3.setLayout(lay_33)
		group_box_4.setLayout(lay_44)
		group_box_z.setLayout(lay_zz)

		lay_up_cb.addWidget(self.update_but)
		lay_up_cb.addWidget(self.column_filtering_but)
		lay_up_cb.addWidget(self.swap_axis_but)
		lay_up_cb.addWidget(self.update_constraints_but)
		lay_up_cb.addWidget(self.undo_but)

		lay_title.addWidget(self.title_label)
		lay_title.addWidget(self.title_name)

		title_f.addWidget(self.enable_title)
		title_f.addLayout(lay_title)

		layout_az.addLayout(lay_3_4)
		layout_az.addLayout(lay_curve_fit_graph_type)
		layout_az.addWidget(group_box_pareto)

		layout.addLayout(title_f)
		layout.addWidget(group_box_x)
		layout.addWidget(group_box_y)
		layout.addWidget(group_box_z)
		layout.addLayout(layout_az)
		layout.addLayout(lay_up_cb)

		lay_gv.addWidget(self.canvas)
		lay_gv.addWidget(self.toolbar)

		#Making the widget resizable and scrollable
		scroll = QScrollArea()          
		temp = QWidget()
		temp.setLayout(layout)
		scroll.setWidget(temp)		
		final_layout.addWidget(scroll)	
		final_layout.addLayout(lay_gv)

		self.slxl.valueChanged.connect(self.print_x_l)
		self.slxh.valueChanged.connect(self.print_x_h)
		self.slyl.valueChanged.connect(self.print_y_l)
		self.slyh.valueChanged.connect(self.print_y_h)
		self.slzl.valueChanged.connect(self.print_z_l)
		self.slzh.valueChanged.connect(self.print_z_h)	
		
		self.setLayout(final_layout)
		self.cb_axes.addItem("Z-Axis")

		self.col_fil = col_filtering_window()
		self.set_cons= update_constraints_window()
	def undo_func(self):						#runs the old version used for generating the constraints file
		f = open("constraints.ecl","w+")
		f.write(range_constraints_string)
		f.write(undo_old);
		f.close()
		os.system("../eclipse/bin/x86_64_linux/eclipse -f ../eclipse/tmp/test.ecl -f constraints.ecl -e main,fail")
		file_change = open("file.txt","r")
		newfile = open("generated.csv","w")
		x = file_change.readlines()
		for i in x:
			newfile.write(i[1:-2]+'\n')
		file_change.close()
		newfile.close()
	

	def pareto_func(self):										#to enable and disable the widgets in the pareto window
		if self.enable_plot_pareto.isChecked():
			self.pareto_x.setEnabled(True)
			self.pareto_y.setEnabled(True)
			self.pareto_cbx.setEnabled(True)
			self.pareto_cby.setEnabled(True)
			self.enable_3d.setEnabled(False)
		else:
			self.pareto_x.setEnabled(False)
			self.pareto_y.setEnabled(False)
			self.pareto_cbx.setEnabled(False)
			self.pareto_cby.setEnabled(False)
			self.enable_3d.setEnabled(True)

	def curve_fitting_func(self):								#to enable and disable the widgets in the curve_fitting window
		if self.enable_curve_fitting.isChecked():
			self.degree_label.setEnabled(True)
			self.curve_fitting_sb.setEnabled(True)
		else:
			self.degree_label.setEnabled(False)
			self.curve_fitting_sb.setEnabled(False)

	def enable_3d_func(self):									#to enable/disable widgets in Z-axis/Secondary Y-Axis window
		b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
		if self.enable_3d.isChecked():
			self.cb_axes.setEnabled(True)
			self.cbz.setEnabled(True)
			if b not in col_with_strings:
				self.slzl.setEnabled(True)
				self.slzh.setEnabled(True)
				self.spzl.setEnabled(True)
				self.spzh.setEnabled(True)
			self.zl.setEnabled(True)
			self.zh.setEnabled(True)
			self.z_axis_label.setEnabled(True)
			self.z_axis_field.setEnabled(True)
			self.enable_plot_pareto.setEnabled(False)
		else:
			self.cb_axes.setEnabled(False)
			self.cbz.setEnabled(False)	
			self.slzl.setEnabled(False)
			self.slzh.setEnabled(False)
			self.spzl.setEnabled(False)
			self.spzh.setEnabled(False)
			self.zl.setEnabled(False)
			self.zh.setEnabled(False)
			self.z_axis_label.setEnabled(False)
			self.z_axis_field.setEnabled(False)
			self.enable_plot_pareto.setEnabled(True)

	def update_plot(self):								#main function to plot graph
														#passes all the parameters(slider ranges,field names,whether to plot 3d/pareto etc.,column filtering information)
														#into a "configure" file (default name 'out_cfg.csv' is hardcoded)
														#which is used by the second module(plot.py)
		
		global out_list									#list which stores all the above mentioned parameters which is used by
													#cfg_writer to write in 'out_cfg.csv'
		global final_constraints
		global col_fil_list
		global col_with_strings
		out_cfg = open("out_cfg.csv",'w')
		cfg_writer = csv.writer(out_cfg)
		global curr_filename
		if curr_filename == "":
			pass 
		else:
			if self.spxl.value()>self.spxh.value():
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Lower limit greater than upper limit for x-axis")
				msg.setWindowTitle("Error")
				msg.setStandardButtons(QMessageBox.Ok)
				msg.exec_()

			elif self.spyl.value()>self.spyh.value():
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Lower limit greater than upper limit for y-axis")
				msg.setWindowTitle("Error")
				msg.setStandardButtons(QMessageBox.Ok)
				msg.exec_()

			else:
				del out_list[:]
				out_list.extend([curr_filename,self.cbx.currentText()])
				if self.enable_custom_formula.isChecked():
					out_list.append(self.custom_formula_box.text())
				else:
					out_list.append(self.cby.currentText())
				if self.enable_3d.isChecked():
					if self.cb_axes.currentText() == "Z-Axis":
						out_list.extend(['1',self.cbz.currentText()])
					elif self.cb_axes.currentText() == "Secondary Y-Axis":
						out_list.extend(['2',self.cbz.currentText()])
				elif self.enable_plot_pareto.isChecked():
					out_list.append('3')
					if self.pareto_cbx.currentText()=="Minimize":
						if self.pareto_cby.currentText()=="Minimize":
							out_list.append('2')
						else:
							out_list.append('1')
					else:
						if self.pareto_cby.currentText()=="Minimize":
							out_list.append('4')
						else:
							out_list.append('3')
				else:
					out_list.extend(['4',''])
				if self.enable_cb_3.isChecked():
					out_list.append(self.cb3.currentText())
				else:
					out_list.append('')
				if self.enable_cb_4.isChecked():
					out_list.append(self.cb4.currentText())
				else:
					out_list.append('')
				if self.enable_title.isChecked():
					out_list.append(self.title_name.text())
				else:
					out_list.append('')
				if self.enable_custom_formula.isChecked():
					out_list.append('t')
				else:
					out_list.append('f')
				out_list.extend([self.spxl.value(),self.spxh.value(),self.spyl.value(),self.spyh.value(),self.spzl.value(),self.spzh.value()])
				out_list.append(len(fields) - len(col_with_strings))
				for key in col_fil_list:
					tup = col_fil_list[key]
					out_list.extend([key,tup[0],tup[1]])
					
				out_list.extend(final_constraints)

				out_list.append(self.graph_type_cb.currentText())
				if self.enable_curve_fitting.isChecked():
					out_list.append(self.curve_fitting_sb.value())
				else:
					out_list.append('')
				out_list.append('junk')
				cfg_writer.writerow(out_list)
				out_cfg.close()
				self.call_plot()						#calls the call_plot function which calles the plotter function from plot.py


	def constraints_file_func(self):
		global final_constraints
		del final_constraints[:]
		cons.clear()
		self.set_cons.show()
		self.set_cons.addItemsinCB()

	def call_plot(self):
		if self.enable_3d.isChecked():
			b = str(PyQt4.QtCore.QString(self.cb_axes.currentText()))
			if b == "Z-Axis":
				plot.plotter(self.figure,self.canvas,1)
			else:
				plot.plotter(self.figure,self.canvas,0)
		else:
			plot.plotter(self.figure,self.canvas,0)

	def enable_func_3(self):							#to enable/disable widgets in third parameter window(shape)
		if self.enable_cb_3.isChecked():
			self.cb3.setEnabled(True)
		else:
			self.cb3.setEnabled(False)

	def enable_func_4(self):							#to enable/disable widgets in fourth parameter window(color)
		if self.enable_cb_4.isChecked():
			self.cb4.setEnabled(True)
		else:
			self.cb4.setEnabled(False)

	def enable_custom_formula_func(self):				#to enable/disable widgets in column_filtering window
		b = str(PyQt4.QtCore.QString(self.cby.currentText()))
		if self.enable_custom_formula.isChecked():
			self.cby.setEnabled(False)
			self.slyl.setEnabled(False)
			self.slyh.setEnabled(False)
			self.spyl.setEnabled(False)
			self.spyh.setEnabled(False)
			self.custom_formula_title.setEnabled(True)
			self.custom_formula_box.setEnabled(True)
		else:
			self.cby.setEnabled(True)
			if b not in col_with_strings:
				self.slyl.setEnabled(True)
				self.slyh.setEnabled(True)
				self.spyl.setEnabled(True)
				self.spyh.setEnabled(True)
			self.custom_formula_title.setEnabled(False)
			self.custom_formula_box.setEnabled(False)	

	def title_func(self):								#to enable/disable title bar
		if self.enable_title.isChecked():
			self.title_label.setEnabled(True)
			self.title_name.setEnabled(True)
		else:
			self.title_label.setEnabled(False)
			self.title_name.setEnabled(False)

	def column_filtering_func(self):					#shows the column filtering window
		self.col_fil.show()

	def swap_axis_func(self):
		xlabel = self.cbx.currentText()
		ylabel = self.cby.currentText()
		if not self.enable_custom_formula.isChecked():
			index_in_cbx = self.cbx.findText(ylabel)
			index_in_cby = self.cby.findText(xlabel)
			if index_in_cby >= 0 and index_in_cby >= 0:
				self.cbx.setCurrentIndex(index_in_cbx)
				self.cby.setCurrentIndex(index_in_cby)
				self.selectionchangex()
				self.selectionchangey()
				self.update_plot()
	def spzl_valuechange(self):							#sets lower value of z-axis slider based on spin box value
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spzl.value())
			else:
				a = (int)(((self.spzl.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spzl.value())
		self.slzl.setValue(a)	

	def spzh_valuechange(self):							#sets upper(higher) value of z-axis slider based on spin box value
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spzh.value())
			else:
				a = (int)(((self.spzh.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spzh.value())
		self.slzh.setValue(a)

	def spxl_valuechange(self):							#sets lower value of x-axis slider based on spin box 
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cbx.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spxl.value())
			else:
				a = (int)(((self.spxl.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spxl.value())
		self.slxl.setValue(a)

	def spxh_valuechange(self):							#sets upper value of x-axis slider based on spin box
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cbx.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spxh.value())
			else:
				a = (int)(((self.spxh.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spxh.value())
		self.slxh.setValue(a)

	def spyl_valuechange(self):							#sets lower value of y-axis slider based on spin box
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cby.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spyl.value())
			else:
				a = (int)(((self.spyl.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spyl.value())
		self.slyl.setValue(a)

	def spyh_valuechange(self):							#sets upper value of y-axis slider based on spin box
		global change
		change = 1
		b = str(PyQt4.QtCore.QString(self.cby.currentText()))
		if b in lower_limit.keys():
			if upper_limit[b] == lower_limit[b]:
				a = (int)(self.spyh.value())
			else:
				a = (int)(((self.spyh.value() - lower_limit[b])*100)/(upper_limit[b] - lower_limit[b]))
		else:
			a = (int)(self.spyh.value())
		self.slyh.setValue(a)



	def selectionchangetype(self):
		b = str(PyQt4.QtCore.QString(self.graph_type_cb.currentText()))
		if b=="histogram":
			self.slyl.setEnabled(False)
			self.slyh.setEnabled(False)
			self.spyh.setEnabled(False)
			self.spyl.setEnabled(False)
			self.cby.setEnabled(False)
			self.enable_custom_formula.setEnabled(False)
			self.enable_curve_fitting.setEnabled(False)
			self.enable_plot_pareto.setEnabled(False)
			self.enable_cb_3.setEnabled(False)



		elif b == "bar-graph":
			self.slyl.setEnabled(True)
			self.slyh.setEnabled(True)
			self.spyh.setEnabled(True)
			self.spyl.setEnabled(True)
			self.cby.setEnabled(True)
			self.enable_curve_fitting.setEnabled(False)
			self.enable_plot_pareto.setEnabled(False)
			self.enable_cb_3.setEnabled(False)
			self.enable_custom_formula.setEnabled(False)

		else:
			self.slyl.setEnabled(True)
			self.slyh.setEnabled(True)
			self.spyh.setEnabled(True)
			self.spyl.setEnabled(True)
			self.cby.setEnabled(True)
			self.enable_custom_formula.setEnabled(True)
			self.enable_curve_fitting.setEnabled(True)
			self.enable_plot_pareto.setEnabled(True)
			self.enable_cb_3.setEnabled(True)

	def selectionchangex(self):							#changes the upper and lower limits of sliders/spin boxes based on the current selected field
														#also disables them if the current field has strings as values(X-AXIS)
		b = str(PyQt4.QtCore.QString(self.cbx.currentText()))
		#print "--->" + b
		if b in col_with_strings:
			self.spxl.setEnabled(False)
			self.spxh.setEnabled(False)
			self.slxl.setEnabled(False)
			self.slxh.setEnabled(False)
		else:
			self.spxl.setEnabled(True)
			self.spxh.setEnabled(True)
			self.slxl.setEnabled(True)
			self.slxh.setEnabled(True)
			if(lower_limit):
				self.spxl.setRange(lower_limit[b],upper_limit[b])
				self.spxh.setRange(lower_limit[b],upper_limit[b])
				self.slxl.setValue(0)
				self.slxh.setValue(100)
				self.spxl.setValue(lower_limit[b])
				self.spxh.setValue(upper_limit[b])

	def selectionchangey(self):							#changes the upper and lower limits of sliders/spin boxes based on the current selected field
														#also disables them if the current field has strings as values(Y-AXIS)
		b = str(PyQt4.QtCore.QString(self.cby.currentText()))
		if b in col_with_strings:
			self.spyl.setEnabled(False)
			self.spyh.setEnabled(False)
			self.slyl.setEnabled(False)
			self.slyh.setEnabled(False)
		else:
			self.spyl.setEnabled(True)
			self.spyh.setEnabled(True)
			self.slyl.setEnabled(True)
			self.slyh.setEnabled(True)
			if(lower_limit): 
				self.spyl.setRange(lower_limit[b],upper_limit[b])
				self.spyh.setRange(lower_limit[b],upper_limit[b])
				self.slyl.setValue(0)
				self.slyh.setValue(100)
				self.spyl.setValue(lower_limit[b])
				self.spyh.setValue(upper_limit[b])

	def selectionchangez(self):							#changes the upper and lower limits of sliders/spin boxes based on the current selected field
														#also disables them if the current field has strings as values(Z-AXIS)
		b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
		if b in col_with_strings:
			self.spzl.setEnabled(False)
			self.spzh.setEnabled(False)
			self.slzl.setEnabled(False)
			self.slzh.setEnabled(False)
		else:
			self.spzl.setEnabled(True)
			self.spzh.setEnabled(True)
			self.slzl.setEnabled(True)
			self.slzh.setEnabled(True)
			if(lower_limit):
				self.spzl.setRange(lower_limit[b],upper_limit[b])
				self.spzh.setRange(lower_limit[b],upper_limit[b])
				self.slzl.setValue(0)
				self.slzh.setValue(100)
				self.spzl.setValue(lower_limit[b])
				self.spzh.setValue(upper_limit[b])

	def print_x_l(self):						#testing function used the check the current lower value of slider(x-axis)
												#the value is printed on command line
												#similarly the other functions for other axes
		global change
		if change == 1:
			change = 0
		else :
			b = str(PyQt4.QtCore.QString(self.cbx.currentText()))
			if b in lower_limit.keys():
				a = lower_limit[b] + (((float)(self.slxl.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slxl.value())
			self.spxl.setValue(a)      

	def print_x_h(self):
		global change
		if change == 1:
			change = 0
		else :
			b = str(PyQt4.QtCore.QString(self.cbx.currentText()))
			if b in upper_limit.keys():
				a = lower_limit[b] + (((float)(self.slxh.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slxh.value())
			self.spxh.setValue(a)      

	def print_y_l(self):
		global change
		if change == 1:
			change = 0
		else:
			b = str(PyQt4.QtCore.QString(self.cby.currentText()))
			if b in lower_limit.keys():
				a = lower_limit[b] + (((float)(self.slyl.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slyl.value())
			self.spyl.setValue(a)      

	def print_y_h(self):
		global change
		if change == 1:
			change = 0
		else:
			b = str(PyQt4.QtCore.QString(self.cby.currentText()))
			if b in upper_limit.keys():
				a = lower_limit[b] + (((float)(self.slyh.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slyh.value())
			self.spyh.setValue(a)      

	def print_z_l(self):
		global change
		if change == 1:
			change = 0
		else:
			b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
			if b in lower_limit.keys():
				a = lower_limit[b] + (((float)(self.slzl.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slzl.value())
			self.spzl.setValue(a)      

	def print_z_h(self):
		global change
		if change == 1:
			change = 0
		else:
			b = str(PyQt4.QtCore.QString(self.cbz.currentText()))
			if b in upper_limit.keys():
				a = lower_limit[b] + (((float)(self.slzh.value())/100) * (upper_limit[b] - lower_limit[b]))
			else:
				a = (float)(self.slzh.value())
			self.spzh.setValue(a)

class tabs(QTabWidget):									#used to implement tabs
														#each tab contains a sub window as defined above
	def __init__(self):
		super(tabs, self).__init__()

class test(QMainWindow):								#main window which houses all the tabs

	count = 0
	def __init__(self):
		super(test, self).__init__()

		self.setWindowTitle("Visualization Tool")

		self.add_button = QToolButton()
		self.add_button.setText('+')
		self.t =tabs() 
		self.t.setCornerWidget(self.add_button)
		self.add_button.clicked.connect(self.add_tab)
		self.t.setTabsClosable(True)
		self.t.setMovable(True)
		self.t.tabCloseRequested.connect(self.close_tab)
		self.setCentralWidget(self.t)
		self.add_tab()

		file_action = QtGui.QAction("Open",self)
		file_action.setShortcut("Ctrl+O")
		file_action.setStatusTip("Open file")
		file_action.triggered.connect(self.get_file)

		add_subwindows = QtGui.QAction("Add",self)
		add_subwindows.setShortcut("Ctrl+A")
		add_subwindows.setStatusTip("Add more sub windows")
		add_subwindows.triggered.connect(self.add_sub)

		quit_action = QtGui.QAction("Quit",self)
		quit_action.setShortcut("Ctrl+Q")
		quit_action.setStatusTip("Quit program")
		quit_action.triggered.connect(self.exit_func)

		self.statusBar()

		main_menu = self.menuBar()
		file_menu = main_menu.addMenu('&File')
		file_menu.addAction(file_action)
		file_menu.addAction(quit_action)
		file_menu.addAction(add_subwindows)

	def exit_func(self):
		sys.exit()

	def close_tab(self,n):									#closes the current tab
		self.t.removeTab(n)
		self.count = self.count - 1
		if self.count == 0:
			sys.exit()

	def add_tab(self):										#adds more tabs(by clicking the + button)
		s = sub_window()
		s.subwindow_id = self.count
		self.t.addTab(s,"New Tab")
		for xy in fields:
			s.cbx.addItem(xy)
			s.cby.addItem(xy)
			s.cb3.addItem(xy)
			s.cb4.addItem(xy)
			s.cbz.addItem(xy)
			if xy not in col_with_strings:
				s.col_fil.cb.addItem(xy)
		
		if(lower_limit):  
			b = str(PyQt4.QtCore.QString(s.cby.currentText()))
			if b not in col_with_strings:
				s.spyl.setRange(lower_limit[b],upper_limit[b])
				s.spyh.setRange(lower_limit[b],upper_limit[b])
				s.slyl.setValue(0)
				s.slyh.setValue(100)
				s.spyl.setValue(lower_limit[b])
				s.spyh.setValue(upper_limit[b])
			b = str(PyQt4.QtCore.QString(s.cbx.currentText()))
			if b not in col_with_strings:
				s.spxl.setRange(lower_limit[b],upper_limit[b])
				s.spxh.setRange(lower_limit[b],upper_limit[b])
				s.slxl.setValue(0)
				s.slxh.setValue(100)
				s.spxl.setValue(lower_limit[b])
				s.spxh.setValue(upper_limit[b])
			b = str(PyQt4.QtCore.QString(s.cbz.currentText()))
			if b not in col_with_strings:
				s.spzl.setRange(lower_limit[b],upper_limit[b])
				s.spzh.setRange(lower_limit[b],upper_limit[b])
				s.slzl.setValue(0)
				s.slzh.setValue(100)
				s.spzl.setValue(lower_limit[b])
				s.spzh.setValue(upper_limit[b])
			s.spzl.setEnabled(False)
			s.spzh.setEnabled(False)
			s.slzl.setEnabled(False)
			s.slzh.setEnabled(False)
			b = str(PyQt4.QtCore.QString(s.col_fil.cb.currentText()))
			s.col_fil.sl_l.setRange(lower_limit[b],upper_limit[b])
			s.col_fil.sl_h.setRange(lower_limit[b],upper_limit[b])
			s.col_fil.sl_l.setValue(0)
			s.col_fil.sl_h.setValue(100)
			s.col_fil.sp_l.setValue(lower_limit[b])
			s.col_fil.sp_h.setValue(upper_limit[b])
		self.count = self.count + 1
		if self.count==20:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Too many windows! (May consume too much memory)")
			msg.setWindowTitle("Error")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

	def add_sub(self):									#adds more tabs (by using the option from file menu)
		num,ok = QInputDialog.getInt(self,"No. of subwindows","Enter a number")

		if ok:
			for i in range(num):
				s = sub_window()
				s.subwindow_id = test.count
				self.t.addTab(s,"New Tab")
				for xy in fields:
					s.cbx.addItem(xy)
					s.cby.addItem(xy)
					s.cb3.addItem(xy)
					s.cb4.addItem(xy)
					s.cbz.addItem(xy)
					if xy not in col_with_strings:
						s.col_fil.cb.addItem(xy)

				if self.count==20:
					msg = QMessageBox()
					msg.setIcon(QMessageBox.Warning)
					msg.setText("Too many windows! (May consume too much memory)")
					msg.setWindowTitle("Error")
					msg.setStandardButtons(QMessageBox.Ok)
					msg.exec_()
				
				if(lower_limit):  
					b = str(PyQt4.QtCore.QString(s.cby.currentText()))
					if b not in col_with_strings:	
						s.spyl.setRange(lower_limit[b],upper_limit[b])
						s.spyh.setRange(lower_limit[b],upper_limit[b])
						s.slyl.setValue(0)
						s.slyh.setValue(100)
						s.spyl.setValue(lower_limit[b])
						s.spyh.setValue(upper_limit[b])
					b = str(PyQt4.QtCore.QString(s.cbx.currentText()))
					if b not in col_with_strings:	
						s.spxl.setRange(lower_limit[b],upper_limit[b])
						s.spxh.setRange(lower_limit[b],upper_limit[b])
						s.slxl.setValue(0)
						s.slxh.setValue(100)
						s.spxl.setValue(lower_limit[b])
						s.spxh.setValue(upper_limit[b])
					b = str(PyQt4.QtCore.QString(s.cbz.currentText()))
					if b not in col_with_strings:	
						s.spzl.setRange(lower_limit[b],upper_limit[b])
						s.spzh.setRange(lower_limit[b],upper_limit[b])
						s.slzl.setValue(0)
						s.slzh.setValue(100)
						s.spzl.setValue(lower_limit[b])
						s.spzh.setValue(upper_limit[b])
					s.spzl.setEnabled(False)
					s.spzh.setEnabled(False)
					s.slzl.setEnabled(False)
					s.slzh.setEnabled(False)
					b = str(PyQt4.QtCore.QString(s.col_fil.cb.currentText()))
					s.col_fil.sl_l.setRange(lower_limit[b],upper_limit[b])
					s.col_fil.sl_h.setRange(lower_limit[b],upper_limit[b])
					s.col_fil.sl_l.setValue(0)
					s.col_fil.sl_h.setValue(100)
					s.col_fil.sp_l.setValue(lower_limit[b])
					s.col_fil.sp_h.setValue(upper_limit[b])
				self.count = self.count + 1

	def get_file(self):										#opens a file and stores the field names and their limits in the respective lists
		for j in range(self.t.count()):
			i = self.t.widget(j)
			i.cbx.clear()
			i.cby.clear()
			i.cb3.clear()
			i.cb4.clear()
			i.cbz.clear()
			i.col_fil.cb.clear()
		global fields
		global lower_limit
		global upper_limit
		global lll
		global ull
		del fields[:]
		global col_fil_list
		global col_with_strings
		col_fil_list.clear()
		del col_with_strings[:]
		lower_limit.clear()
		upper_limit.clear()
		del lll[:]
		del ull[:]
		dlg = QFileDialog()
		dlg.setFileMode(QFileDialog.AnyFile)
		dlg.setFilter("(*.csv)")
		filenames = QStringList()
		f = ""

		if dlg.exec_():
			global curr_filename
			filenames = dlg.selectedFiles()
			try:
				f = open(filenames[0], 'r')
				b = str(PyQt4.QtCore.QString(filenames[0]))
				curr_filename = b
			except:
				pass

		if f != "":
			with f:
				reader = csv.reader(f)
				fields = reader.next()
				flag=0
				for x in fields:
					if x.isdigit():
						flag=1
					lll.append(float("inf"))
					ull.append(float("-inf"))
				if fields[-1] == '':
					del fields[-1]
				if flag==1:
					f = open(cfg_file_name,'r')
					with f:
						reader_temp = csv.reader(f)
						fields = reader_temp.next()
				for r in reader:
					for i in xrange(len(r)):
						if(r[i]!=''):
							try:
								if float(r[i]) < lll[i]:
									lll[i] = float(r[i])
								if float(r[i]) > ull[i]:
									ull[i] = float(r[i])
							except:
								if fields[i] not in col_with_strings:
									col_with_strings.append(fields[i])
				for xy in fields:
					for j in range(self.t.count()):
						i = self.t.widget(j)
						i.cbx.addItem(xy)
						i.cby.addItem(xy)
						i.cb3.addItem(xy)
						i.cb4.addItem(xy)
						i.cbz.addItem(xy)
						if xy not in col_with_strings:
							i.col_fil.cb.addItem(xy)
				for i in xrange(len(fields)):
					if fields[i] not in col_with_strings:
						lower_limit[fields[i]] = lll[i]
						upper_limit[fields[i]] = ull[i]
						col_fil_list[fields[i]] = (lll[i],ull[i])
				for j in range(self.t.count()):
					i = self.t.widget(j)
					b = str(PyQt4.QtCore.QString(i.cby.currentText()))
					if b in col_with_strings:
						i.spyl.setEnabled(False)
						i.spyh.setEnabled(False)
						i.slyl.setEnabled(False)
						i.slyh.setEnabled(False)
					else:
						i.spyl.setRange(lower_limit[b],upper_limit[b])
						i.spyh.setRange(lower_limit[b],upper_limit[b])
						i.slyl.setValue(0)
						i.slyh.setValue(100)
						i.spyl.setValue(lower_limit[b])
						i.spyh.setValue(upper_limit[b])
					b = str(PyQt4.QtCore.QString(i.cbx.currentText()))
					if b in col_with_strings:
						i.spxl.setEnabled(False)
						i.spxh.setEnabled(False)
						i.slxl.setEnabled(False)
						i.slxh.setEnabled(False)
					else:
						i.spxl.setRange(lower_limit[b],upper_limit[b])
						i.spxh.setRange(lower_limit[b],upper_limit[b])
						i.slxl.setValue(0)
						i.slxh.setValue(100)
						i.spxl.setValue(lower_limit[b])
						i.spxh.setValue(upper_limit[b])
					b = str(PyQt4.QtCore.QString(i.cbz.currentText()))
					if b in col_with_strings:
						pass
					else:
						i.spzl.setRange(lower_limit[b],upper_limit[b])
						i.spzh.setRange(lower_limit[b],upper_limit[b])
						i.slzl.setValue(0)
						i.slzh.setValue(100)
						i.spzl.setValue(lower_limit[b])
						i.spzh.setValue(upper_limit[b])
					b = str(PyQt4.QtCore.QString(i.col_fil.cb.currentText()))
					i.col_fil.sp_l.setRange(lower_limit[b],upper_limit[b])
					i.col_fil.sp_h.setRange(lower_limit[b],upper_limit[b])
					i.col_fil.sl_l.setValue(0)
					i.col_fil.sl_h.setValue(100)
					i.col_fil.sp_l.setValue(lower_limit[b])
					i.col_fil.sp_h.setValue(upper_limit[b])
					i.slzl.setEnabled(False)
					i.slzh.setEnabled(False)
					i.spzl.setEnabled(False)
					i.spzh.setEnabled(False)

def main():
	app = QApplication(sys.argv)
	ex = test()
	ex.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
