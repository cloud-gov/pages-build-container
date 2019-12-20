import logging


class BatchHTTPHandler(logging.handlers.BufferingHandler):
    '''
    A Logging handler that buffers and sends them in batches over http

    Most of the code here is a combination of:
        logging.handlers.BufferingHandler
        https://github.com/python/cpython/blob/3.6/Lib/logging/handlers.py#L1205

        logging.handlers.HTTPHandler
        https://github.com/python/cpython/blob/3.6/Lib/logging/handlers.py#L1126

    The semantics are similar to the HTTPHandler with the following exceptions:
        1. Only POST is supported
        2. Data is JSON encoded instead of percent encoded
        3. A list of log records is sent in each request instead of only one
    '''
    def __init__(self, capacity, host, url, secure=False,
                 credentials=None, context=None):
        '''
        Initialize the instance with the buffer capacity, host, and request URL
        '''
        logging.handlers.BufferingHandler.__init__(self, capacity)

        if not secure and context is not None:
            raise ValueError("context parameter only makes sense "
                             "with secure=True")
        self.host = host
        self.url = url
        self.method = "POST"
        self.secure = secure
        self.credentials = credentials
        self.context = context

    def flush(self):
        self.acquire()
        try:
            if len(self.buffer) > 0:
                self.emitMany(self.buffer)
                self.buffer = []
        finally:
            self.release()

    def mapLogRecord(self, record):
        '''
        To be overriden by implementations
        '''
        return record.__dict__

    def emitMany(self, records):
        '''
        Emit a list of records

        Send them to a web server as a percent-encoded dictionary
        (Mostly cribbed from the `emit` method of HTTPHandler)
        '''

        try:
            import http.client
            import json
            host = self.host
            if self.secure:
                h = http.client.HTTPSConnection(host, context=self.context)
            else:
                h = http.client.HTTPConnection(host)
            url = self.url
            # Send a json encoded array under a key of `data`
            data = json.dumps(
                [self.mapLogRecord(record) for record in records])
            # support multiple hosts on one IP address...
            # need to strip optional :port from host, if present
            i = host.find(':')
            if i >= 0:
                host = host[:i]
            # See issue #30904: putrequest call above already adds this header
            # on Python 3.x.
            # h.putheader("Host", host)

            headers = {
                'Content-type': 'application/json',
                'Content-length': str(len(data))
            }

            if self.credentials:
                import base64
                s = ('%s:%s' % self.credentials).encode('utf-8')
                s = 'Basic ' + base64.b64encode(s).strip().decode('ascii')
                headers['Authorization'] = s

            h.request(self.method, url, data, headers)
            # can't do anything with the result
            h.getresponse()
        except Exception:
            # This is expecting a single LogRecord, just send the last one in
            # the buffer. If there is none, this will break.
            self.handleError(records[-1])
