def check_valid_ip_format(input_text):
    if not input_text:
        return False
    
    if len(input_text.split(':')) != 2:
        return False

    ip, port = input_text.split(':')
    
    if len(ip.split('.')) != 4:
        return False
    
    # All bits must be between 0 and 3 digits 
    # and the numerical value from 0 to 255
    for bit in ip.split('.'):
        if not (0 < len(bit) and len(bit) <= 3 and 0 <= int(bit) and 0 < 255):
            return False
    
    if len(port) > 5:
        return False

    return True


    

