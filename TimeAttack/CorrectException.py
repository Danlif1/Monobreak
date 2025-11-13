class CorrectException(Exception):
    """
    If we by mistake hit the correct password we want to know it.
    This is because if we hit the correct password the server might early return for us.
    Also if we hit the correct password we can stop trying.
    So we abuse the exception mechanisem to fast return to main.
    """
    pass
