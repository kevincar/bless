Usage
=====

Create a server, add a GATT tree, then start advertising:

.. code-block:: python

   import asyncio
   from bless import (
       BlessServer,
       GATTCharacteristicProperties,
       GATTAttributePermissions,
   )

   async def run(loop):
       gatt = {
           "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
               "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                   "Properties": (
                       GATTCharacteristicProperties.read
                       | GATTCharacteristicProperties.write
                   ),
                   "Permissions": (
                       GATTAttributePermissions.readable
                       | GATTAttributePermissions.writeable
                   ),
                   "Value": None,
               }
           }
       }

       server = BlessServer(name="Bless Example", loop=loop)
       await server.add_gatt(gatt)
       await server.start()

   loop = asyncio.get_event_loop()
   loop.run_until_complete(run(loop))
