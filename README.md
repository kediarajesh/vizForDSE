# vizForDSE
Visualization tool tailored for Design Space Exploration

Owner: Rajesh Kedia (CSE, IIT Delhi).
Contributors: Manish Yadav, IIT Delhi
              Sanket Sanjay Dhakate, IIT Delhi


Description: 

This is a python based visualization tool which can do generic plotting of data present in csv files. We hope this to be useful when you don't want to write a script to plot the data and want to observe the behavior of the data first.

There are various help documents prepared to help the users understand the interface of the tool.
Starter guide: https://docs.google.com/document/d/e/2PACX-1vRG7XnZ8qOi3RlXKGATuPzoFae09JCIP-yQE4Ws-3BckeBBSeeMum0XApC3uafGaJFGBBPPBBtVeKoW/pub

Videos:
1. http://www.cse.iitd.ac.in/~kedia/visualization_tool/videos/v1.mp4
2. http://www.cse.iitd.ac.in/~kedia/visualization_tool/videos/v3.mp4
3. http://www.cse.iitd.ac.in/~kedia/visualization_tool/videos/v5.mp4


Using the package:

1. Download the package
2. Install the dependency packages (matplotlib and pyqt4)
3. run the command "python test.py". The GUI should open up.


Dependency Package installation:
1. matplotlib: sudo apt-get install python-matplotlib
2. pyqt4: sudo apt-get install python-qt4


Platform: 
1. The tool and the flow has been tested on Ubuntu-14.04 and Ubuntu-16.04

Operating vizForDSE with external tool
1. Download the eclipse package from www.cse.iitd.ac.in/~kedia/compress.tar.gz
2. Extract the tarball and put it in a folder named eclipse in the same directory as this repository
3. Edit eclipse/bin/x86_64_linux/eclipse according to your directory structure
4. Open the example_fields_for_tool.csv file within the vizForDSE tool
5. Open the generate constraints file using the button at the bottom
6. Put in the necessary constraints and click on generate. Wait for a little time as the tool takes time to run.
7. Open generated.csv created in the vizForDSE folder to see the csv for plotting. 


Changelog:

1. The scroll bar allows the user to access all parts of the window in case it is larger than the viewable area.

2. Swap Axis button : To swap the parameters on the X and Y axes.

3. Bar Graph:
To plot a bar graph between the parameters chosen on the Y and X axes. The bars of each value of the fourth parameter chosen are separated slightly so that no two colours overlap (and hence no value gets hidden).
The number of distinct values of the parameter on the X-axis should not be greater than 8 to be able to plot the graph.

4. Histogram:
A plot to show frequency distribution of the parameter chosen on the X axis for different values of the fourth parameter.

5. Pareto plots can be obtained for each value of the third and fourth parameter.

6. The csv file used for plotting can be generated using an external tool.

Open 'example_fields_for_tool.csv' and then press the 'Generate constraints file' button. A new window would pop up comprising of:
1. a combo box to select a field,
2. 3 textboxes to take inputs (constraints) - lower limit , upper limit , discrete values,
3. buttons to apply/generate/cancel

The 'example_fields_for_tool.csv' file lists the fields on which we can set constraints and is hence opened first so that the combo box contains only the allowed fields.

The user can either set the lower limit or the upper limit or both, or can specify discrete values (separated by spaces). 

Press the 'apply' button to add a constraint. When all desired constraints have been set, press the 'generate' button to run the tool. This generates two files - 'file.txt' and 'generated.csv'.
Open 'generated.csv' and press the update button to get the plot.

7. Undo button:
If the plot obtained after setting some new constraints is unsatisfactory, the previous plot can be retrieved by pressing the undo button.

