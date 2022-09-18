""" Our tests are defined in here """

from django_json_api import reqArgs, jsonResponse, errResponse, rawResponse
from django_json_api import xstr, xint, xfloat, xbool

class TestReq:
  def __init__(self, get={}, post={}):
    self.GET = get
    self.POST = post

def test_base():
    assert xstr(None) == ""
    assert xstr("Test") == "Test"

    assert xint(None) == 0 
    assert xint("8lkajsdf") == 8
    assert xint(27) == 27
    assert xint("undefined") == None

    assert xfloat(None) == 0.0
    assert xfloat("8lkajsdf") == 8
    assert xfloat("8.17lkajsdf") == 8.17
    assert xfloat(27) == 27
    assert xfloat(27.2) == 27.2
    assert xfloat("undefined") == None

    assert not xbool(None)
    assert xbool("tRue")
    assert not xbool("falSe")
    assert xbool(True)

def test_req_args():
  @reqArgs(get_opts=('i#test', 'i#test2'))
  def testy( request, test, test2, **kwargs ):
    assert test == 8
    assert test2 == None

  testy( TestReq({'test': 8}) )
