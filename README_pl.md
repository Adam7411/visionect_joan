<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz swoją instancję Home Assistant i przejdź do repozytorium w HACS." /></a>

# Visionect Joan dla Home Assistant

<img width="1280" height="800" alt="Przykładowy ekran główny na tablecie Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">

<br>

⬇️ Visionect Joan 6 ⬇️
 
<img width="421" height="328" alt="image" src="https://github.com/user-attachments/assets/6fd88078-283a-4363-a801-71250b8211f4" />

***
👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇
<details>
  <summary>Pokaż zrzut ekranu</summary> 
  <img width="425" height="574" alt="515106368-0cb2af06-6885-4056-9c51-6835f62c06e9" src="https://github.com/user-attachments/assets/6034d4e4-bfd5-45b2-ab4f-d52c2854f8ee" />
  <img width="758" height="1024" alt="joan" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="rss" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="pog" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="pin" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="kalenda" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="cam" src="https://github.com/user-attachments/assets/9c087661-69b0-463b-937e-19b2567cab6b" />
  <img width="758" height="1024" alt="qr5, 12_49_37" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="graf0_57" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="txt5" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="pog23" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="sta2" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="ener56_34" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="_58_20" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="bat0" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
  
  
</details>

***

</p>

Integracja `visionect_joan` zmienia energooszczędny tablet e‑ink **Joan 6** w potężne, w pełni konfigurowalne centrum informacji dla Twojego inteligentnego domu.

Dzięki rozbudowanym usługom możesz tworzyć zaawansowane automatyzacje: po powrocie do domu pokaż panel energii, po wejściu do kuchni wyświetl listę zakupów, przy wykryciu ruchu wyślij zdjęcie z kamery i automatycznie wróć do głównego pulpitu.

***

## Najważniejsze funkcje

- Pełna kontrola ekranu: wyślij dowolny adres WWW, lokalne panele (np. AppDaemon) lub pojedyncze obrazy.
- Dynamiczne widoki generowane pod e‑ink: pogoda, kalendarz (także siatka miesięczna), lista zadań (To‑Do/Shopping List), panel energii, panel statusów encji, wykresy historii sensorów.
- Interaktywność: dolny pasek z przyciskiem „Wstecz” (←) i dwoma przyciskami akcji (✔ i →), a opcjonalnie „kliknij gdziekolwiek”, aby wykonać akcję lub wrócić.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="561" height="705" alt="505983472-c7d2f579-759e-48dd-8046-5b0606f5de9e" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />

</details>

- Dwa webhooki (akcje): osobne ID dla prawego (→) i środkowego (✔) przycisku.
- Zarządzanie energią: usypianie/wybudzanie urządzenia, możliwość ustawienia interwału odświeżania sesji.
- Podgląd na żywo: encja `camera` zwraca aktualny obraz z ekranu.
- Konfiguracja w UI: widoki predefiniowane i adres głównego menu ustawiasz w opcjach integracji (bez YAML).
  
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="838" height="566" alt="505984606-3d86ce11-44b9-4a65-aa2d-9c4379b77fd3" src="https://github.com/user-attachments/assets/ef9ef69b-413d-4ca4-86d9-373d3117880a" />


</details>


***

## Dostępne encje

- `camera` – Podgląd ekranu na żywo.
- `sensor`
  - Stan online/offline, bateria, temperatura, RSSI, czas pracy, napięcie baterii, pamięć (wolna/całkowita/użyta), „skonfigurowany URL”, ostatnio widziany.
  - Diagnostyka: ostatnia przyczyna połączenia, ostatni kod błędu.
  - Orientacja wyświetlacza (opisowa wartość).
- `binary_sensor`
  - Ładowanie (czy podłączona ładowarka).
- `text`
  - Nazwa urządzenia (zmiana bezpośrednio z HA).
- `number`
  - Screen Refresh (`ReloadTimeout`) – jak często sesja odświeża zawartość (s).
- `select`
  - Choose view – wybór predefiniowanego widoku dla urządzenia.
  - Back button target – domyślny cel „Wstecz”.
  - Dithering Method – metoda ditheringu (np. none/bayer/floyd‑steinberg).
  - Bit Depth – głębia bitowa (zwykle 1 lub 4).
- `button`
  - Force Refresh – natychmiastowy restart sesji renderera.
  - Reboot Device – restart urządzenia.
  - Clear Web Cache – czyszczenie cache przeglądarki.
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="658" height="1002" alt="Zrzut ekranu" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>



---

## Usługi

