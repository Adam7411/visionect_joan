<div align="right">
<a href="README.md">English</a> | <strong>Polski</strong>
</div>

<!-- Odznaki (możesz dodać więcej jeśli chcesz) -->
<p align="center">
  <a href="https://github.com/Adam7411/visionect_joan/releases"><img alt="Wydanie" src="https://img.shields.io/github/v/release/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan"><img alt="Licencja" src="https://img.shields.io/github/license/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan/stargazers"><img alt="Gwiazdki" src="https://img.shields.io/github/stars/Adam7411/visionect_joan?style=for-the-badge"></a>
</p>

# Visionect Joan dla Home Assistant

> Integracja `visionect_joan` zmienia energooszczędny tablet e‑ink **Joan 6** w konfigurowalne centrum informacji i sterowania dla Twojego systemu Home Assistant: panele energii, kalendarz, lista zakupów / zadań, grafy sensorów, pogoda (różne układy), kanał RSS, snapshot kamery, PIN keypad, pokazy slajdów oraz interaktywne przyciski / webhooki.

<img width="1280" height="800" alt="Ekran główny Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
⬇️ Sprzęt: Joan 6 ⬇️  
<br>
<img width="421" height="328" alt="Joan 6 - tablet e-ink" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />
</p>

---

## Spis treści
1. [Opis i przeznaczenie](#opis-i-przeznaczenie)  
2. [Najważniejsze funkcje](#najważniejsze-funkcje)  
3. [Zrzuty ekranu](#zrzuty-ekranu)  
4. [Instalacja](#instalacja)  
5. [Konfiguracja Visionect Software Suite (VSS)](#konfiguracja-visionect-software-suite-vss)  
6. [Predefiniowane widoki (Views)](#predefiniowane-widoki-views)  
7. [Encje](#encje)  
8. [Usługi – skrót](#usługi--skrót)  
9. [Szczegóły usług](#szczegóły-usług)  
10. [Warstwa interaktywna i priorytet “Wstecz”](#warstwa-interaktywna-i-priorytet-wstecz)  
11. [Przykłady automatyzacji](#przykłady-automatyzacji)  
12. [Wydajność i oszczędzanie baterii](#wydajność-i-oszczędzanie-baterii)  
13. [Bezpieczeństwo i webhooki](#bezpieczeństwo-i-webhooki)  
14. [Rozwiązywanie problemów (Troubleshooting)](#rozwiązywanie-problemów-troubleshooting)  
15. [FAQ](#faq)  
16. [Licencja](#licencja)  

---

## Opis i przeznaczenie

Integracja działa jako “most” między Home Assistant a Visionect Software Suite (VSS). Umożliwia generowanie dynamicznych, zoptymalizowanych pod e‑ink ekranów na Joan 6, reagujących na kontekst (zdarzenia, strefy, czas, czujniki). Zamiast zwykłego “dashbordu” możesz wysłać *w pełni renderowany* widok: panel energii, lista zadań z interaktywnym odhaczaniem (webhook), graf historii, sekcja pogody z wykresem, keypad PIN czy panel 12 przycisków.

---

## Najważniejsze funkcje

- Pełna kontrola ekranu: dowolny URL, lokalne strony (AppDaemon, /local/, Lovelace panel embed), obrazy, HTML “data:” inline.
- Widoki zoptymalizowane dla e‑ink:
  - Pogoda: szczegółowy, lista prognozy, panel z wykresem 24h.
  - Kalendarz: lista dni, minimalistyczny, siatka miesięczna + podgląd dnia.
  - Lista zadań / Shopping List z interaktywnym odhaczaniem przez webhook.
  - Panel energii (zużycie, produkcja, import, eksport, konsumpcja).
  - Panel statusów encji (ikony + nazwy + wartości + tłumaczenia stanów).
  - Graf historii sensorów (line / bar) z automatycznym dopasowaniem orientacji.
  - RSS / Atom – paginowany.
  - QR code (np. Wi‑Fi dla gości).
  - Keypad PIN (webhook → automatyzacja weryfikująca kod).
  - Panel 12 przycisków (stateless – każdy wywołuje własny webhook).
- Warstwa interaktywna: dolny pasek (← Wstecz / ✔ środkowy / → prawy), albo pełny ekran jako “tap to action” / “tap to back”.
- Live preview (`camera`) – bieżący zrzut ekranu jako encja kamery.
- Ustawienia w UI (bez YAML): predefiniowane widoki + globalny Main Menu URL.
- Zarządzanie: rotacja ekranu, czyszczenie WebKit cache, wymuszenie odświeżenia, sleep/wake.
- Parametry renderingu: dithering, encoding (głębia bitowa).
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
3. Dodaj repo: `Adam7411/visionect_joan` jako “Integration”.
4. Odnajdź “Visionect Joan” → Install.
5. Restart Home Assistant.

### Ręcznie
1. Pobierz najnowszy release (`visionect-joan.zip` albo “Source code”).
2. Wypakuj do: `/config/custom_components/visionect_joan/`.
3. Restart HA.

---

## Konfiguracja Visionect Software Suite (VSS)

1. Przejdź do `Ustawienia → Urządzenia i usługi`.
2. Kliknij **„+ Dodaj integrację”**.
3. Wyszukaj **„Visionect Joan”** i rozpocznij konfigurację.
4. Wprowadź dane do Visionect Software Suite: [Instalacja Visionect Software Suite](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
   - Adres serwera (np. `192.168.x.x:8081`)(adres Home Assistant)
   - Nazwa użytkownika (`admin`)
   - Hasło (`należy ustawić swoje`)
   - API Key oraz API Secret (dodasz w Visionect Software Suite → Users → Add new API key)

<img width="1567" height="425" alt="a" src="https://github.com/user-attachments/assets/37bbcdb7-e820-4275-b7ed-efc9248048e5" />

<img width="575" height="615" alt="2" src="https://github.com/user-attachments/assets/a70ccc87-bbff-4fa4-aec5-f4e602709f19" />

---

## Predefiniowane widoki (Views)

Widoki zapisujesz w Opcjach integracji:
1. Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.
2. “Add view” → Nazwa + URL.
3. Te nazwy możesz potem wybierać przez encję `Choose view` (select) lub podawać jako `predefined_url` / `url` w usługach.

Format legacy (“Name: URL” linia po linii) jest automatycznie migrowany.

---

## Encje

| Typ encji | Nazwa / Funkcja | Uwagi |
|-----------|-----------------|-------|
| `camera` | Podgląd aktualnego ekranu | Koduje zrzut jako obraz PNG |
| `sensor` | Stan online/offline, bateria, temperatura, RSSI, uptime, napięcie, pamięć, URL, diagn. | Część domyślnie włączona |
| `binary_sensor` | Ładowanie (Charger) | `is_charging` |
| `text` | Nazwa urządzenia | Zmiana wysyłana do API |
| `number` | `ReloadTimeout` (czas odświeżenia sesji) | 0–86400 s |
| `select` | Wybór widoku / Back target / dithering / głębia | Głębia (encoding) i dithering jako opcje sesji |
| `button` | Force Refresh / Reboot / Clear Web Cache | Reboot i Clear domyślnie ukryte |
| (wewnętrzne) | Panel opcji widoków | Przez OptionsFlow |

<details>
  <summary>Pokaż zrzut ekranu</summary>
  <img width="658" height="1002" alt="Zrzut encji" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>

---

## Usługi – skrót

| Usługa | Kategoria | Interaktywność (overlay) | Opis skrócony |
|--------|-----------|--------------------------|---------------|
| `visionect_joan.set_url` | Nawigacja | Opcjonalnie | Ustaw URL lub nazwę widoku |
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
| `visionect_joan.start_slideshow` | Nawigacja | Tak | Rotacja widoków / URL w pętli |
| `visionect_joan.send_keypad` | Wejście | Tak (bez Back domyślnie) | PIN → webhook |
| `visionect_joan.send_button_panel` | Akcje | Tak | Do 12 przycisków (webhook) |
| `visionect_joan.set_session_options` | Render | N/A | Głębia / dithering |
| `visionect_joan.clear_web_cache` | Utrzymanie | N/A | Czyszczenie cache (opcjonalny restart) |
| `visionect_joan.force_refresh` | Utrzymanie | N/A | Restart sesji |
| `visionect_joan.set_display_rotation` | Utrzymanie | N/A | Rotacja + reboot |
| `visionect_joan.clear_display` | Utrzymanie | N/A | Pusty ekran |
| `visionect_joan.sleep_device` / `wake_device` | Zasilanie | N/A | Sen / wybudzenie |

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
  - Uwaga: Slideshow renderuje strony w `iframe`. Wiele zewnętrznych stron (np. google.com, home-assistant.io) blokuje osadzanie – używaj lokalnych URL lub widoków.
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

### Parametry renderingu i zarządzanie

- `visionect_joan.set_session_options` – Ustawia parametry sesji (`encoding` – głębia bitowa, `dithering`).  
- `visionect_joan.clear_web_cache` – Czyści cache WebKit (opcjonalny restart sesji).  
- `visionect_joan.force_refresh` – Natychmiastowy restart sesji (odświeża bieżący widok).  
- `visionect_joan.set_display_rotation` – Trwale zmienia orientację ekranu (wymaga krótkiego restartu).  
- `visionect_joan.clear_display` – Czyści ekran (białe tło).  
- `visionect_joan.sleep_device` / `visionect_joan.wake_device` – Usypianie/wybudzanie (oszczędzanie baterii).

---

## Warstwa interaktywna i priorytet “Wstecz”

Priorytet określania celu powrotu:
1. `back_button_url` (w wywołaniu usługi)
2. Per‑device selektor `Back button target`
3. Globalny `Main menu URL` (opcje integracji)

Wyłączenie widocznych przycisków:
- `click_anywhere_to_action: true` → cały ekran = akcja (webhook).
- `click_anywhere_to_return: true` → cały ekran = powrót.  
Włączenie jednej z opcji ukrywa dolny pasek.

---

## Przykłady automatyzacji

### 1. Prosty komunikat
```yaml
service: visionect_joan.send_text
target:
  device_id: 00000000000000000000000000000000
data:
  message: "Witaj!\n{{ now().strftime('%H:%M') }}"
  text_size: 42
```

### 2. Włącz światło przyciskiem (→)
Automatyzacja webhook:
```yaml
alias: "Joan: światło salon"
trigger:
  - platform: webhook
    webhook_id: joan_light_on
action:
  - service: light.turn_on
    target:
      entity_id: light.salon
```
Wyświetlenie:
```yaml
service: visionect_joan.send_text
target:
  device_id: 00000000000000000000000000000000
data:
  message: "Światło w salonie"
  action_webhook_id: joan_light_on
  add_back_button: true
  back_button_url: MainMenu
```

### 3. Keypad PIN z powrotem do widoku
Pierwsze wywołanie:
```yaml
service: visionect_joan.send_keypad
target:
  device_id: 266a72218733bb9a056aff49bf6f8e2d
data:
  title: "PIN"
  action_webhook_id: joan_pin
```
Automatyzacja:
```yaml
alias: "PIN → dostęp"
mode: single
trigger:
  - platform: webhook
    webhook_id: joan_pin
variables:
  correct_pin: "321"
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.json.pin == correct_pin }}"
        sequence:
          - service: visionect_joan.set_url
            target:
              device_id: 266a72218733bb9a056aff49bf6f8e2d
            data:
              url: DomPanel
    default:
      - service: visionect_joan.send_text
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          message: "Błędny PIN!"
          text_size: 48
          add_back_button: true
          back_button_url: MainMenu
      - delay: "00:00:03"
      - service: visionect_joan.send_keypad
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          title: "PIN"
          action_webhook_id: joan_pin
```

### 4. Panel energii po wejściu do strefy
```yaml
alias: "Powrót do domu → Panel energii"
trigger:
  - platform: zone
    entity_id: person.jan
    zone: zone.home
    event: enter
action:
  - service: visionect_joan.send_energy_panel
    target:
      device_id: 00000000000000000000000000000000
    data:
      power_usage_entity: sensor.house_power
      daily_consumption_entity: sensor.energy_daily_consumption
      add_back_button: true
      back_button_url: MainMenu
```

### 5. Slideshow – rotacja menu informacyjnego
```yaml
service: visionect_joan.start_slideshow
target:
  device_id: 00000000000000000000000000000000
data:
  views: |
    MainMenu
    PogodaPanel
    http://192.168.1.10:8123/local/ogloszenia.png
  seconds_per_slide: 45
  loop: true
  add_back_button: true
```

### 6. Snapshot kamery po ruchu
```yaml
alias: "Ruch → Snapshot"
trigger:
  - platform: state
    entity_id: binary_sensor.motion_hall
    to: "on"
action:
  - service: visionect_joan.send_camera_snapshot
    target:
      device_id: 00000000000000000000000000000000
    data:
      camera_entity: camera.hallway
      caption: "Ruch: {{ now().strftime('%H:%M:%S') }}"
      add_back_button: true
      back_button_url: MainMenu
```

---

## Wydajność i oszczędzanie baterii

| Element | Rekomendacja |
|---------|--------------|
| `ReloadTimeout` | 60–300 s dla paneli informacyjnych; 0 tylko gdy wymuszasz pokaz statyczny |
| Slideshow | ≥ 30 s per slide; unikaj szybkiego “przerzucania” |
| Encoding | `1` dla tekstu / prostych widoków; `4` dla zdjęć i cieniowanych wykresów |
| Dithering | `none` dla czytelności; `floyd-steinberg` dla obrazów |
| Duże obrazy | Skaluj do rozdzielczości ekranu przed wysłaniem |
| Noc | Automatyzacja redukująca odświeżenia (czas lub `person` strefy) |
| Sleep | Użyj `sleep_device` gdy tablet nie potrzebuje aktualizacji dłużej (np. noc) |

---

## Bezpieczeństwo i webhooki

- Webhooki HA (`/api/webhook/<id>`) nie są domyślnie uwierzytelnione – traktuj je jako lokalne triggery.
- Nie wystawiaj przypadkowo portu 8123 publicznie bez reverse proxy/autoryzacji.
- Dla wrażliwych akcji używaj losowych identyfikatorów (`joan_akcji_9342hf` itp.).
- PIN nie zapisuj w logach – porównuj przez szablony lub przechowuj w `input_text`/secrets.
- Oddzielny host? Zadbaj o poprawny `internal_url`, inaczej webhook może być źle skonstruowany.

---

## Rozwiązywanie problemów (Troubleshooting)

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Brak reakcji przycisku | Zły `webhook_id` / brak automatyzacji | Podgląd zdarzeń → sprawdź wejście `webhook` |
| Nie odświeża się ekran | Stara sesja | `force_refresh` lub zmień `ReloadTimeout` |
| “Stare” obrazy / CSS | Cache WebKit | `clear_web_cache` (+ opcjonalny restart) |
| Pusty graf | Brak historii / recorder wyłączony | Włącz zapis historii dla sensorów |
| Błędna rotacja | Sesja nie przeładowana | Po rotacji `set_display_rotation` + reboot |
| PIN zawsze błędny | Automatyzacja nie odbiera JSON | Sprawdź `trigger.json` w Template Editor |
| Kanał RSS pusty | Feed niedostępny / błąd sieci | Otwórz URL w przeglądarce, sprawdź logi |

Aktywacja debug:
```yaml
logger:
  logs:
    custom_components.visionect_joan: debug
```

---

## FAQ

**Czy przyciski mogą pokazywać stan urządzeń (np. światła)?**  
Obecnie panel 12 przycisków jest stateless (brak sprzężenia zwrotnego). Do prezentacji stanów użyj np. paneli statusu lub własnych dashboardów.

**Ghosting na ekranie – normalne?**  
Częste odświeżenia e‑ink powodują artefakty. Ogranicz liczbę aktualizacji i wybierz wyższy kontrast (encoding=1).

**Czy mogę używać z innymi modelami Joan?**  
Testowane na Joan 6. Inne modele mogą działać częściowo – brak oficjalnych testów.

**Dlaczego zewnętrzna strona nie wyświetla się w slideshow?**  
Wiele domen blokuje iframe (CSP / X-Frame-Options). Używaj lokalnych URL / predefiniowanych widoków.

**Czy mogę wysyłać własny HTML?**  
Tak – `data:text/html,<html>...</html>` jako URL w `set_url` lub automatycznie generowane przez usługi.

---

## Licencja

MIT
