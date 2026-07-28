from backend1.db import execute_query

users = execute_query(
    "SELECT * FROM AUTH_USER"
)

print(users)