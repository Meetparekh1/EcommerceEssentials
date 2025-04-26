import re

# Dictionary of Indian states and their PIN code prefixes
INDIAN_PIN_PREFIXES = {
    'Delhi': '11',
    'Haryana': '12, 13',
    'Punjab': '14, 15, 16',
    'Himachal Pradesh': '17',
    'Jammu & Kashmir': '18, 19',
    'Uttar Pradesh': '20, 21, 22, 23, 24, 25, 26, 27, 28',
    'Rajasthan': '30, 31, 32, 33, 34',
    'Gujarat': '36, 37, 38, 39',
    'Maharashtra': '40, 41, 42, 43, 44',
    'Madhya Pradesh': '45, 46, 47, 48, 49',
    'Andhra Pradesh': '50, 51, 52, 53',
    'Karnataka': '56, 57, 58, 59',
    'Tamil Nadu': '60, 61, 62, 63, 64',
    'Kerala': '67, 68, 69',
    'West Bengal': '70, 71, 72, 73, 74',
    'Odisha': '75, 76, 77',
    'Assam': '78',
    'North Eastern': '79',
    'Bihar': '80, 81, 82, 83, 84, 85',
    'Jharkhand': '81, 82, 83',
    'Chhattisgarh': '49'
}

def is_valid_pincode(pincode):
    """
    Validates if the given string is a valid Indian PIN code.
    Valid Indian PIN codes are 6 digits and start with certain prefixes.
    
    Args:
        pincode (str): The PIN code to validate
        
    Returns:
        bool: True if the PIN code is valid, False otherwise
    """
    # Check if it's a 6-digit string
    if not pincode or not re.match(r'^\d{6}$', pincode):
        return False
    
    # Check if it starts with a valid prefix
    prefix_valid = False
    for prefixes in INDIAN_PIN_PREFIXES.values():
        for prefix in prefixes.replace(' ', '').split(','):
            if pincode.startswith(prefix):
                prefix_valid = True
                break
        if prefix_valid:
            break
    
    return prefix_valid

def get_state_from_pincode(pincode):
    """
    Returns the state name for a given PIN code.
    
    Args:
        pincode (str): The PIN code
        
    Returns:
        str: The state name or None if not found
    """
    if not is_valid_pincode(pincode):
        return None
    
    for state, prefixes in INDIAN_PIN_PREFIXES.items():
        for prefix in prefixes.replace(' ', '').split(','):
            if pincode.startswith(prefix):
                return state
    
    return None
