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

taken = 0

id_list = ["001", "010", "011", "111", "110", "100", "000"]
random.shuffle(id_list)

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


# albo pozbędę sie tego pierwszego łajla albo nasza ramka cały czas będzie miała jedną wartość, trzeba zrobić dwie odnogi

def main():
    global taken
    global id_list
    start_server()


def start_server():
    global taken
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
        taken = taken + 1
        try:
            Thread(target=client_thread, args=(connection, ip, port)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()

    soc.close()


if __name__ == "__main__":
    main()


# wcześniejsza kolejność: ID,OP,RESP
# obecna kolejność: OP,RESP,ID
# nowy client thread, odpala, nadaje id, podaje ten przedział a później odpowiada polem odpowiedzi
# WARNING: kolejność danych: OPERACJE, ODPOWIEDZI, ID SESJI, WARTOŚĆ LICZBOWA (jeśli potrzebna)
# for sure będzie while w while'u, bo jeden handluje całe połączenie a drugi będzie działał dopóki nie zgadnie
# ----------------------------------------------------------------------------
# todo-> usuń to ip i port, useless shit
# todo-> dwa różne wysyłania, to z intem i to bez, wtedy wszędzie poza przekazywaniem numerów byłby jeden, a dalej drugi,
# przerwanie klienta wtedy z przyjęciem inta i info (klient przerwał połączenie) a drugie bez inta (klient się grzecznie rozłączył)
# todo-> w kliencie trzeba obsługiwać znak i rozmiar
# todo->change client counter to "taken"

def client_thread(connection, ip, port):
    global id_list, taken
    SECRET_NUMBER = 0
    a = 0
    b = 0
    is_active = True
    second_number = False
    session_id = id_list.pop(0)
    print("Session ID: " + session_id + " start.")
    while is_active:
        OP, RESP, ID, INT = receive_data(connection)
        if OP == "000000" and taken >= 3:
            print("[" + session_id + "] Someone is trying to get in, server is full.")
            send_data(connection, "111111", "000", session_id, 0)
        elif OP == "000000" and taken < 3:
            print("[" + session_id + "] Someone is trying to connect. Hello!")
            send_data(connection, "000000", "000", session_id, 0)
        elif OP == "000001":  # taken nie jest potrzebny, bo go kod wyżej nie przepuści
            print("[" + session_id + "] Client is asking for ID. Sending...")
            send_data(connection, "000001", session_id, session_id, 0)
        elif OP == "000010":
            if second_number == False:
                print(
                    "[" + session_id + "] Client [ID:" + ID + "] has sent me a number: " + INT + ".")  ##to albo to z formatem %s%d
                a = INT
                second_number = True
            else:
                print(
                    "[" + session_id + "] Client [ID:" + ID + "] has sent me a number: " + INT + ".")  ##to albo to z formatem %s%d
                b = INT
                L1 = a - b
                L2 = a + b
                if (L1 < 0):
                    L1 = 0
                    send_data(connection, "010000", "000",
                              session_id,
                              0)  # jesli podana wartość przedziału jest mniejsza, to podaje flage out of range
                if (L2 > 65535):
                    L2 = 65535
                    send_data(connection, "010000", "000", session_id, L2)
                SECRET_NUMBER = random.randint(L1, L2)
                print('%s%d' % ("[" + session_id + "] My secret number is: ", SECRET_NUMBER))
                send_data(connection, OP, RESP, ID, L1)  # lewa wartość przedziału
                send_data(connection, OP, RESP, ID, L2)  # prawa wartość przedziału
        elif OP == "000100":  # tutaj klient będzie miał drugą pętlę
            # odbierz daną
            if INT < SECRET_NUMBER:
                send_data(connection, OP, "001", ID, INT)  # resp=001
                print("[" + session_id + "] Client [ID:" + ID + "] sent a number too small.")
            elif INT > SECRET_NUMBER:
                send_data(connection, OP, "100", ID, INT)  # resp=100
                print("[" + session_id + "] Client [ID:" + ID + "] sent a number too big.")
            else:  # c==secretnum
                send_data(connection, OP, "010", ID, INT)  # resp=010
                print("[" + session_id + "] Client [ID:" + ID + "] guessed a number.")
        # todo-> do komunikatów wszystkich kropki dać
        elif OP == '100000' and taken < 3:
            print("[" + session_id + "] Client [ID:" + ID + "] disconnected.")
            id_list.insert(0, session_id)
            taken = taken - 1
            connection.close()
            is_active = False
        elif OP == "100000" and taken >= 3:
            id_list.insert(0, session_id)
            taken = taken - 1
            connection.close()
            is_active = False
