<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>


<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

# Visionect Joan dla Home Assistant
<img width="1280" height="800" alt="7ca451b4-393c-44c8-99e3-c9e0f88db77b" src="https://github.com/user-attachments/assets/32214988-dc0e-44ce-af14-2d7f71fb8e6c" />



<img width="381" height="570" alt="Bez tytułu" src="https://github.com/user-attachments/assets/993bbcaf-5ee9-47d8-80b4-b886ef897b69" /> <img width="302" height="460" alt="QR" src="https://github.com/user-attachments/assets/d165cd67-79cf-402a-b595-905e3c5cb809" /> <img width="301" height="456" alt="aaaa" src="https://github.com/user-attachments/assets/1594ae1f-0a95-44cb-8edc-cad3b0879c88" /> <img width="301" height="457" alt="cccc" src="https://github.com/user-attachments/assets/5ad26dae-dc77-408f-bf55-0a33ce2601ba" />
<img width="447" height="355" alt="image" src="https://github.com/user-attachments/assets/27b23199-e4c1-4f69-8c45-2e06cd290f3a" />



Niestandardowy dodatek wyświetlający podstawowe informacje tableta e-ink **Joan 6** firmy Visionect w Home Assistant oraz umożliwiający wysyłanie własnego adresu URL, tekstu i zdjęć z poziomu HA.

Pozwoli to na tworzenie zaawansowanych automatyzacji, np. wysyłania powiadomienia o niskim stanie baterii, wyświetlanie encji z poziomem baterii na tablecie, czy wysyłanie zdjęć do różnych powiadomień, po czym automatyczny powrót do dashboardu Appdaemon.


## Funkcjonalności

Integracja dostarcza następujące encje i usługi:

**Sensory:**
- Integracja automatycznie tworzy encję camera dla każdego tabletu Joan, dając Ci podgląd ekranu na żywo w Home Assistant
- Poziom baterii
- Całkowita i zajęta pamięć
- Czas pracy
- Status ładowania (Sensor binarny)
- Interwał odświeżania (Liczba)
- Napięcie baterii
- Status urządzenia (Online/Offline)
- Siła sygnału Wi-Fi
- Temperatura
- Skonfigurowany URL
- Czas ostatniej aktywności
<img width="646" height="860" alt="aaaau" src="https://github.com/user-attachments/assets/140837dd-0434-40a8-8352-753e3cc50f16" />

**Usługi:**
- `visionect_joan.send_text`: Wysyłanie wiadomości tekstowych, teraz z obsługą obrazków i układów. Wspiera szablony Jinja2 do dynamicznej treści.
- `visionect_joan.set_url`: Wyświetlanie dowolnego adresu URL (np. strony `https://www.wikipedia.org/` lub lokalnego obrazka `http://<adres_ip_ha>:8123/local/zdjecie.png`).
- `visionect_joan.clear_display`: Czyszczenie ekranu.
- `visionect_joan.force_refresh`: Natychmiastowe przeładowanie zawartości z ustawionego adresu URL.
- `visionect_joan.set_display_rotation`: Rotacja ekranu.
- `visionect_joan.send_qr_code`: Generowanie Kodów QR: Wyświetlaj niestandardowe kody QR bezpośrednio na ekranie Joan. Idealne dla sieci Wi-Fi dla gości, linków i nie tylko.
- `action: visionect_joan.sleep_device` & `visionect_joan.wake_device`: Usługi Zarządzania Energią: Drastycznie wydłuż żywotność baterii swojego tabletu, usypiając go i wybudzając za pomocą automatyzacji.
- `visionect_joan.send_energy_panel`: Wyświetla panel zużycia i produkcji energii.
- `visionect_joan.send_weather`: Pokazuje szczegółową, powiększoną prognozę pogody.
- `visionect_joan.send_calendar`: Renderuje ulepszony, czytelny kalendarz miesięczny.
- `visionect_joan.send_todo_list`: Wysyła dowolną listę zadań, w tym listę zakupów (todo.shopping_list).
- `visionect_joan.send_camera_snapshot`: Wyślij zrzut ekranu dowolnej kamery z Home Assistant.
- `visionect_joan.send_status_panel`: Wyświetla niestandardowy panel ze stanem wybranych encji, idealny do szybkiego podglądu statusu domu.
- `visionect_joan.send_sensor_graph`: Generuje i wyświetla wykres historii dla jednego lub więcej sensorów. Wykres automatycznie dostosowuje się do orientacji ekranu (pionowej lub poziomej).

### Przycisk "Wstecz" i interaktywność

Wiele usług (takich jak `send_weather`, `send_calendar`, czy `send_sensor_graph`) pozwala na tymczasowe wyświetlenie informacji z możliwością łatwego powrotu do głównego ekranu. Aby z tego skorzystać, zdefiniuj swój główny pulpit w pliku `configuration.yaml`:

```yaml
visionect_joan:
  main_menu_url: "http://<IP_TWOJEGO_HA>:5050/nazwa_dashboardu"
