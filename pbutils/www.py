'''
Construct a cmd-line curl call
'''
# see https://stackoverflow.com/questions/17936555/how-to-construct-the-curl-command-from-python-requests-module
from urllib.parse import urlencode


def curlify(url, method, params=None, headers=None, data=None):
    command = "curl -X {method} -H {headers} '{url}'"  # NOT an f-string
    if params:
        url += F"?{urlencode(params)}"
    if headers:
        headers = ['"{0}: {1}"'.format(k, v) for k, v in headers.items()]
        headers = " -H ".join(headers)
    curl = command.format(method=method, headers=headers, data=data, url=url)
    if data:
        curl += f'-d {data}'
    return curl
