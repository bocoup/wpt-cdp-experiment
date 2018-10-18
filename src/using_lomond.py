import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib2

import lomond

def get_json(url):
    response = urllib2.urlopen(url)
    return json.loads(response.read())

# {"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}

port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ['chromium-browser', '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port, 'http://example.com/5543'],
    stderr=open(os.devnull, 'w')
)

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

    websocket = lomond.WebSocket(debugger_url)
    from lomond.persist import persist
    for event in persist(websocket):
        print event.name
        if event.name == 'ready':
            websocket.send_text(
                u'{"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}'
            )
finally:
    chrome.terminate()
    shutil.rmtree(profile_dir)
