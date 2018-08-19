import matplotlib.pyplot as plt
from numpy import polyfit as pf
import math
import ply.lex as lex
import sys
import ply.yacc as yacc
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage, AnnotationBbox)
from matplotlib.patches import Rectangle
from collections import defaultdict
import collections
import pickle
import os


def plotter (fig,canvas,v):

# plotter function called after update button is pressed
# plots the graph on the canvas
# fig is the figure object of matplotlib
# canvas is the canvas object of matplotlib
# fig and canvas object passed to the function are to be maniulated to draw the graph (fig/canvas can be considered the place where the graph is drawn)


# variables used ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	details=[] 																						# details for hovering
	line = []																							# list of line objects of matplotlib
	
	plotPointsX = []																			# list of list of x,y,z points that is passed to plot function of matplotlib to plot the graph
	plotPointsY = []																				
	plotPointsZ = []

	partitionedPoints = []																		# lift of lists of points partitioned by shape and colour

	fieldLengthList = []																		# list of lengths of fieldnames in the .csv (input file)
	fieldList = []																					# list fields in the .csv (input file)
	fieldNumber = 1																			# no. of fields in .csv (input file)
	fileRow = []																					# a row in .csv (input file)
	fileRowNumber = 0																	# no. of rows in .csv (input file)
	dataBase = []																					# 2d list which stores the whole .csv (input file) (except the first row that contains field names)
	
	style = ['.','^','h','H','>','<','x','+','p','d','8']							# list of initialized marker styles
	colour = ['r','g','b','c','m','y','k','chartreuse']                       # list of initialized marker colors
	patterns = [ "/" , "\\" , "-"  , "x", "o", "O","." "*" ]

	distinctVals3 = []	#for bar graph(the distinct values)
	distinctValues1 = 0																		# no. of 3rd para (shape) values 
	distinctValues2 = 0																		# no. of 3rd para (shape) values 
	distinctValues3 = 0																		# no. of x-axis values (needed if we are making a bar graph)
	plotLines1 = []																				
	plotLines2 = []

	plotULimit = []																				# upper limits selected on fields in column filtering / upper limit in .csv
	plotLLimit = []																				# lower limits selected on fields in column filtering / lower limit in .csv
	numberFields = []																		# fieldname of columns containing numerical data
	configLines=[]																				# list holding data for settings and options selected in UI
	
	yPoints = []
	xPoints = []
	zPoints = []
	
	colNumX = -1																					# column no. for x,y,z axes
	colNumY = -1
	colNumZ = -1
	
	xDict = {}																							# dictionary to hold co-ordinates in case of non numerical data
	yDict = {}																							
	zDict = {}
	
	filterZPoints = []
	filterPoints = []
	paretoPoints = []
	y_start_prev = 0  																		#for retaining the y and x axis limit
	x_start_prev = 0
	y_end_prev = 0
	x_end_prev = 0
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

	def stringParse(x):
		
	# function that parses the input entered for custom formula for y axis (based on lex and yacc; alternatively regex can be used)
	# x is the string to be parsed

		if sys.version_info[0] >= 3:
			raw_input = input

		tokens = (
			'NAME', 'NUMBER',
		)

		literals = ['=', '+', '-', '*', '/', '(', ')']

		# Tokens

		@lex.TOKEN('|'.join(numberFields))  																						# adding filed names as token values

		def t_NAME(t):
			#print (t.value)
			for j in numberFields :

				if t.value == j:
					t.value = [float(i[fieldList.index(j)]) for i in dataBase]		# setting the value as the whole column that is specified in the formula
					break
			return t

		def t_NUMBER(t):
			r'\d+'
			t.value = int(t.value)																														# setting the value as the integer specified in the formula
			return t

		t_ignore = " \t"

		def t_newline(t):
			r'\n+'
			t.lexer.lineno += t.value.count("\n")

		def t_error(t):
			print("Illegal character '%s'" % t.value[0])
			f = open("erLog.txt",'w')																												# setting up the flag in the erLog file in case of incorrect formula
			f.write(x)																																			# this is done as the variable scope is diff. in this function and return values go somewhere else
			f.close()
			t.lexer.skip(1)

		# Build the lexer
		
		lex.lex()

		# Parsing rules

		precedence = (
			('left', '+', '-'),
			('left', '*', '/'),
			('right', 'UMINUS'),
		)

		# dictionary of names
		names = {}

		def p_statement_expr(p):
			'statement : expression'
			f = open("yP.txt",'w')																														# setting the final values in the yP.txt
			for i in p[1] :
				f.write("%s," % i)
			f.close()

		def p_expression_binop(p):
			'''expression : expression '+' expression																				
						  | expression '-' expression
						  | expression '*' expression
						  | expression '/' expression'''
			if p[2] == '+':
				p[0] = [i + j for i, j in zip(p[1], p[3])]																						# calculating the values according the formula
			elif p[2] == '-':
				p[0] = [i - j for i, j in zip(p[1], p[3])]
			elif p[2] == '*':
				p[0] = [i * j for i, j in zip(p[1], p[3])]
			elif p[2] == '/':
				p[0] = [i / j for i, j in zip(p[1], p[3])]


		def p_expression_uminus(p):
			"expression : '-' expression %prec UMINUS"
			p[0] = [-i for i in p[2]]																													   # calculating the values according the formula

		def p_expression_group(p):
			"expression : '(' expression ')'"
			p[0] = p[2]																																			# calculating the values according the formula

		def p_expression_number(p):
			"expression : NUMBER"
			p[0] = [p[1] for i in range(fileRowNumber)]																		# calculating the values according the formula

		def p_expression_name(p):
			"expression : NAME"																														# calculating the values according the formula
			p[0] = p[1]

		def p_error(p):
			if p:
				print("Syntax error at '%s'" % p.value)
			else:
				print("Syntax error at EOF")
			f = open("erLog.txt",'w')																												# setting the flag in erLog.txt
			f.write(x)
			f.close()
		yacc.yacc()

		yacc.parse(x)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	
# reading out_cfg.csv to get the settings from UI
	f = open("out_cfg.csv",'rU')                                                                                                               
	while True :
		configLine = f.readline().split(",") 																								# settings are stored as comma seperated values
		if configLine == [""]:
			break
		configLines.append(configLine)																									# settings are stored in the list configLines[0]

	
	# configLine details
	# configLines[0][0] --> name of input/.csv file
	# configLines[0][1] --> name of x axis column/field
	# configLines[0][2] --> name of y axis column/field
	# configLines[0][3] --> if 1 then 3d enabled
	# configLines[0][4] --> name of the z axis column/field
	# configLines[0][5] --> name of fourth para
	# configLines[0][6] --> name of third para
	# configLines[0][7] --> title if not empty
	# configLines[0][8] --> custom formula enabled if t
	# configLines[0][9] --> lower limit x axis 
	# configLines[0][10] --> upper limit x axis
	# configLines[0][11] --> lower limit y axis
	# configLines[0][12] --> upper limit y axis
	# configLines[0][13] --> lower limit z axis
	# configLines[0][14] --> upper limit z axis
	# configLines[0][15] --> no of numerical fields in the .csv(input file)
	# configLines[0][16] to configLines[0][x] --> fieldname , upper limit (selected in column filtering) , lower limit (selected in column filtering) (for numerical fields)
	# configLines[0][-12] --> color or pattern for bars in bar graph and histogram
	# configLines[0][-11] --> empty if resize axes automatically ( default case )
	# configLines[0][-10] --> empty if y value start value is not given
	# configLines[0][-9] --> empty if no value on bars
	# configLines[0][-8] --> x label if not empty
	# configLines[0][-7] --> y label if not empty
	# configLines[0][-6] --> Normalization or not in histogram 
	# configLines[0][-5] --> Minimum, Average, Maximum for bargraph
	# configLines[0][-4] --> type of graph (line/scatter/histogram/bar)
	# configLines[0][-3] --> empty for curve fit disabled else degree of polynomial
	# configLines[0][-2] --> Interval range(for histogram)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	fig.clf() 	
																																						# clear the previous graph
	if(os.path.isfile("scriptdump.py") == True):
		os.remove("scriptdump.py")
	the_file  = open('scriptdump.py', 'a')
	os.chmod('scriptdump.py', 0777) 
	#everystatement with the_file is for the script(containing the code for plot) that is to be dumped  
	the_file.write('import matplotlib.pyplot as plt\n')
	the_file.write('from numpy import polyfit as pf\n')
	the_file.write('import math\n')
	the_file.write('import ply.lex as lex\n')
	the_file.write('import sys\n')
	the_file.write('import ply.yacc as yacc\n')
	the_file.write('import numpy as np\n')
	the_file.write('from PyQt4.QtCore import *\n')
	the_file.write('from PyQt4.QtGui import *\n')
	the_file.write('from PyQt4 import QtGui, QtCore\n')
	the_file.write('from mpl_toolkits.mplot3d import Axes3D\n')
	the_file.write('from mpl_toolkits.mplot3d import proj3d\n')
	the_file.write('from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage, AnnotationBbox)\n')
	the_file.write('from matplotlib.patches import Rectangle\n')
	the_file.write('from collections import defaultdict\n')
	the_file.write('import collections\n')
	the_file.write('import pickle\n')
	the_file.write('import os\n')
	the_file.write('\n')
	the_file.write('fig = plt.figure()\n')
	# self.canvas = FigureCanvas(self.figure)
	if configLines[0][3] == '1' :																													# check if 3d
		ax = fig.add_subplot(111,projection = '3d')
		the_file.write('ax = fig.add_subplot(111,projection = \'3d\')\n')																		# add 3d plot
	else :
		ax = fig.add_subplot(111)
		the_file.write('ax = fig.add_subplot(111)\n')	
	
	if(os.path.isfile('objs.pkl') == True):
		with open('objs.pkl') as f:  # Python 3: open(..., 'rb')
   			y_start_prev, y_end_prev,x_start_prev,x_end_prev = pickle.load(f)

																										# add 2d plot
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# this part handles the on hovering  details

	offsetbox = TextArea("Test 1",textprops=dict(size=7.5) ,minimumdescent=False)										# offset box object initially set to invisible
	xybox=(75., 75.)
	ab = AnnotationBbox(offsetbox, (0,0), xybox=xybox, xycoords='data', boxcoords="offset points",  pad=0.3,  arrowprops=dict(arrowstyle="->"))
	ax.add_artist(ab)
	ab.set_visible(False)

