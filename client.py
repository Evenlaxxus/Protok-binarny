# VERION 1: NO COMMENTS AND USELESS DEBUG

# TODO -> ten sprawdzacz co Rafał chce (V.1.1)
# TODO -> keyboard interrupt closes program (V 1.05)

import socket
import sys
import struct
import re

data_structure = struct.Struct('BBH')


def receive_data(sock):
    data = sock.recv(data_structure.size)
    s_unpacked = str(data_structure.unpack(data))
    reg_tuple = re.findall(r'\d{1,5}', s_unpacked)
    get_bin = lambda x, n: format(x, 'b').zfill(n)
    binary_byte1 = get_bin(int(reg_tuple[0]), 8)
    binary_byte2 = get_bin(int(reg_tuple[1]), 8)
    byte_stream = binary_byte1 + binary_byte2
    OP = byte_stream[:6]
    RESP = byte_stream[6:9]
    ID = byte_stream[9:12]  # i od 12-16 jest 0000
    INTEGER = int(reg_tuple[2])  # a tutaj normalnie jest int
    return OP, RESP, ID, INTEGER  # i już, zamiast trzech mam jedną


def send_data(sock, OP, RESP, ID, INTEGER):
    x = OP + RESP + ID + "0000"  # dopełnienie do 2 bajtów
    byte1 = int(x[:8], 2)  # bo to trzeba przerobić na liczby
    byte2 = int(x[8:], 2)  # i to też
    values = (byte1, byte2, INTEGER)  # przesyłana zawartość
    packed_data = data_structure.pack(*values)
    sock.sendall(packed_data)  # tu jest wszystko ogarnięte


soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_session_id = 0


def main():
    # s= input("Server ip:")
    global get_bin, my_session_id
    host = "127.0.0.1"
    port = 8888
    range_left = 0
    range_right = 0
    try:
        soc.connect((host, port))
    except:
        print("Connection error")
        sys.exit()

    send_data(soc, "000000", "000", "000", 0)
    number_correct = False
    my_session_id = "000"
    while not number_correct:
        OP, RESP, ID, INT = receive_data(soc)
        if OP == "111111":
            print("Server is full, better check later.")
            send_data(soc, "100000", "000", my_session_id, 0)
            break
        elif OP == "000000":
            print("Server agreed for connection. Requesting id.")
            send_data(soc, "000001", "000", my_session_id, 0)
        elif OP == "000001":
            print("Server sent me a session ID: " + ID)
            my_session_id = ID
            a = input("[" + my_session_id + "] I'm going to send a number to server, input number 0-65535 ->")
            while a.isdigit() == False or (a.isdigit() == True and int(a) > 65535):
                a = input('Enter a NUMBER in range: ')
            send_data(soc, "000010", "000", my_session_id, int(a))

            a =input("[" + my_session_id + "] I'm going to send another number to server, input number 0-65535 ->")
            while a.isdigit() == False or (a.isdigit() == True and int(a) > 65535):
                a = input('Enter a NUMBER in range: ')
            send_data(soc, "000010", "000", my_session_id, int(a))
        elif OP == "010000":
            print("[ERR] Sent numbers caused overflow in range distribution. Values changed")
            # if INT > 1:
            #     print("Right value set to 65535.")
            # else:
            #     print("Left value set to 0.")
        elif OP=="010001":
            print("[ERR] Sent numbers cannot be used to choose anything.")
            print("Left or right range changed so we could play.")
        elif OP == "000010" and RESP == "100":
            print("Server sent left range value.")
            range_left = INT
        elif OP == "000010" and RESP == "001":
            print("Server sent right range value.")
            range_right = INT
            print("Server is ready to go, enter your first number")
            print("Secret number range: (" + str(range_left) +","+ str(range_right) + ")")
            a=input("[" + my_session_id + "] Try to guess a number ->")
            while a.isdigit() == False or (a.isdigit() == True and int(a) >=range_right) or (a.isdigit()==True and int(a)<=range_left):
                a = input("Enter a NUMBER in range: (" + str(range_left) +","+ str(range_right) + ")->")
            send_data(soc, "000100", "000", my_session_id,int(a))
        elif OP == "000100" and RESP == "100" or (OP == "000100" and RESP == "001"):
            if RESP == "100":
                print("[" + my_session_id + "] Secret number is smaller than the one you entered.")
                range_right = int(a)
                print("[" + my_session_id+"]: (" + str(range_left) +","+ str(range_right) + ")->")
            else:  # tego nie jestem pewien
                print("[" + my_session_id + "] Secret number is bigger than the one you entered.")
                range_left = int(a)
                print("[" + my_session_id+"]: (" + str(range_left) + "," + str(range_right) + ")->")
            a=input("[" + my_session_id + "] Try to guess a number ->")
            while a.isdigit() == False or (a.isdigit() == True and int(a) >=range_right) or (a.isdigit() == True and int(a)<=range_left):
                a = input("Enter a NUMBER in range: (" + str(range_left) +","+ str(range_right) + ")->")
            send_data(soc, "000100", "000", my_session_id,int(a))
        elif OP == "000100" and RESP == "010":
            print("[" + my_session_id + "] Good job! That's the number you were looking for!")
            print("[" + my_session_id + "] Disconnecting from the server")
            send_data(soc, "100000", "000", my_session_id,int(a))
            number_correct = True
        elif OP == "111111":
            print("SERVER CLOSED")
            number_correct = True
    soc.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        send_data(soc, my_session_id, "100000", "000")
        soc.close()
