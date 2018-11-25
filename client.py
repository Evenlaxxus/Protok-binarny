#VERION 1: NO COMMENTS AND USELESS DEBUG

# TODO -> ten sprawdzacz co Rafał chce (V.1.1)
# TODO -> keyboard interrupt closes program (V 1.05)

import socket
import sys
import struct
import re


def encapsulation(id, operations, answer):
    x = "0000" + id + answer + operations
    byte1 = int(x[:8], 2)
    byte2 = int(x[8:], 2)
    return byte1, byte2

def packet_parser(unpacked):
    s_unpacked=str(unpacked)
    regex_tuple=re.findall(r'\d{1,3}',s_unpacked)
    return regex_tuple

def deencapsulaton(byte1, byte2):
    get_bin = lambda x, n: format(x, 'b').zfill(n)
    binary_byte1 = get_bin(byte1, 8)
    binary_byte2 = get_bin(byte2, 8)
    byte_stream = binary_byte1 + binary_byte2
    id = byte_stream[4:7]
    answer = byte_stream[7:10]
    operations = byte_stream[10:]
    return id, answer, operations

def send_data(connection, id, operations, answer):
    packer=struct.Struct('BB')
    values=(encapsulation(id,operations,answer))
    packed_data=packer.pack(*values)
    connection.sendall(packed_data)

def receive_data(connection):
    unpacker=struct.Struct('BB')
    data=connection.recv(unpacker.size)
    unpacked_data=unpacker.unpack(data)
    return unpacked_data

def main():
    global get_bin
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8888

    try:
        soc.connect((host, port))
    except:
        print("Connection error")
        sys.exit()

    send_data(soc, "000", "000000", "000")
    number_correct=False
    while not number_correct:

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
            print("[" + my_session_id + "]Bad luck! Let's try another one.")
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
    soc.close()






if __name__ == "__main__":
    main()