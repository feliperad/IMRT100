import random as rd

a = 0; b = 100
guess = rd.randint(a,b)

while True:
    print("My guess is", guess)
    result = input('How did I go? ')

    if result == 'correct':
        print('I got it right!')
        break
    elif result == 'lower':
        b = guess
    elif result == 'higher':
        a = guess

    guess = rd.randint(a,b)



        

