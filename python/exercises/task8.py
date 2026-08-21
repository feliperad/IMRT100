import random as rd

mode = input('Paper, rock, scissor: single or multi-player? ')

while mode!='single' and mode!='multi':
    mode = input('Wrong option! Please type "single" or "multi"')

op1 = input('Player one, please select paper(P), rock(R) or scissor(S): ')

if mode == 'multi':
    op2 = input('Player two, please select paper(P), rock(R) or scissor(S): ') 
else:
    op2 = rd.choice(['P','R','S'])

if op1==op2:
    print('Player 1 choose', op1, 'and player 2 choose', op2,': Its a tie!')

if op1=='P':
    if op2=='R':
        print('Player 1 choose', op1, 'and player 2 choose', op2,': player 1 wins!')
    if op2=='S':
            print('Player 1 choose', op1, 'and player 2 choose', op2,': player 2 wins!')

if op1=='R':
    if op2=='P':
        print('Player 1 choose', op1, 'and player 2 choose', op2,': player 2 wins!')
    if op2=='S':
            print('Player 1 choose', op1, 'and player 2 choose', op2,': player 1 wins!')

if op1=='S':
    if op2=='P':
        print('Player 1 choose', op1, 'and player 2 choose', op2,': player 1 wins!')
    if op2=='R':
            print('Player 1 choose', op1, 'and player 2 choose', op2,': player 2 wins!')