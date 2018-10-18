import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib2

from tornado import websocket
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen

def get_json(url):
    response = urllib2.urlopen(url)
    return json.loads(response.read())

port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ['chromium-browser', '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port, 'http://example.com/5543'],
    stderr=open(os.devnull, 'w')
)

@gen.coroutine
def main():
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

        connection = yield websocket.websocket_connect(debugger_url)
        yield connection.write_message(
            '{"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}'
        )

        print (yield connection.read_message())

        time.sleep(5)

    finally:
        chrome.terminate()
        shutil.rmtree(profile_dir)

if __name__ == '__main__':
    IOLoop.current().run_sync(main)
