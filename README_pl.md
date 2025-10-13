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
<img width="596" height="829" alt="1" src="https://github.com/user-attachments/assets/d55340c3-3058-41b4-b8a4-46cf81cc4040" />



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
- integracja w pełni obsługuje szablony Jinja2 w Home Assistant. Możesz używać szablonów do dynamicznego generowania treści w następujących polach usług:
message w usłudze `visionect_joan.send_text` oraz caption w usłudze `visionect_joan.send_camera_snapshot`
Dzięki temu możesz łatwo wstawiać stany encji i atrybuty bezpośrednio do wiadomości wysyłanych na tablet.

### Przycisk "Wstecz" i Przycisk Action Webhook

Przycisk "Wstecz" - Wiele usług (takich jak `send_weather`, `send_calendar`, czy `send_sensor_graph`) pozwala na tymczasowe wyświetlenie informacji z możliwością łatwego powrotu do głównego ekranu. Aby z tego skorzystać, zdefiniuj swój główny pulpit w pliku `configuration.yaml`:

```yaml
visionect_joan:
  main_menu_url: "http://<IP_TWOJEGO_HA>:5050/nazwa_dashboardu" #przykład panelu menu Appdaemon
```
Następnie, podczas wywoływania usługi, możesz użyć opcji add_back_button: true, aby dodać widoczny przycisk powrotu do ustawionego menu, lub click_anywhere_to_return: true, aby cały ekran stał się klikalny i prowadził z powrotem do menu. <img width="309" height="467" alt="Bez tytułu" src="https://github.com/user-attachments/assets/8a74f4ff-1863-4f24-9a2a-4e599589da3c" />


## Instalacja

Integrację można zainstalować na dwa sposoby: przez **HACS** (zalecane) lub **manualnie**.

### Instalacja przez HACS (zalecana)

1.  Upewnij się, że w Twoim Home Assistant jest zainstalowany [HACS](https://hacs.xyz/).
2.  Przejdź do `HACS -> Integracje`.
3.  Kliknij menu z trzema kropkami w prawym górnym rogu i wybierz **„Niestandardowe repozytoria”**.
4.  Wklej adres URL tego repozytorium, wybierz kategorię **„Integracja”** i kliknij **„Dodaj”**.
5.  Wyszukaj na liście integrację **„Visionect Joan”** i kliknij **„Zainstaluj”**.
6.  Uruchom ponownie Home Assistant, aby zastosować zmiany.

### Instalacja manualna

1.  Pobierz najnowsze wydanie, klikając na `visionect-joan.zip` (lub `Source code (zip)`).
2.  Rozpakuj pobrane archiwum do katalogu `/config/custom_components/`.
3.  Uruchom ponownie Home Assistant.

---

## Konfiguracja

Po poprawnej instalacji i restarcie Home Assistant:

1.  Przejdź do `Ustawienia > Urządzenia i usługi`.
2.  Kliknij **„+ Dodaj integrację”** w prawym dolnym rogu.
3.  Wyszukaj **„Visionect Joan”** i kliknij, aby rozpocząć konfigurację.
4.  Wprowadź dane logowania do Visionect Software Suite: ( [Jeśli niemasz Visionect Software Suite kliknij ](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant)).
    -   Adres serwera (np. `192.168.x.x:8081`)
    -   Nazwa użytkownika (np. `admin`)
    -   Hasło
    -   Klucz API i Sekret API (można je wygenerować w Visionect Software Suite w zakładce "Users" klikając "Add new API key").

<img width="1567" height="425" alt="5" src="https://github.com/user-attachments/assets/356a55f2-342d-43f4-bf64-3ef1c6522d4e" />
<img width="575" height="615" alt="6" src="https://github.com/user-attachments/assets/c467a686-6e58-4b6a-9286-033fc45ddbcd" />

---

## Przykłady użycia

Przykładowe ekrany, które można wyświetlić na tablecie Joan 6 za pomocą serwera Visionect:


<img width="1920" height="848" alt="ada" src="https://github.com/user-attachments/assets/9dce230b-c149-49df-b1be-2802cf761cbe" />
<img width="1920" height="1578" alt="aaaa" src="https://github.com/user-attachments/assets/c3e7cbff-4e94-4172-93e8-c688ca70a7d3" />

**Więcej przykładów:**

<details>
  <summary>Kliknij, aby zobaczyć więcej zrzutów ekranu</summary>
  <img width="566" height="814" alt="temp" src="https://github.com/user-attachments/assets/4cdd9aff-2eff-4108-a5a2-a05ccc21bc9d" />

  <img width="381" height="570" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e1f32a48-0277-42ce-9018-837aeba1b6a8" />
  <img width="510" height="739" alt="3" src="https://github.com/user-attachments/assets/8f8c673d-8447-42ec-9d13-0bd4e9683437" />
  <img width="948" height="791" alt="2" src="https://github.com/user-attachments/assets/4a3c054a-e239-49c1-ab9d-037584cd7989" />
  <img width="607" height="893" alt="1" src="https://github.com/user-attachments/assets/1321cfe8-905d-44ef-b1b9-29d999559a04" />
  <img width="770" height="641" alt="4" src="https://github.com/user-attachments/assets/31e9bca1-d7c6-4245-b32f-4c909251bf2c" />
  <img width="290" height="407" alt="smie" src="https://github.com/user-attachments/assets/ad0d3f54-fe5a-466a-8da6-a5d93a052944" />
  <img width="433" height="290" alt="vvvvu" src="https://github.com/user-attachments/assets/871617fa-b4cb-4d4e-af4b-eae5120b684a" />
  <img width="307" height="457" alt="bater tytułu" src="https://github.com/user-attachments/assets/d7d76fdd-52b7-4c95-8f77-a369e672ab4b" />
  <img width="306" height="456" alt="Bez tytułu" src="https://github.com/user-attachments/assets/e3f248bb-f2c8-4e32-b41d-09cbf24a02bf" />
  <img width="569" height="808" alt="Bez tytułuss" src="https://github.com/user-attachments/assets/f746301e-d0fa-4993-aa7f-b7b4d5c2e15d" />
</details>

---

## Uwagi

-   Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
-   Działa z urządzeniem **Joan 6**, inne modele nie zostały przetestowane.
-   Do szybkiego napisania tego dodatku wykorzystano AI.
-   [Chcesz kupić nowy Joan 6?](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink).
-   [Opis krok po kroku wykorzystania tabletu Joan 6 jako panel sterowania Home Assistant](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant).

## Licencja

Projekt udostępniany na licencji MIT.
