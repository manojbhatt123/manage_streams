import os

from django.conf import settings


def get_logging_config():
    """
    This generate logging configuration w.r.t given params which will be use in
     code base to log something as per need.

    :return: A dict containing logging conf
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': (
                    '%(levelname)s %(asctime)s %(process)d %(thread)d '
                    '%(filename)s %(module)s %(funcName)s '
                    '%(lineno)d %(message)s'
                )
            },
            'simple': {
                'format': '%(levelname)s: %(message)s'
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(
                    settings.BASE_DIR, 'logs/manage_streams.log'
                ),
                'formatter': 'verbose',
                'when': 'midnight',
                'backupCount': 10,
                'encoding': 'utf-8',
            },
            'access_logs': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs/access.log'),
                'formatter': 'simple',
                'when': 'midnight',
                'backupCount': 7,
                'encoding': 'utf-8',
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler'
            },
        },
        'loggers': {
            'django.security.DisallowedHost': {
                'handlers': ['file'],
                'propagate': False,
            },
            '': {
                'handlers': ['file'],
                'level': 'INFO',
            },
            'django': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': True,
            },
            'django.db': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False,
            },
        }
    }
