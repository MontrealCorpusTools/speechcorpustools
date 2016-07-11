.. _installation_tutorial:

Tutorial: Installation Setup
############################

.. _PGDB website: http://montrealcorpustools.github.io/PolyglotDB/

.. _GitHub repository: https://https://github.com/MontrealCorpusTools/speechcorpustools

Installing Neo4j
****************

SCT currently requires that Neo4j version 3.0 be installed locally and running.
To install Neo4j, please use the following links.

Mac version: `Mac <http://info.neotechnology.com/download-thanks.html?edition=community&release=3.0.3&flavour=dmg>`_

Windows version: `Windows <http://info.neotechnology.com/download-thanks.html?edition=community&release=3.0.3&flavour=winstall64>`_

Once downloaded, just run the installer and it'll install the database software that SCT uses locally.

SCT currently requires the following configuration for Neo4j. When you open
up the Neo4j executable, click on options, and then the "Edit..." button
for ``Database configuration`` and replace the text with the following and save it:

::

    #***************************************************************
    # Server configuration
    #***************************************************************

    # This setting constrains all `LOAD CSV` import files to be under the `import` directory. Remove or uncomment it to
    # allow files to be loaded from anywhere in filesystem; this introduces possible security problems. See the `LOAD CSV`
    # section of the manual for details.
    #dbms.directories.import=import

    # Require (or disable the requirement of) auth to access Neo4j
    dbms.security.auth_enabled=false

    #
    # Bolt connector
    #
    dbms.connector.bolt.type=BOLT
    dbms.connector.bolt.enabled=true
    dbms.connector.bolt.tls_level=OPTIONAL
    # To have Bolt accept non-local connections, uncomment this line:
    # dbms.connector.bolt.address=0.0.0.0:7687

    #
    # HTTP Connector
    #
    dbms.connector.http.type=HTTP
    dbms.connector.http.enabled=true
    #dbms.connector.http.encryption=NONE
    # To have HTTP accept non-local connections, uncomment this line:
    #dbms.connector.http.address=0.0.0.0:7474

    #
    # HTTPS Connector
    #
    # To enable HTTPS, uncomment these lines:
    #dbms.connector.https.type=HTTP
    #dbms.connector.https.enabled=true
    #dbms.connector.https.encryption=TLS
    #dbms.connector.https.address=localhost:7476

    # Certificates directory
    # dbms.directories.certificates=certificates

    #*****************************************************************
    # Administration client configuration
    #*****************************************************************


    # Comma separated list of JAX-RS packages containing JAX-RS resources, one
    # package name for each mountpoint. The listed package names will be loaded
    # under the mountpoints specified. Uncomment this line to mount the
    # org.neo4j.examples.server.unmanaged.HelloWorldResource.java from
    # neo4j-examples under /examples/unmanaged, resulting in a final URL of
    # http://localhost:${default.http.port}/examples/unmanaged/helloworld/{nodeId}
    #dbms.unmanaged_extension_classes=org.neo4j.examples.server.unmanaged=/examples/unmanaged

    #*****************************************************************
    # HTTP logging configuration
    #*****************************************************************

    # HTTP logging is disabled. HTTP logging can be enabled by setting this
    # property to 'true'.
    dbms.logs.http.enabled=false

    # Logging policy file that governs how HTTP log output is presented and
    # archived. Note: changing the rollover and retention policy is sensible, but
    # changing the output format is less so, since it is configured to use the
    # ubiquitous common log format
    #org.neo4j.server.http.log.config=neo4j-http-logging.xml

    # Enable this to be able to upgrade a store from an older version.
    #dbms.allow_format_migration=true

    # The amount of memory to use for mapping the store files, in bytes (or
    # kilobytes with the 'k' suffix, megabytes with 'm' and gigabytes with 'g').
    # If Neo4j is running on a dedicated server, then it is generally recommended
    # to leave about 2-4 gigabytes for the operating system, give the JVM enough
    # heap to hold all your transaction state and query context, and then leave the
    # rest for the page cache.
    # The default page cache memory assumes the machine is dedicated to running
    # Neo4j, and is heuristically set to 50% of RAM minus the max Java heap size.
    #dbms.memory.pagecache.size=10g

    #*****************************************************************
    # Miscellaneous configuration
    #*****************************************************************

    # Enable this to specify a parser other than the default one.
    #cypher.default_language_version=3.0

    # Determines if Cypher will allow using file URLs when loading data using
    # `LOAD CSV`. Setting this value to `false` will cause Neo4j to fail `LOAD CSV`
    # clauses that load data from the file system.
    dbms.security.allow_csv_import_from_file_urls=true

    # Retention policy for transaction logs needed to perform recovery and backups.
    dbms.tx_log.rotation.retention_policy=false

    # Enable a remote shell server which Neo4j Shell clients can log in to.
    #dbms.shell.enabled=true
    # The network interface IP the shell will listen on (use 0.0.0.0 for all interfaces).
    #dbms.shell.host=127.0.0.1
    # The port the shell will listen on, default is 1337.
    #dbms.shell.port=1337

    # Only allow read operations from this Neo4j instance. This mode still requires
    # write access to the directory for lock purposes.
    #dbms.read_only=false

    # Comma separated list of JAX-RS packages containing JAX-RS resources, one
    # package name for each mountpoint. The listed package names will be loaded
    # under the mountpoints specified. Uncomment this line to mount the
    # org.neo4j.examples.server.unmanaged.HelloWorldResource.java from
    # neo4j-server-examples under /examples/unmanaged, resulting in a final URL of
    # http://localhost:7474/examples/unmanaged/helloworld/{nodeId}
    #dbms.unmanaged_extension_classes=org.neo4j.examples.server.unmanaged=/examples/unmanaged

Installing SCT
**************

Once Neo4j is set up as above, the latest version of SCT can be downloaded from
the `SCT releases`_ page.

Windows
=======

1. Download the zip archive for Windows
2. Extract the folder
3. Double click on the executable to run SCT.

.. note:
   One possible issue that might arise with Windows computers is related
   to graphics drivers. On the Windows version, a console output will pop
   up in addition to the main SCT window. If you notice a string of
   output containing something like “RuntimeError: OpenGL got errors”
   then your graphics driver is probably a couple of years old. In which
   case, please follow the instructions on
   http://www.wikihow.com/Update-Your-Video-Card-Drivers-on-Windows-7 to update
   them. Macs tend to be better about keeping
   the graphics drivers up to date, and shouldn’t have this issue. SCT
   should run on Windows 7+ and Mac OS X 10.11+

Mac
===

1. Download the DMG
2. Drag the SCT application to your Applications folder.
3. Double click on the SCT application to run.

:ref:`Next <librispeech>`          :ref:`Previous <tutintroduction>`