Poniżej pełna lista usług dostępnych w integracji (wiele z nich możesz połączyć z warstwą interaktywną: przyciski, webhooki, klik‑anywhere):

### Wyświetlanie treści

- `visionect_joan.send_button_panel`
  - Umożliwia stworzenie siatki do 12 konfigurowalnych przycisków. Każdy przycisk może mieć własną nazwę, ikonę i przypisany unikalny webhook_id, który wywołuje automatyzacje w Home Assistant.
  - Wskazówka: Panel wysyła sygnały do Home Assistant za pomocą webhooków. Aby przycisk działał, musisz stworzyć automatyzację, która na ten sygnał zareaguje.
  - ⚠️ Ważne ograniczenie: Brak informacji o stanie
Panel przycisków działa jednokierunkowo. Oznacza to, że przyciski nie pokazują aktualnego stanu urządzeń (np. czy światło jest włączone). Naciśnięcie przycisku wysyła polecenie do Home Assistant, ale wygląd ikony na tablecie nie jest dynamicznie aktualizowany. (informacji o stanie przycisku i inne polecam użyć dashboard AppDaemon)

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1214" height="3814" alt="calastrona" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
</details>

***

- `visionect_joan.set_url`
  - Ustawia dowolny URL lub nazwę zdefiniowanego widoku (predefined).
  - Wskazówka: nazwy widoków dopasowywane są bez rozróżniania wielkości liter. Dodawaj/edytuj widoki w: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1220" height="595" alt="image" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
</details>

***

- `visionect_joan.send_text`
  - Wysyła sformatowany tekst (obsługuje Jinja2), opcjonalnie z obrazem i różnymi układami (text only, text + image).
  - Wskazówki: używaj czcionek o dobrej czytelności na e‑ink; dla obrazów steruj `image_zoom` i `image_rotation`.
 
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1225" height="2066" alt="image" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />

</details>

***

- `visionect_joan.send_image_url` ➊
  - Wyświetla obraz z podanego URL (obsługa m.in. PNG/JPG/SVG/WebP).
  - Wskazówki: dla obrazów lokalnych użyj `http://<HA_IP>:8123/local/...`;
 
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1234" height="1448" alt="image" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />


</details>

***

- `visionect_joan.send_camera_snapshot`
  - Tworzy snapshot z encji `camera` i wyświetla go na ekranie (z podpisem i rotacją obrazu).
 
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1223" height="1472" alt="image" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf25237e08" />

</details>

***

- `visionect_joan.send_status_panel`
  - Panel statusów dowolnych encji: ikony + nazwy + wartości (z tłumaczeniem stanów on/off/open/…).
 
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1230" height="1416" alt="image" src="https://github.com/user-attachments/assets/bb21ddb7-77bf-4db1-bc57-9ecf2c2d5021" />

</details>

***

- `visionect_joan.send_energy_panel`
  - Duży panel energii (bieżący pobór + karty: produkcja/import/eksport/zużycie dzienne). Dobrze wygląda na pionowym układzie.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1230" height="1423" alt="image" src="https://github.com/user-attachments/assets/66b3f26d-f5c3-4276-b837-de6b85cf9fcf" />

</details>

***

- `visionect_joan.send_weather`
  - 3 layouty: szczegółowe podsumowanie, lista prognozy dziennej, panel z wykresem 24 h (automatyczne ikony dzień/noc).

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1225" height="1237" alt="image" src="https://github.com/user-attachments/assets/588660d8-e0ff-48b3-b7a5-6d9432cd2329" />

</details>

***

- `visionect_joan.send_calendar`
  - Lista wydarzeń (1–31 dni) lub siatka miesięczna z podglądem dnia.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1207" height="801" alt="510071400-b6431600-0556-4052-abdf-53eacf79397e" src="https://github.com/user-attachments/assets/83f5d345-69ef-42af-84d3-f7f4f3c3b1a0" />

</details>

***

- `visionect_joan.send_todo_list`
  - Lista zadań (w tym Shopping List). Pozycje są duże i czytelne; wspiera interaktywne odhaczanie przez webhook (patrz niżej).

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1216" height="1201" alt="image" src="https://github.com/user-attachments/assets/6735340b-bec9-47a6-a72e-07d16da20943" />

</details>

***

- `visionect_joan.send_sensor_graph`
  - Wykres historii wskazanych sensorów (line lub bar), automatycznie dopasowany do orientacji ekranu.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1219" height="1895" alt="image" src="https://github.com/user-attachments/assets/c5507b3b-28e6-47a1-a88a-11d936f2f35b" />

</details>

***

