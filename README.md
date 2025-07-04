# visionect_joan
Niestandardowy dodatek wyświetla podstawowe informacje tableta Joan 6 w Home Assistant

Bateria
Całkowita pamięć
Czas pracy
Interwał odświeżania
Napięcie baterii
Status
Sygnał WiFi
Temperatura
itp.

Instalacja
Integrację można zainstalować na dwa sposoby: przez HACS (zalecane) lub manualnie.

Instalacja przez HACS (zalecana metoda)
Upewnij się, że w Twoim Home Assistant jest zainstalowany HACS.
Przejdź do HACS -> Integracje.
Kliknij menu z trzema kropkami w prawym górnym rogu i wybierz "Niestandardowe repozytoria".
Wklej adres URL tego repozytorium, wybierz kategorię "Integracja" i kliknij "Dodaj".
Wyszukaj na liście integrację "Visionect Joan" i kliknij "Zainstaluj".
Uruchom ponownie Home Assistant, aby zastosować zmiany.

Instalacja manualna
Przejdź do strony Releases (Wydania) na GitHubie.
Pobierz najnowsze wydanie, klikając na plik visionect-joan.zip (lub Source code (zip)).
Rozpakuj pobrane archiwum.
Skopiuj cały katalog visionect_joan (ten, w którym znajduje się m.in. plik manifest.json) do folderu custom_components w głównym katalogu konfiguracyjnym Twojego Home Assistant.
Ostateczna ścieżka powinna wyglądać tak:  \config\custom_components\visionect_joan
Uruchom ponownie Home Assistant.

Konfiguracja
Po poprawnej instalacji i ponownym uruchomieniu Home Assistant:
Przejdź do Ustawienia > Urządzenia i usługi.
Kliknij przycisk "+ Dodaj integrację" w prawym dolnym rogu.
Wyszukaj na liście "Visionect Joan" i kliknij, aby rozpocząć konfigurację.
