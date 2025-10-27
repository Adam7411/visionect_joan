<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>


<!-- README.md -->
<div align="right">
<a href="README_en.md">English</a> | <a href="README.md">Polski</a>
</div>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz swoją instancję Home Assistant i przejdź do repozytorium w HACS." /></a>

# Visionect Joan dla Home Assistant

<img width="1280" height="800" alt="Przykładowy ekran główny na tablecie Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
<img width="24%" alt="Widok pogody" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" />
<img width="24%" alt="Kod QR do Wi-Fi" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" />
<img width="24%" alt="Panel statusów" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" />
<img width="24%" alt="Panel energii" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />
<br>
<img width="35%" alt="Wykres temperatury" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />
</p>

Integracja `visionect_joan` zmienia energooszczędny tablet e‑ink **Joan 6** w potężne, w pełni konfigurowalne centrum informacji dla Twojego inteligentnego domu.

Dzięki rozbudowanym usługom możesz tworzyć zaawansowane automatyzacje, np. po powrocie do domu pokazać panel energii, po wejściu do kuchni wyświetlić listę zakupów, a przy wykryciu ruchu wysłać zdjęcie z kamery i automatycznie wrócić do głównego pulpitu.

## Najważniejsze funkcje

- Pełna kontrola ekranu: wyślij dowolny adres WWW, lokalne panele (np. z AppDaemon) lub pojedyncze obrazy.
- Dynamicznie generowane widoki: integracja tworzy zoptymalizowane pod e‑ink panele pogody, kalendarza, zadań (to‑do), energii oraz statusów encji.
- Interaktywność: dodaj przycisk „Wstecz” do widoków tymczasowych lub ustaw, aby cały ekran był klikalny i wracał do głównego menu.
- Dwa przyciski akcji (webhook): prawy (→) i środkowy (✔) mogą wywoływać różne automatyzacje w Home Assistant.
- Pasek przycisków przeniesiony na dół ekranu: wygodniejszy dostęp do „Wstecz” (←), „Akcja” (→) i przycisku środkowego (✔).
- Zarządzanie energią: usługi usypiania i wybudzania urządzenia pomagają wydłużyć czas pracy na baterii.
- Podgląd na żywo: wbudowana encja `camera` pozwala podejrzeć aktualny obraz wyświetlany na tablecie.
- Łatwiejsza konfiguracja widoków i opcji: wszystko ustawisz w interfejsie Home Assistant. Konfiguracja przez `configuration.yaml` nie jest już używana.

### Dostępne encje i usługi

**Encje i czujniki:**
- Podgląd ekranu (`camera`): aktualny obraz z tabletu.
- Bateria (`sensor`): poziom naładowania.
- Status ładowania (`binary_sensor`): czy urządzenie jest podłączone.
- Status urządzenia (`sensor`): czy tablet jest online.
- Nazwa urządzenia (`text`): zmiana nazwy bezpośrednio z HA.
- Interwał odświeżania (`number`): jak często tablet odświeża zawartość.
- Głębia bitowa: liczba odcieni szarości (1‑bit = czerń/biel; 4‑bit = 16 odcieni — lepsza jakość obrazu).
- Metoda ditheringu: poprawa jakości obrazu przez „doszumianie” przejść tonalnych.
- Czyszczenie cache: usuwa zapisaną zawartość (np. obrazy) przy problemach ze starymi treściami.
- I inne: temperatura, siła sygnału Wi‑Fi, napięcie baterii, czas pracy, zajętość pamięci, skonfigurowany URL, ostatnio widziany itp.

<img width="663" height="987" alt="1" src="https://github.com/user-attachments/assets/03f7ec1a-784d-4400-93e1-add56af0bc49" />


**Usługi:**
- `visionect_joan.set_url`: wyświetl dowolny URL lub nazwę zapisanego widoku (predefined).
- `visionect_joan.send_text`: sformatowany tekst z opcjonalnym obrazem.
- `visionect_joan.send_camera_snapshot`: migawka z dowolnej kamery w HA.
- `visionect_joan.send_weather`: czytelny panel pogody (różne layouty).
- `visionect_joan.send_calendar`: lista wydarzeń lub miesięczna siatka z widokiem dnia.
- `visionect_joan.send_energy_panel`: podsumowanie zużycia/produkcji energii.
- `visionect_joan.send_status_panel`: panel ze stanami wybranych encji.
- `visionect_joan.send_sensor_graph`: wykres historii sensorów, dopasowany do orientacji ekranu.
- `visionect_joan.send_todo_list`: lista zadań (np. zakupy).
- `visionect_joan.send_qr_code`: kod QR (np. do gościnnego Wi‑Fi).
- `visionect_joan.sleep_device` i `wake_device`: uśpij/obudź urządzenie.
- `visionect_joan.clear_display`, `force_refresh`, `set_display_rotation`: narzędzia zarządzania ekranem.