- `visionect_joan.send_rss_feed` ➋
  - Pobiera i pokazuje najnowsze wpisy z kanału RSS/Atom (stronicowanie, nagłówek, ikony). Podaj `feed_url`, `max_items`, opcjonalnie własny tytuł.

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1225" height="1255" alt="image" src="https://github.com/user-attachments/assets/56316ce1-8350-49d5-a624-2f7a880b8a4e" />

</details>

***
### Interaktywność i nawigacja

- `visionect_joan.send_qr_code`
  - Generuje kod QR (np. gościnne Wi‑Fi) z opcjonalnym podpisem (pozycja nad/po QR).
    
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1223" height="1765" alt="image" src="https://github.com/user-attachments/assets/a55360c9-9f17-4b81-baf9-b990692bc2a0" />

</details>

***

- `visionect_joan.start_slideshow` 
  - Odtwarza listę widoków (predefiniowane nazwy lub pełne lokalne adresy URL) w pętli z czasem wyświetlania per‑slide.
Wskazówka: Im więcej sekund na przełączenie slajdu tym wydłozy się zużycie baterii. Wyświetla listę widoków (predefiniowane nazwy lub pełne adresy URL) w pętli z określonym czasem na slajd. Ważne: Ten pokaz slajdów renderuje strony wewnątrz ramki iframe. Wiele zewnętrznych witryn internetowych (np. google.com, home-assistant.io) blokuje osadzanie za pomocą X-Frame-Options/Content-Security-Policy i NIE wyświetla się. Aby uzyskać wiarygodne wyniki, używaj wyłącznie adresów lokalnych (Asystent domowy/AppDaemon/pliki lokalne) lub ustawionych widoków skonfigurowanych w integracji Visionect Joan.
 
<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="606" height="729" alt="510095682-106d5ae9-8d8a-4b3f-8f5e-206aab76e0c8" src="https://github.com/user-attachments/assets/91d25761-2709-417b-9a2c-edf2104c5869" />

</details>

***

- `visionect_joan.send_keypad` ➍
  - Pełnoekranowa klawiatura numeryczna. Wpisany PIN wysyłany jest POST‑em do wskazanego webhooka w HA (`trigger.json.pin`).
  - Wskazówka: potrzebna automatyzacja do rozpoznania pinu
  - 
 <details>
  
  <summary><strong>Przykład: Automatyzacja PIN (webhook + keypad) dla Visionect Joan</strong></summary>

Ten przykład pokazuje, jak użyć usługi `visionect_joan.send_keypad` do wprowadzania PIN-u na ekranie Joan i sprawdzania go w automatyzacji z wyzwalaczem webhook. Jeśli PIN jest poprawny — urządzenie przechodzi do wskazanego widoku; jeśli błędny — pojawia się komunikat i klawiatura wraca po chwili.

— Wymagania:
- Zainstalowana integracja Visionect Joan oraz dodane urządzenie (Joan 6).
- Znany `device_id` Twojego tabletu (Ustawienia → Urządzenia i usługi → urządzenie → trzy kropki → Kopiuj identyfikator urządzenia).
- Zdefiniowany widok w opcjach integracji (albo pełny URL, jeśli wolisz).

— Jak uruchomić keypad po raz pierwszy:
- Jednorazowo wywołaj usługę: `visionect_joan.send_keypad` z:
  - device_id: Twój tablet
  - title: np. “Wprowadź PIN”
  - action_webhook_id: np. “joan_pin” (musi się zgadzać z webhookiem w automatyzacji)

— YAML automatyzacji (skopiuj do edytora YAML automatyzacji w HA i podmień wartości w komentarzach):

```
alias: Automatyzacja kodu PIN dla urządzenia Visionect Joan
mode: single

trigger:
  - platform: webhook
    # USTAW SWÓJ WEBHOOK ID (musi być taki sam jak w visionect_joan.send_keypad → action_webhook_id):
    webhook_id: joan_pin

action:
  - choose:
      # Warunek: poprawny PIN?
      - conditions:
          - condition: template
            # USTAW SWÓJ PIN:
            value_template: "{{ trigger.json.pin == '321' }}"
        sequence:
          # SUKCES: przejdź do widoku (nazwa predefiniowanego widoku lub pełny URL)
          - action: visionect_joan.set_url
            target:
              # USTAW SWOJE DEVICE_ID:
              device_id: 266a72218733bb9a056aff49bf6f8e2d
            data:
              # Zmień na nazwę widoku (np. KuchniaGóra) lub wpisz pełny URL
              url: KuchniaGóra
    default:
      # BŁĘDNY PIN: pokaż komunikat
      - action: visionect_joan.send_text
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          message: "Błędny Kod!"
          text_size: 48
          # (opcjonalnie) możesz dodać nakładkę z przyciskiem Wstecz/akcją:
          # add_back_button: true
          # back_button_url: "NazwaWidokuLubURL"
      # krótka pauza
      - delay: "00:00:03"
      # Pokaż keypad ponownie (ten sam webhook_id co w triggerze)
      - action: visionect_joan.send_keypad
        target:
          device_id: 266a72218733bb9a056aff49bf6f8e2d
        data:
          title: "Spróbuj ponownie"
          action_webhook_id: joan_pin
```

