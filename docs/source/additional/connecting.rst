.. _connecting:

**********
Connection
**********


To see an example connection, go to :any:`Connection example <exconnecting>`

In the connection tab, there are various features.

    .. image:: connection.png
        :width: 602px
        :height: 713px
        :alt: Image cannot be displayed in your browser
        :align: center

These are detailed below

IP address (or localhost)
#########################
This is the address of the Neo4j server. In most cases, it will be 'localhost'

Port
####
This is the port through which a connection to the Neo4j server is made. By default, it is 7474. It must always match the port shown in the Neo4j window.

    .. image:: neo4j.png
        :width: 536px
        :height: 28px
        :alt: Image cannot be displayed in your browser
        :align: center

Username and Password
#####################
These are by default not required, but available should you need authentication for your Neo4j server

Connect
#######
This button will actually connect the user to the specified server.

Find local audio files
######################
Pressing this allows the user to browse his/her file system for directories containing audiofiles that correspond to files in a corpus.

Corpora
#######
The user select a corpus (for runnning queries, viewing discourses, enrichment, etc.) by clicking that corpus in the "Available corpora" menu. The selected corpus will be highlighted in blue or grey.

Import local corpus
###################
This is strictly for constructing a new relational database in Neo4j that does not already exist. Any corpus that has already been imported can be accessed by pressing "Connect" and selecting it instead. Re-importing the same corpus will overwrite the previous corpus of the same name, as well as remove any enrichment the user has done on the corpus.

When importing a new corpus, the user selects the directory of the overall corpus, not specific files or subdirectories.
