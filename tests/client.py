from quart import Quart
import mts_ipc as ipc

app=Quart(__name__)

mpc=ipc.Client(secret_key="my secret key",host="test.testerpy.repl.co",path="ipc")

@app.route("/")
async def hi():
  return str(await mpc.request("test"))
  
app.run("0.0.0.0",port=8080,debug=True)