— Wskazówki i bezpieczeństwo:
- Webhook nie wymaga tokenu — najlepiej używać w sieci lokalnej lub za reverse proxy/ACL.
- PIN możesz przechowywać w helperze (`input_text`) lub jako sekret i porównywać w szablonie.
- Zamiast nazwy widoku w `data.url` możesz wpisać pełny URL (np. panel AppDaemon).

</details>
 

<details>
  <summary>Pokaż zrzut ekranu</summary>

  <img width="1220" height="632" alt="image" src="https://github.com/user-attachments/assets/5df2b9d9-ae6e-4a60-9f9f-c787f7658135" />

</details>

***

### Parametry renderingu i zarządzanie

- `visionect_joan.set_session_options` ➎
  - Ustawia parametry sesji: `encoding` (głębia bitowa, zwykle „1” lub „4”) oraz `dithering` (none/bayer/floyd‑steinberg).
  - Wskazówka: 1‑bit = najwyższy kontrast i szybkość, 4‑bit = 16 odcieni szarości (lepsza jakość grafiki).

- `visionect_joan.clear_web_cache`
  - Czyści cache przeglądarki webkit dla wybranych urządzeń; opcjonalnie `restart_session: true`.
  - Wskazówka: użyteczne przy problemach ze „starymi” obrazami lub stylami.

- `visionect_joan.force_refresh`
  - Natychmiast restartuje sesję (odświeża aktualny widok).

- `visionect_joan.set_display_rotation`
  - Trwale zmienia orientację ekranu urządzenia (wymaga krótkiego restartu urządzenia).

- `visionect_joan.clear_display`
  - Czyści ekran do pustego tła (białe tło).

- `visionect_joan.sleep_device` / `visionect_joan.wake_device`
  - Usypianie/wybudzanie urządzenia (oszczędzanie baterii; ustaw czas snu w sekundach).

➊ `send_image_url` – akceptowane rozszerzenia: png, jpg, jpeg, gif, svg, webp (wsparcie formatów zależy też od wersji renderera Visionect).

➋ `send_rss_feed` – integracja parsuje kanał (Feedparser), buduje listy i paginację; świetne na szybkie „newsboardy”.

➌ `start_slideshow` – przyjmie nazwy widoków (z sekcji „Widoki i opcje”) i/lub pełne URL (po jednym w linii).

➍ `send_keypad` – webhook w HA powinien mieć trigger typu Webhook; w warunkach: `{{ trigger.json.pin == '1234' }}`.

➎ `set_session_options` – jeśli zostawisz parametr pusty, bieżąca wartość nie zostanie zmieniona.

---

## Warstwa interaktywna (przyciski, klik‑anywhere, webhooki)

Każda z usług wyświetlających treści może dodać „nakładkę” z przyciskami:
- „Wstecz” (←) – powrót do adresu zdefiniowanego jako:
  1) `back_button_url` w wywołaniu usługi,
  2) encja `Back button target` (per urządzenie),
  3) globalny „Main menu URL” ustawiony w opcjach integracji.
- „Akcja” (→) – wywołuje webhook `action_webhook_id`.
- „Środkowy” (✔) – wywołuje webhook `action_webhook_2_id`.
- „Klik anywhere” – może wywołać akcję (webhook) albo służyć jako szybki „powrót”.

<details>
 
  <summary><strong>Przykład: przycisk akcji (webhook) → włącz lampę</strong></summary>

Ten przykład pokazuje, jak użyć `action_webhook_id` w widoku wysyłanym na Joan, aby po naciśnięciu prawego przycisku (→) włączyć lampę w Home Assistant.

Działa z większością usług wyświetlających treści (send_text, send_status_panel, send_weather, send_image_url, send_todo_list, send_calendar, send_energy_panel, send_sensor_graph, start_slideshow). Poniżej używamy `send_text`.

— Krok 1. Automatyzacja: nasłuch webhooka i włącz lampę

