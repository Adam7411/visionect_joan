<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
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

---

## Co nowego

- Nowa usługa: send_menu — szybkie „menu główne” z kafelkami (przyciskami), które otwierają zapisane widoki lub podane URL‑e. Wspiera small_screen, liczbę kolumn, zegar i nakładkę (Back/webhook).
- Nowa usługa: set_reload_timeout — ustawiasz czas automatycznego przeładowania sesji (0–86400 s) bezpośrednio z HA.
- Nowa usługa: stop_slideshow — zatrzymuje pokaz slajdów i wraca do wskazanego/konfigurowanego ekranu.
- Diagnostyka (Diagnostics): przycisk „Pobierz diagnostykę” w UI generuje bezpieczny zrzut danych o urządzeniach i konfiguracji (wygodne przy zgłaszaniu problemów).
- Poprawiona stabilność usług interaktywnych: brak błędów przy braku opcjonalnych parametrów (np. action_webhook_id).
- Lepsza obsługa adresów wewnętrznych HA przy obrazach i webhookach (preferowane Internal URL, jeśli ustawione).

---

## Najważniejsze funkcje

- Pełna kontrola ekranu: wyślij dowolny adres WWW, lokalne panele (np. AppDaemon) lub pojedyncze obrazy.
- Dynamicznie generowane widoki: integracja tworzy zoptymalizowane pod e‑ink panele pogody, kalendarza, zadań (to‑do), energii oraz statusów encji.
- Interaktywność: dodaj przycisk „Wstecz” do widoków tymczasowych lub ustaw, aby cały ekran był klikalny i wracał do głównego menu.
- Dwa przyciski akcji (webhook): prawy (→) i środkowy (✔) mogą wywoływać różne automatyzacje w Home Assistant.
- Pasek przycisków przeniesiony na dół ekranu: wygodniejszy dostęp do „Wstecz” (←), „Akcja” (→) i przycisku środkowego (✔).
- Zarządzanie energią: usługi usypiania i wybudzania urządzenia pomagają wydłużyć czas pracy na baterii.
- Podgląd na żywo: wbudowana encja `camera` pozwala podejrzeć aktualny obraz wyświetlany na tablecie.
- Łatwiejsza konfiguracja: widoki, menu główne i opcje ustawisz w interfejsie Home Assistant (Options Flow).

<img width="838" height="566" alt="bac2" src="https://github.com/user-attachments/assets/3d86ce11-44b9-4a65-aa2d-9c4379b77fd3" />

---

## Wymagania

- Visionect Software Suite (serwer zarządzający Joan), np. jako Add-on dla HA lub na osobnej maszynie.
- Dostęp sieciowy HA ⇄ Visionect (domyślnie port 8081).
- Zalecane: skonfigurowany Internal URL w Home Assistant (Ustawienia → System → Sieć), aby webhooki i lokalne obrazki były osiągalne z tabletu.

---

## Dostępne encje i usługi

### Encje i czujniki

- Podgląd ekranu (`camera`): aktualny obraz z tabletu.
- Bateria (`sensor`): poziom naładowania.
- Status ładowania (`binary_sensor`): czy urządzenie jest podłączone.
- Status urządzenia (`sensor`): online/offline.
- Nazwa urządzenia (`text`): zmiana nazwy bezpośrednio z HA.
- Interwał odświeżania (`number`): `ReloadTimeout` (0–86400 s).
- Głębia bitowa i dithering (`select`): parametry renderingu sesji.
- „Back button target” (`select`): domyślne miejsce powrotu dla przycisku Wstecz.
- Dodatkowe sensory diagnostyczne: temperatura, RSSI, napięcie baterii, uptime, pamięć, skonfigurowany URL (z bezpiecznym skróceniem), ostatnio widziany itp.

<img width="663" height="987" alt="1" src="https://github.com/user-attachments/assets/03f7eca1-784d-4400-93e1-add56af0bc49" />

### Usługi (skrót)