Integracja obsługuje szablony Jinja2. Możesz dynamicznie tworzyć treści m.in. w:
- `message` (usługa `send_text`)
- `caption` (usługa `send_camera_snapshot`)

### Przycisk Wstecz i przyciski akcji (webhook)

- Przycisk akcji (webhook) — umożliwia dodanie interaktywnych przycisków „Akcja” (→) oraz drugiego przycisku (✔). Po naciśnięciu wysyłane jest żądanie POST do webhooka w Home Assistant, co pozwala wyzwalać automatyzacje (np. włącz światło, zmień scenę) bezpośrednio z ekranu e‑ink.
- Pasek przycisków znajduje się na dole ekranu, co ułatwia obsługę.
- Przycisk „Wstecz” — powrót do głównego panelu (np. AppDaemon). Główne menu ustawisz w opcjach integracji (Konfiguruj).

<img width="1237" height="639" alt="image" src="https://github.com/user-attachments/assets/c1246088-77e0-4be7-8a51-ac49b9d8cd46" />




---

## Instalacja

Integrację można zainstalować na dwa sposoby: przez **HACS** (zalecane) lub **ręcznie**.

### Instalacja przez HACS (zalecane)

1. Upewnij się, że masz zainstalowany [HACS](https://hacs.xyz/) w Home Assistant.
2. Przejdź do `HACS → Integrations`.
3. Kliknij menu „trzy kropki” w prawym górnym rogu i wybierz **Custom repositories**.
4. Wklej adres tego repozytorium, wybierz kategorię **Integration** i kliknij **Add**.
5. Znajdź integrację **Visionect Joan** i kliknij **Install**.
6. Zrestartuj Home Assistant.

### Instalacja ręczna

1. Pobierz najnowsze wydanie (`visionect-joan.zip` lub `Source code (zip)`).
2. Wypakuj archiwum do katalogu `/config/custom_components/`.
3. Zrestartuj Home Assistant.

---

## Konfiguracja

Po instalacji i restarcie Home Assistant:

1. Przejdź do `Ustawienia → Urządzenia i usługi`.
2. Kliknij **„+ Dodaj integrację”**.
3. Wyszukaj **„Visionect Joan”** i rozpocznij konfigurację.
4. Wprowadź dane do Visionect Software Suite: [Instalacja Visionect Software Suite](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
   - Adres serwera (np. `192.168.x.x:8081`)
   - Nazwa użytkownika (np. `admin`)
   - Hasło
   - API Key oraz API Secret (dodasz w Visionect Software Suite → Users → Add new API key)

<img width="1567" height="425" alt="Konfiguracja integracji" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="Dodawanie klucza API w Visionect Software Suite" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Widoki i opcje — konfiguracja w UI

- Wszystkie ustawienia (w tym widoki oraz adres głównego menu) konfiguruje się w UI:
  - `Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj`
- Możesz tam:
  - dodawać/edytować/usuwać widoki (nazwa + URL),
  - ustawić globalny „Main menu URL”.
- W usługach (np. `visionect_joan.set_url`) możesz podać nazwę widoku zamiast pełnego adresu URL — integracja sama go rozpozna (dopasowanie nazw jest niewrażliwe na wielkość liter).
- Konfiguracja przez `configuration.yaml` nie jest już używana.

---

## Przykłady użycia

Ekrany, które możesz wyświetlić na tablecie Joan 6 obsługiwanym przez Visionect:

<img width="1920" height="848" alt="Panel AppDaemon na ekranie Joan 6" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="AppDaemon — motyw ciemny" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**Więcej przykładów:**

<details>
  <summary>Kliknij, aby zobaczyć więcej zrzutów ekranu</summary>
  <img width="381" height="570" alt="Widok 1" src="https://github.com/user-attachments/assets/e1f32a48-0277-42ce-9018-837aeba1b6a8" />
  <img width="510" height="739" alt="Widok 2" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="Widok 3" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="Widok 4" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="Widok 5" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="Widok 6" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="Widok 7" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="307" height="457" alt="Widok 8" src="https://github.com/user-attachments/assets/d7d76fdd-52b7-4c95-8f77-a369e672ab4b" />
  <img width="306" height="456" alt="Widok 9" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="Widok 10" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
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