# function that displays the offset/annotation box when hovering 
	def hover(event):
		j = 0
		strr = ""
		if v == 0:
			for i in line :
				index = -1
				if i.contains(event)[0]:
					l = len(dataBase[details[j][i.contains(event)[1]["ind"][0]]])
					for k in range (l-1):
						strr += fieldList[k] + " : " + dataBase[details[j][i.contains(event)[1]["ind"][0]]][k] + "\n" 
					strr+= fieldList[k+1] + " : " + dataBase[details[j][i.contains(event)[1]["ind"][0]]][k+1]
					index = details[j][i.contains(event)[1]["ind"][0]]

					w,h = fig.get_size_inches()*fig.dpi
					ws = (event.x > w/2.)*-1 + (event.x <= w/2.) 
					hs = (event.y > h/2.)*-1 + (event.y <= h/2.)
					ab.xybox = (xybox[0]*ws, xybox[1]*hs)
					ab.set_visible(True)
					ab.xy = (xPoints[details[j][i.contains(event)[1]["ind"][0]]],yPoints[details[j][i.contains(event)[1]["ind"][0]]])
					offsetbox.set_text(strr)
					break
				else:
					ab.set_visible(False)
				j += 1
			fig.canvas.draw_idle()

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	i = 0
	while i < float(configLines[0][15]) :																															# setting the values of numberFields,plotLLimit,plotULimit using configLines[0] (see related descriptions above)
		numberFields.append(configLines[0][3*i+16])
		plotLLimit.append(float(configLines[0][3*i+17]))
		plotULimit.append(float(configLines[0][3*i+18]))
		i += 1

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	

# open the input(.csv ) file to get the data

	try:																																					# parse the first line of the input file to get field/column names, no. of fields etc. (see description of variables above)
		f = open(configLines[0][0],'r')
		fileFlag = 1																																# variable to know if end of 1st line has been reached 
		fieldLength = 0
		
		while fileFlag == 1:
			ch = f.read(1)
			if ch == ',':
				# add fieldLength to the list
				fieldLengthList.append(fieldLength)
				fieldLength = 0
				fieldNumber = fieldNumber + 1
			elif ch == '\n':
				# add fieldLength to the list
				fieldLengthList.append(fieldLength)
				fileFlag = 0
			else:
				fieldLength = fieldLength + 1
	finally:
		f.close()



	try:
		f = open(configLines[0][0],'r')
		i = 0
		while i < fieldNumber :
			st = f.read(fieldLengthList[i])
			fieldList.append(st)												# read the field/column names into a list
			f.read(1)
			i = i + 1
		while True :																															# read the entire .csv into a 2d list
			fileRow=f.readline().split(",")
			if fileRow == [""]:
				break
			fileRowNumber = fileRowNumber + 1
			try:
				fileRow.remove('\n')
			except:
				pass
			dataBase.append(fileRow)
	finally:
		f.close()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

	cType =  configLines[0][-4] 					# type of graph - line or scatter

	if configLines[0][-3] !='':					# set the degree of polynomial for curve fitting
		curveFit = 'True'
		deg = configLines[0][-3]
		#print "deg = " + deg
	else:
		curveFit = 'False'
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# getting the x,y,z values that are to be parsed

# X
	colNumX = fieldList.index(configLines[0][1]) 																			
	try :
		numberFields.index(configLines[0][1]) 															# check if the x axis selected is numerical
		xPoints = [i[colNumX] for i in dataBase]
	except ValueError :																										# if non numerical make key value pair in dict (key = x value; value = x co-ordinate)
		i = 0
		j = 0
		while i < fileRowNumber :
			if xDict.get(dataBase[i][colNumX]) == None :
				xDict[dataBase[i][colNumX]] = j
				xPoints.append(j)
				j += 1
			else :
				xPoints.append(xDict.get(dataBase[i][colNumX]))
			i += 1

# Y
	try :
		colNumY = fieldList.index(configLines[0][2])  												# check if the y axis supplied is a field or custom frmula
		try :
			numberFields.index(configLines[0][2])														# if field then check if it is numerical
			yPoints = [i[colNumY] for i in dataBase]
		except ValueError :																									# if non numerical make key value pair in dict (key = y value; value = y co-ordinate)
			i = 0
			j = 0
			while i < fileRowNumber :
				if yDict.get(dataBase[i][colNumY]) == None :
					yDict[dataBase[i][colNumY]] = j
					yPoints.append(j)
					j += 1
				else :
					yPoints.append(yDict.get(dataBase[i][colNumY]))
				i += 1
	except :																															# if custom formula call stringParse function and open the yP.txt to get processed y values
		stringParse(configLines[0][2])
		f = open('yP.txt','r')
		yPoints = f.readline().split(",")
		yPoints.pop()
		f.close()

# Z
	if configLines[0][3] == '1' :																						# if 3d enabled then same procedure as for x values
		colNumZ = fieldList.index(configLines[0][4])
		try :
			numberFields.index(configLines[0][4])
			zPoints = [i[colNumZ] for i in dataBase]
		except ValueError :
			i = 0
			j = 0
			while i < fileRowNumber :
				if zDict.get(dataBase[i][colNumZ]) == None :
					zDict[dataBase[i][colNumZ]] = j
					zPoints.append(j)
					j += 1
				else :
					zPoints.append(zDict.get(dataBase[i][colNumZ]))
				i += 1


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# checking for third(shape) parameter (only works for scatter graph)

	if configLines[0][5] != '' and (cType == 'scatter' or cType == 'bar-graph') : 																	# check if 3rd para enabled
		enaDiff1 = fieldList.index(configLines[0][5])																	# enaDiff1 - variable to store the field name of 3rd para
		distinctVals1 = []																															# list of distinct values in the 3rd para field
		i = 0
		try:																																						# set distinctVals1 and distinctValues1
			while i < fileRowNumber :
				try:
					tempIndex = distinctVals1.index(dataBase[i][enaDiff1])
				except:
					distinctVals1.append(dataBase[i][enaDiff1])
					distinctValues1 += 1
				i += 1
		except IndexError :
			print (i)
	else :
		distinctValues1 =  1

# checking for fourth(color) parameter
 	distinctVals2 = []
	if configLines[0][6] != '' :																												# check if 4th para enabled
		enaDiff2 = fieldList.index(configLines[0][6])																	# enaDiff2 - variable to store the field name of 4th para
		i = 0
		while i < fileRowNumber :																										# set distinctVals2 and distinctValues2
			try:
				tempIndex = distinctVals2.index(dataBase[i][enaDiff2])
			except:
				distinctVals2.append(dataBase[i][enaDiff2])
				distinctValues2 += 1
			i += 1
	else :
		distinctValues2 = 1
	distinctVals2.sort()
	i = 0

	# based on the distinctValues1 and distinctValues2 plotPoints in partioned according to shape and color combination
	if (configLines[0][3] == '1') :																										
		while i < distinctValues1 * distinctValues2 :
			plotPointsX.append([])
			plotPointsY.append([])
			plotPointsZ.append([])
			partitionedPoints.append([])
			details.append([])
			i += 1
	else :
		while i < distinctValues1 * distinctValues2 :
			plotPointsX.append([])
			plotPointsY.append([])
			partitionedPoints.append([])
			details.append([])
			i += 1
	
	



