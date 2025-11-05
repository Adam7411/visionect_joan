<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Otwórz swoją instancję Home Assistant i przejdź do repozytorium w HACS." /></a>

# Visionect Joan dla Home Assistant

<img width="1280" height="800" alt="Przykładowy ekran główny na tablecie Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">

<br>
<img width="35%" alt="Wykres temperatury" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />
</p>

Integracja `visionect_joan` zmienia energooszczędny tablet e‑ink **Joan 6** w potężne, w pełni konfigurowalne centrum informacji dla Twojego inteligentnego domu.

Dzięki rozbudowanym usługom możesz tworzyć zaawansowane automatyzacje: po powrocie do domu pokaż panel energii, po wejściu do kuchni wyświetl listę zakupów, przy wykryciu ruchu wyślij zdjęcie z kamery i automatycznie wróć do głównego pulpitu.

---

## Najważniejsze funkcje

- Pełna kontrola ekranu: wyślij dowolny adres WWW, lokalne panele (np. AppDaemon) lub pojedyncze obrazy.
- Dynamiczne widoki generowane pod e‑ink: pogoda, kalendarz (także siatka miesięczna), lista zadań (To‑Do/Shopping List), panel energii, panel statusów encji, wykresy historii sensorów.
- Interaktywność: dolny pasek z przyciskiem „Wstecz” (←) i dwoma przyciskami akcji (✔ i →), a opcjonalnie „kliknij gdziekolwiek”, aby wykonać akcję lub wrócić.
- Dwa webhooki (akcje): osobne ID dla prawego (→) i środkowego (✔) przycisku.
- Zarządzanie energią: usypianie/wybudzanie urządzenia, możliwość ustawienia interwału odświeżania sesji.
- Podgląd na żywo: encja `camera` zwraca aktualny obraz z ekranu.
- Konfiguracja w UI: widoki predefiniowane i adres głównego menu ustawiasz w opcjach integracji (bez YAML).

---

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

Podpowiedzi:
- Lokalny obraz do wyświetlenia umieść w `/config/www`, a URL będzie jak `http://<HA_IP>:8123/local/nazwa.png`.
- Wybór „Back button target” działa globalnie dla danego urządzenia i jest używany przez wszystkie usługi z „przyciskiem wstecz”.

---

## Usługi

Poniżej pełna lista usług dostępnych w integracji (wiele z nich możesz połączyć z warstwą interaktywną: przyciski, webhooki, klik‑anywhere):

### Wyświetlanie treści

- `visionect_joan.set_url`
  - Ustawia dowolny URL lub nazwę zdefiniowanego widoku (predefined).
  - Wskazówka: nazwy widoków dopasowywane są bez rozróżniania wielkości liter. Dodawaj/edytuj widoki w: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj.

- `visionect_joan.send_text`
  - Wysyła sformatowany tekst (obsługuje Jinja2), opcjonalnie z obrazem i różnymi układami (text only, text + image).
  - Wskazówki: używaj czcionek o dobrej czytelności na e‑ink; dla obrazów steruj `image_zoom` i `image_rotation`.

- `visionect_joan.send_image_url` ➊
  - Wyświetla obraz z podanego URL (obsługa m.in. PNG/JPG/SVG/WebP).
  - Wskazówki: dla obrazów lokalnych użyj `http://<HA_IP>:8123/local/...`; zadbaj o dostępność z serwera Visionect (CORS/certyfikat).

- `visionect_joan.send_camera_snapshot`
  - Tworzy snapshot z encji `camera` i wyświetla go na ekranie (z podpisem i rotacją obrazu).

- `visionect_joan.send_status_panel`
  - Panel statusów dowolnych encji: ikony + nazwy + wartości (z tłumaczeniem stanów on/off/open/…).

- `visionect_joan.send_energy_panel`
  - Duży panel energii (bieżący pobór + karty: produkcja/import/eksport/zużycie dzienne). Dobrze wygląda na pionowym układzie.

- `visionect_joan.send_weather`
  - 3 layouty: szczegółowe podsumowanie, lista prognozy dziennej, panel z wykresem 24 h (automatyczne ikony dzień/noc).

