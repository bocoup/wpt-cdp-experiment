import shutil
import subprocess
import tempfile

profile_dir1 = tempfile.mkdtemp()
profile_dir2 = tempfile.mkdtemp()
chrome1 = subprocess.Popen(['chromium-browser', '--user-data-dir=%s' % profile_dir1, '--remote-debugging-port=9876'])
chrome2 = subprocess.Popen(['chromium-browser', '--user-data-dir=%s' % profile_dir2, 'http://localhost:9876'])

try:
    chrome2.wait()
finally:
    chrome1.terminate()
    shutil.rmtree(profile_dir1)
    shutil.rmtree(profile_dir2)
