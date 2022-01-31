pyamplipi
====

pyAmpliPi is a Python library that allows you to
control an `AmpliPi` programmatically via the restful api provided by the device.

The `get_status()` function returns a _Status_ object which contains the current running configuration for the 
controller including the firmware and configuration files used. This can be used to verify connectivity to a 
controller and `keep-alive/healthchecks` regularly, however should be limited to once every 60 seconds. 

As mentioned above, the `Status` object contains the overall state of all subobjects and should not be used for 
calls that require updates more often. In these cases, the specific endpoints should be used:
- get_inputs
- get_sources
- get_groups
- get_zones

`Set` Methods are provided to update inputs, sources, zones, and groups.

`announce` provides access to PA capabilities by providing a URL as the `media` value

Visit the AmpliPi website for additional information.

Installation
------------

pyamplipi requires Python 3.5 or newer.

Use pip:

``pip install pyamplipi``


pyamplipi depends on a number of Python packages. If you use pip to install pyamplipi,
the dependencies will be installed automatically for you. If not, you can inspect
the requirements in the `requirements.txt` file.

MIT license: http://www.opensource.org/licenses/mit-license.php