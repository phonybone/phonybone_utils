'''
'''
import random
import sqlalchemy as sa

create_sql = '''
CREATE TABLE IF NOT EXISTS tags (
oid INT,
key VARCHAR(255),
value VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS oid_idx ON tags (oid);
CREATE INDEX IF NOT EXISTS key_idx ON tags (key);
CREATE INDEX IF NOT EXISTS value_idx ON tags (value)
'''


db = None

def init(db_uri):
    global db
    db = sa.create_engine(db_uri)
    create_table()


def create_table():
    with db.begin() as conn:
        for stmt in create_sql.split(';'):
            conn.execute(sa.text(stmt))


def insert_obj(**tags):
    if not tags:
        raise ValueError("empty object")
    sql = "INSERT INTO tags (oid, key, value) VALUES (:oid, :key, :value)"
    with db.begin() as conn:
        oid = conn.execute(sa.text("SELECT max(oid) from tags")).scalar()
        if oid is None:
            oid = 0
        else:
            oid = oid + 1

        for key, value in tags.items():
            conn.execute(sa.text(sql), oid=oid, key=key, value=value)

    return oid


def add_tags(oid, **tags):
    sql = "INSERT INTO tags (oid, key, value) VALUES (:oid, :key, :value)"
    with db.begin() as conn:
        for key, value in tags.items():
            conn.execute(sa.text(sql), oid=oid, key=key, value=value)


def get_tags(oid):
    ''' return tags for an object '''
    sql = "SELECT key, value FROM tags WHERE oid=:oid"
    with db.begin() as conn:
        results = conn.execute(sa.text(sql), oid=oid).fetchall()
        return {row[0]:row[1] for row in results}


def get_objects(key=None, value=None):
    ''' return oids for a given key/value pair (either can be None) '''
    sql = 'SELECT oid FROM tags'
    where_parts = []
    if key is not None:
        where_parts.append('key=:key')
    if value is not None:
        where_parts.append('value=:value')
    if where_parts:
        where_clause = F" WHERE {' AND '.join(where_parts)}"
        sql += where_clause
    sql += " ORDER BY oid"

    with db.begin() as conn:
        results = conn.execute(sa.text(sql), key=key, value=value).fetchall()
        return [row[0] for row in results]


def search(**tags):
    if len(tags) == 0:
        raise ValueError("no tags to search")

    tblname = 'tags'
    with db.begin() as conn:
        for key, value in tags.items():
            tblname = _search(conn, tblname, key, value)
            if tblname is None:
                return set()
        results = conn.execute(sa.text(F"SELECT oid FROM {tblname}")).fetchall()
        return set(row[0] for row in results)


def _search(conn, src_table, key=None, value=None):
    # find oids for this key/value:
    sql = F"SELECT oid FROM {src_table} WHERE key=:key AND value=:value"
    results = conn.execute(sa.text(sql), key=key, value=value).fetchall()
    oids = [row[0] for row in results]
    if not oids:
        return None
    oids = ", ".join(str(oid) for oid in oids)

    # create temp table with all tag info for these oids:
    dst_table = ''.join(chr(random.randint(ord('A'), ord('Z'))) for _ in range(5))
    sql = F"""CREATE TEMP TABLE {dst_table} AS
WITH select0 AS (
  SELECT oid, key, value FROM {src_table}
  WHERE oid IN ({oids})
) SELECT * FROM select0"""
    conn.execute(sa.text(sql))
    return dst_table


def _dump(conn, tablename):
    sql = F"SELECT oid, key, value FROM {tablename}"
    results = conn.execute(sa.text(sql)).fetchall()
    for row in results:
        args = dict(row)
        args['tablename'] = tablename
        print("{tablename}: [{oid}] {key}={value}".format(**args))

def remove_object(oid=None):
    sql = "DELETE FROM tags"
    args = {}
    if oid is not None:
        sql += " WHERE oid=:oid"
        args['oid'] = oid

    with db.begin() as conn:
        conn.execute(sa.text(sql), **args)


if __name__ == '__main__':
    import json
    from functools import partial
    json2 = partial(json.dumps, indent=2)

    db_uri = "sqlite:///tags.db"
    init(db_uri)
    remove_object()
    with open("bikes.json") as data:
        bikes = json.load(data)
        for bike in bikes:
            insert_obj(**bike)

    # print(F"blue oids: {get_objects(value='blue')}")
    # print(F"named oids: {get_objects(key='name')}")

    def assert_contains_tags(oid, **tags):
        oid_tags = get_tags(oid)
        for key, value in tags.items():
            assert oid_tags[key] == value

    tags = dict(color='orange', brand='ktm')
    oids = search(**tags)
    print(F"ktms: {oids}")
    for oid in oids:
        assert_contains_tags(oid, **tags)

    oids = search(brand='ktm', color='orange')
    print(F"orange ktms: {oids}")

    oids = search(color='orange')
    print(F"orange bikes: {oids}")
