<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>
<img width="447" height="355" alt="image" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />

# Visionect Joan dla Home Assistant
<img width="636" height="399" alt="vision" src="https://github.com/user-attachments/assets/6e30517f-c34a-443e-9e8f-5e02f59c80c7" />



<img width="381" height="570" alt="Bez tytułu" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" /> <img width="302" height="460" alt="QR" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" /> <img width="301" height="456" alt="aaaa" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" /> <img width="301" height="457" alt="cccc" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />




Niestandardowy dodatek wyświetlający podstawowe informacje tableta e-ink **Joan 6** firmy Visionect w Home Assistant oraz umożliwiający wysyłanie własnego adresu URL, tekstu i zdjęć z poziomu HA.

Pozwoli to na tworzenie zaawansowanych automatyzacji, np. wysyłania powiadomienia o niskim stanie baterii, wyświetlanie encji z poziomem baterii na tablecie, czy wysyłanie zdjęć do różnych powiadomień, po czym automatyczny powrót do dashboardu Appdaemon.


## Funkcjonalności

Integracja dostarcza następujące encje i usługi:

**Sensory:**
- Poziom baterii
- Całkowita i zajęta pamięć
- Czas pracy
- Status ładowania (Sensor binarny)
- Interwał odświeżania (Liczba)
- Napięcie baterii
- Status urządzenia (Online/Offline)
- Siła sygnału Wi-Fi
- Temperatura
- Skonfigurowany URL
- Czas ostatniej aktywności
<img width="646" height="860" alt="aaaau" src="https://github.com/user-attachments/assets/140837dd-0434-40a8-8352-753e3cc50f16" />

**Usługi:**
- `visionect_joan.send_text`: Wysyłanie wiadomości tekstowych, teraz z obsługą obrazków i układów. Wspiera szablony Jinja2 do dynamicznej treści.
- `visionect_joan.set_url`: Wyświetlanie dowolnego adresu URL (np. strony `https://www.wikipedia.org/` lub lokalnego obrazka `http://<adres_ip_ha>:8123/local/zdjecie.png`).
- `visionect_joan.clear_display`: Czyszczenie ekranu.
- `visionect_joan.force_refresh`: Natychmiastowe przeładowanie zawartości z ustawionego adresu URL.
- `visionect_joan.set_display_rotation`: Rotacja ekranu.
- `visionect_joan.send_qr_code`: Generowanie Kodów QR: Wyświetlaj niestandardowe kody QR bezpośrednio na ekranie Joan. Idealne dla sieci Wi-Fi dla gości, linków i nie tylko.
- `action: visionect_joan.sleep_device END visionect_joan.wake_device`: Usługi Zarządzania Energią: Drastycznie wydłuż żywotność baterii swojego tabletu, usypiając go i wybudzając za pomocą automatyzacji.
- `visionect_joan.send_energy_panel`: Wyświetla panel zużycia i produkcji energii.
- `visionect_joan.send_weather`: Pokazuje szczegółową, powiększoną prognozę pogody.
- `visionect_joan.send_calendar`: Renderuje ulepszony, czytelny kalendarz miesięczny.
- `visionect_joan.send_todo_list`: Wysyła dowolną listę zadań, w tym listę zakupów (todo.shopping_list).
- `visionect_joan.send_camera_snapshot`: Wyślij zrzut ekranu dowolnej kamery z Home Assistant
- 
<img width="1470" height="678" alt="Screenshot" src="https://github.com/user-attachments/assets/18474371-8779-48aa-8a46-a2270dc120fa" />
<img width="1875" height="1786" alt="a" src="https://github.com/user-attachments/assets/2d29acfa-8655-467c-ba11-4fd391b1766f" />

---

## Instalacja

Integrację można zainstalować na dwa sposoby: przez **HACS** (zalecane) lub **manualnie**.

### Instalacja przez HACS (zalecana)

1.  Upewnij się, że w Twoim Home Assistant jest zainstalowany [HACS](https://hacs.xyz/).
2.  Przejdź do `HACS -> Integracje`.
3.  Kliknij menu z trzema kropkami w prawym górnym rogu i wybierz **„Niestandardowe repozytoria”**.
4.  Wklej adres URL tego repozytorium, wybierz kategorię **„Integracja”** i kliknij **„Dodaj”**.
5.  Wyszukaj na liście integrację **„Visionect Joan”** i kliknij **„Zainstaluj”**.
6.  Uruchom ponownie Home Assistant, aby zastosować zmiany.

### Instalacja manualna

1.  Pobierz najnowsze wydanie, klikając na `visionect-joan.zip` (lub `Source code (zip)`).
2.  Rozpakuj pobrane archiwum do katalogu `/config/custom_components/`.
3.  Uruchom ponownie Home Assistant.

---

## Konfiguracja

Po poprawnej instalacji i restarcie Home Assistant:

1.  Przejdź do `Ustawienia > Urządzenia i usługi`.
2.  Kliknij **„+ Dodaj integrację”** w prawym dolnym rogu.
3.  Wyszukaj **„Visionect Joan”** i kliknij, aby rozpocząć konfigurację.
4.  Wprowadź dane logowania do Visionect Software Suite:
    -   Adres serwera (np. `192.168.x.x:8081`)
    -   Nazwa użytkownika (np. `admin`)
    -   Hasło
    -   Klucz API i Sekret API (można je wygenerować w Visionect Software Suite w zakładce "Users" klikając "Add new API key").

<img width="1567" height="425" alt="5" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="6" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Przykłady użycia

Przykładowe ekrany, które można wyświetlić na tablecie Joan 6 za pomocą serwera Visionect:


<img width="1920" height="848" alt="ada" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="aaaa" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**Więcej przykładów:**

<details>
  <summary>Kliknij, aby zobaczyć więcej zrzutów ekranu</summary>
  <img width="381" height="570" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e1f32a48-0277-42ce-9018-837aeba1b6a8" />
  <img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="smie" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="vvvvu" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="307" height="457" alt="bater tytułu" src="https://github.com/user-attachments/assets/d7d76fdd-52b7-4c95-8f77-a369e672ab4b" />
  <img width="306" height="456" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="Bez tytułuss" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
</details>

---

## Uwagi

-   Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
-   Działa z urządzeniem **Joan 6**, inne modele nie zostały przetestowane.
-   Do szybkiego napisania tego dodatku wykorzystano AI.
-   [Chcesz kupić nowy Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink).
-   [Opis krok po kroku wykorzystania tabletu Joan 6 jako panel sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## Licencja

Projekt udostępniany na licencji MIT.
