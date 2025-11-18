<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>

<p align="center">
  <a href="https://github.com/Adam7411/visionect_joan/releases"><img alt="Wydanie" src="https://img.shields.io/github/v/release/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan"><img alt="Licencja" src="https://img.shields.io/github/license/Adam7411/visionect_joan?style=for-the-badge"></a>
  <a href="https://hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge"></a>
  <a href="https://github.com/Adam7411/visionect_joan/stargazers"><img alt="Gwiazdki" src="https://img.shields.io/github/stars/Adam7411/visionect_joan?style=for-the-badge"></a>
</p>

# Visionect Joan dla Home Assistant

> Zamień energooszczędny tablet e‑ink Joan 6 w w pełni konfigurowalne centrum informacji i akcji dla Home Assistant: panele energii, kalendarz, lista zakupów, wykresy sensorów, snapshot kamery, PIN keypad, RSS, pokazy slajdów, przyciski webhook.

<img width="1280" height="800" alt="Przykładowy ekran główny na Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

---

## Spis treści
- [Opis](#opis)
- [Najważniejsze funkcje](#najważniejsze-funkcje)
- [Zrzuty ekranu](#zrzuty-ekranu)
- [Dostępne encje](#dostępne-encje)
- [Usługi (tabela skrótowa)](#usługi-tabela-skrótowa)
- [Szczegóły usług](#szczegóły-usług)
- [Warstwa interaktywna i webhooki](#warstwa-interaktywna-i-webhooki)
- [Instalacja](#instalacja)
- [Konfiguracja](#konfiguracja)
- [Przykłady użycia](#przykłady-użycia)
- [Wydajność i bateria](#wydajność-i-bateria)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Bezpieczeństwo](#bezpieczeństwo)
- [Plan rozwoju](#plan-rozwoju)
- [Wkład / Contributing](#wkład--contributing)
- [Licencja](#licencja)

---

## Opis
Integracja `visionect_joan` komunikuje się z Visionect Software Suite (VSS), generując zoptymalizowane dla e‑ink widoki na tablecie Joan 6. Dzięki usługom możesz kontekstowo wyświetlać właściwe ekrany (np. panel energii po powrocie do domu, listę zakupów w kuchni, snapshot kamery przy ruchu).

---

## Najważniejsze funkcje
- Pełna kontrola ekranu: dowolny URL, lokalne dashboardy (AppDaemon), obrazy.
- Dynamiczne widoki: pogoda, kalendarz (lista / siatka), lista zadań / zakupów, panel energii, status encji, wykres historii sensorów, kanał RSS.
- Interaktywność:
  - Dolny pasek: Wstecz (←), Akcja (→), Środkowy (✔).
  - Opcjonalne “klik w dowolne miejsce” jako akcja.
  - Osobne webhook_id dla każdego przycisku.
- Zarządzanie energią i sesją: usypianie, wybudzanie, interwał odświeżania, orientacja, dithering, głębia bitowa.
- Podgląd na żywo: encja `camera` pokazuje aktualny obraz ekranu.
- Konfiguracja w UI: predefiniowane widoki + URL głównego menu.
- Klawiatura PIN (keypad) – weryfikacja kodu przez webhook.
- Pokaz slajdów (rotacja widoków / URL).
- Generowanie kodów QR (np. Wi‑Fi dla gości).

---

## Zrzuty ekranu
<details>
  <summary>Pokaż zrzuty ekranu</summary>
  <!-- Zachowaj oryginalne obrazy -->
  <img width="425" height="574" alt="Panel startowy" src="https://github.com/user-attachments/assets/6034d4e4-bfd5-45b2-ab4f-d52c2854f8ee" />
  <img width="758" height="1024" alt="Widok główny" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="Kanał RSS" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="Pogoda" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="PIN keypad" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="Kalendarz miesięczny" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="Snapshot kamery" src="https://github.com/user-attachments/assets/9c087661-69b0-463b-937e-19b2567cab6b" />
  <img width="758" height="1024" alt="Kod QR" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="Wykres sensora" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="Komunikat tekstowy" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="Pogoda – layout 2" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="Statusy encji" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="Panel energii" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="Podgląd na żywo" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="Diagnostyka" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
</details>

---

## Dostępne encje
(bez zmian – można później dodać tabelę)

- `camera` – podgląd ekranu na żywo
- `sensor` – bateria, temperatura, RSSI, czas pracy, napięcie, pamięć, URL, ostatnio widziany, diagnostyka, orientacja
- `binary_sensor` – ładowanie
- `text` – nazwa urządzenia
- `number` – interwał odświeżania
- `select` – wybór widoku, cel Wstecz, dithering, głębia bitowa
- `button` – Force Refresh, Reboot, Clear Web Cache

---

## Usługi (tabela skrótowa)
| Usługa | Kategoria | Interaktywność | Notatka |
|--------|-----------|----------------|---------|
| send_button_panel | Treść / Akcje | Tak | Do 12 przycisków webhook (bez stanu) |
| set_url | Nawigacja | Opcjonalnie | URL lub nazwa widoku |
| send_text | Treść | Tak | Tekst + opcjonalny obraz |
| send_image_url | Treść | Tak | Obraz z URL |
| send_camera_snapshot | Treść | Tak | Snapshot z encji `camera` |
| send_status_panel | Status | Tak | Ikony + wartości |
| send_energy_panel | Energia | Tak | Produkcja / zużycie |
| send_weather | Pogoda | Tak | Podsumowanie / lista / wykres |
| send_calendar | Kalendarz | Tak | Lista / siatka miesięczna |
| send_todo_list | Lista | Tak | Zadania / zakupy |
| send_sensor_graph | Sensory | Tak | Wykres historii |
| send_rss_feed | Treść | Tak | RSS / Atom |
| send_qr_code | Treść | Tak | QR + podpis |
| start_slideshow | Nawigacja | Tak | Pętla widoków |
| send_keypad | Wejście | Tak | Kod PIN → webhook |
| set_session_options | Render | N/A | Głębia / dithering |
| clear_web_cache | Utrzymanie | N/A | Czyszczenie cache |
| force_refresh | Utrzymanie | N/A | Restart sesji |
| set_display_rotation | Utrzymanie | N/A | Orientacja |
| clear_display | Utrzymanie | N/A | Puste tło |
| sleep_device / wake_device | Zasilanie | N/A | Oszczędzanie baterii |

---

## Szczegóły usług
(Zachowaj istniejące szczegółowe opisy; uzupełnij miejsca z “[...]”)

---

## Warstwa interaktywna i webhooki
Priorytety celu przycisku “Wstecz”:
1. `back_button_url` w wywołaniu usługi
2. encja `Back button target`
3. globalny “Main menu URL” (opcje integracji)

Webhooki są bezstanowe – przyciski nie pokazują bieżącego stanu urządzeń (światła itd.).

---

## Instalacja

### Przez HACS (zalecane)
1. Zainstaluj [HACS](https://hacs.xyz/).
2. HACS → Integrations → menu (⋮) → Custom repositories.
3. Dodaj repo jako Integration.
4. Znajdź “Visionect Joan” → Install.
5. Restart HA.

### Ręcznie
1. Pobierz najnowsze wydanie.
2. Wypakuj do `/config/custom_components/visionect_joan/`.
3. Restart HA.

---

## Konfiguracja
1. Ustawienia → Urządzenia i usługi → Dodaj integrację.
2. Wyszukaj “Visionect Joan”.
3. Podaj dane Visionect Software Suite (adres, użytkownik, hasło, API key/secret).
4. Skonfiguruj predefiniowane widoki i URL menu głównego.

---

## Przykłady użycia
- Automatyzacja przycisku → włącz lampę.
- PIN keypad → dostęp do widoku.
- Slideshow → rotacja widoków informacyjnych.
- Panel energii przy wejściu do strefy “Dom”.

(Dodaj więcej w osobnym `przyklady.md` w przyszłości.)

---

## Wydajność i bateria
- Krótsze interwały odświeżania = większe zużycie baterii.
- 1‑bit (encoding=1) → najlepszy kontrast i najmniejsze zużycie.
- 4‑bit (encoding=4) → lepsze grafiki (wykresy, zdjęcia), ale wolniej / więcej energii.
- Unikaj bardzo częstych zmian dużych obrazów (snapshot kamera co kilka sekund).

---

## Rozwiązywanie problemów
| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| Brak reakcji webhooka | webhook_id niezgodny | Sprawdź usługę i automatyzację |
| Stare obrazy na ekranie | Cache przeglądarki | `clear_web_cache` lub `force_refresh` |
| Wykres pusty | Brak historii encji | Włącz recorder |
| Wolne odświeżanie | Wysoka głębia / duże obrazy | Zmień na 1‑bit, zmniejsz obraz |
| Brak powrotu “Wstecz” | Brak docelowego URL | Ustaw `back_button_url` lub encję |

---

## Bezpieczeństwo
- Webhooki bez autoryzacji → używaj w sieci lokalnej lub za reverse proxy.
- Nie wystawiaj surowych adresów webhooków publicznie.
- Rozważ ACL / filtr IP przy dostępie z zewnątrz.

---

## Plan rozwoju
- Obsługa innych modeli Joan.
- Dwukierunkowe przyciski (wizualizacja stanu).
- Tematy / motywy (fonts / layouty).
- Szybsza kompresja obrazów dla e‑ink.

---

## Wkład / Contributing
1. Fork → branch.
2. Konwencje commitów (feat:, fix:, docs:).
3. Dodaj opis zmian + zrzuty (jeśli UI).
4. Pull Request.

---

## Uwagi
- Nie jest to oficjalna integracja Visionect ani Home Assistant.
- Testowane na Joan 6.
- AI wykorzystane do przyspieszenia rozwoju.
- [Instalacja Visionect Software Suite](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
- [Zakup nowego Joan 6](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink)

---

## Licencja
MIT
