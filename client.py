#VERION 1: NO COMMENTS AND USELESS DEBUG

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
my_session_id=0

def main():
    s= input("Server ip:")
    global get_bin, my_session_id
    host = s
    port = 8888

    try:
        soc.connect((host, port))
    except:
        print("Connection error")
        sys.exit()

    send_data(soc, "000", "000000", "000")
    number_correct=False
    while not number_correct:
        #
        reg_tuple=packet_parser(receive_data(soc))
        byte1=reg_tuple[0]
        byte2=reg_tuple[1]
        id,answer,operation=deencapsulaton(int(byte1),int(byte2))
        if operation=="111111":
            print("Server is full, better check later.")
            send_data(soc, "000","100000", "000")
            break
        elif operation=="000000":
            print("Server agreed for connection. Requesting id.")
            send_data(soc,"000","000001","000")
        elif operation=="000001":
            print("Server sent me a session ID: "+answer)
            my_session_id=answer
            inp = int(input("["+my_session_id+"] I'm going to send a number to server, input number 0-7 ->"))
            if inp>7:
                inp=7
            elif inp<0:
                inp=0
            get_bin = lambda x, n: format(x, 'b').zfill(n)
            inp_bin=get_bin(inp,3)
            send_data(soc,my_session_id,"000010",inp_bin)
            inp = int(input("["+my_session_id+"] I'm going to send another number to server, input number 0-7 ->"))
            if inp > 7:
                inp = 7
            elif inp < 0:
                inp = 0
            inp_bin=get_bin(inp,3)
            send_data(soc, my_session_id, "000010", inp_bin)

            input_good=False
            while not input_good:
             inp= int(input("["+my_session_id+"] Try to guess a number ->"))
             if inp<0 or inp>7:
                 print("That's definitely not that, try to use a number in range")
             else:
                 input_good=True
                 inp_bin=get_bin(inp,3)
                 send_data(soc,my_session_id, "000100", inp_bin)
        elif operation=="010000":
            input_good=False
            print("[" + my_session_id + "] Bad luck! Let's try another one.")
            while not input_good:
                inp = int(input("[" + my_session_id + "] Guess a number ->"))
                if inp<0 or inp>7:
                    print("That's definitely not that, try to use a number in range")
                else:
                    input_good=True
                    inp_bin=get_bin(inp,3)
                    send_data(soc, my_session_id, "000100", inp_bin)
        elif operation=="001000":
            print("["+my_session_id+"] Good job! That's the number you were looking for!")
            print("["+my_session_id+"] Disconnecting from the server")
            send_data(soc, my_session_id,"100000","000")
            number_correct=True
        elif operation=="111111" and id=="111" and answer=="111":
            print("SERVER CLOSED")
            number_correct=True
    soc.close()






if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        send_data(soc, my_session_id, "100000", "000")
        soc.close()