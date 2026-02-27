import bcrypt


def hash_access_token(token: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(token.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_access_token(token: str, hashed_token: str) -> bool:
    try:
        return bcrypt.checkpw(token.encode('utf-8'), hashed_token.encode('utf-8'))
    except Exception:
        return False
