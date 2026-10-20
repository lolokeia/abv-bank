
def checksum_create(nums):
    digits = [int(c) for c in str(nums)]
    # for i, d in enumerate(digits):
    #     print(i, d)
    
    
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            dd = d * 2
            if dd > 9:
                dd -= 9
            total += dd
        else:
            total += d
    
    return (10 - (total % 10)) % 10


def check_checksum(num):
    num = str(num)
    old_checksum = int(num[-1])
    number = int(num[:-1])

    new_checksum = checksum_create(number)
    if old_checksum != new_checksum: return False
    else: return True