#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	
	# points stored in xPoints,yPoints and zPoints are detrmined to be valid or not based on column filtering, x axis sliders, y axis sliders
	# predicate value is evaluated - if true then the point satisfies the restrictions of column filtering, x axis sliders anf y axis sliders else false
	# store these points in filterPoints or filterZPoints
	i = 0
	m=0
	if configLines[0][3] != '1':
		while i < fileRowNumber :
			x = float(xPoints[i])
			y = float(yPoints[i])
			tValue = 'True'
			if configLines[0][8] == 't':
				if bool(xDict) :
					predicate = 'True'
				else :
					predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]))
			else :
				if bool(xDict) and bool(yDict) :
					predicate = 'True'
				elif bool(xDict) and not bool(yDict) :
					predicate = ( y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]) )
				elif not bool(xDict) and bool(yDict) :
					predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]))
				else :
					predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]) and y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]) )
			if predicate :
				j = 0
				while j < float(configLines[0][15]) :
					dat = float(dataBase[i][fieldList.index(numberFields[j])])
					if (dat > plotULimit[j] or dat < plotLLimit[j]) :
						tValue = 'False'
					j += 1
			else :
				tValue = 'False'
			if tValue == 'True':
				filterPoints.append((x,y,i))
				m += 1
			i += 1
	else :
		while i < fileRowNumber :

			x = float(xPoints[i])
			y = float(yPoints[i])
			z = float(zPoints[i])
			tValue = 'True'
			if configLines[0][8] == 't':
				if not bool(xDict) :
					if bool(zDict) :
						predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]))
					else :
						predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]) and z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))
				else :
					if bool(zDict) :
						predicate = 'True'
					else :
						predicate = (z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))

			else:

				if not bool(xDict) :
					if bool(yDict) :
						if bool(zDict) :
							predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]))
						else :
							predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]) and z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))

					else:
						if bool(zDict) :
							predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]) and y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]))
						else :
							predicate = (x >= (float)(configLines[0][9]) and x <= (float)(configLines[0][10]) and y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]) and z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))
				else :
					if bool(yDict) :
						if bool(zDict) :
							predicate = 'True'
						else :
							predicate = (z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))

					else:
						if bool(zDict) :
							predicate = ( y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]))
						else :
							predicate = ( y >= (float)(configLines[0][11]) and y <= (float)(configLines[0][12]) and z >= (float)(configLines[0][13]) and z <= (float)(configLines[0][14]))
			if predicate :
				j = 0
				while j < float(configLines[0][15]) :
					dat = float(dataBase[i][fieldList.index(numberFields[j])])
					if (dat > plotULimit[j] or dat < plotLLimit[j]) :
						tValue = 'False'
					j += 1
			else :
				tValue = 'False'

			if tValue == 'True':
				filterPoints.append((x,y,i))
				filterZPoints.append((z,i))
				m += 1
			i += 1
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

	i = 0
	if configLines[0][3] == '1' :
		if distinctValues1 > 1 and distinctValues2 > 1 :
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])*distinctValues2 + distinctVals2.index(dataBase[k[2]][enaDiff2])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				plotPointsZ[dex].append(filterZPoints[i][0])
				details[dex].append(k[2])
				i+=1
		elif distinctValues1 > 1:
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				plotPointsZ[dex].append(filterZPoints[i][0])
				details[dex].append(k[2])
				i += 1
		elif distinctValues2 > 1:
			for k in filterPoints :
				dex = distinctVals2.index(dataBase[k[2]][enaDiff2])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				plotPointsZ[dex].append(filterZPoints[i][0])
				details[dex].append(k[2])
				i += 1
		else :
			for k in filterPoints :
				plotPointsX[0].append(k[0])
				plotPointsY[0].append(k[1])
				plotPointsZ[0].append(filterZPoints[i][0])
				details[0].append(k[2])
				i += 1

	if configLines[0][3] == '4' :
		if distinctValues1 > 1 and distinctValues2 > 1 :
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])*distinctValues2 + distinctVals2.index(dataBase[k[2]][enaDiff2])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				details[dex].append(k[2])
		elif distinctValues1 > 1:
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				details[dex].append(k[2])
		elif distinctValues2 > 1:
			for k in filterPoints :
				dex = distinctVals2.index(dataBase[k[2]][enaDiff2])
				plotPointsX[dex].append(k[0])
				plotPointsY[dex].append(k[1])
				details[dex].append(k[2])
		else :
			for k in filterPoints :
				plotPointsX[0].append(k[0])
				plotPointsY[0].append(k[1])
				details[0].append(k[2])

	if configLines[0][3] == '3' :
		if distinctValues1 > 1 and distinctValues2 > 1 :
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])*distinctValues2 + distinctVals2.index(dataBase[k[2]][enaDiff2])
				partitionedPoints[dex].append(k)
		elif distinctValues1 > 1:
			for k in filterPoints :
				dex = distinctVals1.index(dataBase[k[2]][enaDiff1])
				partitionedPoints[dex].append(k)
		elif distinctValues2 > 1:
			for k in filterPoints :
				dex = distinctVals2.index(dataBase[k[2]][enaDiff2])
				partitionedPoints[dex].append(k)
		else :
			for k in filterPoints :
				partitionedPoints[0].append(k)
		ind = 0
		for colourList in partitionedPoints:
			paretoPoints =[]
			if configLines[0][4] == '1' :
				tempList = sorted(colourList)
				paretoPoints.append(tempList[0])
				j = 0
				for x_,y_,z_ in tempList :
					if y_ >= paretoPoints[j][1] :
						paretoPoints.append((x_,y_,z_))
						j+=1
				paretoPoints.pop(0)
				for k in paretoPoints:
					plotPointsX[ind].append(k[0])
					plotPointsY[ind].append(k[1])
					details[ind].append(k[2])
				ind += 1
			elif configLines[0][4] == '2' :
				tempList = sorted(colourList)
				paretoPoints.append(tempList[0])
				j = 0
				for x_,y_,z_ in tempList :
					if y_ <= paretoPoints[j][1] :
						paretoPoints.append((x_,y_,z_))
						j+=1
				paretoPoints.pop(0)
				for k in paretoPoints:
					plotPointsX[ind].append(k[0])
					plotPointsY[ind].append(k[1])
					details[ind].append(k[2])
				ind += 1
			elif configLines[0][4] == '3' :
				tempList = sorted(colourList,reverse=True)
				paretoPoints.append(tempList[0])
				j = 0
				for x_,y_,z_ in tempList :
					if y_ >= paretoPoints[j][1] :
						paretoPoints.append((x_,y_,z_))
						j+=1
				paretoPoints.pop(0)
				for k in paretoPoints:
					plotPointsX[ind].append(k[0])
					plotPointsY[ind].append(k[1])
					details[ind].append(k[2])
				ind += 1
			elif configLines[0][4] == '4' :
				tempList = sorted(colourList,reverse=True)
				paretoPoints.append(tempList[0])
				j = 0
				for x_,y_,z_ in tempList :
					if y_ <= paretoPoints[j][1] :
						paretoPoints.append((x_,y_,z_))
						j+=1
				paretoPoints.pop(0)
				for k in paretoPoints:
					plotPointsX[ind].append(k[0])
					plotPointsY[ind].append(k[1])
					details[ind].append(k[2])
				ind += 1
				
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

	# checking for number of distinct values of x-axis for making a bar-graph or histogram or bar-scatter(should be smaller than 8 for this to be possible)
	if cType == "bar-scatter":
		enaDiff3 = fieldList.index(configLines[0][1])
		distinctVals3 = []																															# list of distinct values in the 4th para field
		i = 0
		while i < fileRowNumber :																										# set distinctVals2 and distinctValues2
			try:
				tempIndex = distinctVals3.index(dataBase[i][enaDiff3])
			except:
				distinctVals3.append(dataBase[i][enaDiff3])
				distinctValues3 += 1
			if distinctValues3 > 8: 									#if we get more than 8 values we cannot make the bar-graph
				distinctValues3 = float("inf")
				break
			i += 1
		if distinctValues3 < 8 and distinctValues3 > 1:
			distinctVals3.sort()
			min_diff_x = float("inf")
			for index_diff in range(1,len(distinctVals3)):
				if float(distinctVals3[index_diff]) - float(distinctVals3[index_diff-1]) < min_diff_x:
					min_diff_x = float(distinctVals3[index_diff]) - float(distinctVals3[index_diff-1])	

	elif(cType == "bar-graph" or cType == "histogram"):
		len_dict = {}
		len_dict = defaultdict(lambda:0,len_dict)

		for pp in plotPointsX:
			for value in pp:
				len_dict[value] = len_dict[value] + 1
		
				if(len(len_dict)>8):
					distinctValues3 = float("inf")
					break;
				else: 
					distinctValues3 = len(len_dict)

		
		final_vals = collections.OrderedDict(sorted(len_dict.items()))
		distinctVals3 = list(final_vals.keys())
	
	else :
		distinctValues3 = float("inf")

