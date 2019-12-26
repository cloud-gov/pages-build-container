import logging
import psycopg2


class DBHandler(logging.Handler):
    def __init__(self, conn_url, build_id):
        self.conn_url = conn_url
        self.build_id = build_id
        self.source = 'ALL'

        self.conn = None

        try:
            self.conn = psycopg2.connect(self.conn_url)
        except Exception:
            raise Exception(f'Cannot connect to {self.conn_url}')

        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            self.exec(
                ('INSERT INTO buildlog (build, source, output) '
                 'VALUES (%s, %s, %s);'),
                (self.build_id, self.source, self.format(record))
            )
        except Exception:
            self.handleError(record)

    def close(self):
        self.conn.close()

    def exec(self, stmt, args):
        cursor = self.conn.cursor()
        cursor.execute(stmt, args)
        self.conn.commit()
        cursor.close()
