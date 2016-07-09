.. _installation_tutorial:

Tutorial: Installation Setup
##################

.. _PGDB website: http://montrealcorpustools.github.io/PolyglotDB/

.. _GitHub repository: https://https://github.com/mmcauliffe/speechcorpustools

This document assumes the following:

 * Neo4j is installed
 * Speech Corpus Tools is installed
 * You have a database for the Librispeech Test Corpus on your local machine.

Installing Neo4j
*********************

SCT currently requires that Neo4j version 3.0 be installed locally and running.  To install Neo4j, please use the following links.

Mac version: `Mac <http://info.neotechnology.com/download-thanks.html?edition=community&release=2.3.3&flavour=dmg>`_

Windows version: `Windows <http://info.neotechnology.com/download-thanks.html?edition=community&release=2.3.3&flavour=winstall64>`_

Once downloaded, just run the installer and it'll install the database software that SCT uses locally.

To ease initial set up, it's helpful to turn off authentication for Neo4j.  If you run the server software, it'll pop up a window with a button that says "Options..." down in the lower left.  Click on that and hit the button "Edit..." for "Server configuration".  That will pop open a text editor, and you just have to change the line near the top that says:

``dbms.security.auth_enabled=true``

to:

``dbms.security.auth_enabled=false``

and save the file.  Neo4j should be ready to use.

If security is enabled, you'll first have to click on the link in the Neo4j server (when it's running) that says ``localhost:7474`` which will take you to a browser page where you can set a password for the ``neo4j`` user.  If you leave it enabled, remember your password for when you connect via Speech Corpus Tools.

:ref:`Next <installation2>`          :ref:`Previous <tutintroduction>`


