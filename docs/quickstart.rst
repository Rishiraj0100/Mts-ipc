Quickstart
==========

Before doing anything, it is highly recommended to read discord.py's quickstart.
You can find it by clicking :ref:`this here <discord:quickstart>`.

Firstly, we will begin from installing mts_ipc:

Installing
--------------------

.. code-block::

    pip install -U git+https://github.com/Rishiraj0100/mts-ipc@master

Then we will create a server:

Creating a server
----------------------

.. code-block:: python3

    import mts_ipc as ipc
    from discord.ext import commands

    bot = commands.Bot(command_prefix="$")
    bot.ipc = ipc.Server(bot, secret_key="my_key")

    @bot.ipc.route(name="test1")
    async def test1(data):
        return data

    # or

    @ipc.server.route(name="test2")
    async def test2(data):
        return "tested " + data.endpoint

    bot.ipc.start(host="0.0.0.0",port=8080,path="/ipc")
    bot.run(token)

Then we will connect to our hosted server

Connecting to an server
-------------------------

.. code-block:: python3

    import mts_ipc as ipc
    import quart

    app = quart.Quart(__name__)
    ipc = ipc.Server(host="test.mts_ipc.rrrdev.cf", path="/ipc", secret_key="my_key")
    # above one hosted on a VPS, here host is domain of web VPS

    @app.route("/")
    async def index():
        return "data is" + str(await ipc.request("test1"))

    app.run(host="0.0.0.0",port=9090)
    
    
