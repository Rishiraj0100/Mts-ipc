class IpcError(Exception):
  """Base error"""
  pass

class JSONEncodeError(IpcError):
  """An error raised when JSONDecode problem is there"""
  pass
