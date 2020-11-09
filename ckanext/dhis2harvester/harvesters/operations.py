ADD = 'ADD'
SUBTRACT = 'SUBTRACT'


def aggregation_factor_for_operation(operation):
    if operation == ADD:
        return 1
    elif operation == SUBTRACT:
        return -1
    else:
        raise ValueError("Unsupported operation: {}".format(operation))
