import urllib.request, sys
url = 'http://127.0.0.1:5000/user-management/bulk-import/template'
try:
    resp = urllib.request.urlopen(url)
    print('Status:', resp.getcode())
    # Check content type header
    print('Content-Type:', resp.headers.get('Content-Type'))
    data = resp.read()
    print('Bytes received:', len(data))
except Exception as e:
    print('Error:', e)
    sys.exit(1)
