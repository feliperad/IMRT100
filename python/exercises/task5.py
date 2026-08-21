secret_word = 'chair'
attempts = 0
guessed_word = input('Guess the word (hint #1: is a furniture): ')

while secret_word != guessed_word:
    if attempts==1:
        print('you got it wrong! Hint #2: it can be made of several materials')
        guessed_word = input('Guess the word (hint #2: is a furniture): ')

    if attempts==2:
        print('Wrong again! Hint #3: it is used to sit')
        guessed_word = input('Guess the word (hint #3: is a furniture): ')

    if attempts==3:
        print('You have failed!')
        break

    attempts+=1

if secret_word==guessed_word:
    print('you got it right!!')