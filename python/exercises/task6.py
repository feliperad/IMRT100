import random as rd

secret_number = rd.randint(1,100)
guessed_number = int(input('Please guess the number: '))

while guessed_number!=secret_number:
    if guessed_number>secret_number:
        print('the secret number is smaller')
        
    elif guessed_number<secret_number:
        print('the secret number is bigger')

    guessed_number = int(input('try again: '))

print('You got it right!')

