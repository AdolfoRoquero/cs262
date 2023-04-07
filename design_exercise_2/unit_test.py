import random
from scale_model import Config

def action_generation(config, msg_queue, logical_clock):
        action = -1
        # If there is a message in the queue
        if msg_queue:
            msg = msg_queue.pop(0)
            logical_clock = max(logical_clock, int(msg))
            code = [] 
        else:  
            action = random.randint(0,config.rand_upper_bound)
            if action in list(range(len(config.out_ports))):
                """ Send to ONE of the other machines a message that is:
                    - the local logical clock time, 
                    - update it's own logical clock, 
                    - and update the log with the send, 
                    - the system time, and 
                    - the logical clock time"""
                code = [config.out_ports[action]]
            elif action == len(config.out_ports):
                code = config.out_ports
            else:
                """Treat the cycle as an internal event: 
                - update the local logical clock, 
                - log the internal event, the system time, and the logical clock value."""
                code = []

        return code, action, msg_queue, logical_clock
            
def unit_test_empty_queue():
    rand_upper = 9
    config = Config('P3', "localHost", "port3", ["port1", "port2"], 1, rand_upper)
    empty_queue = []
    start_logical_clock = 0
    code, action, post_msg_queue, post_logical_clock = action_generation(config, empty_queue, start_logical_clock)
    assert action != -1 
    assert action < rand_upper+1
    assert post_msg_queue == []
    assert post_logical_clock == start_logical_clock
    if action > len(config.out_ports):
        assert code == []
    print("Empty Queue test pass")

def unit_test_filled_queue_higher_received_logical_clock():
    rand_upper = 9
    config = Config('P3', "localHost", "port3", ["port1", "port2"], 1, rand_upper)
    queue = [15]
    start_logical_clock = 0

    code, action, post_msg_queue, post_logical_clock = action_generation(config, queue, start_logical_clock)
    assert action == -1 
    assert post_msg_queue == []
    assert post_logical_clock == 15
    print("Filled Queue with higher received logical clock test pass")

def unit_test_filled_queue_lower_received_logical_clock():
    rand_upper = 9
    config = Config('P3', "localHost", "port3", ["port1", "port2"], 1, rand_upper)
    queue = [0]
    start_logical_clock = 15

    code, action, post_msg_queue, post_logical_clock = action_generation(config, queue, start_logical_clock)
    assert action == -1 
    assert post_msg_queue == []
    assert post_logical_clock == start_logical_clock
    print("Filled Queue with lower received logical clock test pass")



if __name__ == "__main__":
    unit_test_empty_queue()
    unit_test_filled_queue_higher_received_logical_clock()
    unit_test_filled_queue_lower_received_logical_clock()

    print("ALL TEST PASSED")