# check if any error else make the graph and display
	yString = ''
	try:
		f = open('erLog.txt','r')
		yString = f.readline()
		f.close()
	except:
		pass																																		# check if incorrect formula
	if yString == configLines[0][2]:
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Incorrect Formula")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	
	elif distinctValues1 > 8:																																	# check if 3rd para exceeds limits
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Third Parameter has too many values")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()

	elif distinctValues2 > 8:																																	# check if 4th para exceeds limits
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Fourth Parameter has too many values")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	elif distinctValues3 > 8 and cType == "bar-graph":
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("X-Axis has too many values for a bar-graph")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	elif distinctValues3 > 8 and cType == "bar-scatter":
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("X-Axis has too many values for a bar-scatter")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	elif configLines[0][-10] !='' and configLines[0][-11] != '':
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Cannot select both \'Set y-start value\'' and \'Do not automatically resize axes\'")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	elif configLines[0][-11] != '' and y_start_prev == 0 and y_end_prev == 0 :
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Cannot select \'Do not automatically resize axes\' for the first plot as no previous plot found")
		msg.setWindowTitle("Error")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	else:          # no error plot graph
		the_file.write('patterns = ' + str(patterns) + '\n')
		the_file.write('colour = ' + str(colour) + '\n' )
		the_file.write('style = [\'.\',\'^\',\'h\',\'H\',\'>\',\'<\',\'x\',\'+\',\'p\',\'d\',\'8\']\n')
		#------------------------------------------------------------------------------------------------------------------------------------------------
		if cType == 'histogram':

			if(configLines[0][-8] != ''):
				ax.set_xlabel(configLines[0][-8])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][-8] + '\')\n')
			else:
				ax.set_xlabel(configLines[0][1])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][1] + '\')\n')

			ax.set_ylabel("Frequency")
			the_file.write('ax.set_ylabel("Frequency")\n')
			ax.set_title(configLines[0][7])
			the_file.write('ax.set_title(' + '\'' + configLines[0][7] + '\')\n')
			
			#with third parameter(color or pattern)
			if(configLines[0][6]!=''):
				#when x distinct values < 8, we will have bars
				if (distinctValues3 < 8) :
					opacity = 0.8
					bar_width = (0.2 *16) /(len(distinctVals3)*len(distinctVals2))
					y_pos = np.arange(len(distinctVals3))
					ax1 = plt.subplot(111)
					ax1.bar(y_pos,y_pos)
					rects_temp = ax1.patches
					for rect in rects_temp:
					    bar_width = rect.get_width()
					    break;
					ax1.clear()
					bar_width = bar_width/len(distinctVals2)
					the_file.write('bar_width = ' + str(bar_width) + '\n')
					the_file.write('distinctVals2 = ' + str(distinctVals2) + '\n')
					the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n')
					
					y_list = []
					if(configLines[0][-6] == "Yes"):									#when normalizations true
						ax.set_ylabel("Probability")
						the_file.write('ax.set_ylabel("Probability")\n')
					for q in range(len(distinctVals2)):
						dict_x = {}
						dict_x = defaultdict(lambda:0,dict_x)

						for key in distinctVals3:
							dict_x[key] = 0

						for point in plotPointsX[q]:
							dict_x[point] = dict_x[point] + 1
						
						if(configLines[0][-6] == "Yes"):
							for key in dict_x:
								dict_x[key] = float(1.0*dict_x[key]/len(plotPointsX[0]))

						final_d = collections.OrderedDict(sorted(dict_x.items()))

						ys = list(final_d.values())
						y_list.append(ys)
						if configLines[0][-12] == 'Pattern':
							ax.bar(y_pos + q*bar_width,ys, bar_width,
								alpha = opacity,
								color='yellow', edgecolor='black', hatch=patterns[q],
								label = distinctVals2[q])
						else: ax.bar(y_pos + q*bar_width,ys, bar_width,
								alpha = opacity,
								color= colour[q],
								label = distinctVals2[q])
					
					the_file.write('opacity = ' + str(opacity) + '\n')
					with open('objs_sd.pkl', 'w') as f: 
						pickle.dump([y_pos, y_list], f)	
					the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, y_list = pickle.load(f)\n')
					the_file.write('for q in range(len(distinctVals2)):\n')
					the_file.write('\t')
					if configLines[0][-12] == 'Pattern':
						the_file.write('ax.bar(y_pos + q*bar_width, y_list[q], bar_width, alpha = opacity, color=\'yellow\', edgecolor=\'black\', hatch=patterns[q], label = distinctVals2[q])\n')
					else:
						the_file.write('ax.bar(y_pos + q*bar_width, y_list[q], bar_width, alpha = opacity, color= colour[q], label = distinctVals2[q])\n')
					if(configLines[0][-9] != ''):
						the_file.write('rects = ax.patches\n')
						rects = ax.patches
						# For each bar: Place a label
						the_file.write('for rect in rects:\n')
						the_file.write('\ty_value = rect.get_height()\n')
						the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
						the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
						the_file.write('\tplt.annotate(label,(x_value, y_value),xytext=(0, 12),textcoords="offset points",ha=\'center\',va=\'top\')\n')
						
						for rect in rects:
						    y_value = rect.get_height()
						    x_value = rect.get_x() + rect.get_width() / 2
						    label = "{:.2f}".format(y_value)
						    plt.annotate(
						        label,                      # Use `label` as label
						        (x_value, y_value),         # Place label at end of the bar
						        xytext=(0, 12),          # Vertically shift label by `space`
						        textcoords="offset points", # Interpret `xytext` as offset in points
						        ha='center',                # Horizontally center label
						        va='top')  

					plt.xticks(y_pos + len(distinctVals2)*bar_width/2, distinctVals3) 					#to place the labels at correct positions on x axis
					the_file.write('plt.xticks(y_pos + len(distinctVals2)*bar_width/2, distinctVals3) 					#to place the labels at correct positions on x axis\n')
					ax.legend(loc = 'best',title = configLines[0][6])
					the_file.write('ax.legend(loc = \'best\',title = \'' + configLines[0][6] + '\')\n')
					
				#when continues data on x axis
				else:
					num_bins = 5
					lb = min(plotPointsX[0])
					ub = max(plotPointsX[0])
					if(configLines[0][-2] != ''):
						interval_size = float(configLines[0][-2])
						num_bins = int ( math.ceil(1.0*(ub - lb)/interval_size) )
					else:
						interval_size = (ub - lb)/num_bins

					the_file.write('num_bins = ' + str(num_bins) + '\n')
					the_file.write('distinctVals2 = ' + str(distinctVals2) + '\n')

					# if(configLines[0][-12] == 'Pattern'):
					# 	ax1 = plt.subplot(111)
					# 	the_file.write('ax1 = plt.subplot(111)\n')
					
					colr = ['yellow']*len(distinctVals2)
					if(configLines[0][-6] == 'Yes'):
						ax.set_ylabel("Probability")
						the_file.write('ax.set_ylabel("Probability")\n')
						weights = []
						for q in range(len(distinctVals2)):
							weights.append(np.ones_like(plotPointsX[q])/float(len(plotPointsX[q])))
						with open('objs_sd.pkl', 'w') as f: 
							pickle.dump([plotPointsX, weights], f)	
						the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'plotPointsX, weights = pickle.load(f)\n')
						
						if(configLines[0][-12] == 'Pattern'):
							counts, bins, patches = ax.hist(plotPointsX, weights=weights, bins=num_bins, color = colr, align = 'mid', label = distinctVals2)
							the_file.write('colr = [\'yellow\']*len(distinctVals2)\n')
							the_file.write('counts, bins, patches = ax.hist(plotPointsX, weights=weights, bins=num_bins, color = colr, align = \'mid\', label = distinctVals2)\n')
						else:
							counts, bins, patches = ax.hist(plotPointsX, weights=weights, bins=num_bins, align = 'mid', label = distinctVals2)
							the_file.write('counts, bins, patches = ax.hist(plotPointsX, weights=weights, bins=num_bins, align = \'mid\', label = distinctVals2)\n')
					else:
						with open('objs_sd.pkl', 'w') as f: 
							pickle.dump(plotPointsX, f)	
						the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'plotPointsX = pickle.load(f)\n')
						if(configLines[0][-12] == 'Pattern'):
							counts, bins, patches = ax.hist(plotPointsX, bins=num_bins, color = colr, align = 'mid', label = distinctVals2)
							# ax1.clear()
							the_file.write('colr = [\'yellow\']*len(distinctVals2)\n')
							the_file.write('counts, bins, patches = ax.hist(plotPointsX, bins=num_bins, color = colr, align = \'mid\', label = distinctVals2)\n')
							# the_file.write('ax1.clear()\n')
						else:
							counts, bins, patches = ax.hist(plotPointsX, bins=num_bins, align = 'mid', label = distinctVals2)
							the_file.write('counts, bins, patches = ax.hist(plotPointsX, bins=num_bins, align = \'mid\', label = distinctVals2)\n')
					


					ax.set_xlim( lb - 0.1*interval_size, None )
					the_file.write('ax.set_xlim(' + str(lb - 0.1*interval_size) + ', None)\n')
					if configLines[0][-12] == 'Pattern':
						for n1,patch in enumerate(patches):
							for p in patch:
								p.set_hatch(patterns[n1])
								ax.add_patch(p)
						the_file.write('for n1,patch in enumerate(patches):\n')
						the_file.write('\tfor p in patch:\n')
						the_file.write('\t\tp.set_hatch(patterns[n1])\n')
						the_file.write('\t\tax.add_patch(p)\n')

					if(configLines[0][-9] != ''):
						for patch in patches:
							for rect in patch:
								x_value = rect.get_x() + rect.get_width()/2
								y_value = rect.get_height()
								label = "{:.2f}".format(y_value)
								plt.annotate(
									label,                      # Use `label` as label
									(x_value, y_value),         # Place label at end of the bar
									xytext=(0, 12),          # Vertically shift label by `space`
									textcoords="offset points", # Interpret `xytext` as offset in points
									ha='center',                # Horizontally center label
									va='top') 
						the_file.write('for patch in patches:\n')
						the_file.write('\tfor rect in patch:\n')
						the_file.write('\t\ty_value = rect.get_height()\n')
						the_file.write('\t\tx_value = rect.get_x() + rect.get_width() / 2\n')
						the_file.write('\t\tlabel = "{:.2f}".format(y_value)\n')
						the_file.write('\t\tplt.annotate(label,(x_value, y_value),xytext=(0, 12),textcoords="offset points",ha=\'center\',va=\'top\')\n')
						

					ax.legend(loc= 'best',title = configLines[0][6])
					the_file.write('ax.legend(loc= \'best\',title = \'' + configLines[0][6] + '\')\n')
					

			else:
				#when x distinct values < 8
				if (distinctValues3 < 8) :
					dict_x = {}
					dict_x = defaultdict(lambda:0,dict_x)
					for point in plotPointsX[0]:
						dict_x[point] = dict_x[point] + 1

					if(configLines[0][-6] == "Yes"):
						ax.set_ylabel("Probability")
						the_file.write('ax.set_ylabel("Probability")')
						for key in dict_x:
							dict_x[key] = float(1.0*dict_x[key]/len(plotPointsX[0]))

					final_d = collections.OrderedDict(sorted(dict_x.items()))

					#plotting------------------------------------------------------------------------
					y_pos = np.arange(len(distinctVals3))
					ys = list(final_d.values())
					with open('objs_sd.pkl', 'w') as f: 
						pickle.dump([distinctVals3, y_pos, ys] , f)	
					the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'distinctVals3, y_pos, ys = pickle.load(f)\n')
					
					plt.bar(y_pos,ys)
					the_file.write('plt.bar(y_pos,ys)')

					rects = ax.patches
					# For each bar: Place a label
				
					the_file.write('rects = ax.patches\n')
					the_file.write('for rect in rects:\n')
					the_file.write('\ty_value = rect.get_height()\n')
					the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
					the_file.write('\tbw = rect.get_width()\n')
					the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
					if(configLines[0][-9] != ''):
						the_file.write('\tplt.annotate(label,(x_value, y_value),xytext=(0, 12),textcoords="offset points",ha=\'center\',va=\'top\')\n')
					for rect in rects:
					    y_value = rect.get_height()
					    x_value = rect.get_x() + rect.get_width() / 2
					    bw = rect.get_width()
					   
					    label = "{:.2f}".format(y_value)
					    if(configLines[0][-9] != ''):
						    plt.annotate(
						        label,                      # Use `label` as label
						        (x_value, y_value),         # Place label at end of the bar
						        xytext=(0, 12),          # Vertically shift label by `space`
						        textcoords="offset points", # Interpret `xytext` as offset in points
						        ha='center',                # Horizontally center label
						        va='top')
					the_file.write('bw = rect.get_width()\n')
					
					plt.xticks(y_pos + bw/2, distinctVals3)
					the_file.write('plt.xticks(y_pos + bw/2, distinctVals3)\n')
				

				#when continues data on x axis
				else:
					num_bins = 5
					lb = min(plotPointsX[0])
					ub = max(plotPointsX[0])
					if(configLines[0][-2] != ''):
						interval_size = float(configLines[0][-2])
						num_bins = int ( math.ceil(1.0*(ub - lb)/interval_size) )
					else:
						interval_size = (ub - lb)/num_bins
					the_file.write('num_bins = ' + str(num_bins) + '\n')
					if(configLines[0][-6] == 'Yes'):
						ax.set_ylabel("Probability")
						the_file.write('ax.set_ylabel("Probability")\n')
						weights = np.ones_like(plotPointsX[0])/float(len(plotPointsX[0]))
						with open('objs_sd.pkl', 'w') as f: 
							pickle.dump([plotPointsX, weights] , f)	
						the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'plotPointsX, weights = pickle.load(f)\n')

						counts, bins, patches = ax.hist(plotPointsX[0], weights=weights, bins=num_bins, align = 'mid')
						the_file.write('counts, bins, patches = ax.hist(plotPointsX[0], weights=weights, bins=num_bins, align = \'mid\')\n')
					else:
						with open('objs_sd.pkl', 'w') as f: 
							pickle.dump(plotPointsX , f)	
						the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'plotPointsX = pickle.load(f)\n')
						counts, bins, patches = ax.hist(plotPointsX[0], bins=num_bins, align = 'mid')
						the_file.write('counts, bins, patches = ax.hist(plotPointsX[0], bins=num_bins, align = \'mid\')\n')

					ax.set_xlim( lb - 0.1*interval_size, None )
					the_file.write('ax.set_xlim(' + str(lb - 0.1*interval_size) + ', None)\n')

					if(configLines[0][-9] != ''):
						the_file.write('rects = ax.patches\n')
						the_file.write('for rect in rects:\n')
						the_file.write('\ty_value = rect.get_height()\n')
						the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
						the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
						the_file.write('\tplt.annotate(label,(x_value, y_value),xytext=(0, 12),textcoords="offset points",ha=\'center\',va=\'top\')\n')  
						for rect in patches:
							x_value = rect.get_x() + rect.get_width()/2
							y_value = rect.get_height()
							label = "{:.2f}".format(y_value)
							plt.annotate(
						        label,                      # Use `label` as label
						        (x_value, y_value),         # Place label at end of the bar
						        xytext=(0, 12),          # Vertically shift label by `space`
						        textcoords="offset points", # Interpret `xytext` as offset in points
						        ha='center',                # Horizontally center label
						        va='top')
							
			

		#------------------------------------------------------------------------------------------------------------------------------------------------
		elif cType == 'bar-graph':


			#with third and fourth parameter----------------------------------------------------------------
			if(configLines[0][6] != '' and configLines[0][5] != ''):
				opacity = 0.8
				bar_width = (0.2 *16) /(len(distinctVals3)*len(distinctVals2)*len(distinctVals1))
				y_pos1 = np.arange(len(distinctVals3)*len(distinctVals1))
				ax1 = plt.subplot(111)
				ax1.bar(y_pos1,y_pos1)
				rects_temp = ax1.patches
				for rect in rects_temp:
				    bar_width = rect.get_width()
				    break;
				ax1.clear()
				bar_width = bar_width/(len(distinctVals2))
				the_file.write('bar_width = ' + str(bar_width) +'\n')
				the_file.write('opacity = ' + str(opacity) + '\n' )
				the_file.write('distinctVals1 = ' + str(distinctVals1) + '\n') 
				the_file.write('distinctVals2 = ' + str(distinctVals2) + '\n') 
				the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n') 
				the_file.write('distinctValues2 = ' + str(distinctValues2) + '\n') 
				the_file.write('distinctValues3 = ' + str(distinctValues3) + '\n') 
				the_file.write('distinctValues1 = ' + str(distinctValues1) + '\n') 
				main_list_list = []
				for q in range(len(distinctVals2)):
					main_list = []
					for f in range(len(distinctVals1)):
						#average---------------------------------------------------------------------
						
						if configLines[0][-5] == 'Average':
							average_dict = {}
							average_dict = defaultdict(lambda:0,average_dict)
							len_dict = {}
							len_dict = defaultdict(lambda:0,len_dict)

							for key in distinctVals3:
								average_dict[key] = 0
								len_dict[key] = 0 

							for z,value in enumerate(plotPointsY[f*distinctValues2 +q]):
								average_dict[plotPointsX[f*distinctValues2 + q][z]] = (average_dict[plotPointsX[f*distinctValues2 + q][z]] + value)
								len_dict[plotPointsX[f*distinctValues2 + q][z]] = len_dict[plotPointsX[f*distinctValues2 + q][z]] + 1

							for key in average_dict:
								if(len_dict[key] != 0):
									average_dict[key] = average_dict[key]/len_dict[key]

							final_d = collections.OrderedDict(sorted(average_dict.items()))
							
						#max----------------------------------------------------------------------------
						if configLines[0][-5] == 'Maximum':
							max_dict = {}
							max_dict = defaultdict(lambda:float("-inf"),max_dict)
							
							for key in distinctVals3:
								max_dict[key] = float("-inf") 

							for z,value in enumerate(plotPointsY[q]):
								max_dict[plotPointsX[q][z]] = max(max_dict[plotPointsX[q][z]],value)
								
							final_d = collections.OrderedDict(sorted(max_dict.items()))
							for key in distinctVals3:
								if(final_d[key] == float('-inf')):
									final_d[key] = 0
						
						#min---------------------------------------------------------------------------
						if configLines[0][-5] == 'Minimum':
							min_dict = {}
							min_dict = defaultdict(lambda:float("inf"),min_dict)
							
							for key in distinctVals3:
								min_dict[key] = float("inf") 

							for z,value in enumerate(plotPointsY[q]):
								min_dict[plotPointsX[q][z]] = min(min_dict[plotPointsX[q][z]],value)
							
							final_d = collections.OrderedDict(sorted(min_dict.items()))
			 				for key in distinctVals3:
								if(final_d[key] == float('inf')):
									final_d[key] = 0

						ys = list(final_d.values())
						main_list = main_list + ys
					main_list_list.append(main_list)	
					y_pos = np.arange(len(distinctVals3)*len(distinctVals1))
					
					#color or pattern
					if configLines[0][-12] == 'Color':
						rec = ax.bar(y_pos + (q)*bar_width,main_list, bar_width,
							alpha = opacity,
							color= colour[q],
							label = distinctVals2[q])
					else:
						rec = ax.bar(y_pos + (q)*bar_width,main_list, bar_width,
							alpha = opacity,
							label = distinctVals2[q],
							color='yellow', edgecolor='black', hatch=patterns[q])	
				
				with open('objs_sd.pkl', 'w') as f: 
					pickle.dump([y_pos,main_list_list] , f)	
				the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, main_list_list = pickle.load(f)\n')
				the_file.write('for q in range(len(distinctVals2)):\n')
				if configLines[0][-12] == 'Color':
					the_file.write('\trec = ax.bar(y_pos + (q)*bar_width,main_list_list[q], bar_width,alpha = opacity,color= colour[q],label = distinctVals2[q])\n')
				else:
					the_file.write('\trec = ax.bar(y_pos + (q)*bar_width,main_list_list[q], bar_width,alpha = opacity,color=\'yellow\', edgecolor=\'black\', hatch=patterns[q] ,label = distinctVals2[q])\n')

				the_file.write('rects = ax.patches\n')
				the_file.write('for num,rect in enumerate(rects):\n')
				the_file.write('\ty_value = rect.get_height()\n')
				the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
				the_file.write('\tspace = 5\n')
				the_file.write('\tva = \'bottom\'\n')
				the_file.write('\tif y_value < 0:\n\t\tspace *= -1\n\t\tva = \'top\'\n')
				the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
				the_file.write('\tif (num+1)%(len(distinctVals3)) == 0 and num < distinctValues1*distinctValues3:\n')
				the_file.write('\t\tplt.annotate("|", (y_pos[num] + bar_width*distinctValues2, 0),xytext=(0,-30),textcoords="offset points", ha=\'center\', va=\'center\')\n')
				the_file.write('\tif num % distinctValues3 == 0 and num < distinctValues3*distinctValues1:\n')
				the_file.write('\t\tplt.annotate(distinctVals1[num/distinctValues3],(y_pos[num] + (y_pos[num + distinctValues3 -1] - y_pos[num] + (bar_width*distinctValues2) )/2, 0),xytext=(0, -30), textcoords="offset points", ha=\'center\', va=\'center\')\n')
				the_file.write('\t\tplt.annotate("|", (y_pos[num], 0), xytext=(0, -30), textcoords="offset points", ha=\'center\', va=\'center\')\n')
				if(configLines[0][-9] != ''):
					the_file.write('\tplt.annotate( label,(x_value, y_value),xytext=(0, space),textcoords="offset points", ha=\'center\', va=va)\n')
				 
				rects = ax.patches
				for num,rect in enumerate(rects):
					y_value = rect.get_height()
					x_value = rect.get_x() + rect.get_width() / 2
					space = 5
					va = 'bottom'
					if y_value < 0:
						space *= -1
				    	va = 'top'
					label = "{:.2f}".format(y_value)
					if (num+1)%(len(distinctVals3)) == 0 and num < distinctValues1*distinctValues3:
						plt.annotate("|", (y_pos[num] + bar_width*distinctValues2, 0),
							xytext=(0,-30),
							textcoords="offset points", ha='center', va='center')
					if num % distinctValues3 == 0 and num < distinctValues3*distinctValues1:
						plt.annotate(distinctVals1[num/distinctValues3],
							(y_pos[num] + (y_pos[num + distinctValues3 -1] - y_pos[num] + (bar_width*distinctValues2) )/2, 0),
							xytext=(0, -30), 
							textcoords="offset points", ha='center', va='center')
						plt.annotate("|", (y_pos[num], 0), xytext=(0, -30), textcoords="offset points", ha='center', va='center')		
					
					
					if(configLines[0][-9] != ''):
					    plt.annotate(
					        label,                      # Use `label` as label
					        (x_value, y_value),         # Place label at end of the bar
					        xytext=(0, space),          # Vertically shift label by `space`
					        textcoords="offset points", # Interpret `xytext` as offset in points
					        ha='center',                # Horizontally center label
					        va=va)

				vals = distinctVals3*len(distinctVals1)
				the_file.write('vals = ' + str(vals) + '\n')
				plt.xticks(y_pos + len(distinctVals2)*bar_width/2, vals)
				the_file.write('plt.xticks(y_pos + len(distinctVals2)*bar_width/2, vals)\n')
				ax.legend(loc = 'best',title = configLines[0][6])
				the_file.write('ax.legend(loc= \'best\',title = \'' + configLines[0][6] + '\')\n')
				

			#with only fourth parameter--------------------------------------------------------------------
			elif(configLines[0][5] != ''):
				opacity = 0.8
				the_file.write('opacity = ' + str(opacity) + '\n' )
				the_file.write('distinctVals1 = ' + str(distinctVals1) + '\n')
				the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n')
				the_file.write('distinctValues3 = ' + str(distinctValues3) + '\n') 
				the_file.write('distinctValues1 = ' + str(distinctValues1) + '\n')

				main_list = []
				for f in range(len(distinctVals1)):
					#average---------------------------------------------------------------------
					if configLines[0][-5] == 'Average':
						average_dict = {}
						average_dict = defaultdict(lambda:0,average_dict)
						len_dict = {}
						len_dict = defaultdict(lambda:0,len_dict)

						for key in distinctVals3:
							average_dict[key] = 0
							len_dict[key] = 0 

						for z,value in enumerate(plotPointsY[f*distinctValues2 +0]):
							average_dict[plotPointsX[f*distinctValues2 + 0][z]] = (average_dict[plotPointsX[f*distinctValues2 + 0][z]] + value)
							len_dict[plotPointsX[f*distinctValues2 + 0][z]] = len_dict[plotPointsX[f*distinctValues2 + 0][z]] + 1

						for key in average_dict:
							if(len_dict[key] != 0):
								average_dict[key] = average_dict[key]/len_dict[key]

						final_d = collections.OrderedDict(sorted(average_dict.items()))
						
					#max----------------------------------------------------------------------------
					if configLines[0][-5] == 'Maximum':
						max_dict = {}
						max_dict = defaultdict(lambda:float("-inf"),max_dict)
						
						for key in distinctVals3:
							max_dict[key] = float("-inf") 

						for z,value in enumerate(plotPointsY[0]):
							max_dict[plotPointsX[0][z]] = max(max_dict[plotPointsX[0][z]],value)
							
						final_d = collections.OrderedDict(sorted(max_dict.items()))
						for key in distinctVals3:
							if(final_d[key] == float('-inf')):
								final_d[key] = 0
					
					#min---------------------------------------------------------------------------
					if configLines[0][-5] == 'Minimum':
						min_dict = {}
						min_dict = defaultdict(lambda:float("inf"),min_dict)
						
						for key in distinctVals3:
							min_dict[key] = float("inf") 

						for z,value in enumerate(plotPointsY[0]):
							min_dict[plotPointsX[0][z]] = min(min_dict[plotPointsX[0][z]],value)
						
						final_d = collections.OrderedDict(sorted(min_dict.items()))
		 				for key in distinctVals3:
							if(final_d[key] == float('inf')):
								final_d[key] = 0

					ys = list(final_d.values())
					main_list = main_list + ys
				y_pos = np.arange(len(distinctVals3)*len(distinctVals1))
				
				rec = ax.bar(y_pos , main_list, alpha = opacity)
					

				with open('objs_sd.pkl', 'w') as f: 
					pickle.dump([y_pos,main_list] , f)	
				the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, main_list = pickle.load(f)\n')
				
				the_file.write('rec = ax.bar(y_pos , main_list,alpha = opacity)\n')
				

				the_file.write('rects = ax.patches\n')
				the_file.write('for num,rect in enumerate(rects):\n')
				the_file.write('\ty_value = rect.get_height()\n')
				the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
				the_file.write('\tbw = rect.get_width()\n')
				the_file.write('\tspace = 5\n')
				the_file.write('\tva = \'bottom\'\n')
				the_file.write('\tif y_value < 0:\n\t\tspace *= -1\n\t\tva = \'top\'\n')
				the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
				the_file.write('\tif (num+1)%(len(distinctVals3)) == 0 and num < distinctValues1*distinctValues3:\n')
				the_file.write('\t\tplt.annotate("|", (y_pos[num] + bw, 0),xytext=(0,-30),textcoords="offset points", ha=\'center\', va=\'center\')\n')
				the_file.write('\tif num % distinctValues3 == 0 and num < distinctValues3*distinctValues1:\n')
				the_file.write('\t\tplt.annotate(distinctVals1[num/distinctValues3],(y_pos[num] + (y_pos[num + distinctValues3 -1] - y_pos[num])/2, 0),xytext=(0, -30), textcoords="offset points", ha=\'center\', va=\'center\')\n')
				the_file.write('\t\tplt.annotate("|", (y_pos[num], 0), xytext=(0, -30), textcoords="offset points", ha=\'center\', va=\'center\')\n')
				if(configLines[0][-9] != ''):
					the_file.write('\tplt.annotate( label,(x_value, y_value),xytext=(0, space),textcoords="offset points", ha=\'center\', va=va)\n')

				rects = ax.patches
				for num,rect in enumerate(rects):
					y_value = rect.get_height()
					x_value = rect.get_x() + rect.get_width() / 2
					bw = rect.get_width()
					space = 5
					va = 'bottom'
					if y_value < 0:
						space *= -1
				    	va = 'top'
					label = "{:.2f}".format(y_value)
					if (num+1)%(len(distinctVals3)) == 0 and num < distinctValues1*distinctValues3:
						plt.annotate("|", (y_pos[num] + bw, 0),
							xytext=(0,-30),
							textcoords="offset points", ha='center', va='center')
					if num % distinctValues3 == 0 and num < distinctValues3*distinctValues1:
						plt.annotate(distinctVals1[num/distinctValues3],
							(y_pos[num] + (y_pos[num + distinctValues3 -1] - y_pos[num] )/2, 0),
							xytext=(0, -30), 
							textcoords="offset points", ha='center', va='center')
						plt.annotate("|", (y_pos[num], 0), xytext=(0, -30), textcoords="offset points", ha='center', va='center')		
					
					
					if(configLines[0][-9] != ''):
					    plt.annotate(
					        label,                      # Use `label` as label
					        (x_value, y_value),         # Place label at end of the bar
					        xytext=(0, space),          # Vertically shift label by `space`
					        textcoords="offset points", # Interpret `xytext` as offset in points
					        ha='center',                # Horizontally center label
					        va=va)
				
				vals = distinctVals3*len(distinctVals1)
				the_file.write('vals = ' + str(vals) + '\n')
				plt.xticks(y_pos, vals)
				the_file.write('plt.xticks(y_pos, vals)\n')

			elif(configLines[0][6] != ''):							#third parameter
				opacity = 0.8
				bar_width = (0.2 *16) /(len(distinctVals3)*len(distinctVals2))
				
				y_pos = np.arange(len(distinctVals3))
				ax1 = plt.subplot(111)
				ax1.bar(y_pos,y_pos)
				rects_temp = ax1.patches
				for rect in rects_temp:
				    bar_width = rect.get_width()
				    break;
				ax1.clear()
				bar_width = bar_width/len(distinctVals2)

				the_file.write('bar_width = ' + str(bar_width) +'\n')
				the_file.write('opacity = ' + str(opacity) + '\n' )
				the_file.write('distinctVals2 = ' + str(distinctVals2) + '\n') 
				the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n')
				main_list_list = []
				for q in range(len(distinctVals2)):
					#average---------------------------------------------------------------------
					if configLines[0][-5] == 'Average':
						average_dict = {}
						average_dict = defaultdict(lambda:0,average_dict)
						len_dict = {}
						len_dict = defaultdict(lambda:0,len_dict)

						for key in distinctVals3:
							average_dict[key] = 0
							len_dict[key] = 0 

						for z,value in enumerate(plotPointsY[q]):
							average_dict[plotPointsX[q][z]] = (average_dict[plotPointsX[q][z]] + value)
							len_dict[plotPointsX[q][z]] = len_dict[plotPointsX[q][z]] + 1

						for key in average_dict:
							if(len_dict[key] != 0):
								average_dict[key] = average_dict[key]/len_dict[key]

						final_d = collections.OrderedDict(sorted(average_dict.items()))
						

					#max----------------------------------------------------------------------------
					if configLines[0][-5] == 'Maximum':
						max_dict = {}
						max_dict = defaultdict(lambda:float("-inf"),max_dict)
						
						for key in distinctVals3:
							max_dict[key] = float("-inf") 

						for z,value in enumerate(plotPointsY[q]):
							max_dict[plotPointsX[q][z]] = max(max_dict[plotPointsX[q][z]],value)
							
						final_d = collections.OrderedDict(sorted(max_dict.items()))
						for key in distinctVals3:
							if(final_d[key] == float('-inf')):
								final_d[key] = 0
					
					#min---------------------------------------------------------------------------
					if configLines[0][-5] == 'Minimum':
						min_dict = {}
						min_dict = defaultdict(lambda:float("inf"),min_dict)
						
						for key in distinctVals3:
							min_dict[key] = float("inf") 

						for z,value in enumerate(plotPointsY[q]):
							min_dict[plotPointsX[q][z]] = min(min_dict[plotPointsX[q][z]],value)
						
						final_d = collections.OrderedDict(sorted(min_dict.items()))
		 				for key in distinctVals3:
							if(final_d[key] == float('inf')):
								final_d[key] = 0
					
					#plotting------------------------------------------------------------------------
					ys = list(final_d.values())
					main_list_list.append(ys)
					

					if configLines[0][-12] == 'Pattern' :
						rec = ax.bar(y_pos + q*bar_width,ys, bar_width,
							alpha = opacity,
							label = distinctVals2[q],color='yellow', edgecolor='black', hatch=patterns[q])
					else:
						rec = ax.bar(y_pos + q*bar_width,ys, bar_width,
							alpha = opacity,
							color= colour[q],
							label = distinctVals2[q])

				with open('objs_sd.pkl', 'w') as f: 
					pickle.dump([y_pos,main_list_list] , f)	
				the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, main_list_list = pickle.load(f)\n')
				the_file.write('for q in range(len(distinctVals2)):\n')
				if configLines[0][-12] == 'Pattern' :
					the_file.write('\trec = ax.bar(y_pos + q*bar_width,main_list_list[q], bar_width,alpha = opacity,label = distinctVals2[q],color=\'yellow\', edgecolor=\'black\', hatch=patterns[q])\n')
					
				else:
					the_file.write('\trec = ax.bar(y_pos + q*bar_width,main_list_list[q], bar_width,alpha = opacity,color= colour[q],label = distinctVals2[q])\n')
					
				rects = ax.patches
				# For each bar: Place a label
				if(configLines[0][-9] != ''):
					the_file.write('rects = ax.patches\n')
					the_file.write('for num,rect in enumerate(rects):\n')
					the_file.write('\ty_value = rect.get_height()\n')
					the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
					the_file.write('\tspace = 5\n')
					the_file.write('\tva = \'bottom\'\n')
					the_file.write('\tif y_value < 0:\n\t\tspace *= -1\n\t\tva = \'top\'\n')
					the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
					the_file.write('\tplt.annotate( label,(x_value, y_value),xytext=(0, space),textcoords="offset points", ha=\'center\', va=va)\n')


				if(configLines[0][-9] != ''):
					for rect in rects:
					    y_value = rect.get_height()
					    x_value = rect.get_x() + rect.get_width() / 2
					    space = 5
					    va = 'bottom'
					    if y_value < 0:
					        space *= -1
					        va = 'top'
					    label = "{:.2f}".format(y_value)
					    plt.annotate(
						    label,                      # Use `label` as label
						    (x_value, y_value),         # Place label at end of the bar
						    xytext=(0, space),          # Vertically shift label by `space`
						    textcoords="offset points", # Interpret `xytext` as offset in points
						    ha='center',                # Horizontally center label
						    va=va)  

				plt.xticks(y_pos + len(distinctVals2)*bar_width/2, distinctVals3)
				the_file.write('plt.xticks(y_pos + len(distinctVals2)*bar_width/2, distinctVals3)\n')
				ax.legend(loc = 'best',title = configLines[0][6])
				the_file.write('ax.legend(loc= \'best\',title = \'' + configLines[0][6] + '\')\n')
				

			else:
				#all---------------------------------------------------------------------------
				if(configLines[0][-5] == 'All'):
					opacity = 0.8
					bar_width = (0.2 *16) /(len(distinctVals3)*3)
					y_pos = np.arange(len(distinctVals3))
					ax1 = plt.subplot(111)
					ax1.bar(y_pos,y_pos)
					rects_temp = ax1.patches
					for rect in rects_temp:
					    bar_width = rect.get_width()
					    break;
					ax1.clear()
					bar_width = bar_width/3
					the_file.write('bar_width = ' + str(bar_width) +'\n')
					the_file.write('opacity = ' + str(opacity) + '\n' )
					the_file.write('distinctVals2 = ' + str(distinctVals2) + '\n') 
					the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n')
					ys_list = []
					#min---------------------------------------------------------------------------
					
					min_dict = {}
					min_dict = defaultdict(lambda:float("inf"),min_dict)
					
					for key in distinctVals3:
							min_dict[key] = float("inf") 

					for q,value in enumerate(plotPointsY[0]):
						min_dict[plotPointsX[0][q]] = min(min_dict[plotPointsX[0][q]],value)
						
					final_d = collections.OrderedDict(sorted(min_dict.items()))

					for key in distinctVals3:
							if(final_d[key] == float('inf')):
								final_d[key] = 0

					ys = list(final_d.values())
					ys_list.append(ys)
					if configLines[0][-12] == 'Pattern' :
						rec = ax.bar(y_pos + 0*bar_width,ys, bar_width,
							alpha = opacity,
							color='yellow', edgecolor='black', hatch=patterns[0],
							label = "Minimum")
					else:
						rec = ax.bar(y_pos + 0*bar_width,ys, bar_width,
							alpha = opacity,
							color= colour[0],
							label = "Minimum")

					#average---------------------------------------------------------------------
					average_dict = {}
					average_dict = defaultdict(lambda:0,average_dict)
					len_dict = {}
					len_dict = defaultdict(lambda:0,len_dict)
					for key in distinctVals3:
							average_dict[key] = 0
							len_dict[key] = 0 
					for q,value in enumerate(plotPointsY[0]):
						average_dict[plotPointsX[0][q]] = (average_dict[plotPointsX[0][q]] + value)
						len_dict[plotPointsX[0][q]] = len_dict[plotPointsX[0][q]] + 1

					for key in average_dict:
						average_dict[key] = average_dict[key]/len_dict[key]

					final_d = collections.OrderedDict(sorted(average_dict.items()))
					ys = list(final_d.values())
					ys_list.append(ys)
					if configLines[0][-12] == 'Pattern' :
						ax.bar(y_pos + 1*bar_width,ys, bar_width,
							alpha = opacity,
							color='yellow', edgecolor='black', hatch=patterns[1],
							label = "Average")
					else:
						ax.bar(y_pos + 1*bar_width,ys, bar_width,
							alpha = opacity,
							color= colour[1],
							label = "Average")

					#max----------------------------------------------------------------------------
					max_dict = {}
					max_dict = defaultdict(lambda:float("-inf"),max_dict)
					
					
					for key in distinctVals3:
							max_dict[key] = float("-inf") 

					for q,value in enumerate(plotPointsY[0]):
						max_dict[plotPointsX[0][q]] = max(max_dict[plotPointsX[0][q]],value)
						

					final_d = collections.OrderedDict(sorted(max_dict.items()))
					for key in distinctVals3:
							if(final_d[key] == float('-inf')):
								final_d[key] = 0
					ys = list(final_d.values())
					ys_list.append(ys)

					if configLines[0][-12] == 'Pattern' :
						ax.bar(y_pos + 2*bar_width,ys, bar_width,
							alpha = opacity,
							color='yellow', edgecolor='black', hatch=patterns[2],
							label = "Maximum")
					else:
						ax.bar(y_pos + 2*bar_width,ys, bar_width,
							alpha = opacity,
							color= colour[2],
							label = "Maximum")

					with open('objs_sd.pkl', 'w') as f: 
						pickle.dump([y_pos,ys_list] , f)	
					the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, ys_list = pickle.load(f)\n')
					if configLines[0][-12] == 'Pattern' :
						the_file.write('rec = ax.bar(y_pos + 0*bar_width,ys_list[0], bar_width,alpha = opacity,color=\'yellow\', edgecolor=\'black\', hatch=patterns[0],label = "Minimum")\n')
						the_file.write('rec = ax.bar(y_pos + 1*bar_width,ys_list[1], bar_width,alpha = opacity,color=\'yellow\', edgecolor=\'black\', hatch=patterns[1],label = "Average")\n')
						the_file.write('rec = ax.bar(y_pos + 2*bar_width,ys_list[2], bar_width,alpha = opacity,color=\'yellow\', edgecolor=\'black\', hatch=patterns[2],label = "Maximum")\n')
					else:
						the_file.write('rec = ax.bar(y_pos + 0*bar_width,ys_list[0], bar_width,alpha = opacity,color= colour[0],label = "Minimum")\n')
						the_file.write('rec = ax.bar(y_pos + 1*bar_width,ys_list[1], bar_width,alpha = opacity,color= colour[1],label = "Average")\n')
						the_file.write('rec = ax.bar(y_pos + 2*bar_width,ys_list[2], bar_width,alpha = opacity,color= colour[2],label = "Maximum")\n')
						

					
					rects = ax.patches
					# For each bar: Place a label
					for rect in rects:
					    y_value = rect.get_height()
					    x_value = rect.get_x() + rect.get_width() / 2
					    space = 5
					    va = 'bottom'
					    if y_value < 0:
					        space *= -1
					        va = 'top'
					    label = "{:.2f}".format(y_value)
					    if(configLines[0][-9] != ''):
						    plt.annotate(
						        label,                      # Use `label` as label
						        (x_value, y_value),         # Place label at end of the bar
						        xytext=(0, space),          # Vertically shift label by `space`
						        textcoords="offset points", # Interpret `xytext` as offset in points
						        ha='center',                # Horizontally center label
						        va=va)  

					if(configLines[0][-9] != ''):
						the_file.write('rects = ax.patches\n')
						the_file.write('for num,rect in enumerate(rects):\n')
						the_file.write('\ty_value = rect.get_height()\n')
						the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
						the_file.write('\tspace = 5\n')
						the_file.write('\tva = \'bottom\'\n')
						the_file.write('\tif y_value < 0:\n\t\tspace *= -1\n\t\tva = \'top\'\n')
						the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
						the_file.write('\tplt.annotate( label,(x_value, y_value),xytext=(0, space),textcoords="offset points", ha=\'center\', va=va)\n')
					plt.xticks(y_pos + 3*bar_width/2, distinctVals3)
					the_file.write('plt.xticks(y_pos + 3*bar_width/2, distinctVals3)\n')
					ax.legend(loc = 'best',title = configLines[0][6])
					the_file.write('ax.legend(loc= \'best\',title = \'' + configLines[0][6] + '\')\n')
					

				else:												#third and fourth parameter disabled
					#average---------------------------------------------------------------------
					if configLines[0][-5] == 'Average':
						average_dict = {}
						average_dict = defaultdict(lambda:0,average_dict)
						len_dict = {}
						len_dict = defaultdict(lambda:0,len_dict)

						for q,value in enumerate(plotPointsY[0]):
							average_dict[plotPointsX[0][q]] = (average_dict[plotPointsX[0][q]] + value)
							len_dict[plotPointsX[0][q]] = len_dict[plotPointsX[0][q]] + 1

						for key in average_dict:
							average_dict[key] = average_dict[key]/len_dict[key]

						final_d = collections.OrderedDict(sorted(average_dict.items()))
					

					#max----------------------------------------------------------------------------
					if configLines[0][-5] == 'Maximum':
						max_dict = {}
						max_dict = defaultdict(lambda:float("-inf"),max_dict)
						
						for q,value in enumerate(plotPointsY[0]):
							max_dict[plotPointsX[0][q]] = max(max_dict[plotPointsX[0][q]],value)
							
						final_d = collections.OrderedDict(sorted(max_dict.items()))
					
					#min---------------------------------------------------------------------------
					if configLines[0][-5] == 'Minimum':
						min_dict = {}
						min_dict = defaultdict(lambda:float("inf"),min_dict)
						
						for q,value in enumerate(plotPointsY[0]):
							min_dict[plotPointsX[0][q]] = min(min_dict[plotPointsX[0][q]],value)
							
						final_d = collections.OrderedDict(sorted(min_dict.items()))

					#plotting------------------------------------------------------------------------
					the_file.write('distinctVals3 = ' + str(distinctVals3) + '\n')
					y_pos = np.arange(len(distinctVals3))
					ys = list(final_d.values())
					with open('objs_sd.pkl', 'w') as f: 
						pickle.dump([y_pos,ys] , f)	
					the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'y_pos, ys = pickle.load(f)\n')
					plt.bar(y_pos,ys)
					the_file.write('plt.bar(y_pos,ys)\n')
					rects = ax.patches
					# For each bar: Place a label
					for rect in rects:
					    y_value = rect.get_height()
					    x_value = rect.get_x() + rect.get_width() / 2
					    bw = rect.get_width()
					    space = 5
					    va = 'bottom'
					    if y_value < 0:
					        space *= -1
					        va = 'top'

					    label = "{:.2f}".format(y_value)
					    if(configLines[0][-9] != ''):
						    plt.annotate(
						        label,                      # Use `label` as label
						        (x_value, y_value),         # Place label at end of the bar
						        xytext=(0, space),          # Vertically shift label by `space`
						        textcoords="offset points", # Interpret `xytext` as offset in points
						        ha='center',                # Horizontally center label
						        va=va)  

					
					the_file.write('rects = ax.patches\n')
					the_file.write('for num,rect in enumerate(rects):\n')
					the_file.write('\ty_value = rect.get_height()\n')
					the_file.write('\tx_value = rect.get_x() + rect.get_width() / 2\n')
					the_file.write('\tbw = rect.get_width()\n')
					the_file.write('\tspace = 5\n')
					the_file.write('\tva = \'bottom\'\n')
					the_file.write('\tif y_value < 0:\n\t\tspace *= -1\n\t\tva = \'top\'\n')
					the_file.write('\tlabel = "{:.2f}".format(y_value)\n')
					if(configLines[0][-9] != ''):
						the_file.write('\tplt.annotate( label,(x_value, y_value),xytext=(0, space),textcoords="offset points", ha=\'center\', va=va)\n')
					
					plt.xticks(y_pos + bw/2, distinctVals3)
					the_file.write('plt.xticks(y_pos + bw/2, distinctVals3)\n')
			if(configLines[0][-7] != ''):
				ax.set_ylabel(configLines[0][-7])
				the_file.write('ax.set_ylabel(' + '\'' + configLines[0][-7] + '\')\n')
			else:
				ax.set_ylabel(configLines[0][2])
				the_file.write('ax.set_ylabel(' + '\'' + configLines[0][2] + '\')\n')
			

			if(configLines[0][-8] != ''):
				ax.set_xlabel(configLines[0][-8])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][-8] + '\')\n')
			else:
				ax.set_xlabel(configLines[0][1])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][1] + '\')\n')

			
			ax.set_title(configLines[0][7])
			the_file.write('ax.set_title(' + '\'' + configLines[0][7] + '\')\n')

		#------------------------------------------------------------------------------------------------------------------------------------------------		
		else:																	
			i = 0
			
			if(configLines[0][-7] != ''):
				ax.set_ylabel(configLines[0][-7])
				the_file.write('ax.set_ylabel(' + '\'' + configLines[0][-7] + '\')\n')
			else:
				ax.set_ylabel(configLines[0][2])
				the_file.write('ax.set_ylabel(' + '\'' + configLines[0][2] + '\')\n')
			

			if(configLines[0][-8] != ''):
				ax.set_xlabel(configLines[0][-8])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][-8] + '\')\n')
			else:
				ax.set_xlabel(configLines[0][1])
				the_file.write('ax.set_xlabel(' + '\'' + configLines[0][1] + '\')\n')

			
			ax.set_title(configLines[0][7])
			the_file.write('ax.set_title(' + '\'' + configLines[0][7] + '\')\n')

			if configLines[0][3] != '1' :											# 3d disabled
				
				while i < distinctValues1 * distinctValues2 :
					
					if cType == 'scatter':
						Line, = ax.plot(plotPointsX[i],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])

					elif cType == 'bar-scatter':
						Line, = ax.plot([float(plotPointsX[i][j]) + i * min_diff_x * 0.06 for j in range(len(plotPointsX[i]))],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])

					elif cType =='line':
						dict_x = {}
						print(plotPointsY[i])
						for num,point in enumerate(plotPointsX[i]):
							dict_x[point] = plotPointsY[i][num]
						# print(dict_x)
						final_d = collections.OrderedDict(sorted(dict_x.items()))
						plotx = list(final_d.keys())
						ploty = list(final_d.values())
						# print(plotx,ploty)
						Line = ax.plot(plotx,ploty,color=colour[int(i%distinctValues2)])
						# Line = ax.plot(plotPointsX[i] ,plotPointsY[i],color=colour[int(i%distinctValues2)])
					
					if curveFit != 'False':												# curvefit enabled
						pX=[]
						for j in plotPointsX :
							pX=pX+j
						pY =[]
						for j in plotPointsY:
							pY=pY+j
						coeff = pf (pX,pY,int(deg),rcond=None, full=False, w=None, cov=False)
						cList=[]
						for j in coeff:
							if j<0.01:
								cList.append(0)
							else:
								cList.append(round(j,2))
						k=0
						txt = ''
						while k<int(deg):
							txt =txt+'a'+str(k)+'='+str(cList.pop())+','
							k+=1
						txt=txt+'a'+str(k)+'='+str(cList.pop())
						#ax.text(0.1,0.1,txt)
						# txt_list.append(txt)
						ax.text(0.95, 0.01, txt,verticalalignment='bottom', horizontalalignment='right',transform=ax.transAxes,color='black', fontsize=10)
						
					if i < distinctValues2:
						plotLines1.append(Line)
					if distinctValues2 == 1:
						plotLines2.append(Line)
					elif i%distinctValues2 == 1 :
						plotLines2.append(Line)
					line.append(Line)
					#print (int(i/distinctValues1),int(i%distinctValues2))
					
					i = i + 1

				
				with open('objs_sd.pkl', 'w') as f: 
					pickle.dump([distinctValues1,distinctValues2,distinctVals2, plotPointsX, plotPointsY] , f)	
				the_file.write('with open(\'objs_sd.pkl\') as f:'+'\n'+'\t'+'distinctValues1,distinctValues2,distinctVals2, plotPointsX, plotPointsY = pickle.load(f)\n')
				the_file.write('i = 0\n')
				the_file.write('while i < distinctValues1 * distinctValues2 :\n')
				if cType == 'scatter':
					the_file.write('\tLine, = ax.plot(plotPointsX[i],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])\n')
				elif cType == 'bar-scatter':
					the_file.write( '\tmin_diff_x = ' + str(min_diff_x) + '\n')
					the_file.write('\tLine, = ax.plot([float(plotPointsX[i][j]) + i * min_diff_x * 0.06 for j in range(len(plotPointsX[i]))],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])\n')
				the_file.write('\ti = i + 1 \n')


			else :																																															#3d enabled
				ax.set_zlabel(configLines[0][4])
				while i < distinctValues1 * distinctValues2 :
					
					if cType == 'scatter':
						Line, = ax.plot(plotPointsX[i],plotPointsY[i],plotPointsZ[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])
					elif cType =='line':

						Line, = ax.plot(plotPointsX[i],plotPointsY[i],plotPointsZ[i],color=colour[int(i%distinctValues2)])
						
					if i < distinctValues2:
						plotLines1.append(Line)
					if distinctValues2 == 1:
						plotLines2.append(Line)
					elif i%distinctValues2 == 1 :
						plotLines2.append(Line)
					line.append(Line)
					#print (int(i/distinctValues1),int(i%distinctValues2))
					
					i = i + 1

			if bool(xDict) :
				plt.xticks([value for key, value in xDict.items()],[key for key, value in xDict.items()],rotation=70)
			if bool(yDict) :
				plt.yticks([value for key, value in yDict.items()],[key for key, value in yDict.items()],rotation=0)
			if bool(zDict) :
				ax.set_zticklabels([value for key, value in zDict.items()],[key for key, value in zDict.items()])
			
			if configLines[0][6] != '' :
				legend1 = ax.legend(plotLines1,distinctVals2,loc='center', bbox_to_anchor=(0.99, 0.9),title = configLines[0][6])
				# check whether plt.gca() works , it does work in this standalone program
				fig.gca().add_artist(legend1)
			if configLines[0][5] != '' and cType != 'line' :
				ax.legend(plotLines2,distinctVals1,loc='center', bbox_to_anchor=(0.01, 0.9),title = configLines[0][5])
			
		if(configLines[0][-11] != ''):
			ax.set_ylim(y_start_prev, y_end_prev)
			ax.set_xlim(x_start_prev, x_end_prev)
			the_file.write('ax.set_ylim(' + str(y_start_prev) + ',' +  str(y_end_prev) + ')\n')
			the_file.write('ax.set_xlim(' + str(x_start_prev) + ',' +  str(x_end_prev) + ')\n')

		if(configLines[0][-10] != ''):
			val = float(configLines[0][-10])
			ax.set_ylim(ymin=val)
			the_file.write('ax.set_ylim(ymin=' + str(val) + ')\n')

		the_file.write('plt.show()')
		the_file.flush()
		the_file.close()

		y_start_prev,y_end_prev = ax.get_ylim()
		x_start_prev, x_end_prev = ax.get_xlim()

		with open('objs.pkl', 'w') as f: 
			pickle.dump([y_start_prev, y_end_prev, x_start_prev,x_end_prev], f)

		canvas.draw()
		fig.canvas.mpl_connect('motion_notify_event', hover)

	f.close()
