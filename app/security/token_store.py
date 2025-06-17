revoked_tokens = set()

def revoke_token(jti: str):
    revoked_tokens.add(jti)

def is_token_revoked(jti: str) -> bool:
    return jti in revoked_tokens


# Eventually we can swap this to use Redis.