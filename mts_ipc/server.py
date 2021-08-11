import logging
import discord
import asyncio

import aiohttp.web

from typing import Union, Optional, Tuple
from aiohttp import web
from discord.ext import commands
from mts_ipc.errors import *

log = logging.getLogger(__name__)


def route(name: str = None):
	"""Used to register a coroutine as an endpoint when you don't have
    access to an instance of :class:`.Server`

    Parameters
    ----------
    name: str
        The endpoint name. If not provided the method name will be
        used.
	
   
    This can be used in cogs. For ex -
    
    .. code:: python3
    
        import mts_ipc as ipc
        from discord.ext import commands
        
        class IpcCog(commands.Cog):
            def __init__(self, bot):
                self.bot = bot
                
            @ipc.server.route(name = "test")
            async def test(self, data: ipc.server.IpcServerResponse):
                return "Successfully tested the endpoint, which name is " + str(data.endpoint)
    """
	def decorator(func):
		if not name:
			Server.ROUTES[func.__name__] = func
		else:
			Server.ROUTES[name] = func

		return func

	return decorator


class IpcServerResponse:
	"""Server response made for handling coroutines reserved for endpoints.
  
  Parameters
  ----------
  data: dict
    The data from which response is to be made.
"""
	def __init__(self, data: dict):
		self._json = data
		self.length = len(data)

		self.endpoint = data["endpoint"]

		for key, value in data["data"].items():
			setattr(self, key, value)

	def to_json(self):
		return self._json

	def __repr__(self):
		return "<IpcServerResponse length={0.length}>".format(self)

	def __str__(self):
		return self.__repr__()


