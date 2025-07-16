# Lambda function that performs a calculation based on request
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    # Grab user input numbers and operation
    a = event.get('a')
    b = event.get('b')
    op = event.get('op')

    if a is None or b is None or op is None:
        raise Exception('Keys must be of form a, b, op')
    
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        raise Exception("Values for 'a' and 'b' must be numeric")

    # Perform and store calculation
    if op == '+':
        result = a + b
    elif op == '-':
        result = a - b
    elif op == '*':
        result = a * b
    elif op == '/':
        if (b == 0):
            raise Exception("Divide by zero is undefined")
        result = a / b
    else:
        raise Exception("operand not supported, must be +, -, *, or /")

    # Log and return result
    logger.info(f"Performed Calculation:\n{a} {op} {b} = {result}")
    
    return {
        'statusCode': 200,
        'result': result
    }