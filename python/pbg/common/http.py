from mimetools import Message
from collections import namedtuple
from StringIO import StringIO


ParsedHTTPResponse = namedtuple(
    'ParsedHTTPReponse',
    ['http_version', 'status', 'reason', 'headers', 'body'])


def parse_http_response(s):
    head, body = s.split('\r\n\r\n', 1)
    status_line, headers_text = head.split('\r\n', 1)
    http_version, status_code, reason = status_line.split()
    status = int(status_code)
    headers = Message(StringIO(headers_text)).dict

    return ParsedHTTPResponse(http_version, status, reason, headers, body)
