import discord
from discord.ext import commands
import mts_ipc as ipc
import aiohttp
from aiohttp import web

bot = commands.Bot(command_prefix="$$")
bot.ipc = ipc.Server(bot,sck="my secret key")



@ipc.server.route(name = "test")
async def test(data):
  return "test"

@bot.ipc.route(name = "test2")
async def test2(data):
  return "tested"

@bot.event
async def on_ipc_error(endpoint,error):
  print("an error occurred in endpoint {0}:\n{1}".format(endpoint,error))

async def run(port: int = 8080):
  app = web.Application()
  app.router.add_post("/ipc", bot.ipc.handle_accept)
  runner = web.AppRunner(app)
  await runner.setup()
  webserver = web.TCPSite(runner, "0.0.0.0", port)
  await webserver.start()
  bot.run("Your token here")

