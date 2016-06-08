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

Perhaps a researcher would be interested in knowing whether word-initial segments in some word categories are longer than in others. To get related information (phone timing information and label, word category) into a .csv file, the export profile would be something like:
	.. image:: exprofile2.png
		:width: 683px
		:align: center
		:height: 412px
		:alt: Image cannot be displayed in your browser
Here, "phone" has been selected as the linguistic object to find (since that is what we're interested in) so any property without a preceding dropdown menu is a property of the target phone -- in this case, alignment would have been used to specify "word-initial phones".  

Another option is to use the "simple export" window. 
	.. image:: simpleexport.png
		:width: 720px
		:align: center
		:height: 650px
		:alt: Image cannot be displayed in your browser
Here, there are several commong options that can be selected by checking them. Once checked, they will appear as columns in the query profile:
	.. image:: simpleexportfull.png
		:width: 720px
		:align: center
		:height: 650px
		:alt: Image cannot be displayed in your browser


While many of the column options are the same as ones available for `building queries <http://sct.readthedocs.io/en/latest/additional/buildingqueries.html>`_ there are some differences :
	
* "alignment" and "subset" are not valid column options
* column options do not change depending on the linguistic object that was chosen earlier
	* instead, you can select "word" and then "label" (or some other option) or "phone" + options, etc.
* you can edit the column name by typing what you would like to call it in the "Output name:" box. These names are by default very descriptive, but perhaps too long for the user's purposes.

Since the options are similar but not all identical, here is a full list of all the options available:

* **following** Specifies the object after the current object. There will be another dropdown menu to select a property of this following object.
* **previous** Specifies the object before the current object. There will be another dropdown menu to select a property of this preceding object.
* **duration** Adds how much time the object occupies as a column
* **begin** Adds the start of the object in time (seconds) as a column
* **end** Adds the end of the object in time (seconds) as a column
* **label** Adds the orthographic contents of an object as a column
* **word** Specifies a word (another dropdown menu will become available to specify another property to add as a column). The following are only available if "word" is selected either as the original object to search for, or as the first property in a column.
	* **category** Adds the word category as a column
	* **transcription** Adds the underlying phonetic transcription of the word in the corpus as a column
	* **surface_transcription** Adds the surface transcription of the word in the corpus as a column
	* **utterance** Specifies the utterance that the word came from (another dropdown menu will become available to specify another property to add as a column)
* **phone** Specifies a phone (another dropdown menu will become available to specify another property to add as a column)
* **speaker** Specifies the speaker (another dropdown menu will become available to specify another property to add as a column)
* **discourse** Specifies the discourse, or file (another dropdown menu will become available to specify another property to add as a column)



Once the profile is ready, pressing "run" will open the following window:
	
	.. image:: saveas.png
		:width: 427px
		:align: center
		:height: 190px
		:alt: Image cannot be displayed in your browser

Here the user can pick a name and location for the final file. After pressing save, the query will run and the results will be written in the desired columns to the file. 

