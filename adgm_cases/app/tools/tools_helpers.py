def sum_values(numbers_str: str) -> float:
    """
    Tool: sum_values
    Use to sum a list of numbers.
    Input format: A stringified list of floats (e.g., "[1000, 2000, 3000]").
    """
    return sum(eval(numbers_str))


def multiply_values(x: str) -> float:
    """
    Tool: multiply_values
    Use to multiply two numeric values.
    Input format: 'value1,value2' (e.g., '11000,3')
    """
    a, b = [
        float(val.strip().replace("'", "").replace('"', "")) for val in x.split(",")
    ]
    return a * b


def check_claim_correct(x: str) -> str:
    """
    Tool: check_claim_correct
    Compares the calculated result with the claimed amount.
    Input format: 'calculated,claimed'
    Returns a message stating if the claim is correct or not.
    """
    calculated, claimed = [
        float(val.strip().replace("'", "").replace('"', "")) for val in x.split(",")
    ]
    difference = abs(calculated - claimed)
    if difference < 1e-2:
        return "The claim value is Correct."
    else:
        return f"Conflict: Claimed value {claimed} while Calculated value is {calculated}, with difference of {difference}"