Skopiuj do edytora YAML automatyzacji (zmień WEBHOOK_ID oraz encję lampy):

```
alias: "Joan: włącz lampę przyciskiem"
mode: single

trigger:
  - platform: webhook
    # USTAW SWÓJ WEBHOOK ID (musi zgadzać się z action_webhook_id w kroku 2):
    webhook_id: joan_light_on

action:
  - service: light.turn_on
    target:
      entity_id: light.twoja_lampa  # np. light.kuchnia_lampa
    data:
      brightness_pct: 100  # opcjonalnie
```

— Krok 2. Wyślij na Joan widok z przyciskiem akcji (→)

Wywołaj usługę `visionect_joan.send_text` (Narzędzia deweloperskie → Usługi) z `action_webhook_id: joan_light_on`. To doda dolny pasek z przyciskami; prawy (→) wyśle webhook do HA.

```
service: visionect_joan.send_text
data:
  message: "Włącz lampę"
  add_back_button: true                # opcjonalnie pokaż 'Wstecz' (←)
  back_button_url: "Main"              # nazwa zdefiniowanego widoku lub pełny URL (opcjonalnie)
  action_webhook_id: joan_light_on     # MUSI zgadzać się z 'webhook_id' w automatyzacji
target:
  device_id: 00000000000000000000000000000000  # <- wstaw swój device_id Joana
```

Wariant: cały ekran jako przycisk
- Jeśli zamiast widocznych przycisków na dole wolisz, aby kliknięcie w dowolne miejsce ekranu włączyło lampę, użyj:

```yaml
service: visionect_joan.send_text
data:
  message: "Dotknij, aby włączyć lampę"
  click_anywhere_to_action: true       # ukryje pasek przycisków i uczyni cały ekran 'kliknij aby wykonać akcję'
  action_webhook_id: joan_light_on
target:
  device_id: 00000000000000000000000000000000
```

Wskazówki:
- Prawy przycisk (→) korzysta z `action_webhook_id`. Środkowy (✔) to `action_webhook_2_id`.
- „Wstecz” (←) możesz dodać parametrem `add_back_button: true`. Cel „Wstecz”:
  1) `back_button_url` z wywołania usługi,
  2) encja „Back button target” dla urządzenia,
  3) globalny „Main menu URL” z opcji integracji.
- Najpewniejsze działanie webhooków jest, gdy Visionect Server działa jako dodatek w HA (integracja użyje prawidłowego adresu wewnętrznego). Jeśli Visionect działa na innym hoście, upewnij się, że ma dostęp HTTP/HTTPS do HA.
- Ten sam schemat zadziała także z innymi usługami wyświetlania (np. `send_status_panel`, `send_image_url`) — wystarczy dodać `action_webhook_id`.

Troubleshooting:
- Naciśnięcie przycisku nic nie robi? Sprawdź w Podglądzie zdarzeń, czy webhook dochodzi i czy `trigger.json` jest widoczne w automatyzacji.
- Jeśli masz certyfikat HTTPS i osobne hosty, zweryfikuj poprawność adresu wewnętrznego HA w Ustawienia → System → Sieć.
  
</details>


Wskazówki:
- Najpewniejsze działanie webhooków uzyskasz, gdy Visionect Server działa jako dodatek HA (ten sam host) – integracja automatycznie użyje prawidłowego adresu wewnętrznego HA dla webhooków.
- Jeśli Visionect stoi na innym hoście, zadbaj o łączność HTTP do HA oraz certyfikat (jeśli https).

---

## Instalacja

### Przez HACS (zalecane)
1. Zainstaluj [HACS](https://hacs.xyz/) w Home Assistant.
2. HACS → Integrations → menu (⋮) → Custom repositories.
3. Dodaj to repo jako Integration i kliknij Add.
4. Znajdź „Visionect Joan” i kliknij Install.
5. Zrestartuj Home Assistant.

### Ręcznie
1. Pobierz najnowsze wydanie (`visionect-joan.zip` lub `Source code (zip)`).
2. Wypakuj do `/config/custom_components/visionect_joan/`.
3. Zrestartuj Home Assistant.

---

## Konfiguracja


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

## Przykłady użycia

Ekrany, które możesz wyświetlić na tablecie Joan 6:


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
  <img width="758" height="1024" alt="joan" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  
</details>

---


## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Testowany na **Joan 6**; inne modele nie były weryfikowane.
- Do szybszego rozwoju użyto AI.
- [Chcesz kupić nowy Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink)
- [Opis: Visionect Software Suite - Instalacja](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)

---

## Licencja

MIT
