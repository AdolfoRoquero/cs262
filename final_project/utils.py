def check_valid_ip_format(input_text):
    """
    Helper function to check if an input 
    string has the format of a valid address <ip>:<address>
    """
    if not input_text:
        print("\nCode can't be empty \n")
        return False
    
    if len(input_text.split(':')) != 2:
        print("\nCode must be of form `<ip_address>:<port>` \n")
        return False

    ip, port = input_text.split(':')
    
    if len(ip.split('.')) != 4:
        print("\nIp address must be of form `<bit0>:<bit1>:<bit2>:<bit3>` \n")
        return False
    
    # All bits must be between 0 and 3 digits 
    # and the numerical value from 0 to 255
    for idx, bit in enumerate(ip.split('.')):
        if not (0 < len(bit) and len(bit) <= 3):
            print(f"\n<bit{idx}>: {bit} is invalid\n")
            return False
        
        if not bit.isdigit():
           print(f"\n<bit{idx}>: is not an integer")
           return False
        
        if not (0 <= int(bit) and int(bit) <= 255):
            print(f"\n<bit{idx}>: value {bit} is invalid [0,255]\n")
            return False

    if len(port) > 6:
        print(f"\nPort length is too large\n")
        return False

    if not port.isdigit():
        print(f"\nPort is not an integer\n")
        return False

    return True


    

