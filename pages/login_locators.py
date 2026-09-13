import re


class LoginLocators:
    EMAIL = re.compile("email", re.IGNORECASE)
    EMAIL_PLACEHOLDER = re.compile("you@example.com", re.IGNORECASE)
    PASSWORD = re.compile("password", re.IGNORECASE)
    SIGN_IN = re.compile("sign in|log in", re.IGNORECASE)
