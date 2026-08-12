- Pełna kontrola ekranu: URL, AppDaemon, `/local/`, HTML `data:`, obrazy.
- Gotowe ekrany e‑ink: pogoda (3 układy), kalendarz, to‑do/zakupy, energia, status encji, wykres sensora, RSS, QR, **panel crypto**, snapshot kamery.
- Keypad PIN i panel do 12 przycisków (webhooki HA).
- Warstwa interaktywna: pasek ← / ✔ / → lub tap na cały ekran.
- Podgląd na żywo (`camera`), encja **`dashboard_ok`** (czy URL = AppDaemon).
- Pełna kontrola ekranu: dowolny URL, lokalne strony (AppDaemon, `/local/`, Lovelace panel embed), obrazy, HTML `data:` inline.
- Widoki zoptymalizowane dla e‑ink:
  - Pogoda: szczegółowy, lista prognozy, panel z wykresem 24h.
  - Kalendarz: lista dni, minimalistyczny, siatka miesięczna + podgląd dnia.
  - Lista zadań / Shopping List z interaktywnym odhaczaniem przez webhook.
  - Panel energii (zużycie, produkcja, import, eksport, konsumpcja).
  - Panel statusów encji (ikony + nazwy + wartości + tłumaczenia stanów).
  - Graf historii sensorów (line / bar) z automatycznym dopasowaniem orientacji.
  - RSS / Atom – paginowany.
  - QR code (np. Wi‑Fi dla gości).
  - **Panel crypto** (CryptoCompare + sparkline).
  - Keypad PIN (webhook → automatyzacja weryfikująca kod).
  - Panel 12 przycisków (stateless – każdy wywołuje własny webhook).
- Warstwa interaktywna: dolny pasek (← Wstecz / ✔ środkowy / → prawy), albo pełny ekran jako „tap to action” / „tap to back”.
- Live preview (`camera`) – bieżący zrzut ekranu jako encja kamery.
- Encja **`dashboard_ok`** – czy URL sesji = AppDaemon / Main menu.
- **Profile Eco / Normal / Alert** + **battery guard** (skip PUT gdy URL bez zmian).
- Powiadomienia HA: bateria, offline, ErrorCode VSS, orphan.
- Recovery HTTP + probe AppDaemon po rebootcie HA.
- Opcjonalna analiza logów przez **Ollama**.
- Ustawienia w UI: predefiniowane widoki, powiadomienia, recovery page, Ollama.
- Zarządzanie: rotacja ekranu, czyszczenie WebKit cache, wymuszenie odświeżenia, sleep/wake.
- Parametry renderingu: dithering, encoding (głębia bitowa).
- Safe Config TCLV (odczyt / zapis / przywracanie kopii).
- Czyszczenie plików tymczasowych w `www/`.
- Mechanizm cleanup plików tymczasowych (snapshoty / grafy) w `www/`.
<details>
  <summary>Zrzut: dolny pasek z przyciskami</summary>

[21 lines collapsed]

  <img width="758" height="1024" alt="Kod QR" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="Graf sensora" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Tekst wiadomości" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="Drugi układ pogody" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="Status panel encji" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="Panel energii" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Podgląd live" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />

[6 lines collapsed]

