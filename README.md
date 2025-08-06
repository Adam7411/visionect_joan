
# Visionect Joan

![image](https://github.com/user-attachments/assets/9d9a18c6-5518-432f-81c1-b7a4286760d8)


Niestandardowy dodatek wyświetlający podstawowe informacje tableta **Joan 6** w Home Assistant.
Główny zamiar kontrola poziomu baterii wyświetlacza Joan 6 
## Wyświetlane informacje:

- Bateria
- Całkowita pamięć
- Czas pracy
- Interwał odświeżania
- Napięcie baterii
- Status
- Sygnał WiFi
- Temperatura
- Wysyłanie adresu url ( https://www.google.com/)  lub zdjęć ( przykład http://192.168.xxx.xxx:8123/local/zdjecie_test.png ) (zdjecie_test.png do katalogu \\192.168.xxx.xxx\config\www\ )

---

## Instalacja dodatku

Integrację można zainstalować na dwa sposoby: przez **HACS** (zalecane) lub **manualnie**.

### Instalacja przez HACS (zalecana)

1. Upewnij się, że w Twoim Home Assistant jest zainstalowany [HACS](https://hacs.xyz/).
2. Przejdź do `HACS -> Integracje`.
3. Kliknij menu z trzema kropkami w prawym górnym rogu i wybierz **„Niestandardowe repozytoria”**.
4. Wklej adres URL tego repozytorium, wybierz kategorię **„Integracja”** i kliknij **„Dodaj”**.
5. Wyszukaj na liście integrację **„Visionect Joan”** i kliknij **„Zainstaluj”**.
6. Uruchom ponownie Home Assistant, aby zastosować zmiany.

### Instalacja manualna


1. Pobierz najnowsze wydanie, klikając na `visionect-joan.zip` (lub `Source code (zip)`).
2. Rozpakuj pobrane archiwum do /config/custom_components/
3. Uruchom ponownie Home Assistant.

---

## Konfiguracja

Po poprawnej instalacji i restarcie Home Assistant:

1. Przejdź do `Ustawienia > Urządzenia i usługi`.
2. Kliknij **„+ Dodaj integrację”** w prawym dolnym rogu.
3. Wyszukaj **„Visionect Joan”** i kliknij, aby rozpocząć konfigurację.
4. Wprowadź dane logowania do Visionect Software Suite:
- Adres URL (192.168.x.x:8081)
- Login
- Hasło
- API Key i API Secret (tworzymy w [Visionect Software Suite](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant) w zakładce Users przyciskiem Add new API key)


### Przykładowe zrzuty ekranu

![image](https://github.com/user-attachments/assets/98a9c588-365c-47d1-bde6-532055221460)

![image](https://github.com/user-attachments/assets/186c46f7-2b59-472d-aafc-bde40979baea)

---

## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Działa z urządzeniem **Joan 6**, inne modele nie zostały przetestowane.
- Użyłem AI aby szybko napisać ten dodatek.
- [Opis krok po kroku wykorzystania tabletu Joan 6 jako panel sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## Licencja

Projekt udostępniany na licencji MIT.







