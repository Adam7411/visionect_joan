
# Visionect Joan


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
- Wysyłanie adresu url np. ( https://www.wikipedia.org/ )  lub zdjęć ( przykład http://adresHA:8123/local/zdjecie_test.png ) (plik zdjecie_test.png umieszczamy w katalogu \\192.168.xxx.xxx\config\www\ )

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

<img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
<img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
<img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
<img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />

---

## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Działa z urządzeniem **Joan 6**, inne modele nie zostały przetestowane.
- Użyłem AI aby szybko napisać ten dodatek.
- [Opis krok po kroku wykorzystania tabletu Joan 6 jako panel sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## Licencja

Projekt udostępniany na licencji MIT.







