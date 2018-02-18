def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_user(cursor, userid):
    cursor.execute("SELECT users.* FROM users WHERE users.id=(?)", (userid,))
    user = cursor.fetchone()

    cursor.execute("SELECT skills.name, skills.rating FROM skills WHERE skills.userid=(?)", (userid,))
    skills = cursor.fetchall()

    user["skills"] = skills
    return user