# NOTICE: This example is incomplete

import json
import os
import shutil
import socket
import subprocess
import tempfile
import urllib2
import urlparse
import wspy

def get_json(url):
    response = urllib.urlopen(url)
    return json.loads(response.read())

port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ['chromium-browser', '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port, 'http://example.com/5543'],
    stderr=open(os.devnull, 'w')
)

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


        url_parts = urlparse.urlparse(debugger_url)
        def recv_callback(*args):
            print args

        sock = wspy.websocket(location=url_parts.path,
                              recv_callback=recv_callback)
        sock.connect(('', url_parts.port))
        #sock.setblocking(0)
        sock.send(wspy.Frame(
            wspy.OPCODE_TEXT,
            '{"id":122,"method":"Page.navigate","params":{"url":"http://bocoup.com"}}'
        ))

        # This loop reports "no data read from socket" indefinitely
        while True:
            try:
                print sock.recv()
                break
            except socket.error as e:
                pass

    finally:
        chrome.terminate()
        shutil.rmtree(profile_dir)

if __name__ == '__main__':
    main()
