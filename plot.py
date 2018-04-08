import matplotlib.pyplot as plt
from numpy import polyfit as pf
import math
import ply.lex as lex
import sys
import ply.yacc as yacc
import numpy as np
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage, AnnotationBbox)
from matplotlib.patches import Rectangle


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
	# configLines[0][5] --> name of third para
	# configLines[0][6] --> name of fourth para
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
	# configLines[0][-3] --> type of graph (line/scatter/histogram/bar)
	# configLines[0][-2] --> empty for curve fit disabled else degree of polynomial

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	fig.clf() 																																						# clear the previous graph
	
	if configLines[0][3] == '1' :																													# check if 3d
		ax = fig.add_subplot(111,projection = '3d')																				# add 3d plot
	else :
		ax = fig.add_subplot(111)																												# add 2d plot
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
			fieldList.append(f.read(fieldLengthList[i]))														# read the field/column names into a list
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

	cType =  configLines[0][-3] 					# type of graph - line or scatter

	if configLines[0][-2] !='':					# set the degree of polynomial for curve fitting
		curveFit = 'True'
		deg = configLines[0][-2]
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

	if configLines[0][5] != '' and cType == 'scatter' : 																	# check if 3rd para enabled
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
 
	if configLines[0][6] != '' :																												# check if 4th para enabled
		enaDiff2 = fieldList.index(configLines[0][6])																	# enaDiff2 - variable to store the field name of 4th para
		distinctVals2 = []																															# list of distinct values in the 4th para field
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
	
	# checking for number of distinct values of x-axis for making a bar-graph (should be smaller than 8 for this to be possible)
	if cType == "bar-graph":
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
	else :
		distinctValues3 = float("inf")
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
	else:          # no error plot graph
		if cType == 'histogram':
			ax.set_xlabel(configLines[0][1])
			ax.set_ylabel("frequency")
			ax.set_title(configLines[0][7])

			# n, bins, patches = plt.hist(plotPointsX, 50, normed=1, facecolor='g', alpha=0.75)
			# plt.hist([x, y], color=['g','r'], alpha=0.75, bins=50)

			handles = [Rectangle((0,0),1,1,color=colour[int(i%distinctValues2)] ,ec="k") for i in range(distinctValues2)]
			ax.legend(handles, distinctVals2,loc='center', bbox_to_anchor=(0.99, 0.9),title = configLines[0][6])

			ax.hist([plotPointsX[i] for i in range(distinctValues2)], color=[colour[int(i%distinctValues2)] for i in range(distinctValues2)], alpha=0.8, bins=50)
		else:																	
			i = 0
			ax.set_xlabel(configLines[0][1])
			ax.set_ylabel(configLines[0][2])
			ax.set_title(configLines[0][7])
			if configLines[0][3] != '1' :											# 3d disabled
				while i < distinctValues1 * distinctValues2 :
					
					if cType == 'scatter':
						Line, = ax.plot(plotPointsX[i],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])
					elif cType == 'bar-graph':
						Line, = ax.plot([float(plotPointsX[i][j]) + i * min_diff_x * 0.06 for j in range(len(plotPointsX[i]))],plotPointsY[i],style[int(i/distinctValues2)],color=colour[int(i%distinctValues2)])
					elif cType =='line':
						Line, = ax.plot(plotPointsX[i],plotPointsY[i],color=colour[int(i%distinctValues2)])
					
					
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
			
		canvas.draw()
		fig.canvas.mpl_connect('motion_notify_event', hover)

	f.close()
