from functools import wraps

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from sanic import text
import datetime
from settings import JWT_KEY, TRANSACTIONS
from Crypto.Hash import SHA1
from hashlib import md5


def check_token(request):
    if not request.token:
        return False

    try:
        result = jwt.decode(
            request.token, JWT_KEY, algorithms=["HS256"]
        )
        print(result)
    except jwt.exceptions.InvalidTokenError:
        return False
    else:
        return True


def need_authentification(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated = check_token(request)

            if is_authenticated:
                response = await f(request, *args, **kwargs)
                return response
            return text("You are unauthorized.", 401)

        return decorated_function

    return decorator(wrapped)


def get_encripdted_password(password):
    return md5(password.encode()).hexdigest()


def get_user_auth_token(login):
    return jwt.encode({
                'login': login
            },
            JWT_KEY,
            algorithm="HS256"
        )


def get_activation_token(user):
    return jwt.encode({
                'id': user.id,
                'exp': datetime.datetime.now() + datetime.timedelta(days=1)
            },
            JWT_KEY,
            algorithm="HS256"
        )


def check_activation_token(token):
    try:
        decoded = jwt.decode(
            token, JWT_KEY, algorithms=["HS256"]
        )
        return decoded['id']
    except (InvalidTokenError, ExpiredSignatureError):
        return None


def get_transaction_signasture(transaction_id, user_id, account_id, amount):
    private_key = TRANSACTIONS['private_key']
    hash_data = SHA1.new()
    hash_data.update(
        f'{private_key}:{transaction_id}:{user_id}:{account_id}:{amount}'.encode()
    )
    return hash_data.hexdigest()
