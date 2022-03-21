#-------------------------------------------------------------------------------
# Author        https://github.com/WouterJD
#               wouter.dubbeldam@xs4all.nl
#-------------------------------------------------------------------------------
# Version info
#-------------------------------------------------------------------------------
__version__ = "2022-03-15"
# 2022-03-15    This implementation works, Windows10 and Raspberry
#               One open issue: How to set the Generic Access Profile
#                   characteristics, such as DeviceName and Appearance.
#               See: https://github.com/kevincar/bless/issues/75
# 2022-03-08    Class to create a bless server
# 2020-12-18    First version, obtained from: " hbldh\bless"
#               inspired by examples\gattserver.py
#               Example for a BLE 4.0 Server using a GATT dictionary of
#               characteristics
#-------------------------------------------------------------------------------
import asyncio
import atexit
import logging
from   socket               import timeout
import time
import threading

from typing import Any, Dict

from bless import (
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
        )

#-------------------------------------------------------------------------------
# c l s B l e S e r v e r
#-------------------------------------------------------------------------------
# Class to create a BLE server, using bless
#
# User methods:
#   __init__()      When the instance is created, the data structure is made
#                   but no functions yet executed. Open()/Close() to be used.
#   Open()          Creates the FTMS server
#   Close()         Closes the FTMS server
#
#   ClientDisconnected()
#                   Is called when a client disconnects, so that the child-class
#                   can act accordingly
#
#   ReadRequest()   Can be overwritten by child-class if so desired
#   WriteRequest()  Should be implemented by child-class to make the server work
#
# User attributes:
#   Message         User message to indicate status of the BLE server
#   ClientConnected Boolean, indicating that a client is connected
#   BlessServer     to be used in child-class to access characteristics
#
# Yes indeed, this class is not of much use for an application yet, the child
# must implement the real functionality.
#-------------------------------------------------------------------------------
class clsBleServer:
    #---------------------------------------------------------------------------
    # External attributes
    #---------------------------------------------------------------------------
    Message             = ''            # Shows status of interface

    #---------------------------------------------------------------------------
    # Internal processing data
    #---------------------------------------------------------------------------
    OK                  = False         # FTMS is operational
    BlessServer         = None          # The BlessServer instance
    loop                = None          # Loop instance to support BlessServer
    ClientConnected     = False         # copy of BlessServer.is_connected()
    ClientWasConnected  = False

    myServiceName       = "NoNameService"   # Provided on creation
    myGattDefinition    = "<not provided>"

    # --------------------------------------------------------------------------
    # _ _ i n i t _ _
    # --------------------------------------------------------------------------
    # Input     myServiceName, myGattDefinition
    #
    # Function  Create the instance,
    #           note thatFTMS starting is done through Open().
    #
    # Output    .Message, .myServiceName, .myGattDefinition
    # --------------------------------------------------------------------------
    def __init__(self, myServiceName, myGattDefinition):
        self.Message            = ", Bluetooth interface available (bless)"
        self.myServiceName      = myServiceName
        self.myGattDefinition   = myGattDefinition
        #-----------------------------------------------------------------------
        # register self.Close() to make sure the BLE server is stopped
        #   ON program termination
        # Note that __del__ is called too late to be able to close.
        #-----------------------------------------------------------------------
        atexit.register(self.Close)

    # --------------------------------------------------------------------------
    # O p e n
    # --------------------------------------------------------------------------
    # Input     None
    #
    # Function  In a separate thread;
    #               Create a loop and then activate FortiusAntServer
    #
    # Output    OK = True
    #
    # Returns   self.OK
    # --------------------------------------------------------------------------
    def Open(self):
        #-----------------------------------------------------------------------
        # Logging
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer.Open()")

        #-----------------------------------------------------------------------
        # Create a thread and run the server in that thread
        #-----------------------------------------------------------------------
        thread = threading.Thread(target=self._OpenThread)
        thread.start()

        #-----------------------------------------------------------------------
        # Allow thread to start
        #-----------------------------------------------------------------------
        time.sleep(1)

        #-----------------------------------------------------------------------
        # After a second, the thread will be initiated and self.OK = True
        # (For the time being, at least)
        #-----------------------------------------------------------------------
        return self.OK

    def _OpenThread(self):
        self.OK      = True
        self.Message = ", Bluetooth interface open" # Assume it will work OK

        #loop = asyncio.get_event_loop()            # Crashes: "There is no current event loop in thread"
        self.loop    = asyncio.new_event_loop()     # Because we're in a thread
        self.loop.run_until_complete(self._Server())
        self.loop    = None

    # --------------------------------------------------------------------------
    # _ S e r v e r
    # --------------------------------------------------------------------------
    # Input     .myServiceName
    #           .myGattDefinition
    #           .OK
    #           .loop
    #
    # Function  A BLE-server is created with the required services and characteristics
    #           The server will remain active until Close() is called
    #
    # Output    BLE Server/Service/Characteristics
    # --------------------------------------------------------------------------
    async def _Server(self):
        #-----------------------------------------------------------------------
        # Create the server
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer._Server(%s)" % self.myServiceName)

        if self.OK:
            self.BlessServer = BlessServer(name=self.myServiceName, loop=self.loop)
            
            self.BlessServer.read_request_func  = self.ReadRequest
            self.BlessServer.write_request_func = self.WriteRequest

        #-----------------------------------------------------------------------
        # Add the gatt-services and start
        # Note:
        # Windows 10: BLE crashes on add_gatt() if there is no BLE-5 dongle
        #             BLE crashes on start()    if interface is not compatible
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer._Server(): self.BlessServer.add_gatt()")
        if self.OK:
            try:
                await self.BlessServer.add_gatt(self.myGattDefinition)
            except Exception as e:
                self.OK = False
                self.logfileConsole("clsBleServer._Server(); add_gatt() exception %s" % e)

        self.logfileWrite("clsBleServer._Server(): self.BlessServer.start()")
        if self.OK:
            try:
                await self.BlessServer.start()
            except Exception as e:
                self.OK = False
                self.logfileConsole("clsBleServer._Server(); start() exception %s" % e)

        if not self.OK:
            self.Message = ", Bluetooth interface n/a; BLE-5 required!"
            self.logfileConsole(self.Message)

        #-----------------------------------------------------------------------
        # Server is now active
        # read/write through ReadRequest() and WriteRequest() functions
        # Server will stop when OK = False.
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer._Server(): 1 second loop untill Close() called")
        WeWereOK = self.OK
        while self.OK:
            await asyncio.sleep(1)
            #-------------------------------------------------------------------
            # Check whether there are clients connected
            # If a client disconnects, notify the subclass, perhaps action must
            #       be taken.
            # There is no reason to stop, simply keep active untill the next
            #       client connects.
            #-------------------------------------------------------------------
            self.ClientConnected = await self.BlessServer.is_connected()
                               # = len(self.BlessServer._subscribed_clients) > 0

            if not self.ClientConnected and self.ClientWasConnected:
                self.ClientDisconnected()
                self.logfileWrite(
                    "clsBleServer._Server: A client was active and is disconnected.")

            self.ClientWasConnected = self.ClientConnected

        #-----------------------------------------------------------------------
        # Cleanup
        # self.OK is always False, since set by Close()!!
        #-----------------------------------------------------------------------
        if WeWereOK:
            self.logfileWrite("clsBleServer._Server(): self.BlessServer.stop()")
            await self.BlessServer.stop()

        #-----------------------------------------------------------------------
        # Logging
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer._Server() ended")

    # --------------------------------------------------------------------------
    # C l i e n t D i s c o n n e c t e d
    # --------------------------------------------------------------------------
    # Input     None
    #
    # Function  A disconnect is detected, one may use this to react accordingly
    #
    # Output    None
    # --------------------------------------------------------------------------
    def ClientDisconnected(self):
        pass

    # --------------------------------------------------------------------------
    # C l o s e
    # --------------------------------------------------------------------------
    # Input     None
    #
    # Function  Indicate that FortiusAntServer() must stop
    #
    # Output    OK = False
    # --------------------------------------------------------------------------
    def Close(self):
        #-----------------------------------------------------------------------
        # Logging
        #-----------------------------------------------------------------------
        self.logfileWrite("clsBleServer.Close()")

        #-----------------------------------------------------------------------
        # Signal FortiusAntServer to stop
        #-----------------------------------------------------------------------
        self.Message = ", Bluetooth interface closed"
        self.OK      = False

        #-----------------------------------------------------------------------
        # Allow thread to close
        #-----------------------------------------------------------------------
        time.sleep(2)

    #---------------------------------------------------------------------------
    # L o g f i l e W r i t e / C o n s o l e
    #---------------------------------------------------------------------------
    # Input:    message to be written to logfile
    #
    # Function  Use python logging functions
    #
    # Output:   none
    #---------------------------------------------------------------------------
    def logfileWrite(self, message):
        logging.info(message)

    def logfileConsole(self, message):
        logging.error(message)

    #---------------------------------------------------------------------------
    # R e a d R e q u e s t
    #---------------------------------------------------------------------------
    # Input:    characteristic for which the value is requested
    #
    # Function  Return the requested value, without further processing
    #
    # Output:   characteristic.value
    #---------------------------------------------------------------------------
    def ReadRequest(self,
            characteristic: BlessGATTCharacteristic,
            **kwargs
            ) -> bytearray:

        uuid  = str(characteristic._uuid)

        #---------------------------------------------------------------------------
        # Logging
        #---------------------------------------------------------------------------
        self.logfileWrite('clsBleServer.ReadRequest(): characteristic uuid="%s", value = %s' %
                            (uuid, characteristic._value))

        return characteristic.value

    #-------------------------------------------------------------------------------
    # W r i t e R e q u e s t
    #-------------------------------------------------------------------------------
    # Input:    characteristic for which the value must be updated
    #
    # Function  Check what characteristic must be changed and act accordingly
    #
    # Output:   To be defined by child class.
    #-------------------------------------------------------------------------------
    def WriteRequest(self,
            characteristic: BlessGATTCharacteristic,
            value: Any,
            **kwargs
            ):

        uuid  = str(characteristic._uuid)
        
        #---------------------------------------------------------------------------
        # Logging
        #---------------------------------------------------------------------------
        self.logfileWrite('clsBleServer.WriteRequest(): characteristic "%s", actual value = %s, provided value = %s' %
                (uuid, characteristic.value, value))
        self.logfileConsole('clsBleServer.WriteRequest() error: Not implemented!')

# ==============================================================================
# Main program
# ==============================================================================
if __name__ == "__main__":
    print("bleBlessClient.py cannot be executed on it's own.")