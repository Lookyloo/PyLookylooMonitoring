Welcome to PyLookylooMonitorings documentation!
=============================================

This is the client API for `Lookyloo Monitoring <https://github.com/Lookyloo/monitoring>`_

Installation
------------

The package is available on PyPi, so you can install it with::

  pip install pylookyloomonitoring


Usage
-----

You can use `lookyloo_monitor` as a python script::

	$ lookyloo_monitor -h
	usage: lookyloo_monitor [-h] --url URL (--monitor_url MONITOR_URL | --compare COMPARE)

	Talk to a Lookyloo Monitoring instance.

	options:
	  -h, --help            show this help message and exit
	  --url URL             URL of the instance.
	  --monitor_url MONITOR_URL
							URL to monitor. It will be monitered hourly.
	  --compare COMPARE     UUID of the monitoring.


Or as a library:

.. toctree::
   :glob:

   api_reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
