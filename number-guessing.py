from random import randint

info_user = input("your name: ")
n_machine = randint(1, 3)
trying = 0
while True:
    try:     
        trying += 1
        proposition = int(input("your proposition (betwen 1 and 5): "))
        if proposition == n_machine:
            print(f"{info_user} YOU WIN IN {trying} try(s)! the number was {n_machine}")
            CONT =  input("WOULD YOU CONTINUE ? : ")
            if CONT == 'yes':
                continue
            else:
                break
        if proposition > n_machine:
            print("too hight")
        if proposition < n_machine:
            print("too low")
    except ValueError:
        print("please enter a valid number")
        
        
    