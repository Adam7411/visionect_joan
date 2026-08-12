***
- [Visionect Software Suite - Instalacja w Proxmox](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)
- [Visionect Server v3 (All-in-One) w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md)
- [Dodatek Joan 6/13 PRO: Generator dashboardów AppDaemon](https://github.com/Adam7411/joan_generator/)
- [Visionect Software Suite - Instalacja w Home Assistant](https://github.com/Adam7411/visionect-v3-allinone/blob/main/visionect-v3-allinone/README_pl.md)
- [Dodatek Joan 6/13 PRO: AppDaemon Dashboard Generator](https://github.com/Adam7411/joan_generator/)
- [Baza wiedzy dla developera](./docs/INTEGRATION_KNOWLEDGE.md)
***
<div align="center">
<div align="right">
<a href="README.md">English</a> | <strong>Polski</strong>
</div>
[English](./README.md) | **Polski**
<p align="center">
  <a href="https://github.com/Adam7411/visionect_joan/releases"><img alt="Wydanie" src="https://img.shields.io/github/v/release/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan"><img alt="Licencja" src="https://img.shields.io/github/license/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan/stargazers"><img alt="Gwiazdki" src="https://img.shields.io/github/stars/Adam7411/visionect_joan?style=for-the-badge"></a>
</p>
![Version](https://img.shields.io/badge/wersja-3.9.14-blue) ![E-Ink](https://img.shields.io/badge/Zoptymalizowane%20pod-E--Ink-black) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integracja%20custom-41bdf5)
# Visionect Joan dla Home Assistant <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz HACS" /></a>
# Visionect Joan dla Home Assistant
> Integracja **`visionect_joan`** łączy energooszczędny tablet e‑ink **Joan 6 / 13 PRO** z Home Assistant przez **Visionect Software Suite (VSS)** — z ochroną baterii, gotowymi ekranami e‑ink, wsparciem **AppDaemon** + **[joan_generator](https://github.com/Adam7411/joan_generator)** oraz interaktywnymi webhookami.
</div>
<img width="1280" height="800" alt="Ekran główny Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />
> Integracja **`visionect_joan`** łączy energooszczędne tablety e-ink **Joan 6 / 13 PRO** z Home Assistant przez **Visionect Software Suite (VSS)** — z ochroną baterii przy URL, gotowymi ekranami e-ink, wsparciem dashboardu AppDaemon i interaktywnymi webhookami.
<p align="center">
⬇️ Sprzęt: Joan 6 lub 13 PRO ⬇️  
<br>
<img width="421" height="328" alt="Joan 6 - tablet e-ink" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />
<img width="1484" height="1278" alt="Joan 13 PRO" src="https://github.com/user-attachments/assets/99fb87e0-3d8c-4ecc-b411-ad81f203665d" />
</p>
---

[2 lines collapsed]

1. [Zalecana konfiguracja (AppDaemon)](#zalecana-konfiguracja-appdaemon)
2. [Opis i przeznaczenie](#opis-i-przeznaczenie)
3. [Najważniejsze funkcje](#najważniejsze-funkcje)
4. [Instalacja](#instalacja)
5. [VSS i konfiguracja integracji](#vss-i-konfiguracja-integracji)
6. [Profile synchronizacji i battery guard](#profile-synchronizacji-i-battery-guard)
7. [Encje](#encje)
8. [Usługi — skrót](#usługi--skrót)
9. [Warstwa interaktywna i recovery](#warstwa-interaktywna-i-recovery)
10. [Przykłady automatyzacji](#przykłady-automatyzacji)
11. [Wydajność i bateria](#wydajność-i-bateria)
12. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
13. [FAQ](#faq)
14. [Rozwój integracji](#rozwój-integracji)
15. [Licencja](#licencja)
4. [Zrzuty ekranu](#zrzuty-ekranu)
5. [Instalacja](#instalacja)
6. [Konfiguracja VSS i integracji](#konfiguracja-vss-i-integracji)
7. [Opcje integracji (UI)](#opcje-integracji-ui)
8. [Predefiniowane widoki (Views)](#predefiniowane-widoki-views)
9. [Encje](#encje)
10. [Profile synchronizacji i battery guard](#profile-synchronizacji-i-battery-guard)
11. [Usługi – pełna lista](#usługi--pełna-lista)
12. [Szczegóły usług](#szczegóły-usług)
13. [Warstwa interaktywna, recovery i zdarzenia](#warstwa-interaktywna-recovery-i-zdarzenia)
14. [Przykłady automatyzacji](#przykłady-automatyzacji)
15. [Wydajność i oszczędzanie baterii](#wydajność-i-oszczędzanie-baterii)
16. [Bezpieczeństwo i webhooki](#bezpieczeństwo-i-webhooki)
17. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
18. [FAQ](#faq)
19. [Rozwój integracji](#rozwój-integracji)
20. [Licencja](#licencja)
---
## Zalecana konfiguracja (AppDaemon)
U większości użytkowników tablet **cały czas** pokazuje **jeden dashboard AppDaemon** wygenerowany dodatkiem **[Joan Dashboard Generator](https://github.com/Adam7411/joan_generator)**:
U większości użytkowników tablet **cały czas** pokazuje jeden dashboard **AppDaemon** wygenerowany dodatkiem **Joan Dashboard Generator**:
```
joan_generator (GUI) → pliki *.dash w AppDaemon → http://<HA>:5050/Dashboard?widget=…
URL sesji tabletu   → ten sam adres AppDaemon (ustawiasz raz)
visionect_joan      → operacje urządzenia: bateria, recovery, chwilowe overlaye
joan_generator → pliki *.dash → AppDaemon :5050 → tablet (URL sesji VSS)
visionect_joan → bateria, recovery, alerty, chwilowe overlaye (send_*)
```
**Ustaw raz w opcjach integracji:**
| Ustawienie | Przykład |
|------------|----------|
| URL AppDaemon | `http://192.168.100.80:5050/Dashboard?skin=default&widget=joan_salon&count=1` |
| **Main menu URL** (`configuration.yaml`) | ten sam adres — cel przycisku Wstecz i probe recovery |
| **Recovery probe URL** (YAML, opcjonalnie) | domyślnie = Main menu URL |
| **Tryb synchronizacji** | **Eco** |
| Opcja | Przykład |
|-------|----------|
| **Main menu URL** | `http://192.168.100.80:5050/Dashboard?skin=default&widget=joan_salon&count=1` |
| **Recovery probe URL** | ten sam URL (czekanie na AppDaemon po restarcie HA) |
| **Tryb synchronizacji** (per tablet) | **Eco** przy stałym dashboardzie |
AppDaemon sam odświeża widgety z encji HA — **nie** trzeba co chwilę wołać `set_url`. Usługi `send_*` używaj jako **krótkich overlayów** z `auto_return_seconds`.
AppDaemon sam odświeża widgety z encji HA — **nie** trzeba co chwilę wołać `set_url` ani robić harmonogramu treści.
Opcjonalnie w `configuration.yaml`:
Usługi wbudowane (`send_text`, snapshot kamery, pogoda, …) używaj jako **chwilowych overlayów** z `auto_return_seconds` → powrót na AppDaemon.
```yaml
visionect_joan:
  main_menu_url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
  recovery_probe_url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
  views:
    - name: MainMenu
      url: "http://192.168.100.80:5050/Dashboard?widget=joan_salon&count=1"
```
---

[1 line collapsed]

Integracja to most między **Home Assistant** a **VSS**. Umożliwia:
- Ustawianie i pilnowanie URL sesji (AppDaemon, `/local/`, Lovelace, obrazy).
- Renderowanie **ekranów overlay** zoptymalizowanych pod e-ink (energia, pogoda, kalendarz, przyciski, PIN, RSS, …).
- Sensory, diagnostykę, Naprawy (Repairs) i sterowanie synchronizacją / zasilaniem.
- Odzyskiwanie sesji po restarcie HA/VSS bez zbędnego budzenia tabletu (tryb Eco).
- Ustawianie URL sesji tabletu (AppDaemon, `/local/`, Lovelace, obrazy).
- Generowanie dynamicznych ekranów e‑ink (energia, pogoda, kalendarz, przyciski, PIN, RSS, crypto, …).
- Monitorowanie stanu, baterii, orphan sesji; **Naprawy HA** (Repairs).
- Odzyskiwanie po restarcie HA/VSS z **Eco recovery** (bez zbędnego budzenia tabletu).
---
## Najważniejsze funkcje
### Treść i nawigacja
- Dowolny URL, predefiniowane widoki, `/local/`, dashboardy AppDaemon, inline `data:text/html`.
- Gotowe ekrany: pogoda (3 układy), kalendarz, lista zadań/zakupów, panel energii, status encji, wykres sensora, RSS, QR, panel crypto, snapshot kamery.
- Dolny pasek (← Wstecz / ✔ / →) lub tap na cały ekran; webhooki do automatyzacji HA.
- Slideshow widoków/URL (w Eco — długie interwały).
- Pełna kontrola ekranu: URL, AppDaemon, `/local/`, HTML `data:`, obrazy.
- Gotowe ekrany e‑ink: pogoda (3 układy), kalendarz, to‑do/zakupy, energia, status encji, wykres sensora, RSS, QR, **panel crypto**, snapshot kamery.
- Keypad PIN i panel do 12 przycisków (webhooki HA).
- Warstwa interaktywna: pasek ← / ✔ / → lub tap na cały ekran.
- Podgląd na żywo (`camera`), encja **`dashboard_ok`** (czy URL = AppDaemon).
- **Profile Eco / Normal / Alert** + **battery guard** (skip PUT gdy URL bez zmian).
- Powiadomienia HA: bateria, offline, ErrorCode VSS, orphan.
- Recovery HTTP + probe AppDaemon po rebootcie HA.
- Opcjonalna analiza logów przez **Ollama**.
- Safe Config TCLV (odczyt / zapis / przywracanie kopii).
- Czyszczenie plików tymczasowych w `www/`.
### Zarządzanie urządzeniem
- **Profil synchronizacji** per tablet: Eco / Normal / Alert.
- **Battery guard** — pomija PUT do VSS gdy URL się nie zmienił; `wake_tablet` wymusza zapis.
- **Recovery** po rebootcie: probe HTTP AppDaemon → opcjonalny restart sesji; w **Eco skip** gdy URL już OK.
- Bezpieczny odczyt/zapis/przywracanie TCLV, rotacja ekranu, czyszczenie cache WebKit, sleep/wake.
- **Naprawy HA** przy offline VSS i orphan sesji.
- Opcjonalna analiza urządzenia przez **Ollama** (Options).
<details>
  <summary>Zrzut: dolny pasek z przyciskami</summary>
  <img width="561" height="705" alt="Dolny pasek akcji" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />
</details>
### Diagnostyka
- `sensor.*_configured_url`, `binary_sensor.*_dashboard_ok`, powiadomienia offline/bateria/błąd.
- Zdarzenie `visionect_joan_command_result` z polami `push_result`, `skipped_wake`.
- Podgląd na żywo — encja `camera`.
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
  <img width="758" height="1024" alt="Status panel encji" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
