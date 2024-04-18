from enum import StrEnum


def get_median(amount: list[float]) -> float:
    if len(amount) % 2 == 1:
        median = amount[len(amount) // 2]
    else:
        mid_1 = amount[len(amount) // 2 - 1]
        mid_2 = amount[len(amount) // 2]
        median = (mid_1 + mid_2) / 2 
    
    return median


class AMOUNT_TYPE(StrEnum):
    MEDIAN = 'median'
    AVERAGE = 'avg'
    MIN = 'min'
    MAX = 'max'



def get_amount(input: list[float], type:AMOUNT_TYPE = 'median') -> float:
    if type == 'median':
        median = 0
        if len(input) % 2 == 1:
            median = input[len(input) // 2]
        else:
            mid_1 = input[len(input) // 2 - 1]
            mid_2 = input[len(input) // 2]
            median = (mid_1 + mid_2) / 2 
        return median
    elif type == 'avg':
        return round(sum(input) / len(input), 1)

    elif type == 'min':
        return min(input)
    else:
        return max(input)

