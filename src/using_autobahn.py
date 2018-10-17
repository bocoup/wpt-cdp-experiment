import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib

from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory

def get_json(url):
    # TODO: Investigate why urllib rejects the response from Chrome's HTTP
    # server
    #response = urllib.urlopen(url)
    #return json.loads(response.read())

    return json.loads(subprocess.check_output(['curl', '--silent', url]))

# {"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}

class MyClientProtocol(WebSocketClientProtocol):
   def onOpen(self):
      self.sendMessage(u'{"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}'.encode('utf8'))

   def onMessage(self, payload, isBinary):
      if isBinary:
         print('Binary message received: {0} bytes'.format(len(payload)))
      else:
         print('Text message received: {0}'.format(payload.decode('utf8')))

port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ['chromium-browser', '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port, 'http://example.com/5543'],
    stderr=open(os.devnull, 'w')
)

log.startLogging(sys.stdout)
try:
    while True:
        try:
            instances = get_json('http://localhost:%s/json' % port)
            break
        except:
            pass

    for instance in instances:
        if instance['url'] == 'http://example.com/5543':
            debugger_url = instance['webSocketDebuggerUrl']
            break
    else:
        raise Exception('Could not find browser')

    factory = WebSocketClientFactory(debugger_url)
    factory.protocol = MyClientProtocol

    reactor.connectTCP('127.0.0.1', port, factory)
    reactor.run()
finally:
    chrome.terminate()
    shutil.rmtree(profile_dir)