- `visionect_joan.send_calendar`
  - Lista wydarzeń (1–31 dni) lub siatka miesięczna z podglądem dnia.

- `visionect_joan.send_todo_list`
  - Lista zadań (w tym Shopping List). Pozycje są duże i czytelne; wspiera interaktywne odhaczanie przez webhook (patrz niżej).

- `visionect_joan.send_sensor_graph`
  - Wykres historii wskazanych sensorów (line lub bar), automatycznie dopasowany do orientacji ekranu.

- `visionect_joan.send_rss_feed` ➋
  - Pobiera i pokazuje najnowsze wpisy z kanału RSS/Atom (stronicowanie, nagłówek, ikony). Podaj `feed_url`, `max_items`, opcjonalnie własny tytuł.

### Interaktywność i nawigacja

- `visionect_joan.send_qr_code`
  - Generuje kod QR (np. gościnne Wi‑Fi) z opcjonalnym podpisem (pozycja nad/po QR).

- `visionect_joan.start_slideshow` ➌
  - Odtwarza listę widoków (nazwy predefined lub pełne URL) w pętli, z czasem wyświetlania slajdu.
  - Wskazówka: krótki interwał = częstsze odświeżenia e‑ink i większe zużycie baterii. Zalecane ≥ 30 s.

- `visionect_joan.send_keypad` ➍
  - Pełnoekranowa klawiatura numeryczna. Wpisany PIN wysyłany jest POST‑em do wskazanego webhooka w HA (`trigger.json.pin`).
  - Wskazówka: idealne do prostego rozbrajania alarmu, otwierania furtki itp.

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

Po restarcie:
1. Ustawienia → Urządzenia i usługi → + Dodaj integrację → „Visionect Joan”.
2. Wprowadź dane do Visionect Software Suite:
   - Host: adres serwera VSS (zwykle `192.168.x.x:8081` lub host dodatku),
   - Username/Password (np. `admin` / własne hasło),
   - API Key i Secret (Visionect → Users → Add new API key).
3. W opcjach integracji (Konfiguruj) dodaj:
   - Widoki (nazwa + URL) – będą dostępne w selektorze „Choose view” oraz w usługach przez `predefined_url`,
   - Globalny „Main menu URL”.

Wskazówki:
- Obrazy lokalne – umieszczaj w `/config/www` i odwołuj jako `http://<HA_IP>:8123/local/plik.png`.
- Jeżeli używasz automatyzacji z webhookami – sprawdź w Podglądzie zdarzeń czy webhook przychodzi oraz czy `trigger.json` zawiera oczekiwane pola (np. `pin`).

---

## Przykłady użycia

Ekrany, które możesz wyświetlić na tablecie Joan 6:

<img width="1920" height="848" alt="Panel AppDaemon na ekranie Joan 6" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="AppDaemon — motyw ciemny" src="https://github.com/user-attachments/assets/c3e7cbff-4e4-4172-93e8-c688ca70a7d3" />

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

## Wskazówki i dobre praktyki

- Slideshow: im krótszy „seconds_per_slide”, tym częściej odświeża się ekran e‑ink (większe zużycie baterii).
- „Klik anywhere” i przyciski akcji: w środowisku rozproszonym użyj adresów, które Visionect „widzi” (DNS/SSL).
- To‑Do (Shopping List): aby odhaczanie pozycji działało naprawdę (a nie tylko wizualnie), skonfiguruj webhook w HA i podaj `action_webhook_id` – integracja wyśle JSON z `uid` i nowym `status`.
- Bit Depth i Dithering: w razie wątpliwości użyj 4 bpp i „floyd‑steinberg” do zdjęć/wykresów; 1 bpp i „none” do maksymalnego kontrastu tekstu.

---

## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Testowany na **Joan 6**; inne modele nie były weryfikowane.
- Do szybszego rozwoju użyto AI.
- [Chcesz kupić nowy Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink)
- [Opis: jak użyć Joan 6 jako panelu sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)

---

## Licencja

MIT
