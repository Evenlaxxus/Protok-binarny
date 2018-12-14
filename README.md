# Protok-binarny
Projekt z przedmiotu Technologie Sieciowe lab7, nr zadania: 13
https://drive.google.com/file/d/17ty_VBR0Cl4ceHmgmkt3KdaaIw39pWA5/view?usp=sharing
Działanie programu wg zawartości ww. dokumentu

Komunikacja klient-serwer


K1                S                 K2
|              T1 | T2              |           \
|                 |                 |           |
Hi->             /|\             <-Hi           |
|            <-Hi | Hi->            |           |> CONNECTION INIT
ID->            | | |            <-ID           |
|            <-ID | ID->            |           /
|               | | |               |           \
NUM->           | | .               |           |
|               | | .               |           |
|               . | .               |           |> NUMBERS INIT
|               . | .           <-NUM           |
|               | | |               |           |
|            <-L1 | L1->            |           |
|            <-L2 | L2->            |           /
GUESS->        |  | |         <-GUESS           \
|         <-RESP  | RESP->          |           |
                  .                             |
               Guessing                         |> THE GAME
                  .                             |
                  .                             |
|       <-GUESSED | GUESSED->       |           /
BYE->           | | |         <-BYE |           \
CONNECTION_END  \ | /           CONNECTION_END  /CLOSING CONNECTION
              

Każdy z nowych połączeń wiąże się z utworzeniem nowego wątku zamykanego po zakończonej sesji.

Segment CONNECTION_INIT to seria komunikatów uruchamiających program.
>Klient nawiązuje połączenie używając komunikatu HI
>Serwer odpowiada na komunikat HI
  * Odrzuca połączenie w przypadku, gdy l.połączonych.klientów>2
  * Akceptuje połączenie (do gry potrzebnych jest 2 uczestników)
>Klient prosi serwer o nadanie mu unikatowego identyfikatora sesji.
>Serwer wysyła dany identyfikator sesji, oczekuje na dalsze instrukcje


Segment NUMBERS_INIT jest odpowiedzialny za przygotowanie zmiennych potrzebnych do gry.
*W tym segmencie jeden klient może wysłać tylko jedną cyfrę z przedziału (0-1048575)*
Jako, że komunikacja oparta jest o wątki wymagane było wprowadzenie pewnych norm:
  >Wątek, który jako pierwszy otrzyma cyfrę od klienta umieszcza ją w zewnętrznym kontenerze i przechodzi w stan uśpienia z pomocą funkcji Event
  >Wątek, który jako drugi otrzyma cyfrę w zewnętrznych kontenerach umieszcza:
    *otrzymaną cyfrę
    *obliczone przedziały liczby losowanej
    *liczbę do odgadnięcia
  następnie budzi wątek pierwszy do dalszego działania.
  Interpretacja graficzna problemu:
          T1        Kontenery_zewnętrzne    T2
          |                 |               |
 Cyfra->  |                 |               |
          | Cyfra->         |               |
       event.clear()        1               |
       event.wait()         1               |
          .                 1         <-Cyfra
          .                 2           <obliczenia>
          .                 2         <-L1  |
          .                 3         <-L2  |
          .                 4         <-SECRET NUMBER
          .                 5           event.set()
          |                 5               |
                  ...           ...
   >Podane cyfry, które spowodują błędy uniemożliwiające grę są naprawiane i komunikowane użytkownikowi.
   >Po wysłaniu obu przedziałów (L1,L2 z kontenera) rozpoczynamy segment kolejny

THE GAME
>Klienci otrzymują przedział (L1,L2), w którym zawiera się liczba.
>Każdy strzał zawęża obszar poszukiwań informując o relacji wprowadzonej liczby z sekretną (większe, mniejsze)
>Gra kończy się w momencie, gdy jeden z użytkowników odgadnie tajną liczbę.



Reguły połączenia:
>Serwer obsługuje tylko dwójkę graczy, każdy kolejny gracz zostanie poinformowany o "zamknietych drzwiach".
>Drzwi zamknięte są w dwóch przypadkach
  *liczba graczy==2
  *liczba graczy<2 ale rozgrywka nadal trwa
  -koniec rozgrywki definiowany jest na dwa sposoby:
    ::gracz odgadł tajną liczbę
    ::obydwu graczy opuści rozgrywkę
   w przypadku odejścia jednego z graczy rozgrywka nadal trwa
 >Po odgadnięciu liczby gracze informują serwer o zerwaniu połączenia i zamykają gniazdo.
 
 Gracz może odejść w każdym momencie rozgrywki wysyłając przerwanie klawiaturowe CTRL+C.
 
 Tablica komunikatów:
 
 Dla ułatwienia czytelności:
 <- "odebranie"
 -> "wysłanie"
 
   OP   | RESPONSE| OP TRANSLATE|                                    Serwer                  |             Klient
 000000 |   ---   | HI          | -> odpowiedzi na zapytanie klienta, nawiązanie połączenia. | -> zapytania klienta o nawiązanie połączenia 
 000001 |   ---   | ID          | -> ID                                                      | -> prośby udzielenia ID
 000010 |   ---   | NUMBERS_INIT| <- cyfry L                                                 | -> cyfry L
 000010 |   ---   | NUMBERS_INIT| -> prawej wartości przedziału                              | <- prawej wartości przedziału
 000010 |   ---   | NUMBERS_INIT| -> lewej wartości przedziału                               | <- lewej wartości przedziału
 000100 |   ---   | THE_GAME    | ->Podana liczba jest za duża                               | <- danej informacji, zawężenie przedziału
 000100 |   ---   | THE_GAME    | ->Podana liczba jest za mała                               | <- danej informacji, zawężenie przedziału
 000100 |   ---   | THE_GAME    | -> informacji o trafieniu                                  | <- informacji o trafieniu
 001000 |   ---   | RANGE_ERROR | -> informacji o wprowadzeniu zmian do tworzonego przedziału| <- informacji o błędzie
 010000 |   ---   | OVERFLOW_ER | -> informacji o przepełnieniu wartości przedziału          | <- informacji o błędzie
 100000 |   ---   | DISCONNECT  | <- informacji o rozłączeniu klienta                        | -> wiadomości pożegnalnej
 111111 |   ---   | DOOR_CLOSED | -> informacji o "zamkniętych drzwiach"                     | <- wiadomości o zamkniętych drzwiach
 
 
 Wysłanie informacji o błędzie (RANGE_ERROR\OVERFLOW_ERROR) zawsze wiąże się z wprowadzeniem zmian.
 
 Segment przesyłanych wygląda następująco:
 
 a) w przypadku, gdy niepotrzebne jest przesłanie cyfry:
   |OPERACJA|ODPOWIEDŹ|ID|
   |  6b    |   3b    |3b|
 b) w przypadku, gdy przesłanie cyfry jest wymagane (instrukcje operacji NUMBERS_INIT oraz THE_GAME)
   |OPERACJA|ODPOWIEDŹ|ID|CYFRA|
   |  6b    |   3b    |3b| 20b |
 
 
 


UWAGA: W IMPLEMENTACJI UŻYTO NIESTANDARDOWEJ BIBLIOTEKI BITSTRING: https://pythonhosted.org/bitstring/
