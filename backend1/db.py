from django.db import connection

def execute_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))

                for row in rows
            ]
        return None