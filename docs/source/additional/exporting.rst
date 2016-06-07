.. _exporting:

*****************
Exporting Queries
*****************

While getting in-app results can be a quick way to visualize data, most often the user will want to further manipulate the data (i.e. in R, MatLab, etc.) To this end, there is the "Export query results" feature. It allows the user to specify the information that is exported by adding columns to the final output file. This is somewhat similar to `building queries <http://sct.readthedocs.io/en/latest/additional/buildingqueries.html>`_ , but not quite the same. Insttead of filters, pressing the "+" button will add a column to the exported file. 

For example, if the user wanted the timing information (begin/end) and lables for the object found and the object before it, the export profile would look like:
	.. image:: exprofile.png
		:width: 656px
		:align: center
		:height: 240px
		:alt: Image cannot be displayed in your browser

While many of the column options are the same as ones available for `building queries <http://sct.readthedocs.io/en/latest/additional/buildingqueries.html>`_ there are some differences :
	
* "alignment" and "subset" are not valid column options
* column options do not change depending on the linguistic object that was chosen earlier
	* instead, you can select "word" and then "label" (or some other option) or "phone" + options, etc.
* you can edit the column name by typing what you would like to call it in the "Output name:" box. These names are by default very descriptive, but perhaps too long for the user's purposes.

Once the profile is ready, pressing "run" will open the following window:
	
	.. image:: saveas.png
		:width: 427px
		:align: center
		:height: 190px
		:alt: Image cannot be displayed in your browser

Here the user can pick a name and location for the final file. After pressing save, the query will run and the results will be written in the desired columns to the file. 