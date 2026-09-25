from server import db
import datetime


def get_current_datetime():
    current_datetime = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return current_datetime

def resolve(token):
    row = db.get_uuid_from_token(token)
    if row is None:
        return None
    user_uuid, expires_at = row

    if expires_at < get_current_datetime():
        db.remove_token(token)
        return None
    else:
        return user_uuid

def revoke(token):
    db.remove_token(token)

def revoke_all(user_uuid):
    db.remove_token_by_uuid(user_uuid)