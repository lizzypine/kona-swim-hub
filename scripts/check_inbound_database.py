"""Read-only production schema check; never prints a DSN or exception message."""

import argparse
from getpass import getpass
import sys

import psycopg2


def check_database(database_url):
    connection = None
    try:
        connection = psycopg2.connect(database_url, connect_timeout=10)
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '10s'")
            cursor.execute("SELECT to_regclass('django_migrations'), to_regclass('inbound_inboundemail')")
            migration_table, inbound_table = cursor.fetchone()
            print("Database connection: OK")
            applied = False
            if migration_table:
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM django_migrations WHERE app = %s AND name = %s)",
                    ("inbound", "0001_initial"),
                )
                applied = cursor.fetchone()[0]
            print("Inbound migration recorded:", "YES" if applied else "NO")
            print("Inbound table exists:", "YES" if inbound_table else "NO")
            if not inbound_table:
                print("Result: inbound schema is missing in this database/search path.")
                return 1
            cursor.execute(
                "SELECT has_table_privilege('inbound_inboundemail', 'SELECT'), "
                "has_table_privilege('inbound_inboundemail', 'INSERT'), "
                "has_table_privilege('inbound_inboundemail', 'UPDATE')"
            )
            privileges = cursor.fetchone()
            for name, granted in zip(("SELECT", "INSERT", "UPDATE"), privileges):
                print(f"Inbound {name} permission:", "YES" if granted else "NO")
            if not all(privileges):
                print("Result: the configured database role lacks forwarding permissions.")
                return 1
            cursor.execute(
                "SELECT email_id, status, forward_to, forward_from, attempts, lease_id, "
                "lease_until, first_send_at, payload_sha256, forwarded_id, forwarded_at, "
                "error_code, created_at, updated_at FROM inbound_inboundemail WHERE false"
            )
            print("Inbound schema columns readable: YES")
            if not applied:
                print("Result: table exists, but migration history needs review; do not fake/reset it blindly.")
                return 1
            print("Result: migration, table, and required table permissions are present.")
            return 0
    except psycopg2.Error as exc:
        code = exc.pgcode or "unavailable"
        print("Database check failed; credentials and exception details were suppressed.")
        print("SQLSTATE:", code if code.isascii() and code.isalnum() and len(code) == 5 else "unavailable")
        return 1
    finally:
        if connection is not None:
            try:
                connection.rollback()
            except psycopg2.Error:
                pass
            try:
                connection.close()
            except psycopg2.Error:
                pass


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    if not sys.stdin.isatty():
        print("Run this command in an interactive terminal so the database URL can be entered privately.")
        return 2
    database_url = getpass("Current Lightsail DATABASE_URL (hidden): ")
    if not database_url:
        print("No database URL entered; nothing was checked.")
        return 2
    return check_database(database_url)


if __name__ == "__main__":
    sys.exit(main())
