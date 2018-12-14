# Klient projektu nr 13 lab 7. Ewiak, Kulczak, 28.11.2018
import socket
import sys
import math
from bitstring import BitArray
from threading import Timer
##
# 000000 -> hello
# 000001 -> ID operations
# 000010 -> preparing for a game
# 000100 -> Game
# 001000 -> range error
# 010000 -> overflow error
# 100000 -> client disconnected
# 111111 -> not enough seats
##



def send_data(sock, OP, RESP, ID, INTEGER):
    if INTEGER==-1:
        sock.sendall(BitArray('0b' + OP + RESP + ID).tobytes())
    else:
        get_bin = lambda x, n: format(x, 'b').zfill(n)
        sock.sendall(BitArray('0b' + OP + RESP + ID + get_bin(INTEGER, 20)).tobytes())


def receive_data(sock):
    x = BitArray(sock.recv(4096)).bin
    OP = x[:6]
    RESP = x[6:9]
    ID = x[9:12]
    if len(x) < 32:
        INTEGER=-1
    else:
        INTEGER = int(x[12:], 2)
    return OP, RESP, ID, INTEGER



def tim():
    print("Waiting for second client to insert a number...")

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_session_id = 0



def main():
    last_sent_int=0
    global get_bin, my_session_id
    t = Timer(2, tim)
    automate= False
    host = "127.0.0.1"
    port = 8888
    range_left = 0
    range_right = 0
    try:
        soc.connect((host, port))
    except:
        print("Connection error.")
        sys.exit()

    send_data(soc, "000000", "000", "000", -1)
    number_correct = False
    my_session_id = "000"
    while not number_correct:
        OP, RESP, ID, INT = receive_data(soc)
        if OP == "111111":
            print("Server is full, better check later.")
            send_data(soc, "100000", "000", my_session_id, -1)
            break
        elif OP == "000000":
            print("Server agreed for connection. Requesting id.")
            send_data(soc, "000001", "000", my_session_id, -1)
        elif OP == "000001":
            print("Server sent me a session ID: " + ID)
            my_session_id = ID
            a = input("[" + my_session_id + "] I'm going to send a number to server, input number 0-1048575 ->")
            while a.isdigit() == False or (a.isdigit() == True and int(a) > 1048575):
                a = input('Enter'
                          ' a NUMBER(INT) in range: ')
            send_data(soc, "000010", "000", my_session_id, int(a))
            t.start()
        elif OP == "010000":
            t.cancel()
            print("[SERV ERR] Sent numbers caused overflow in range distribution. Values changed.")
        elif OP == "001000":
            t.cancel()
            print("[SERV ERR] Sent numbers cannot be used to choose anything.")
            print("Left or right range changed so we could play.")
        elif OP == "000010" and RESP == "100":
            t.cancel()
            print("Server sent left range value.")
            range_left = INT
        elif OP == "000010" and RESP == "001":
            t.cancel()
            print("Server sent right range value.")
            range_right = INT

            print("Server is ready to go.")
            print("Secret number range: (" + str(range_left) + "," + str(range_right) + ").")
            s = str(input("Press 'y' to automate communication: "))
            if s == "Y" or s == "y":
                automate = True
                sr = math.floor((range_left + range_right) / 2)
                print("Sending " + str(sr) + ".")
                send_data(soc, "000100", "000", my_session_id, int(sr))
            else:
                a = input("[" + my_session_id + "] Try to guess a number ->")
                while a.isdigit() == False or (a.isdigit() == True and int(a) >= range_right) or (
                        a.isdigit() == True and int(a) <= range_left):
                    a = input("Enter a NUMBER(INT) in range: (" + str(range_left) + "," + str(range_right) + ")->")
                last_sent_int=int(a)
                send_data(soc, "000100", "000", my_session_id, int(a))
        elif OP == "000100" and RESP == "100" or (OP == "000100" and RESP == "001"):
            if automate == True:
                if RESP == "100":
                    print("[" + my_session_id + "] Secret number is smaller.")
                    range_right = sr - 1
                    sr = math.floor((range_left + range_right) / 2)
                    print("Sending " + str(sr) + ".")
                    last_sent_int=int(sr)
                    send_data(soc, "000100", "000", my_session_id, int(sr))
                if RESP =="001":
                    print("[" + my_session_id + "] Secret number is bigger.")
                    range_left = sr+1
                    sr = math.floor((range_left + range_right) / 2)
                    print("Sending " + str(sr) + ".")
                    last_sent_int = int(sr)
                    send_data(soc, "000100", "000", my_session_id, int(sr))
            if automate == False:
                if RESP == "100":
                    print("[" + my_session_id + "] Secret number is smaller than the one you entered.")
                    range_right = int(a)
                    print("[" + my_session_id + "]: (" + str(range_left) + "," + str(range_right) + ")")
                else:  # tego nie jestem pewien
                    print("[" + my_session_id + "] Secret number is bigger than the one you entered.")
                    range_left = int(a)
                    print("[" + my_session_id + "]: (" + str(range_left) + "," + str(range_right) + ")")
                a = input("[" + my_session_id + "] Try to guess a number ->")
                while a.isdigit() == False or (a.isdigit() == True and int(a) >= range_right) or (
                        a.isdigit() == True and int(a) <= range_left):
                    a = input("Enter a NUMBER(INT) in range: (" + str(range_left) + "," + str(range_right) + ")->")
                last_sent_int=int(a)
                send_data(soc, "000100", "000", my_session_id, int(a))
        elif OP == "000100" and RESP == "010":
            if last_sent_int==INT:
                print("[" + my_session_id + "] Good job! That's the number you were looking for!")
            else:
                print("[" + my_session_id + "] Another client guessed the number! Game over.")
            print("[" + my_session_id + "] Disconnecting from the server.")
            send_data(soc, "100000", "000", my_session_id, -1)
            number_correct = True
        elif OP == "111111":
            print("SERVER CLOSED.")
            number_correct = True
    soc.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        send_data(soc, "100000","000", "000", -1)
        soc.close()
