PyGalil
=======


Python library for talking to Galil (http://www.galilmc.com/) motion controllers.

Currently only tested with Galil DMC-21xx controllers (those are the only ones I have).

Heavily tested to be reliable over extremely long-duration connections (weeks!).

Supports multiple mechanisms for remote monitoring of a connected galil as well.

Entirely python-native, only depends on the built-in `socket`, `threading` and `struct` libraries.

License: BSD/MIT