- Wyświetlanie treści:
  - `visionect_joan.set_url`: wyświetl dowolny URL lub nazwę zapisanego widoku.
  - `visionect_joan.send_menu` (nowość): siatka kafelków z widokami/URL‑ami (menu główne).
  - `visionect_joan.send_text`: sformatowany tekst z opcjonalnym obrazem.
  - `visionect_joan.send_image_url`: wyświetl obraz z URL (PNG/JPG/SVG/…).
  - `visionect_joan.send_camera_snapshot`: migawka z wybranej kamery w HA.
  - `visionect_joan.send_weather`: czytelny panel pogody (różne layouty).
  - `visionect_joan.send_calendar`: lista wydarzeń lub miesięczna siatka z widokiem dnia.
  - `visionect_joan.send_energy_panel`: podsumowanie zużycia/produkcji energii.
  - `visionect_joan.send_status_panel`: panel ze stanami wybranych encji.
  - `visionect_joan.send_sensor_graph`: wykres historii sensorów.

- Interakcja i nawigacja:
  - `visionect_joan.send_qr_code`: kod QR (np. do gościnnego Wi‑Fi).
  - `visionect_joan.start_slideshow`: pokaz slajdów (lista widoków/URL).
  - `visionect_joan.stop_slideshow` (nowość): zatrzymaj pokaz i wróć do wskazanego ekranu.
  - `visionect_joan.send_keypad`: pełnoekranowa klawiatura numeryczna (PIN do webhooka HA).

- Zarządzanie i diagnostyka:
  - `visionect_joan.force_refresh`: natychmiastowe przeładowanie aktualnego URL.
  - `visionect_joan.clear_display`: wyczyść ekran do bieli.
  - `visionect_joan.set_display_rotation`: ustaw obrot ekranu (i zrestartuj).
  - `visionect_joan.sleep_device` / `wake_device`: uśpij/obudź urządzenie.
  - `visionect_joan.clear_web_cache`: wyczyść cache WWW (opcjonalny restart sesji).
  - `visionect_joan.set_session_options`: ustaw dithering i bit depth (encoding).
  - `visionect_joan.set_reload_timeout` (nowość): ustaw `ReloadTimeout` (0–86400 s).

Integracja obsługuje szablony Jinja2. Możesz dynamicznie tworzyć treści m.in. w:
- `message` (usługa `send_text`)
- `caption` (usługa `send_camera_snapshot`)

---

## Przycisk Wstecz i przyciski akcji (webhook)

- Przycisk akcji (webhook) — interaktywne przyciski „Akcja” (→) i drugi (✔). Po naciśnięciu wysyłane jest żądanie POST do webhooka w Home Assistant, co pozwala wyzwalać automatyzacje (np. włącz światło, zmień scenę) bezpośrednio z ekranu e‑ink.
- Pasek przycisków znajduje się na dole ekranu, co ułatwia obsługę.
- Przycisk „Wstecz” — powrót do głównego panelu (np. AppDaemon). Główne menu ustawisz w opcjach integracji (Konfiguruj).
- Tryby „kliknij gdziekolwiek”: ekran może być w całości linkiem powrotnym lub wyzwalać webhook (wygodne w kiosk mode).

<img width="1237" height="639" alt="image" src="https://github.com/user-attachments/assets/c1246088-77e0-4be7-8a51-ac49b9d8cd46" />
<img width="561" height="705" alt="bac" src="https://github.com/user-attachments/assets/c7d2f579-759e-48dd-8046-5b0606f5de9e" />

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
4. Wprowadź dane do Visionect Software Suite:
   - Adres serwera Visionect (np. `http://192.168.x.x:8081`)
   - Nazwa użytkownika (np. `admin`)
   - Hasło (należy ustawić własne)
   - API Key oraz API Secret (Visionect Software Suite → Users → Add new API key)

<img width="1567" height="425" alt="Konfiguracja integracji" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="Dodawanie klucza API w Visionect Software Suite" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Widoki, menu i opcje — konfiguracja w UI

- Wszystkie ustawienia (w tym widoki oraz adres głównego menu) konfiguruje się w UI:
  - `Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj`
- Możesz tam:
  - dodawać/edytować/usuwać widoki (nazwa + URL),
  - ustawić globalny „Main menu URL”.