### Przez HACS (zalecane)
1. Zainstaluj [HACS](https://hacs.xyz/).
2. HACS → Integracje → ⋮ → Repozytoria → dodaj `https://github.com/Adam7411/visionect_joan`.
3. Zainstaluj **Visionect Joan** → restart Home Assistant.
1. Zainstaluj [HACS](https://hacs.xyz/) (jeśli nie masz).
2. W HACS → Integrations kliknij ⋮ → Custom repositories.
3. Dodaj repo: `https://github.com/Adam7411/visionect_joan` jako „Integration”.
4. Odnajdź „Visionect Joan” → Install.
5. Restart Home Assistant.
### Ręcznie
1. Pobierz release lub sklonuj repo do `/config/custom_components/visionect_joan/`.
2. Restart Home Assistant.
1. Pobierz najnowszy release (`visionect-joan.zip` albo „Source code”).
2. Wypakuj do: `/config/custom_components/visionect_joan/`.
3. Restart HA.
**Wymagania:** VSS ([visionect-v3-allinone](https://github.com/Adam7411/visionect-v3-allinone)), tablet w VSS, opcjonalnie AppDaemon + joan_generator.
---
## Konfiguracja VSS i integracji
## Konfiguracja Visionect Software Suite (VSS)
1. **Ustawienia → Urządzenia i usługi → Dodaj integrację → Visionect Joan**
2. Połączenie z VSS:
   - Host: `http://192.168.x.x:8081` (domyślny port VSS)
   - Login/hasło **lub** API Key + Secret (VSS → Users → Add new API key)
3. **Konfiguruj** integrację (menu opcji — patrz niżej).
4. Raz ustaw URL tabletu (`set_url` lub Configurator Visionect) — zwykle AppDaemon.
1. Przejdź do `Ustawienia → Urządzenia i usługi`.
2. Kliknij **„+ Dodaj integrację”**.
3. Wyszukaj **„Visionect Joan”** i rozpocznij konfigurację.
4. Wprowadź dane do Visionect Software Suite: [Instalacja Visionect Software Suite](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
   - Adres serwera (np. `http://192.168.x.x:8081`) — adres VSS (zwykle ten sam host co HA)
   - Nazwa użytkownika (`admin`)
   - Hasło (ustaw własne)
   - API Key oraz API Secret (VSS → Users → Add new API key)
5. **Konfiguruj** integrację (widoki, recovery, powiadomienia).
6. Raz ustaw URL tabletu — zwykle AppDaemon (`set_url` z `wake_tablet: true`).
<img width="1567" height="425" alt="Konfiguracja integracji" src="https://github.com/user-attachments/assets/37bbcdb7-e820-4275-b7ed-efc9248048e5" />

[8 lines collapsed]

| Menu | Co ustawiasz |
|------|----------------|
| **Zarządzaj widokami** | Dodaj / edytuj / usuń widoki (nazwa + URL) |
| **Domyślny adres URL** | Token strony recovery — wklej wygenerowany URL do VSS → Settings → HTML Backend → Default URL |
| **Czyszczenie cache i dysku** | `cleanup_max_age_hours`, `cleanup_interval_hours` — wiek plików tymcz. w `www/` |
| **Język tabletu** | PL / EN / DE / … / Auto — teksty na tablecie i powiadomienia HA |
| **Powiadomienia** | Podmenu poniżej |
| **Analiza logów Ollama** | URL, model, interwał — opcjonalna diagnoza AI |
| **Domyślny adres URL** | Token strony recovery — wklej URL do VSS → Settings → HTML Backend → Default URL |
| **Czyszczenie cache i dysku** | Wiek plików tymcz. w `www/` |
| **Język tabletu** | PL / EN / DE / … / Auto |
| **Powiadomienia** | Bateria, ErrorCode, offline, orphan |
| **Analiza logów Ollama** | URL, model, interwał (opcjonalnie) |
### Podmenu Powiadomienia
| Sekcja | Parametry |
|--------|-----------|
| **Bateria** | Próg 5/10/15 %; alert na tablecie; powiadomienia HA (niski stan, pełne naładowanie); **battery guard interval** (sek.) |
| **Błędy (ErrorCode)** | Powiadomienie HA gdy VSS zgłosi kod błędu tabletu |
| **Offline** | Włącz/wyłącz; próg **1 / 4 / 24 h**; aktualizacja co pełną godzinę (v3.9.13+) |
| **Stan / orphan** | Automatyczne powiadomienie przy problemie sesji VSS |
| **Bateria** | Próg 5/10/15 %; alert na tablecie; powiadomienia HA; battery guard interval |
| **Błędy (ErrorCode)** | Powiadomienie HA przy kodzie błędu VSS |
| **Offline** | Włącz/wyłącz; próg 1 / 4 / 24 h (aktualizacja co godzinę, v3.9.13+) |
| **Stan / orphan** | Automatyczne powiadomienie przy problemie sesji |
### Opcjonalnie YAML (`configuration.yaml`)
```yaml
visionect_joan:
  main_menu_url: "http://..."
  recovery_probe_url: "http://..."
  cleanup_max_age_hours: 24
  cleanup_interval_hours: 6
  views:
    - name: Salon
      url: "http://192.168.1.10:5050/Dashboard?widget=salon"
```
---
## Predefiniowane widoki (Views)
1. Opcje integracji → **Zarządzaj widokami** → Dodaj (nazwa + URL).
2. Używaj w usługach jako `url: NazwaWidoku` lub w select **Wybierz widok**.
3. Per tablet: select **Cel przycisku Wstecz** i atrybut `assigned_home_view`.
Widoki zapisujesz w Opcjach integracji:
Legacy format (`Nazwa: URL` linia po linii) jest nadal parsowany.
1. Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.
2. „Add view” → Nazwa + URL.
3. Te nazwy możesz potem wybierać przez encję `Choose view` (select) lub podawać jako `predefined_url` / `url` w usługach.
Format legacy („Name: URL” linia po linii) jest automatycznie migrowany.
---
## Encje
| Typ | Encja / funkcja | Uwagi |
|-----|-----------------|-------|
| `camera` | Podgląd ekranu | PNG bieżącego widoku |
| `sensor` | Stan, bateria, RSSI, temperatura, uptime, napięcie, pamięć, **configured_url**, last_seen, **error_code**, connect_reason | Część domyślnie wyłączona |
| `binary_sensor` | **Online**, **health** (orphan), **is_charging**, **dashboard_ok** | `dashboard_ok` = URL sesji zgadza się z Main menu / widokiem tabletu |
| `text` | Nazwa urządzenia | Zapis do VSS |
| `number` | **ReloadTimeout** (odświeżanie sesji VSS) | 0–86400 s |
| `select` | Widok, cel Wstecz, **tryb synchronizacji** (eco/normal/alert), rozmiar ekranu (joan6/joan13), rotacja, dithering, encoding, **harmonogram snu** | Per tablet |
| `button` | **Sprawdź stan**, Force Refresh, Reboot, Clear Web Cache, **Analiza Ollama** | Reboot / Clear często wyłączone domyślnie |
| Typ encji | Nazwa / Funkcja | Uwagi |
|-----------|-----------------|-------|
| `camera` | Podgląd aktualnego ekranu | Koduje zrzut jako obraz PNG |
| `sensor` | Stan online/offline, bateria, temperatura, RSSI, uptime, napięcie, pamięć, **configured_url**, last_seen, **error_code** | Część domyślnie wyłączona |
| `binary_sensor` | **Online**, **health** (orphan), **is_charging**, **dashboard_ok** | `dashboard_ok` = URL sesji zgadza się z Main menu |
| `text` | Nazwa urządzenia | Zmiana wysyłana do API |
| `number` | `ReloadTimeout` (czas odświeżenia sesji) | 0–86400 s |
| `select` | Widok, Back target, **tryb synchronizacji** (eco/normal/alert), rozmiar ekranu, rotacja, dithering, encoding, harmonogram snu | Per tablet |
| `button` | **Sprawdź stan**, Force Refresh, Reboot, Clear Web Cache, **Analiza Ollama** | Reboot / Clear często ukryte |
| (wewnętrzne) | Panel opcji widoków | Przez OptionsFlow |
<details>
  <summary>Zrzut encji urządzenia</summary>
  <img width="658" height="1002" alt="Encje Joan" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
  <summary>Pokaż zrzut ekranu</summary>
  <img width="658" height="1002" alt="Zrzut encji" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>
---

[6 lines collapsed]

|--------|--------------|------------|
| **Eco** | Stały dashboard AppDaemon (domyślny) | Minimalny polling; **nie** robi PUT do VSS gdy URL się nie zmienił |
| **Normal** | Okazjonalne overlaye | Battery guard aktywny |
| **Alert** | Kamery, pilne alerty | Szybszy refresh; możliwe wymuszenie wake |
| **Alert** | Kamery, pilne alerty | Szybszy refresh |
**Usługa `set_url`:** pole **`wake_tablet: true`** — wymusza zapis sesji nawet w Eco.
**Eco recovery (v3.9.14):** po restarcie HA, gdy probe AppDaemon OK i URL sesji poprawny → **pomijany** zbędny restart sesji VSS.
**Eco recovery (v3.9.14):** po restarcie HA, gdy probe AppDaemon OK i URL sesji poprawny → pomijany zbędny restart sesji VSS.
**Zdarzenie:** `visionect_joan_command_result` — pola m.in. `push_result` (`success`, `skipped_unchanged`, `skipped_guard`), `skipped_wake`.
**Zdarzenie:** `visionect_joan_command_result` — m.in. `push_result` (`success`, `skipped_unchanged`, `skipped_guard`).
---
## Usługi – pełna lista
## Usługi – skrót
| Usługa | Kategoria | Overlay | Opis |
|--------|-----------|---------|------|
| `visionect_joan.set_url` | Nawigacja | — | URL lub widok; `{uuid}`, **`wake_tablet`** |
| `visionect_joan.send_text` | Treść | Tak | Tekst + obraz, Jinja2 |
| `visionect_joan.send_image_url` | Treść | Tak | Obraz z URL |
| `visionect_joan.send_camera_snapshot` | Treść | Tak | Snapshot encji `camera` |
| `visionect_joan.send_status_panel` | Status | Tak | Ikony + stany encji |
| `visionect_joan.send_energy_panel` | Energia | Tak | Moc + dzienne PV/import/export |
| `visionect_joan.send_weather` | Pogoda | Tak | 3 layouty |
| `visionect_joan.send_calendar` | Kalendarz | Tak | Lista / minimal / siatka miesiąca |
| `visionect_joan.send_todo_list` | Lista | Tak | To‑Do / Shopping + webhook toggle |
| `visionect_joan.send_sensor_graph` | Historia | Tak | Wykres line/bar |
| `visionect_joan.send_rss_feed` | RSS | Tak | Paginacja wpisów |
| `visionect_joan.send_qr_code` | QR | Tak | QR + podpis |
| Usługa | Kategoria | Interaktywność (overlay) | Opis skrócony |
|--------|-----------|--------------------------|---------------|
| `visionect_joan.set_url` | Nawigacja | Opcjonalnie | Ustaw URL lub nazwę widoku; **`wake_tablet`** |
| `visionect_joan.send_text` | Treść | Tak | Tekst + układ obrazu (Jinja2) |
| `visionect_joan.send_image_url` | Treść | Tak | Sam obraz (PNG/JPG/SVG/WebP) |
| `visionect_joan.send_camera_snapshot` | Treść | Tak | Snapshot z encji kamery |
| `visionect_joan.send_status_panel` | Status | Tak | Lista encji (ikony + stan) |
| `visionect_joan.send_energy_panel` | Energia | Tak | Zużycie + produkcja/import/export |
| `visionect_joan.send_weather` | Pogoda | Tak | 3 layouty (szczegóły / lista / wykres) |
| `visionect_joan.send_calendar` | Kalendarz | Tak | Lista / minimalistyczna / miesięczna |
| `visionect_joan.send_todo_list` | Lista | Tak | To-Do / Shopping List + webhook toggle |
| `visionect_joan.send_sensor_graph` | Historia | Tak | Wykres line/bar wielu sensorów |
| `visionect_joan.send_rss_feed` | RSS | Tak | Lista + paginacja |
| `visionect_joan.send_qr_code` | QR | Tak | Kod + podpis |
| `visionect_joan.send_crypto` | Crypto | Tak | Notowania CryptoCompare + sparkline |
| `visionect_joan.start_slideshow` | Nawigacja | Tak | Rotacja widoków / URL w pętli |
| `visionect_joan.send_keypad` | Wejście | Tak (bez Back domyślnie) | PIN → webhook |
| `visionect_joan.send_button_panel` | Akcje | Tak | Do 12 przycisków (webhook) |
| `visionect_joan.send_keypad` | Wejście | Tak | PIN → webhook JSON |
| `visionect_joan.start_slideshow` | Nawigacja | Tak | Rotacja widoków/URL |
| `visionect_joan.set_session_options` | Render | — | Encoding, dithering |
| `visionect_joan.set_display_rotation` | Utrzymanie | — | Rotacja + reboot |
| `visionect_joan.force_refresh` | Utrzymanie | — | Restart sesji |
| `visionect_joan.clear_web_cache` | Utrzymanie | — | Cache WebKit |
| `visionect_joan.clear_display` | Utrzymanie | — | Biały ekran |
| `visionect_joan.sleep_device` / `wake_device` | Zasilanie | — | Sen / wybudzenie |
| `visionect_joan.read_safe_device_config` | Safe TCLV | — | Krok 1/3: odczyt |
| `visionect_joan.apply_safe_device_config` | Safe TCLV | — | Krok 2/3: zapis (heartbeat, system screens, touch) |
| `visionect_joan.restore_safe_device_config` | Safe TCLV | — | Krok 3/3: przywróć kopię |
| `visionect_joan.set_session_options` | Render | N/A | Głębia / dithering |
| `visionect_joan.clear_web_cache` | Utrzymanie | N/A | Czyszczenie cache (opcjonalny restart) |
| `visionect_joan.force_refresh` | Utrzymanie | N/A | Restart sesji |
| `visionect_joan.set_display_rotation` | Utrzymanie | N/A | Rotacja + reboot |
| `visionect_joan.clear_display` | Utrzymanie | N/A | Pusty ekran |
| `visionect_joan.sleep_device` / `wake_device` | Zasilanie | N/A | Sen / wybudzenie |
| `visionect_joan.read_safe_device_config` | Safe TCLV | N/A | Odczyt konfiguracji urządzenia |
| `visionect_joan.apply_safe_device_config` | Safe TCLV | N/A | Zapis + kopia zapasowa |
| `visionect_joan.restore_safe_device_config` | Safe TCLV | N/A | Przywróć kopię |
**Diagnostyka w UI (bez osobnych usług):** przycisk **Sprawdź stan** (`check_orphans`), **Analiza logów Ollama**, Naprawy HA, encja `dashboard_ok`.
Pełna lista pól: `services.yaml` oraz **Narzędzia deweloperskie → Usługi**.
Wspólne pola wielu usług treści: `add_back_button`, `back_button_url`, `auto_return_seconds`, `click_anywhere_to_return`, `click_anywhere_to_action`, `action_webhook_id`, `screen_size` (joan6/joan13).
Wspólne pola overlay: `add_back_button`, `back_button_url`, `auto_return_seconds`, `click_anywhere_to_return`, `click_anywhere_to_action`, `action_webhook_id`, `screen_size`.
Pełna specyfikacja pól: **Narzędzia deweloperskie → Usługi** oraz plik [`services.yaml`](./services.yaml).
---
<details>
<summary>Pełna lista pól wspólnych (overlay / interakcja)</summary>
## Szczegóły usług
| Pole | Typ | Opis |
|------|-----|------|
| `add_back_button` | bool | Dolny pasek z ← |
| `back_button_url` | string | Cel Wstecz (widok lub URL) |
| `auto_return_seconds` | int | Po czasie wraca do poprzedniego URL (AppDaemon) |
| `click_anywhere_to_return` | bool | Tap w dowolne miejsce = Wstecz (ukrywa pasek) |
| `click_anywhere_to_action` | bool | Tap = akcja webhook (ukrywa pasek) |
| `action_webhook_id` | string | ID webhooka HA dla → / tap |
| `screen_size` | select | `joan6` / `joan13` — rozdzielczość layoutu |
| `predefined_url` | string | Alias widoku z opcji integracji |
Poniżej opis wybranych usług wraz ze zrzutami ekranu (zwijane sekcje). Pełna lista pól i selektorów znajduje się w `services.yaml` oraz w UI Home Assistant (Developer Tools → Services).
</details>
### Wyświetlanie treści
---
- `visionect_joan.send_button_panel`  
  - Umożliwia stworzenie siatki do 12 konfigurowalnych przycisków. Każdy przycisk może mieć własną nazwę, ikonę i przypisany unikalny `webhook_id`, który wywołuje automatyzacje w Home Assistant.  
  - Wskazówka: Panel wysyła sygnały do Home Assistant za pomocą webhooków. Aby przycisk działał, musisz stworzyć automatyzację, która na ten sygnał zareaguje.  
  - ⚠️ Ważne ograniczenie: Brak informacji o stanie. Panel przycisków działa jednokierunkowo (stateless). Wygląd nie aktualizuje się zależnie od stanu urządzeń (do stanów użyj np. dashboardu AppDaemon).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1214" height="3814" alt="Panel przycisków" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
  </details>
## Szczegóły usług
***
### Wyświetlanie treści
- `visionect_joan.set_url`  
  - Ustawia dowolny URL lub nazwę zdefiniowanego widoku (predefined).  
  - Wskazówka: nazwy widoków dopasowywane są bez rozróżniania wielkości liter. Dodawaj/edytuj widoki w: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.  
  - **`wake_tablet: false`** (domyślnie w Eco) oszczędza baterię, gdy URL się nie zmienił.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1220" height="595" alt="Ustaw URL" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
  </details>
- **`send_button_panel`** — do 12 przycisków, każdy z `webhook_id`. Stateless — nie pokazuje live stanów encji (do tego AppDaemon / `send_status_panel`).
  <details><summary>Zrzut</summary>
  <img width="1214" alt="Panel przycisków" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
***
- `visionect_joan.send_text`  
  - Wysyła sformatowany tekst (obsługuje Jinja2), opcjonalnie z obrazem i różnymi układami (text only, text + image).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1225" height="2066" alt="Wiadomość tekstowa" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />
  </details>
- **`set_url`** — URL, nazwa widoku lub `{uuid}`. **`wake_tablet: false`** (domyślnie w Eco) oszczędza baterię gdy URL bez zmian.
  <details><summary>Zrzut</summary>
  <img width="1220" alt="Set URL" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
***
- `visionect_joan.send_image_url`  
  - Wyświetla obraz z podanego URL (PNG/JPG/SVG/WebP). Dla plików lokalnych użyj `http://<HA_IP>:8123/local/...`.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1234" height="1448" alt="Obraz z URL" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />
  </details>
- **`send_text`** — Jinja2, layouty text/image.
  <details><summary>Zrzut</summary>
  <img width="1225" alt="Tekst" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />
***
- `visionect_joan.send_camera_snapshot`  
  - Tworzy snapshot z encji `camera` i wyświetla go (z podpisem i rotacją obrazu).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1223" height="1472" alt="Snapshot kamery" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf-25237e08" />
