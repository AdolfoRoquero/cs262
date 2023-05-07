def check_valid_ip_format(input_text):
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
        if not (0 < len(bit) and len(bit) <= 3 and 0 <= int(bit) and 0 < 255):
            print(f"\n<bit{idx}>: {bit} is invalid\n")
            return False
    
    if len(port) > 5:
        return False

    return True


    

