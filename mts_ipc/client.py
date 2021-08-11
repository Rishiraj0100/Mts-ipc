import asyncio
import logging
import typing

import aiohttp

from mts_ipc.errors import IpcError

class Client:
	"""
    Handles webserver side requests to the bot process.
    
    Parameters
    ----------
    host: str
        The IP or host of the IPC server, defaults to localhost.
    path: str
        The path of the IPC server's IPC connections, defaults to /ipc.
    secret_key: Union[str, bytes]
        The secret key for your IPC server. Must match the server secret_key or requests will not go ahead, defaults to None
    """
	def __init__(self, host: "localhost", secret_key: typing.Union[str, bytes] = "public-ipc-key",path: str = "/ipc"):
		"""Constructor"""
		self.loop = asyncio.get_event_loop()
		self.path = "/"+str(path) if not str(path).startswith("/") else path
		self.secret_key = secret_key
		self.host = host

	@property
	def url(self):
		return "https://{0.host}{1}".format(self, self.path)

	async def request(self, endpoint, **kwargs):
		"""Make a request to the IPC server process.

        Parameters
        ----------
        endpoint: str
            The endpoint to request on the server
        **kwargs
            The data to send to the endpoint
        """
		payload = {"endpoint": endpoint, "data": kwargs}
		headers = {"Authorization": self.secret_key}
		async with aiohttp.ClientSession() as ses:
			ret = await ses.post(self.url, json=payload, headers=headers)
			ret = await ret.json()
			if "error" in ret:
			  raise IpcError(ret["error"])
			resp = ret["content"]
			await ses.close()
		return resp

  
