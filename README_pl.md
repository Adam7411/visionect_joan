<div align="right">
***
- [Visionect Software Suite - Instalacja w Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
- [Visionect Software Suite - Instalacja w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md)
- [Dodatek Joan 6/13 PRO: AppDaemon Dashboard Generator](https://github.com/Adam7411/joan_generator/)
- [Baza wiedzy dla developera](./docs/INTEGRATION_KNOWLEDGE.md)
***
[English](./README.md) | **Polski**
<div align="right">
<a href="README.md">English</a> | <strong>Polski</strong>
</div>
<p align="center">

[11 lines collapsed]

  </a>
</p>
> Integracja **`visionect_joan`** łączy energooszczędny tablet e‑ink **Joan 6 / 13 PRO** z Home Assistant przez **Visionect Software Suite (VSS)** — z ochroną baterii, gotowymi ekranami e‑ink, wsparciem **AppDaemon** + **[joan_generator](https://github.com/Adam7411/joan_generator)** oraz interaktywnymi webhookami.
> Integracja **`visionect_joan`** zmienia energooszczędny tablet e‑ink **Joan 6 / 13 PRO** w konfigurowalne centrum informacji i sterowania dla Twojego systemu Home Assistant: panele energii, kalendarz, lista zakupów / zadań, grafy sensorów, pogoda (różne układy), kanał RSS, snapshot kamery, PIN keypad, panel crypto, pokazy slajdów oraz interaktywne przyciski / webhooki. Wspiera **AppDaemon** + **[joan_generator](https://github.com/Adam7411/joan_generator)** z profilem **Eco** i ochroną baterii.
**Powiązane projekty:** [VSS w Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant) · [VSS w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md) · [Joan Dashboard Generator](https://github.com/Adam7411/joan_generator/) · [Baza wiedzy](./docs/INTEGRATION_KNOWLEDGE.md)
<img width="1280" height="800" alt="Ekran główny Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />
<p align="center">

[12 lines collapsed]

3. [Najważniejsze funkcje](#najważniejsze-funkcje)
4. [Zrzuty ekranu](#zrzuty-ekranu)
5. [Instalacja](#instalacja)
6. [Konfiguracja VSS i integracji](#konfiguracja-vss-i-integracji)
6. [Konfiguracja Visionect Software Suite (VSS)](#konfiguracja-visionect-software-suite-vss)
7. [Opcje integracji (UI)](#opcje-integracji-ui)
8. [Predefiniowane widoki (Views)](#predefiniowane-widoki-views)
9. [Encje](#encje)
10. [Profile synchronizacji i battery guard](#profile-synchronizacji-i-battery-guard)
11. [Usługi – pełna lista](#usługi--pełna-lista)
11. [Usługi – skrót](#usługi--skrót)
12. [Szczegóły usług](#szczegóły-usług)
13. [Warstwa interaktywna, recovery i zdarzenia](#warstwa-interaktywna-recovery-i-zdarzenia)
13. [Warstwa interaktywna i priorytet „Wstecz”](#warstwa-interaktywna-i-priorytet-wstecz)
14. [Przykłady automatyzacji](#przykłady-automatyzacji)
15. [Wydajność i oszczędzanie baterii](#wydajność-i-oszczędzanie-baterii)
16. [Bezpieczeństwo i webhooki](#bezpieczeństwo-i-webhooki)
17. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
17. [Rozwiązywanie problemów (Troubleshooting)](#rozwiązywanie-problemów-troubleshooting)
18. [FAQ](#faq)
19. [Rozwój integracji](#rozwój-integracji)
20. [Licencja](#licencja)
19. [Licencja](#licencja)
---

[11 lines collapsed]

| URL AppDaemon | `http://192.168.100.80:5050/Dashboard?skin=default&widget=joan_salon&count=1` |
| **Main menu URL** (`configuration.yaml`) | ten sam adres — cel przycisku Wstecz i probe recovery |
| **Recovery probe URL** (YAML, opcjonalnie) | domyślnie = Main menu URL |
| **Tryb synchronizacji** | **Eco** |
| **Tryb synchronizacji** (select per tablet) | **Eco** |
AppDaemon sam odświeża widgety z encji HA — **nie** trzeba co chwilę wołać `set_url`. Usługi `send_*` używaj jako **krótkich overlayów** z `auto_return_seconds`.

[12 lines collapsed]

## Opis i przeznaczenie
Integracja to most między **Home Assistant** a **VSS**. Umożliwia:
Integracja działa jako „most” między Home Assistant a Visionect Software Suite (VSS). Umożliwia generowanie dynamicznych, zoptymalizowanych pod e‑ink ekranów na Joan 6 / 13 PRO, reagujących na kontekst (zdarzenia, strefy, czas, czujniki). Zamiast zwykłego dashboardu możesz wysłać *w pełni renderowany* widok: panel energii, lista zadań z interaktywnym odhaczaniem (webhook), graf historii, sekcja pogody z wykresem, keypad PIN, panel crypto czy panel 12 przycisków.
- Ustawianie URL sesji tabletu (AppDaemon, `/local/`, Lovelace, obrazy).
- Generowanie dynamicznych ekranów e‑ink (energia, pogoda, kalendarz, przyciski, PIN, RSS, crypto, …).
- Monitorowanie stanu, baterii, orphan sesji; **Naprawy HA** (Repairs).
- Odzyskiwanie po restarcie HA/VSS z **Eco recovery** (bez zbędnego budzenia tabletu).
Monitoruje też stan tabletu, baterię, orphan sesji VSS, oferuje **Naprawy HA** (Repairs) i **Eco recovery** po restarcie Home Assistant.
---
## Najważniejsze funkcje
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
