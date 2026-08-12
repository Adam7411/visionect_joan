***
- [Visionect Software Suite - Instalacja w Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
- [Visionect Software Suite - Instalacja w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md)
- [Dodatek Joan 6/13 PRO: AppDaemon Dashboard Generator](https://github.com/Adam7411/joan_generator/)
- [Baza wiedzy dla developera](./docs/README.md)
***

<div align="right">
<a href="README.md">English</a> | <strong>Polski</strong>
</div>

<p align="center">
  <a href="https://github.com/Adam7411/visionect_joan/releases"><img alt="Wydanie" src="https://img.shields.io/github/v/release/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan"><img alt="Licencja" src="https://img.shields.io/github/license/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan/stargazers"><img alt="Gwiazdki" src="https://img.shields.io/github/stars/Adam7411/visionect_joan?style=for-the-badge"></a>
</p>

<h1 align="center">Visionect Joan dla Home Assistant</h1>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz repozytorium w HACS" />
  </a>
</p>

> Integracja **`visionect_joan`** zmienia energooszczędny tablet e‑ink **Joan 6 / 13 PRO** w konfigurowalne centrum informacji i sterowania dla Twojego systemu Home Assistant: panele energii, kalendarz, lista zakupów / zadań, grafy sensorów, pogoda (różne układy), kanał RSS, snapshot kamery, PIN keypad, panel crypto, pokazy slajdów oraz interaktywne przyciski / webhooki. Wspiera **AppDaemon** + **[joan_generator](https://github.com/Adam7411/joan_generator)** z profilem **Eco** i ochroną baterii.

<img width="1280" height="800" alt="Ekran główny Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
⬇️ Sprzęt: Joan 6 lub 13 PRO ⬇️  
<br>
<img width="421" height="328" alt="Joan 6 - tablet e-ink" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />
<img width="1484" height="1278" alt="Joan 13 PRO" src="https://github.com/user-attachments/assets/99fb87e0-3d8c-4ecc-b411-ad81f203665d" />
</p>

---

## Spis treści

1. [Zalecana konfiguracja (AppDaemon)](#zalecana-konfiguracja-appdaemon)
2. [Opis i przeznaczenie](#opis-i-przeznaczenie)
3. [Najważniejsze funkcje](#najważniejsze-funkcje)
4. [Zrzuty ekranu](#zrzuty-ekranu)
5. [Instalacja](#instalacja)
6. [Konfiguracja Visionect Software Suite (VSS)](#konfiguracja-visionect-software-suite-vss)
7. [Opcje integracji (UI)](#opcje-integracji-ui)
8. [Predefiniowane widoki (Views)](#predefiniowane-widoki-views)
9. [Encje](#encje)
10. [Profile synchronizacji i battery guard](#profile-synchronizacji-i-battery-guard)
11. [Usługi – skrót](#usługi--skrót)
12. [Szczegóły usług](#szczegóły-usług)
13. [Warstwa interaktywna i priorytet „Wstecz”](#warstwa-interaktywna-i-priorytet-wstecz)
14. [Przykłady automatyzacji](#przykłady-automatyzacji)
15. [Wydajność i oszczędzanie baterii](#wydajność-i-oszczędzanie-baterii)
16. [Bezpieczeństwo i webhooki](#bezpieczeństwo-i-webhooki)
17. [Rozwiązywanie problemów (Troubleshooting)](#rozwiązywanie-problemów-troubleshooting)
18. [FAQ](#faq)
19. [Licencja](#licencja)

---

## Zalecana konfiguracja (AppDaemon)

U większości użytkowników tablet **cały czas** pokazuje jeden dashboard **AppDaemon** wygenerowany dodatkiem **Joan Dashboard Generator**:

```
joan_generator → pliki *.dash → AppDaemon :5050 → tablet (URL sesji VSS)
visionect_joan → bateria, recovery, alerty, chwilowe overlaye (send_*)
```

| Ustawienie | Przykład |
|------------|----------|
| URL AppDaemon | `http://192.168.100.80:5050/Dashboard?skin=default&widget=joan_salon&count=1` |
| **Main menu URL** (`configuration.yaml`) | ten sam adres — cel przycisku Wstecz i probe recovery |
| **Recovery probe URL** (YAML, opcjonalnie) | domyślnie = Main menu URL |
| **Tryb synchronizacji** (select per tablet) | **Eco** |

AppDaemon sam odświeża widgety z encji HA — **nie** trzeba co chwilę wołać `set_url`. Usługi `send_*` używaj jako **krótkich overlayów** z `auto_return_seconds`.

Opcjonalnie w `configuration.yaml`:

```yaml
visionect_joan:
  main_menu_url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
  recovery_probe_url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
  views:
    - name: MainMenu
      url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
```

---

## Opis i przeznaczenie

Integracja działa jako „most” między Home Assistant a Visionect Software Suite (VSS). Umożliwia generowanie dynamicznych, zoptymalizowanych pod e‑ink ekranów na Joan 6 / 13 PRO, reagujących na kontekst (zdarzenia, strefy, czas, czujniki). Zamiast zwykłego dashboardu możesz wysłać *w pełni renderowany* widok: panel energii, lista zadań z interaktywnym odhaczaniem (webhook), graf historii, sekcja pogody z wykresem, keypad PIN, panel crypto czy panel 12 przycisków.

Monitoruje też stan tabletu, baterię, orphan sesji VSS, oferuje **Naprawy HA** (Repairs) i **Eco recovery** po restarcie Home Assistant.

---

## Najważniejsze funkcje

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
- Ustawienia w UI: predefiniowane widoki, powiadomienia, recovery page, Ollama.
- Zarządzanie: rotacja ekranu, czyszczenie WebKit cache, wymuszenie odświeżenia, sleep/wake.
- Parametry renderingu: dithering, encoding (głębia bitowa).
- Safe Config TCLV (odczyt / zapis / przywracanie kopii).
- Mechanizm cleanup plików tymczasowych (snapshoty / grafy) w `www/`.

<details>
  <summary>Zrzut: dolny pasek z przyciskami</summary>
  <img width="561" height="705" alt="Dolny pasek akcji" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />
</details>

<details>
  <summary>Opcje integracji (widoki predefiniowane)</summary>
  <img width="838" height="566" alt="Opcje integracji" src="https://github.com/user-attachments/assets/ef9ef69b-413d-4ca4-86d9-373d3117880a" />
</details>

---

## Zrzuty ekranu

<details>
  <summary>Kliknij, aby rozwinąć listę przykładowych ekranów</summary>
  <img width="425" height="574" alt="Panel startowy" src="https://github.com/user-attachments/assets/fea6f969-3785-4efd-961a-58e9086becfd" />
  <img width="758" height="1024" alt="Panel domowy" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="Kanał RSS" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="Pogoda szczegółowa" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="Keypad PIN" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="Kalendarz miesięczny" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="Snapshot kamery" src="https://github.com/user-attachments/assets/a73e16a8-af85-47a0-9088-f21b932f9231" />
  <img width="758" height="1024" alt="Kod QR" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="Graf sensora" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Tekst wiadomości" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="Drugi układ pogody" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="Status panel encji" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="Panel energii" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Podgląd live" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="Diagnostyka / bateria" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
</details>

---

## Instalacja

### Przez HACS (zalecane)

1. Zainstaluj [HACS](https://hacs.xyz/) (jeśli nie masz).
2. W HACS → Integrations kliknij ⋮ → Custom repositories.
3. Dodaj repo: `https://github.com/Adam7411/visionect_joan` jako „Integration”.
4. Odnajdź „Visionect Joan” → Install.
5. Restart Home Assistant.

### Ręcznie

1. Pobierz najnowszy release (`visionect-joan.zip` albo „Source code”).
2. Wypakuj do: `/config/custom_components/visionect_joan/`.
3. Restart HA.

**Wymagania:** VSS ([visionect-v3-allinone](https://github.com/Adam7411/visionect-v3-allinone)), tablet w VSS, opcjonalnie AppDaemon + joan_generator.

---

## Konfiguracja Visionect Software Suite (VSS)

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

<img width="575" height="615" alt="Encje urządzenia" src="https://github.com/user-attachments/assets/a70ccc87-bbff-4fa4-aec5-f4e602709f19" />

---

## Opcje integracji (UI)

**Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj**

| Menu | Co ustawiasz |
|------|----------------|
| **Zarządzaj widokami** | Dodaj / edytuj / usuń widoki (nazwa + URL) |
| **Domyślny adres URL** | Token strony recovery — wklej URL do VSS → Settings → HTML Backend → Default URL |
| **Czyszczenie cache i dysku** | Wiek plików tymcz. w `www/` |
| **Język tabletu** | PL / EN / DE / … / Auto |
| **Powiadomienia** | Bateria, ErrorCode, offline, orphan |
| **Analiza logów Ollama** | URL, model, interwał (opcjonalnie) |

### Podmenu Powiadomienia

| Sekcja | Parametry |
|--------|-----------|
| **Bateria** | Próg 5/10/15 %; alert na tablecie; powiadomienia HA; battery guard interval |
| **Błędy (ErrorCode)** | Powiadomienie HA przy kodzie błędu VSS |
| **Offline** | Włącz/wyłącz; próg 1 / 4 / 24 h (aktualizacja co godzinę, v3.9.13+) |
| **Stan / orphan** | Automatyczne powiadomienie przy problemie sesji |

---

## Predefiniowane widoki (Views)

Widoki zapisujesz w Opcjach integracji:

1. Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.
2. „Add view” → Nazwa + URL.
3. Te nazwy możesz potem wybierać przez encję `Choose view` (select) lub podawać jako `predefined_url` / `url` w usługach.

Format legacy („Name: URL” linia po linii) jest automatycznie migrowany.

---

## Encje

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
  <summary>Pokaż zrzut ekranu</summary>
  <img width="658" height="1002" alt="Zrzut encji" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>

---

## Profile synchronizacji i battery guard

**Select: Tryb synchronizacji z Home Assistant**

| Profil | Kiedy używać | Zachowanie |
|--------|--------------|------------|
| **Eco** | Stały dashboard AppDaemon (domyślny) | Minimalny polling; **nie** robi PUT do VSS gdy URL się nie zmienił |
| **Normal** | Okazjonalne overlaye | Battery guard aktywny |
| **Alert** | Kamery, pilne alerty | Szybszy refresh |

**Usługa `set_url`:** pole **`wake_tablet: true`** — wymusza zapis sesji nawet w Eco.

**Eco recovery (v3.9.14):** po restarcie HA, gdy probe AppDaemon OK i URL sesji poprawny → pomijany zbędny restart sesji VSS.

**Zdarzenie:** `visionect_joan_command_result` — m.in. `push_result` (`success`, `skipped_unchanged`, `skipped_guard`).

---

## Usługi – skrót

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
| `visionect_joan.set_session_options` | Render | N/A | Głębia / dithering |
| `visionect_joan.clear_web_cache` | Utrzymanie | N/A | Czyszczenie cache (opcjonalny restart) |
| `visionect_joan.force_refresh` | Utrzymanie | N/A | Restart sesji |
| `visionect_joan.set_display_rotation` | Utrzymanie | N/A | Rotacja + reboot |
| `visionect_joan.clear_display` | Utrzymanie | N/A | Pusty ekran |
| `visionect_joan.sleep_device` / `wake_device` | Zasilanie | N/A | Sen / wybudzenie |
| `visionect_joan.read_safe_device_config` | Safe TCLV | N/A | Odczyt konfiguracji urządzenia |
| `visionect_joan.apply_safe_device_config` | Safe TCLV | N/A | Zapis + kopia zapasowa |
| `visionect_joan.restore_safe_device_config` | Safe TCLV | N/A | Przywróć kopię |

Pełna lista pól: `services.yaml` oraz **Narzędzia deweloperskie → Usługi**.

Wspólne pola overlay: `add_back_button`, `back_button_url`, `auto_return_seconds`, `click_anywhere_to_return`, `click_anywhere_to_action`, `action_webhook_id`, `screen_size`.

---

## Szczegóły usług

Poniżej opis wybranych usług wraz ze zrzutami ekranu (zwijane sekcje). Pełna lista pól i selektorów znajduje się w `services.yaml` oraz w UI Home Assistant (Developer Tools → Services).

### Wyświetlanie treści

- `visionect_joan.send_button_panel`  
  - Umożliwia stworzenie siatki do 12 konfigurowalnych przycisków. Każdy przycisk może mieć własną nazwę, ikonę i przypisany unikalny `webhook_id`, który wywołuje automatyzacje w Home Assistant.  
  - Wskazówka: Panel wysyła sygnały do Home Assistant za pomocą webhooków. Aby przycisk działał, musisz stworzyć automatyzację, która na ten sygnał zareaguje.  
  - ⚠️ Ważne ograniczenie: Brak informacji o stanie. Panel przycisków działa jednokierunkowo (stateless). Wygląd nie aktualizuje się zależnie od stanu urządzeń (do stanów użyj np. dashboardu AppDaemon).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1214" height="3814" alt="Panel przycisków" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
  </details>

***

- `visionect_joan.set_url`  
  - Ustawia dowolny URL lub nazwę zdefiniowanego widoku (predefined).  
  - Wskazówka: nazwy widoków dopasowywane są bez rozróżniania wielkości liter. Dodawaj/edytuj widoki w: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.  
  - **`wake_tablet: false`** (domyślnie w Eco) oszczędza baterię, gdy URL się nie zmienił.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1220" height="595" alt="Ustaw URL" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
  </details>

***

- `visionect_joan.send_text`  
  - Wysyła sformatowany tekst (obsługuje Jinja2), opcjonalnie z obrazem i różnymi układami (text only, text + image).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1225" height="2066" alt="Wiadomość tekstowa" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />
  </details>

***

- `visionect_joan.send_image_url`  
  - Wyświetla obraz z podanego URL (PNG/JPG/SVG/WebP). Dla plików lokalnych użyj `http://<HA_IP>:8123/local/...`.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1234" height="1448" alt="Obraz z URL" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />
  </details>

***

- `visionect_joan.send_camera_snapshot`  
  - Tworzy snapshot z encji `camera` i wyświetla go (z podpisem i rotacją obrazu).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1223" height="1472" alt="Snapshot kamery" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf-25237e08" />
  </details>

***

- `visionect_joan.send_status_panel`  
  - Panel statusów dowolnych encji: ikony + nazwy + wartości (z tłumaczeniami stanów).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1230" height="1416" alt="Panel statusów" src="https://github.com/user-attachments/assets/bb21ddb7-77bf-4db1-bc57-9ecf2c2d5021" />
  </details>

***

- `visionect_joan.send_energy_panel`  
  - Duży panel energii (bieżący pobór + karty: produkcja/import/eksport/zużycie dzienne). Świetny w pionie.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1230" height="1423" alt="Panel energii" src="https://github.com/user-attachments/assets/66b3f26d-f5c3-4276-b837-de6b85cf9fcf" />
  </details>

***

- `visionect_joan.send_weather`  
  - 3 layouty: szczegółowy, dzienna lista, panel z wykresem 24h (auto ikony dzień/noc).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1225" height="1237" alt="Pogoda" src="https://github.com/user-attachments/assets/588660d8-e0ff-48b3-b7a5-6d9432cd2329" />
  </details>

***

- `visionect_joan.send_calendar`  
  - Lista wydarzeń (1–31 dni) lub siatka miesięczna z podglądem dnia.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1207" height="801" alt="Kalendarz miesięczny" src="https://github.com/user-attachments/assets/83f5d345-69ef-42af-84d3-f7f4f3c3b1a0" />
  </details>

***

- `visionect_joan.send_todo_list`  
  - Lista zadań (w tym Shopping List). Duże, czytelne pozycje; wspiera interaktywne odhaczanie przez webhook.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1216" height="1201" alt="Lista zadań" src="https://github.com/user-attachments/assets/6735340b-bec9-47a6-a72e-07d16da20943" />
  </details>

***

- `visionect_joan.send_sensor_graph`  
  - Wykres historii wskazanych sensorów (line lub bar), automatycznie dopasowany do orientacji ekranu.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1219" height="1895" alt="Wykres sensora" src="https://github.com/user-attachments/assets/c5507b3b-28e6-47a1-a88a-11d936f2f35b" />
  </details>

***

- `visionect_joan.send_rss_feed`  
  - Pobiera i pokazuje najnowsze wpisy z kanału RSS/Atom (stronicowanie, nagłówek, ikony).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1225" height="1255" alt="Kanał RSS" src="https://github.com/user-attachments/assets/56316ce1-8350-49d5-a624-2f7a880b8a4e" />
  </details>

***

- `visionect_joan.send_crypto`  
  - Panel notowań kryptowalut z CryptoCompare (bitcoin, ethereum, …; waluta PLN/USD/EUR) ze sparkline.

### Interaktywność i nawigacja

- `visionect_joan.send_qr_code`  
  - Generuje kod QR (np. gościnne Wi‑Fi) z opcjonalnym podpisem (nad/po QR).
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1223" height="1765" alt="Kod QR" src="https://github.com/user-attachments/assets/a55360c9-9f17-4b81-baf9-b990692bc2a0" />
  </details>

***

- `visionect_joan.start_slideshow`  
  - Odtwarza listę widoków (predefiniowane nazwy lub pełne lokalne adresy URL) w pętli z czasem per slajd.  
  - Uwaga: Slideshow renderuje strony w `iframe`. Wiele zewnętrznych stron (np. google.com, home-assistant.io) blokuje osadzanie – używaj lokalnych URL lub widoków. W profilu **Eco** min. ~120 s na slajd.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="606" height="729" alt="Slideshow" src="https://github.com/user-attachments/assets/91d25761-2709-417b-9a2c-edf2104c5869" />
  </details>

***

- `visionect_joan.send_keypad`  
  - Pełnoekranowa klawiatura numeryczna. Wpisany PIN jest POSTowany do webhooka HA (`trigger.json.pin`).  
  - Wymaga automatyzacji z wyzwalaczem Webhook po stronie HA.
  <details>
    <summary>Pokaż zrzut ekranu</summary>
    <img width="1220" height="632" alt="Wywołanie send_keypad" src="https://github.com/user-attachments/assets/5df2b9d9-ae6e-4a60-9f9f-c787f7658135" />
  </details>

***

### Safe Config (TCLV)

- `visionect_joan.read_safe_device_config` — odczyt (heartbeat, system screens, touch).  
- `visionect_joan.apply_safe_device_config` — zapis + automatyczna kopia zapasowa.  
- `visionect_joan.restore_safe_device_config` — przywrócenie ostatniej kopii.

### Parametry renderingu i zarządzanie

- `visionect_joan.set_session_options` – Ustawia parametry sesji (`encoding` – głębia bitowa, `dithering`).  
- `visionect_joan.clear_web_cache` – Czyści cache WebKit (opcjonalny restart sesji).  
- `visionect_joan.force_refresh` – Natychmiastowy restart sesji (odświeża bieżący widok).  
- `visionect_joan.set_display_rotation` – Trwale zmienia orientację ekranu (wymaga krótkiego restartu).  
- `visionect_joan.clear_display` – Czyści ekran (białe tło).  
- `visionect_joan.sleep_device` / `visionect_joan.wake_device` – Usypianie/wybudzanie (oszczędzanie baterii).

**Diagnostyka w UI:** przycisk **Sprawdź stan**, **Analiza logów Ollama**, Naprawy HA, encja `dashboard_ok`.

---

## Warstwa interaktywna i priorytet „Wstecz”

Priorytet określania celu powrotu:

1. `back_button_url` (w wywołaniu usługi)
2. Per‑device selektor `Back button target`
3. Globalny `Main menu URL` (`configuration.yaml`)

Wyłączenie widocznych przycisków:

- `click_anywhere_to_action: true` → cały ekran = akcja (webhook).
- `click_anywhere_to_return: true` → cały ekran = powrót.  

Włączenie jednej z opcji ukrywa dolny pasek.

**Overlay → AppDaemon:** przed `send_*` integracja zapamiętuje bieżący URL; `auto_return_seconds` lub ← przywraca dashboard.

**Recovery po restarcie HA:** HTTP GET recovery probe URL → Eco skip restart sesji gdy URL OK → safety net 5/8/10 min.

---

## Przykłady automatyzacji

Poniżej przykłady z komentarzami (`#`).

### 0. Stały dashboard AppDaemon (raz)

```yaml
service: visionect_joan.set_url
target:
  device_id: 00000000000000000000000000000000  # ← Wstaw swoje device_id
data:
  url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
  wake_tablet: true  # Wymuś zapis sesji przy pierwszym ustawieniu
```

### 1. Prosty komunikat

```yaml
service: visionect_joan.send_text            # Wywołujemy usługę wysyłającą tekst
target:
  device_id: 00000000000000000000000000000000  # ← Wstaw swoje device_id (Urz. i usługi → urządzenie → trzy kropki → Kopiuj ID)
data:
  message: "Witaj!\n{{ now().strftime('%H:%M') }}"  # Treść (obsługa Jinja2)
  text_size: 42                                     # Rozmiar czcionki (px)
  auto_return_seconds: 60                           # Powrót do AppDaemon po 60 s
```

### 2. Włącz światło przyciskiem (→)

Automatyzacja webhook (reaguje na naciśnięcie przycisku):

```yaml
alias: "Joan: światło salon"             # Nazwa automatyzacji
trigger:
  - platform: webhook
    webhook_id: joan_light_on            # MUSI się zgadzać z action_webhook_id w wywołaniu usługi
action:
  - service: light.turn_on
    target:
      entity_id: light.salon             # Encja światła do włączenia
```

Wyświetlenie widoku z przyciskiem akcji:

```yaml
service: visionect_joan.send_text
target:
  device_id: 00000000000000000000000000000000  # Joan 6
data:
  message: "Światło w salonie"           # Tekst na ekranie
  action_webhook_id: joan_light_on       # Po naciśnięciu (→) zostanie wywołany ten webhook
  add_back_button: true                   # Dodaj przycisk Wstecz (←)
  back_button_url: MainMenu               # Cel Wstecz: nazwa widoku lub pełny URL
  auto_return_seconds: 120
```

### 3. Keypad PIN z powrotem do widoku

Pierwsze wywołanie (pokazanie klawiatury PIN):

```yaml
service: visionect_joan.send_keypad
target:
  device_id: 266a72218733bb9a056aff49bf6f8e2d  # Joan 6
data:
  title: "PIN"                         # Nagłówek nad klawiaturą (opcjonalny)
  action_webhook_id: joan_pin         # Webhook, na który zostanie POSTowany PIN (JSON: {"pin": "1234"})
```

Automatyzacja (walidacja PIN i nawigacja):

```yaml
alias: "PIN → dostęp"                      # Nazwa automatyzacji
mode: single
trigger:
  - platform: webhook
    webhook_id: joan_pin                   # Musi odpowiadać action_webhook_id z send_keypad
variables:
  correct_pin: "321"                       # PIN referencyjny (rozważ secrets/input_text)
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.json.pin == correct_pin }}"  # Porównanie PIN
        sequence:
          - service: visionect_joan.set_url
            target:
              device_id: 266a72218733bb9a056aff49bf6f8e2d           # Joan 6
            data:
              url: DomPanel                                         # Nazwa widoku lub pełny URL
              wake_tablet: true
    default:
      - service: visionect_joan.send_text
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          message: "Błędny PIN!"             # Komunikat o błędnym PIN
          text_size: 48
          add_back_button: true
          back_button_url: MainMenu
      - delay: "00:00:03"                    # Krótka pauza
      - service: visionect_joan.send_keypad  # Ponowne wyświetlenie klawiatury
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          title: "PIN"
          action_webhook_id: joan_pin
```

### 4. Panel energii po wejściu do strefy

```yaml
alias: "Powrót do domu → Panel energii"   # Opis celu automatyzacji
trigger:
  - platform: zone
    entity_id: person.jan                 # Osoba, której wejście do strefy śledzimy
    zone: zone.home                       # Strefa "home"
    event: enter                          # Zdarzenie wejścia
action:
  - service: visionect_joan.send_energy_panel
    target:
      device_id: 00000000000000000000000000000000  # Joan 6
    data:
      power_usage_entity: sensor.house_power           # Aktualny pobór mocy (W/kW)
      daily_consumption_entity: sensor.energy_daily_consumption  # Dzienne zużycie (kWh)
      add_back_button: true
      back_button_url: MainMenu                        # Dokąd wrócić po (←)
      auto_return_seconds: 180
```

### 5. Slideshow – rotacja menu informacyjnego

```yaml
service: visionect_joan.start_slideshow
target:
  device_id: 00000000000000000000000000000000  # Joan 6
data:
  views: |                                     # Każda linia: nazwa widoku LUB pełny lokalny URL
    MainMenu
    PogodaPanel
    http://192.168.1.10:8123/local/ogloszenia.png
  seconds_per_slide: 120                       # Eco: min. ~120 s; krócej = większe zużycie baterii
  loop: true                                   # Po ostatnim wróć do pierwszego
  add_back_button: true                        # Dodaj (←) z powrotem do np. MainMenu
```

### 6. Snapshot kamery po ruchu

```yaml
alias: "Ruch → Snapshot"                  # Gdy wykryto ruch, pokaż zdjęcie z kamery
trigger:
  - platform: state
    entity_id: binary_sensor.motion_hall  # Czujka ruchu
    to: "on"
action:
  - service: visionect_joan.send_camera_snapshot
    target:
      device_id: 00000000000000000000000000000000  # Joan 6
    data:
      camera_entity: camera.hallway                # Encja kamery
      caption: "Ruch: {{ now().strftime('%H:%M:%S') }}"  # Podpis pod obrazem
      add_back_button: true
      back_button_url: MainMenu
      auto_return_seconds: 90
```

### 7. Nasłuch wyniku push (battery guard)

```yaml
trigger:
  - platform: event
    event_type: visionect_joan_command_result
action:
  - service: logbook.log
    data:
      message: "{{ trigger.event.data }}"
```

---

## Wydajność i oszczędzanie baterii

| Element | Rekomendacja |
|---------|--------------|
| **Na co dzień** | AppDaemon + profil **Eco**; unikaj powtarzanego `set_url` |
| **`wake_tablet`** | `true` tylko przy pierwszym ustawieniu URL lub świadomym wybudzeniu |
| `ReloadTimeout` | 60–300 s dla paneli informacyjnych; wysokie dla statycznego AppDaemon |
| Slideshow | ≥ 120 s w Eco; ≥ 30 s w Normal |
| Encoding | `1` dla tekstu / prostych widoków; `4` dla zdjęć i cieniowanych wykresów |
| Dithering | `none` dla czytelności; `floyd-steinberg` dla obrazów |
| Duże obrazy | Skaluj do rozdzielczości ekranu przed wysłaniem |
| Recovery probe | Ustaw na URL AppDaemon |
| Noc | Harmonogram snu tabletu; `sleep_device` opcjonalnie |
| Sleep | Użyj `sleep_device` gdy tablet nie potrzebuje aktualizacji dłużej (np. noc) |

---

## Bezpieczeństwo i webhooki

- Webhooki HA (`/api/webhook/<id>`) nie są domyślnie uwierzytelnione – traktuj je jako lokalne triggery.
- Nie wystawiaj przypadkowo portu 8123 publicznie bez reverse proxy/autoryzacji.
- Dla wrażliwych akcji używaj losowych identyfikatorów (`joan_akcji_9342hf` itp.).
- PIN nie zapisuj w logach – porównuj przez szablony lub przechowuj w `input_text`/secrets.
- Oddzielny host? Zadbaj o poprawny `internal_url`, inaczej webhook może być źle skonstruowany.
- Token strony recovery — traktuj jak hasło.

---

## Rozwiązywanie problemów (Troubleshooting)

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Brak reakcji przycisku | Zły `webhook_id` / brak automatyzacji | Podgląd zdarzeń → sprawdź wejście `webhook` |
| Nie odświeża się ekran | Stara sesja | `force_refresh` lub zmień `ReloadTimeout` |
| Connection refused po restarcie HA | AppDaemon niedostępny | Recovery probe URL; log `Eco recovery skip` |
| Zły ekran | Zły URL sesji | `sensor.*_configured_url`, `binary_sensor.*_dashboard_ok` |
| Alert offline „zawsze 4 h” | Stary bug (naprawiony v3.9.13) | Przeładuj integrację |
| „Stare” obrazy / CSS | Cache WebKit | `clear_web_cache` (+ opcjonalny restart) |
| Pusty graf | Brak historii / recorder wyłączony | Włącz zapis historii dla sensorów |
| Błędna rotacja | Sesja nie przeładowana | Po rotacji `set_display_rotation` + reboot |
| PIN zawsze błędny | Automatyzacja nie odbiera JSON | Sprawdź `trigger.json` w Template Editor |
| Kanał RSS pusty | Feed niedostępny / błąd sieci | Otwórz URL w przeglądarce, sprawdź logi |
| Orphan / VSS | Problem sesji | Naprawy HA; przycisk **Sprawdź stan** |

Aktywacja debug:

```yaml
logger:
  logs:
    custom_components.visionect_joan: debug
```

Po zmianach YAML: **Sprawdź konfigurację** w HA.

---

## FAQ

**Najlepsza konfiguracja przy stałym dashboardzie?**  
[joan_generator](https://github.com/Adam7411/joan_generator) + AppDaemon + jednorazowy `set_url` + Eco.

**Czy przyciski mogą pokazywać stan urządzeń (np. światła)?**  
Obecnie panel 12 przycisków jest stateless (brak sprzężenia zwrotnego). Do prezentacji stanów użyj np. paneli statusu, AppDaemon lub własnych dashboardów.

**Ghosting na ekranie – normalne?**  
Częste odświeżenia e‑ink powodują artefakty. Ogranicz liczbę aktualizacji i wybierz wyższy kontrast (encoding=1).

**Czy mogę używać z innymi modelami Joan?**  
Testowane na Joan 6 / 13 PRO. Inne modele mogą działać częściowo – brak oficjalnych testów.

**Dlaczego zewnętrzna strona nie wyświetla się w slideshow?**  
Wiele domen blokuje iframe (CSP / X-Frame-Options). Używaj lokalnych URL / predefiniowanych widoków.

**Czy mogę wysyłać własny HTML?**  
Tak – `data:text/html,<html>...</html>` jako URL w `set_url` lub automatycznie generowane przez usługi.

**Czy integracja rotuje treść sama?**  
Nie domyślnie — AppDaemon odświeża widgety. Slideshow/automaty opcjonalnie.

---

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Testowany na **Joan 6 / 13 PRO**; inne modele nie były weryfikowane.
- Do szybszego rozwoju użyto AI.
- **Wersja:** 3.9.14 · **Dokumentacja:** [`docs/README.md`](./docs/README.md) · [`docs/INTEGRATION_KNOWLEDGE.md`](./docs/INTEGRATION_KNOWLEDGE.md)

***
- [Visionect Software Suite - Instalacja w Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
- [Visionect Software Suite - Instalacja w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md)
- [Dodatek Visionect Joan dla Home Assistant](https://github.com/Adam7411/visionect_joan/blob/main/README_pl.md)
- [Dodatek Joan 6/13 PRO: AppDaemon Dashboard Generator](https://github.com/Adam7411/joan_generator/)
***

## Licencja

MIT
