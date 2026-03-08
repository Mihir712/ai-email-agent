def classify_email(email):

    email = email.lower()

    if "meeting" in email or "call" in email:
        return "meeting_request"

    if "price" in email or "pricing" in email:
        return "pricing_request"

    return "clarification"