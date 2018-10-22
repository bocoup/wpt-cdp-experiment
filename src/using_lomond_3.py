import json
import os
import Queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib2

import lomond
from lomond.persist import persist

def get_json(url):
    response = urllib2.urlopen(url)
    return json.loads(response.read())

class Client(object):
    def __init__(self, url):
        self._websocket = lomond.WebSocket(debugger_url)
        self._id = 0
        self._messages = Queue.Queue()
        self._locks = {}
        self._results = {}
        self._exit_event = threading.Event()

    def connect(self):
        is_ready = False

        options = {
            'exit_event': self._exit_event,
            'poll': 0.1,
            'ping_rate': 0
        }

        for event in persist(self._websocket, **options):
            if is_ready:
                try:
                    message = self._messages.get(False)
                    #print 'SEND %s' % message
                    self._websocket.send_text(
                        unicode(json.dumps(message), 'utf-8')
                    )
                except Queue.Empty:
                    pass

            if event.name == 'ready':
                is_ready = True
            if event.name == 'text':
                body = json.loads(event.text)
                if 'id' in body:
                    #print 'RECV %s' % (body,)
                    self._results[body['id']] = body
                    self._locks.pop(body['id']).release()
                elif body.get('method') == 'Target.receivedMessageFromTarget':
                    result = json.loads(body['params']['message'])
                    if 'id'in result:
                        #print 'RECV %s' % (body,)
                        self._results[result['id']] = result
                        self._locks.pop(result['id']).release()

    def send_to_target(self, target_id, method, params):
        self._id += 1
        inner_message_id = self._id
        session_id = client.send('Target.attachToTarget', {'targetId': target_id})['sessionId']
        message = json.dumps({'id': inner_message_id, 'method': method, 'params': params})
        lock = threading.Lock()
        self._locks[inner_message_id] = lock
        lock.acquire()

        self.send('Target.sendMessageToTarget', {'sessionId': session_id, 'message': message})

        lock.acquire()
        result = self._results.pop(inner_message_id)
        if 'error' in result:
            raise Exception('%s - %s - %s' % (method, result['error']['message'], result['error']['data']))
        return result['result']

    def send(self, method, params):
        self._id += 1
        message_id = self._id
        lock = threading.Lock()
        self._locks[message_id] = lock
        lock.acquire()
        self._messages.put({
            'id': message_id,
            'method': method,
            'params': params
        })
        lock.acquire()
        result = self._results.pop(message_id)
        if 'error' in result:
            raise Exception('%s - %s - %s' % (method, result['error']['message'], result['error'].get('data')))
        return result['result']

    def close(self):
        self._exit_event.set()

port = 9876
profile_dir = tempfile.mkdtemp()
chrome = subprocess.Popen(
    [
        'chromium-browser', '--disable-popup-blocking',
        '--user-data-dir=%s' % profile_dir, '--remote-debugging-port=%s' % port,
        'http://example.com/5543'
    ],
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

    client = Client(debugger_url)
    handler = threading.Thread(target=lambda: client.connect())
    handler.start()

    client.send('Page.navigate', {'url': 'data:text/html,<script>open("about:blank");</script>'})
    targets = client.send('Target.getTargets', {})['targetInfos']

    print client.send('Runtime.evaluate', {'expression': 'location.href'})
    print client.send_to_target(targets[0]['targetId'], 'Runtime.evaluate', {'expression': 'location.href'})
finally:
    client.close()
    chrome.terminate()
    time.sleep(1)
    shutil.rmtree(profile_dir)
