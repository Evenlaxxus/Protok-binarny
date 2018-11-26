# VERSION 1: NO COMMENTS AND DEBUG THRASH
# TODO -> ten sprawdzacz co Rafał chce (obsolete teraz)
# TODO -> keyboard interrupt closes program (może kiedyś)
# TODO -> kolejność według rozpiski, w polu odpowiedzi są tylko odpowiedzi serwera, dodatkowe to są dane 32 bity do unsigned inta, serwer ma przesyłać przedział, info o tym, że przedział<0 i ustawienie przedziału na 0
# Merlin Merlin Merlin Merlin Merlin Merlin Merlin.

#############################################
#   ->Serwer inicjuje działanie, powiązuje socket i nasłuchuje nadchodzących połączeń (do 5 w kolejce)
#   ->Gdy połączenie zostaje nawiązane uruchamia nowy wątek i obsługuje go w odpowiedni sposób
#   ->Wysyłanie paczki: encapsulation->send_data
#   ->Odbieranie paczki: receive data->packet_parser->deencapsulation
#############################################
# * do enkapsulacji i dekapsulacji użyto funkcji klasy Struct() pakującej do ustalonego dla nas formatu, czy cos
# *https://docs.python.org/3/library/struct.html
#
#
#
#############################################
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
            print("[" + session_id + "] Someone is trying to get in, we are closed now")
            send_data(connection, session_id, "111111", "000")  # sending ERR and closing
        elif operations == "000000" and client_counter < 3:
            print("[" + session_id + "] Someone's trying to connect! Hello!")
            send_data(connection, session_id, "000000", "000")  # sending HELLO
        elif operations == "000001" and client_counter < 3:
            print("[" + session_id + "] Client is asking for ID. Sending one.")
            send_data(connection, session_id, "000001", session_id)  # sending ID
        elif operations == "000010" and client_counter < 3:
            if which_number == 1:
                a = int(answer, 2)
                which_number = which_number + 1
                print('%s%d' % ("[" + session_id + "] Client [ID:" + id + "] has sent me a number ", a))
            else:  # which_number==2:
                b = int(answer, 2)
                print('%s%d' % ("[" + session_id + "] Client [ID:" + id + "] has sent me a number: ", b))
                L1 = a - b
                if L1 < 0:
                    L1 = 0
                L2 = a + b
                if L2 > 7:
                    L2 = 7
                SECRET_NUMBER = random.randint(L1, L2)
                print('%s%d' % ("[" + session_id + "] My secret number is: ", SECRET_NUMBER))
        elif operations == "000100" and client_counter < 3:
            c = int(answer, 2)
            if c == SECRET_NUMBER:
                send_data(connection, session_id, "001000", "000")
                print("[" + session_id + "] Client [ID:" + id + "] guessed a number")  # insert number
            else:
                send_data(connection, session_id, "010000", "000")
                print("[" + session_id + "] Client [ID:" + id + "] missed a number")  # insert number
        elif operations == "100000" and client_counter < 3:
            print("[" + session_id + "] Client [ID:" + id + "] disconnected")
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



#nowy client thread, odpala, nadaje id, podaje ten przedział a później odpowiada polem odpowiedzi
#WARNING: kolejność danych: OPERACJE, ODPOWIEDZI, ID SESJI, WARTOŚĆ LICZBOWA (jeśli potrzebna)
#for sure będzie while w while'u, bo jeden handluje całe połączenie a drugi będzie działał dopóki nie zgadnie

def new_client_thread(connection, ip, port):
    is_active=True
    session_id=id_list.pop(0)
    print("Session ID: "+session_id+" start.")
    while is_active:
        #odbierz dane, muszę przerobić odbieranie, żeby brał inta
        if OP =="000000" and taken>=3:
            print ("["+session_id+"] Someone is trying to get in, server is full")
            send_data(OP,RESP,ID,INTEGER)
        elif OP=="000000" and taken<3:
            print("[" + session_id + "] Someone is trying to connect. Hello!")
            send_data(OP,RESP,ID,INTEGER)
        elif OP=="000001": #taken nie jest potrzebny, bo go kod wyżej nie przepuści
            print("[" + session_id + "] Client is asking for ID. Sending...")
            send_data(OP,RESP,ID,INTEGER)
        elif OP=="000010":
            #a=INTEGER
            if second_number==False:
                print("[" + session_id + "] Client [ID:" + ID + "] has sent me a number: "+ INTEGER+".") ##to albo to z formatem %s%d
                #KONTENER_A=INTEGER
            else:
                print("[" + session_id + "] Client [ID:" + ID + "] has sent me a number: " + INTEGER + ".")  ##to albo to z formatem %s%d
                #KONTENER_B=INTEGER
                #KONTENER_C=A-B
                #KONTENER B+=A
                #SECRET_NUMBER=random.randint(KONTENER_C, KONTENER_B)
                print('%s%d' % ("[" + session_id + "] My secret number is: ", SECRET_NUMBER))
                send_data(OP,RESP,ID,INTEGER) #lewa wartość przedziału
                send_data(OP,RESP,ID,INTEGER) #prawa wartość przedziału
        elif OP=="000100": #tutaj klient będzie miał drugą pętlę
            #odbierz daną
            c=int(INTEGER,2) #wstępnie tak
            if c<SECRET_NUMBER:
                send_data(OP,RESP,ID,INTEGER) #resp=001
                print("[" + session_id + "] Client [ID:" + id + "] sent a number too small")
            elif c>SECRET_NUMBER:
                send_data(OP,RESP,ID,INTEGER) #resp=100
                print("[" + session_id + "] Client [ID:" + id + "] sent a number too big")
            else: #c==secretnum
                send_data(OP,RESP,ID,INTEGER) #resp=010
                print("[" + session_id + "] Client [ID:" + id + "] guessed a number")
    #todo-> do komunikatów wszystkich kropki dać
            elif OP == "100000" and taken < 3:
                print("[" + session_id + "] Client [ID:" + id + "] disconnected")
                id_list.insert(0, session_id)
                client_counter = taken - 1
                connection.close()
                is_active = False
            elif operations == "100000" and taken >= 3:
                id_list.insert(0, session_id)
                client_counter = taken - 1
                connection.close()
                is_active = False


