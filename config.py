class Config():
    DEBUG = False
    SQL_ALCHEMY_TRACK_MODIFICATIONS =  False

class LocalDevelopment(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite3"
    SECURITY_PASSWORD_HASH =  'bcrypt'
    SECURITY_PASSWORD_SALT =   'meowmeowonasaltybeach'
    SECRET_KEY = 'forinternalsecurity'
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'

    CACHE_TYPE = 'RedisCache'
    CACHE_DEFAULT_TIMEOUT = 30
    CACHE_REDIS_PORT = 6379

    WTF_CSRF_ENABLED = False