- W usługach (np. `visionect_joan.set_url`) możesz podać nazwę widoku zamiast pełnego adresu URL — integracja sama go rozpozna (dopasowanie nazw jest niewrażliwe na wielkość liter).
- Nowość: `visionect_joan.send_menu` potrafi automatycznie zbudować ekran z kafelkami z tych widoków — idealny „home screen”.

---

## Przykłady użycia (skrót)

- Wyświetl menu z zapisanych widoków (2 kolumny, z zegarem):
```yaml
service: visionect_joan.send_menu
data:
  device_id: <TWÓJ_DEVICE_ID>
  title: "Panel domowy"
  columns: 2
  include_clock: true
  add_back_button: false
```

- Własne pozycje menu:
```yaml
service: visionect_joan.send_menu
data:
  device_id: <TWÓJ_DEVICE_ID>
  items: |
    Status: Home Status
    Pogoda: Weather
    Kamera: http://<HA_IP>:8123/local/hall.jpg
  columns: 3
```

- Zatrzymaj pokaz slajdów i wróć do „Główne menu”:
```yaml
service: visionect_joan.stop_slideshow
data:
  device_id: <TWÓJ_DEVICE_ID>
  predefined_url: "Main Menu"
```

- Ustaw ReloadTimeout na 24h:
```yaml
service: visionect_joan.set_reload_timeout
data:
  device_id: <TWÓJ_DEVICE_ID>
  seconds: 86400
```

- Podpis pod migawką z kamery z szablonem:
```yaml
service: visionect_joan.send_camera_snapshot
data:
  device_id: <TWÓJ_DEVICE_ID>
  camera_entity: camera.drzwi
  caption: >
    Ostatnie otwarcie: {{ states('sensor.drzwi_last_open') }}
```

---

## Diagnostyka

- W `Ustawienia → Urządzenia i usługi → Visionect Joan → ⋮ → Pobierz diagnostykę` pobierzesz zredagowany JSON z kluczowymi informacjami (konfiguracja wpisu, lista urządzeń, aktualne URL, rotacja, ReloadTimeout, itp.).
- Plik nie zawiera haseł ani sekretów (są zacienione) i przyspiesza rozwiązywanie problemów.

---

## Ikony SVG

- Integracja wykorzystuje zestaw ikon SVG (dla encji i pogody) z katalogu `custom_components/visionect_joan/svg/`.
- Jeśli brakuje pliku, integracja użyje `default.svg` i zapisze ostrzeżenie w logach.
- Rekomendowane jest uzupełnienie braków (np. `window-open.svg`, `blinds-open.svg`, `wi-showers.svg`, …), aby widoki wyglądały spójnie.

---

## FAQ i rozwiązywanie problemów

- Ekran „miga” co jakiś czas:
  - To normalne: ekrany e‑ink wykonują okresowe pełne odświeżenie by usunąć ghosting.
  - Dodatkowo odświeżenie następuje po zmianie treści (np. wywołanie usługi lub restart sesji).

- „Nie ładuje kalendarza” / błędy `KeyError: 'action_webhook_id'`:
  - W najnowszej wersji opcjonalne pola są obsługiwane bezbłędnie (używane są wartości domyślne).
  - Zaktualizuj integrację i sprawdź logi. Upewnij się, że encja `calendar` zwraca zdarzenia w okresie, który wybierasz.

- Obrazy lokalne i webhooki nie działają:
  - Ustaw i używaj Internal URL w HA (Ustawienia → System → Sieć). Integracja preferuje adres wewnętrzny, aby urządzenie mogło połączyć się z HA.

- Automatyczne odświeżanie treści jest za częste/za rzadkie:
  - Użyj encji `number` (ReloadTimeout) albo usługi `set_reload_timeout`, aby dopasować interwał (0 = wyłączone, 86400 = 24h).

---

## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Działa z urządzeniem **Joan 6**, inne modele nie zostały przetestowane.
- Do szybkiego napisania tego dodatku wykorzystano AI.
- [Chcesz kupić nowy Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink).
- [Opis krok po kroku wykorzystania tabletu Joan 6 jako panel sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## Licencja

Projekt udostępniany na licencji MIT.
