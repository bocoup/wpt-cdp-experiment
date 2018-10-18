import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib

import websocket

def get_json(url):
    # TODO: Investigate why urllib rejects the response from Chrome's HTTP
    # server
    #response = urllib.urlopen(url)
    #return json.loads(response.read())

    return json.loads(subprocess.check_output(['curl', '--silent', url]))


port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ['chromium-browser', '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port, 'http://example.com/5543'],
    stderr=open(os.devnull, 'w')
)

def _handle(url, locks):

    def on_message(ws, message):
        data = json.loads(message)
        locks[message['id']].release()
        del locks[message['id']]
    def on_error(ws, error):
        print error
    def on_close(ws):
        print 'Closed!'

    ws = websocket.WebSocketApp(url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

class Connection(object):
    def __init__(self, url):
        self.url = url
        self.locks = {}
        self.handler = threading.Thread(target=_handler,
                                        args=(url, self.locks))

    def send(self, name, params):
        pass

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

    print debugger_url
finally:
    chrome.terminate()
    shutil.rmtree(profile_dir)