class Server:
	"""The IPC server. Usually used on the bot process for receiving requests from the client.

    Parameters
    ----------
    bot: Union[:class:`~discord.Client`, :class:`~discord.ext.commands.Bot`, :class:`~discord.ext.commands.AutoShardedBot`]
        Your bot instance
    secret_key: str
        A secret key. Used for authentication and should be the same as your client's secret key.
    """

	ROUTES: dict = {}

	def __init__(self,
	             bot: Union[discord.Client, commands.Bot,
	                        commands.AutoShardedBot],
	             secret_key: str = "public-ipc-key"):
		self.bot = bot
		self.loop = bot.loop
		self.endpoints: dict = {}
		self.secret_key: str = secret_key
		self._app: aiohttp.web.Application = None
		self._is_closed: dict = False
		self.host: str = None
		self.path: str = None
		self.port: int = None
		self._webserver: web.TCPSite = None

	def route(self, name: str = None):
		"""Used to register a coroutine as an endpoint when you have
        access to an instance of :class:`.Server`.

        Parameters
        ----------
        name: str
            The endpoint name. If not provided the method name will be used.
       """
		def decorator(func):
			if not name:
				self.endpoints[func.__name__] = func
			else:
				self.endpoints[name] = func

			return func

		return decorator

	def update_endpoints(self):
		"""Called internally to update the server's endpoints for cog routes."""
		self.endpoints = {**self.endpoints, **self.ROUTES}
		self.ROUTES = {}

	@property
	def app(self):
		return self._app

	async def handle_accept(self, request: aiohttp.web.Request):
		"""Handles client requests from the client process.

        Parameters
        ----------
        request: :class:`~aiohttp.web.Request`
            The request made by the client, parsed by aiohttp.
            
        """
		self.update_endpoints()

		auth = request.headers.get("Authorization", "")
		if not auth == self.secret_key:
			resp = {
			    "code": 403,
			    "error": "Forbidden, No token or invalid token provided"
			}
			return aiohttp.web.json_response(resp)
		_data = await request.json()
		#print(_data)
		endpoint = _data.get("endpoint", "")
		if not endpoint or endpoint not in self.endpoints:
			resp = {
			    "error": "no endpoint provided or invalid provided",
			    "code": 500
			}
			return aiohttp.web.json_response(resp)
		server_resp = IpcServerResponse(_data)
		try:
			attempted_cls = self.bot.cogs.get(
			    self.endpoints[endpoint].__qualname__.split(".")[0])

			if attempted_cls:
				args = (attempted_cls, server_resp)
			else:
				args = (server_resp, )
		except AttributeError:
			args = (server_resp, )
		try:
			ret = await self.endpoints[endpoint](*args)
			resp = {"content": ret}
		except Exception as error:
			self.bot.dispatch("ipc_error", endpoint, error)
			resp = {"error_in_server": error, "code": 500}
		try:
			return aiohttp.web.json_response(resp)
		except TypeError as error:
			if str(error).startswith("Object of type") and str(error).endswith(
			    "is not JSON serializable"):
				error_response = [
				    "IPC route returned values which are not able to be sent over sockets.",
				    " If you are trying to send a discord.py object,",
				    " please only send the data you need."
				]
				resp = {"error": error_response, "code": 500}
				raise JSONEncodeError("".join(error_response))

	def start(self, *args, **kwargs) -> Tuple[web.Application, web.TCPSite]:
		"""Method to start IPC
    
    Parameters
    ----------
    app: Optional[:class:`~aiohttp.web.Application`]
      An aiohttp application if already made with important things. It is optional creates a new one when None given.
    path: Optional[str]
      The path where IPC connections are to be made, takes "/ipc" when None given.
    host: Optional[str]
      The host where the app has to be host for ex '0.0.0.0' for repl, defaults to localhost.
    port: Optional[int]
      The port where app has to be run, defaults to 8080
      
    Returns
    -------
    Tuple[:class:`~aiohttp.web.Application`, :class:`~aiohttp.web.TCPSite`]"""
		self.loop.run_until_complete(self._start(*args, **kwargs))
		return (self._app, self._webserver)

	def setup(self,
	          app: Optional[web.Application] = None,
	          path: Optional[str] = "/ipc") -> web.Application:
		"""Setups IPC app but doesn't runs it
		
		Parameters
		----------
		app: Optional[:class:`~aiohttp.web.Application`]
		  An aiohttp application if already made with important things. It is optional creates a new one when None given.
		path: Optional[str]
		  The path where IPC connections are to be made, takes "/ipc" when None given.
		  
		Returns
		-------
		application
		  formatted application"""
		self.loop.run_until_complete(self._setup(app, path))
		return self._app

	async def _setup(self,
	                 app: Optional[web.Application] = None,
	                 path: Optional[str] = "/ipc"):
		"""Setups IPC app but doesn't runs it
		
		Parameters
		----------
		app: Optional[:class:`~aiohttp.web.Application`]
		  An aiohttp application if already made with important things. It is optional creates a new one when None given.
		path: Optional[str]
		  The path where IPC connections are to be made, takes "/ipc" when None given."""
		self._app = app or web.Application(loop=self.loop)
		self._app.router.add_post(path, self.handle_accept)
		self.bot.dispatch("ipc_setup")

	async def _start(self,
	                 app: Optional[web.Application] = None,
	                 path: Optional[str] = "/ipc",
	                 host: Optional[str] = "localhost",
	                 port: Optional[int] = 8080):
		"""A coro to start IPC
    
    Parameters
    ----------
    app: Optional[:class:`~aiohttp.web.Application`]
      An aiohttp application if already made with important things. It is optional creates a new one when None given.
    path: Optional[str]
      The path where IPC connections are to be made, takes "/ipc" when None given.
    host: Optional[str]
      The host where the app has to be host for ex '0.0.0.0' for repl, defaults to localhost.
    port: Optional[int]
      The port where app has to be run, defaults to 8080"""
		self.setup(app=app, path=path)
		self.host, self.port, self.path = host, port, path
		runner = web.AppRunner(app)
		await runner.setup()
		self._webserver = web.TCPSite(runner, self.host, self.port)
		await self._webserver.start()
		self.bot.dispatch("ipc_ready")
		
