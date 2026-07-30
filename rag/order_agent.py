# order_agent.py

import re

ORDER_STEPS = [
    "customer_name",
    "product_name",
    "quantity",
    "delivery_address",
    "contact_number",
    "payment_mode",
    "confirmation",
]

QUESTIONS = {
    "customer_name": "May I have your full name?",
    "product_name": "Which product would you like to order?",
    "quantity": "How many units would you like to order? (enter a number)",
    "delivery_address": "Please provide the complete delivery address.",
    "contact_number": "Please provide your contact number.",
    "payment_mode": "How would you like to pay?\n1. Cash on Delivery",
    "confirmation": "Please confirm. Reply with YES to place the order."
}

def validate_answer(session, answer):
    """Return (is_valid, cleaned_value, error_message)"""
    step = session["step"]
    field = ORDER_STEPS[step] if step < len(ORDER_STEPS) else None
    if field is None:
        return False, None, "Invalid step."

    if field == "quantity":
        numbers = re.findall(r'\d+', answer)
        if not numbers:
            return False, None, "Please enter a valid number (e.g., 5)."
        quantity = int(numbers[0])
        if quantity <= 0:
            return False, None, "Quantity must be greater than 0."
        return True, str(quantity), None

    elif field == "contact_number":
        digits = re.sub(r'\D', '', answer)
        if len(digits) < 8:
            return False, None, "Please enter a valid contact number (minimum 8 digits)."
        return True, answer, None

    elif field == "payment_mode":
        if answer.strip() == "1" or "cash" in answer.lower():
            return True, "Cash on Delivery", None
        # add other payment modes if needed
        return False, None, "Please select a valid payment option (1 for Cash on Delivery)."

    # For other fields, accept as is
    return True, answer, None

def save_answer(session, answer):
    step = session["step"]
    field = ORDER_STEPS[step]
    is_valid, cleaned, error = validate_answer(session, answer)
    if not is_valid:
        raise ValueError(error)
    session["data"][field] = cleaned
    session["step"] += 1
    return session

def new_session():
    return {"step": 0, "data": {}}

def validate_answer(session, answer):
    """
    Validate the user's answer for the current step.
    Returns (is_valid, cleaned_value, error_message)
    """
    step = session["step"]
    field = ORDER_STEPS[step] if step < len(ORDER_STEPS) else None
    if field is None:
        return False, None, "Invalid step."

    if field == "quantity":
        # Try to extract a number from the answer
        # Allow "5", "5 units", "5kg", etc.
        numbers = re.findall(r'\d+', answer)
        if not numbers:
            return False, None, "Please enter a valid number (e.g., 5)."
        quantity = int(numbers[0])
        if quantity <= 0:
            return False, None, "Quantity must be greater than 0."
        return True, str(quantity), None

    elif field == "contact_number":
        # Basic validation: at least 8 digits
        digits = re.sub(r'\D', '', answer)  # remove non-digits
        if len(digits) < 8:
            return False, None, "Please enter a valid contact number (minimum 8 digits)."
        return True, answer, None

    elif field == "payment_mode":
        # Accept "1" or "Cash on Delivery"
        if answer.strip() == "1" or "cash" in answer.lower():
            return True, "Cash on Delivery", None
        # Add more payment modes as needed
        return False, None, "Please select a valid payment option (1 for Cash on Delivery)."

    # For other fields, accept as is (you can add more validations)
    return True, answer, None

def save_answer(session, answer):
    step = session["step"]
    field = ORDER_STEPS[step]
    # Validate and clean
    is_valid, cleaned, error = validate_answer(session, answer)
    if not is_valid:
        raise ValueError(error)
    session["data"][field] = cleaned
    session["step"] += 1
    return session

def next_question(session):
    if session["step"] >= len(ORDER_STEPS):
        return None
    field = ORDER_STEPS[session["step"]]
    return QUESTIONS[field]

def completed(session):
    return session["step"] == len(ORDER_STEPS)

def summary(session):
    d = session["data"]
    return f"""
Customer : {d.get('customer_name')}
Product  : {d.get('product_name')}
Quantity : {d.get('quantity')}
Address  : {d.get('delivery_address')}
Contact  : {d.get('contact_number')}
Payment  : {d.get('payment_mode')}

Reply YES to place the order.
"""