"""Custom warnings"""

__all__ = ['LoudDeprecationWarning']


class LoudDeprecationWarning(UserWarning):
    """Python's DeprecationWarning is silent by default"""
    pass
