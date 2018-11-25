# VERSION 1: NO COMMENTS AND DEBUG THRASH
# TODO -> ten sprawdzacz co Rafał chce (V.1.1)
# TODO -> keyboard interrupt closes program (V 1.05)

# Merlin Merlin Merlin Merlin Merlin Merlin Merlin.

import socket
import sys
import traceback
import struct
import random
import re
from threading import Thread


client_counter = 0

id_list = ["001", "010", "011", "111", "110", "100", "000"]
random.shuffle(id_list)



def main():
    global client_counter
    global id_list
    start_server()


def encapsulation(id, operations, answer):
    x = "0000" + id + answer + operations
    byte1 = int(x[:8], 2)
    byte2 = int(x[8:], 2)
    return byte1, byte2


def start_server():
    global client_counter
    host = "127.0.0.1"
    port = 8888  # arbitrary non-privileged port

    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                   1)  # SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without waiting for its natural timeout to expire
    print("Socket created")

    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()

    soc.listen(5)  # queue up to 5 requests
    print("Socket now listening")
    print("Server ready.")

    # infinite loop- do not reset for every requests
    while True:
        connection, address = soc.accept()
        ip, port = str(address[0]), str(address[1])
        client_counter = client_counter + 1
        try:
            Thread(target=client_thread, args=(connection, ip, port)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()

    soc.close()


def packet_parser(unpacked):
    s_unpacked = str(unpacked)
    regex_tuple = re.findall(r'\d{1,3}', s_unpacked)
    byte1 = int(regex_tuple[0])
    byte2 = int(regex_tuple[1])
    return byte1, byte2


def deencapsulaton(byte1, byte2):
    get_bin = lambda x, n: format(x, 'b').zfill(n)
    binary_byte1 = get_bin(byte1, 8)
    binary_byte2 = get_bin(byte2, 8)
    byte_stream = binary_byte1 + binary_byte2
    id = byte_stream[4:7]
    answer = byte_stream[7:10]
    operations = byte_stream[10:]
    return id, answer, operations


def client_thread(connection, ip, port):
    global id_list
    which_number = 1
    SECRET_NUMBER = 0
    a = 0
    b = 0
    global client_counter
    is_active = True
    session_id = id_list.pop(0)
    while is_active:
        # otrzymuje hello
        reg_tuple = packet_parser(receive_data(connection))
        byte1 = reg_tuple[0]
        byte2 = reg_tuple[1]
        id, answer, operations = deencapsulaton(int(byte1), int(byte2))
        if operations == "000000" and client_counter >= 3:
            print("["+session_id+"] Someone is trying to get in, we are closed now")
            send_data(connection, session_id, "111111", "000")  # sending ERR and closing
        elif operations == "000000" and client_counter < 3:
            print("["+session_id+"] Someone's trying to connect! Hello!")
            send_data(connection, session_id, "000000", "000")  # sending HELLO
        elif operations == "000001" and client_counter < 3:
            print("["+session_id+"] Client is asking for ID. Sending one.")
            send_data(connection, session_id, "000001", session_id)  # sending ID
        elif operations == "000010" and client_counter < 3:
            if which_number == 1:
                a = int(answer, 2)
                which_number = which_number + 1
                print('%s%d' % ("[" + session_id + "] Client [ID:" + id + "] has sent me a number ", a))
            else:  # which_number==2:
                b = int(answer, 2)
                print ('%s%d' % ("[" + session_id + "] Client [ID:" + id + "] has sent me a number: ", b))
                L1 = a - b
                if L1 < 0:
                    L1 = 0
                L2 = a + b
                if L2 > 7:
                    L2 = 7
                SECRET_NUMBER = random.randint(L1, L2)
                print('%s%d' % ("[" + session_id + "] My secret number is: ",SECRET_NUMBER))
        elif operations == "000100" and client_counter < 3:
            c = int(answer, 2)
            if c == SECRET_NUMBER:
                send_data(connection, session_id, "001000", "000")
                print("["+session_id+"] Client [ID:" + id + "] guessed a number")  # insert number
            else:
                send_data(connection, session_id, "010000", "000")
                print("["+session_id+"] Client [ID:" + id + "] missed a number")  # insert number
        elif operations == "100000" and client_counter < 3:
            print("["+session_id+"] Client [ID:" + id + "] disconnected")
            id_list.insert(0, session_id)
            client_counter = client_counter - 1
            connection.close()
            is_active = False
        elif operations == "100000" and client_counter >= 3:
            id_list.insert(0, session_id)
            client_counter = client_counter - 1
            connection.close()
            is_active = False


def send_data(connection, id, operations, answer):
    packer = struct.Struct('BB')
    byte_1, byte_2 = encapsulation(id, operations, answer)
    values = (byte_1, byte_2)
    packed_data = packer.pack(*values)
    connection.sendall(packed_data)


def receive_data(connection):
    unpacker = struct.Struct('BB')
    data = connection.recv(unpacker.size)
    unpacked_data = unpacker.unpack(data)
    return unpacked_data


if __name__ == "__main__":
    main()
