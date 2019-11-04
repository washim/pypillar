Welcome to PyPillar's documentation!
====================================
This is an open source REST tool which allow to run any python script as a distributed task to monitor its all events during execution.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Why PyPillar
====================================
This is an open source REST tool which allow to run any python script as a distributed task to monitor its all events during execution.

#. Priceless and its free
#. Distribute your large python script in several task
#. Monitor task logs
#. Investigate python task exception.
#. Investigate requests history in future at any point of time.
#. Create multiple projects.
#. Live code editor which allow to change code associated with task.
#. Quickly and easily run REST to test the REST api.

Installation
=====================================
.. code-block:: shell

    pip install pypillar

Start Server
=====================================
To start PyPillar server run below command in terminal

.. code-block:: shell
   pypillar run

It will expose the server in http://localhost:5000

PyPillar Runtime Objects
=====================================
To get PyPillar runtime objects inside your task python script include below code snippets just beginning of your python script.

.. code-block:: python

   import json
   import argparse

   parser = argparse.ArgumentParser(description='Pypillar argument processing')
   parser.add_argument('--PYPILLAR', help='Variable which contain all pypillar objects for future references.')
   args = parser.parse_args()

   pypillar = json.loads(args.PYPILLAR) # This variable contaion all the information
   print(json.dumps(pypillar)) # Dump the variable and debug in PyPillar Task logger.