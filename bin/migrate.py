import os
import psycopg2


def migrate():
    conn = psycopg2.connect(os.environ['DB_URL'])
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS buildlog (id serial PRIMARY KEY, '
        'build integer, source varchar, output varchar)'
    )
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    migrate()
