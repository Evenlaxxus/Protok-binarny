# Merlin Merlin Merlin Merlin Merlin Merlin Merlin.
import socket
import sys
import traceback
import random
from threading import Thread, Event
from bitstring import BitArray

taken = 0

id_list = ["001", "010", "011", "111", "110", "100", "000"]
random.shuffle(id_list)
senderr = [False, False]
range_numbers = []
SECRET_NUMBER = 0
ev = Event()
numbers = []
number_guessed = False


def send_data(sock, OP, RESP, ID, INTEGER):
    get_bin = lambda x, n: format(x, 'b').zfill(n)
    sock.sendall(BitArray('0b' + OP + RESP + ID + get_bin(INTEGER, 20)).tobytes())


def receive_data(sock):
    x = BitArray(sock.recv(4096)).bin
    OP = x[:6]
    RESP = x[6:9]
    ID = x[9:12]
    INTEGER = int(x[12:], 2)
    return OP, RESP, ID, INTEGER


game_running = False


def client_thread(connection, ip, port):
    global numbers, taken, SECRET_NUMBER, senderr, number_guessed, game_running
    global taken, id_list
    is_active = True
    session_id = id_list.pop(0)
    print("Session ID: " + session_id + " start.")
    while is_active:
        OP, RESP, ID, INT = receive_data(connection)
        if OP == "000000":
            if game_running:
                print("[" + session_id + "] is trying to get in. Game already started.")
                send_data(connection, "111111", "000", session_id, 0)
            elif taken >= 3:
                print("[" + session_id + "] Someone is trying to get in, server is full.")
                send_data(connection, "111111", "000", session_id, 0)
            elif taken < 3 and not game_running:
                print("[" + session_id + "] Someone is trying to connect. Hello!")
                send_data(connection, "000000", "000", session_id, 0)
        elif OP == "000001":  # taken nie jest potrzebny, bo go kod wyżej nie przepuści
            print("[" + session_id + "] Client is asking for ID. Sending...")
            print("Waiting for next move from client.")
            send_data(connection, "000001", "000", session_id, 0)
            if taken == 2:
                game_running = True
        elif OP == "000010":  ##przyjmuje cyferki
            print("[" + session_id + "] Client [ID:" + ID + "] has sent me a number: " + str(INT) + ".")
            b = INT
            numbers.append(b)
            if len(numbers) < 2:
                ev.clear()
                print("Waiting for second client to enter a number.")
                ev.wait()
            elif len(numbers) == 2:
                ev.set()
                ev.clear()
                ev.wait()  # jeden śpi, drugi pracuje
            else:
                print("ERR")
            if len(range_numbers) < 2:
                if numbers[0] > numbers[1]:
                    range_numbers.append(numbers[0] - numbers[1])
                else:
                    range_numbers.append(numbers[1] - numbers[0])
                range_numbers.append(numbers[0] + numbers[1])
                if range_numbers[1] > 1048575:
                    range_numbers[1] = 1048575
                    senderr[0] = True
                if range_numbers[0] == range_numbers[1]:
                    range_numbers[0] = 0
                    if not senderr[0]:
                        senderr[0] = True
                if (range_numbers[1] - range_numbers[0] < 2):
                    if range_numbers[0] == 0:
                        range_numbers[1] = range_numbers[1] + 2
                    if range_numbers[1] == 1048575:
                        range_numbers[0] = range_numbers[0] - 2
                SECRET_NUMBER = random.randint(range_numbers[0] + 1, range_numbers[1] - 1)  # zeby byl otwarty przedzial
                print('%s%d%s' % ("[" + session_id + "] My secret number is: ", SECRET_NUMBER, "."))
            ev.set()
            if senderr[0]:
                send_data(connection, "010000", "000", session_id, 0)
                print("Sending info about overflow.")
            if senderr[1]:
                print("Sending info about changes.")
                send_data(connection, "001000", "000", session_id, 0)
            send_data(connection, "000010", "100", ID, range_numbers[0])  # lewa wartość przedziału
            print("Left value sent")
            send_data(connection, "000010", "001", ID, range_numbers[1])  # prawa wartość przedziału
            print("Both values sent")
        elif "000100" == OP:  # tutaj klient będzie miał drugą pętlę
            # odbierz daną
            if number_guessed == False:
                if INT < SECRET_NUMBER:
                    send_data(connection, "000100", "001", ID, 0)  # resp=001
                    print("[" + session_id + "] Client [ID:" + ID + "] sent a number too small.")
                elif INT > SECRET_NUMBER:
                    send_data(connection, "000100", "100", ID, 0)  # resp=100
                    print("[" + session_id + "] Client [ID:" + ID + "] sent a number too big.")
                else:  # c==secretnum
                    send_data(connection, "000100", "010", ID, SECRET_NUMBER)  # resp=010
                    print("[" + session_id + "] Client [ID:" + ID + "] guessed a number.")
                    range_numbers.clear()
                    game_running = False
                    senderr = [False, False]
                    numbers.clear()
                    number_guessed = True
            else:
                send_data(connection, "000100", "010", ID, SECRET_NUMBER)  # resp=010
                print("[" + session_id + "] Client [ID:" + ID + "] guessed a number.")
        elif OP == '100000' and taken < 3:
            print("[" + session_id + "] Client [ID:" + session_id + "] disconnected.")
            id_list.insert(0, session_id)
            taken = taken - 1
            if taken == 0:
                game_running = False
            connection.close()
            is_active = False
        elif OP == "100000" and taken >= 3:
            id_list.insert(0, session_id)
            taken = taken - 1
            connection.close()
            is_active = False


def main():
    global taken
    global id_list, numbers
    start_server()


def start_server():
    global taken, numbers

    host = "127.0.0.1"
    port = 8888

    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                   1)
    print("Socket created")

    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()

    soc.listen(5)
    print("Socket now listening")
    print("Server ready.")

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
