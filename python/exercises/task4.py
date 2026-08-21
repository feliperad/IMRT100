age = int(input('Type your age: '))
actual_year = 2026
hundred_in = actual_year + (100-age)

if (100-age)>0:
    print('you will turn 100 in', hundred_in)
elif (100-age)<0:
    print('you have already completed 100 years')
