<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>


<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

# Visionect Joan dla Home Assistant

<img width="1280" height="800" alt="Przykładowy ekran główny na tablecie Joan 6" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />

<p align="center">
<img width="24%" alt="Widok pogody" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" />
<img width="24%" alt="Kod QR do Wi-Fi" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" />
<img width="24%" alt="Panel statusu" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" />
<img width="24%" alt="Panel energii" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />
<br>
<img width="35%" alt="Wykres temperatury" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />
</p>

Integracja `visionect_joan` transformuje Twój energooszczędny tablet e-ink **Joan 6** w potężne, w pełni konfigurowalne centrum informacji dla Twojego inteligentnego domu. Zamiast statycznego kalendarza, zyskujesz dynamiczny, dotykowy ekran, na którym możesz wyświetlać dowolne dane z Home Assistant – od paneli kontrolnych, przez prognozę pogody, aż po zrzuty z kamer.

Dzięki rozbudowanym usługom możesz tworzyć zaawansowane automatyzacje, np. wyświetlić panel energii po powrocie do domu, pokazać listę zakupów po wejściu do kuchni, czy wysłać powiadomienie ze zdjęciem z kamery, a następnie automatycznie powrócić do głównego dashboardu.

## Kluczowe Możliwości

- **Pełna kontrola nad ekranem:** Wysyłaj dowolne strony internetowe, lokalne dashboardy (np. z AppDaemon) lub pojedyncze obrazy.
- **Dynamicznie generowane widoki:** Integracja potrafi tworzyć zoptymalizowane pod e-ink panele, takie jak prognoza pogody, kalendarz, lista zadań, panel energii czy statusy encji.
- **Interaktywność:** Dodaj przycisk "wstecz" do tymczasowych widoków lub spraw, by cały ekran był klikalny, umożliwiając łatwy powrót do głównego menu.
- **Zarządzanie energią:** Maksymalizuj czas pracy na baterii dzięki usługom usypiania i wybudzania urządzenia w ramach automatyzacji.
- **Podgląd na żywo:** Wbudowana encja `camera` pozwala na bieżąco sprawdzać, co jest wyświetlane na tablecie, bezpośrednio z interfejsu Home Assistant.

### Dostępne encje i usługi

**Sensory i encje:**
- **Podgląd na żywo (`camera`):** Zobacz aktualny obraz z ekranu tabletu.
- **Bateria (`sensor`):** Monitoruj poziom naładowania.
- **Status ładowania (`binary_sensor`):** Sprawdź, czy urządzenie jest podłączone do ładowarki.
- **Status urządzenia (`sensor`):** Weryfikuj, czy tablet jest online.
- **Nazwa urządzenia (`text`):** Zmieniaj nazwę tabletu bezpośrednio z HA.
- **Interwał odświeżania (`number`):** Dostosuj, jak często tablet ma odświeżać zawartość.
- Oraz wiele innych: temperatura, siła sygnału Wi-Fi, napięcie baterii, czas pracy, zajęte miejsce, skonfigurowany URL i czas ostatniej aktywności.
<img width="646" height="860" alt="Lista encji dla urządzenia" src="https://github.com/user-attachments/assets/140837dd-0434-40a8-8352-753e3cc50f16" />

**Usługi:**
- `visionect_joan.set_url`: Wyświetl dowolny adres URL.
- `visionect_joan.send_text`: Wyślij formatowaną wiadomość tekstową z opcjonalnym obrazkiem.
- `visionect_joan.send_camera_snapshot`: Wyślij zrzut ekranu z dowolnej kamery w Home Assistant.
- `visionect_joan.send_weather`: Pokaż estetyczny i czytelny panel pogodowy.
- `visionect_joan.send_calendar`: Wyświetl wydarzenia z kalendarza w formie listy lub siatki miesięcznej.
- `visionect_joan.send_energy_panel`: Pokaż podsumowanie zużycia i produkcji energii.
- `visionect_joan.send_status_panel`: Wyświetl panel z aktualnym stanem wybranych encji.
- `visionect_joan.send_sensor_graph`: Generuj wykres historii dla sensorów, dopasowany do orientacji ekranu.
- `visionect_joan.send_todo_list`: Wyświetl listę zadań (np. listę zakupów).
- `visionect_joan.send_qr_code`: Pokaż kod QR (np. do sieci Wi-Fi dla gości).
- `visionect_joan.sleep_device` & `wake_device`: Usypiaj i wybudzaj urządzenie.
- `visionect_joan.clear_display`, `force_refresh`, `set_display_rotation`: Narzędzia do zarządzania ekranem.

### Przycisk "Wstecz" i interaktywność

Wiele usług (takich jak `send_weather`, `send_calendar`, czy `send_sensor_graph`) pozwala na tymczasowe wyświetlenie informacji z możliwością łatwego powrotu do głównego ekranu. Aby z tego skorzystać, zdefiniuj swój główny pulpit w pliku `configuration.yaml`:

```yaml
visionect_joan:
  main_menu_url: "http://<IP_TWOJEGO_HA>:5050/nazwa_dashboardu"



