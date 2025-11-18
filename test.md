<!-- README_PL.md -->
<div align="right">
<a href="README.md">English</a> | <a href="README_pl.md">Polski</a>
</div>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Adam7411&repository=visionect_joan&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs.svg" alt="Otwórz w HACS"></a>

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
  <!-- Oryginalne zrzuty zachowane -->
  <img width="425" height="574" alt="panel start" src="https://github.com/user-attachments/assets/6034d4e4-bfd5-45b2-ab4f-d52c2854f8ee" />
  <img width="758" height="1024" alt="joan" src="https://github.com/user-attachments/assets/fd78c164-6691-477e-84e1-e47a1f70a8cc" />
  <img width="758" height="1024" alt="rss" src="https://github.com/user-attachments/assets/f5a1f528-8201-47a0-9f7a-15b435f9152c" />
  <img width="758" height="1024" alt="pog" src="https://github.com/user-attachments/assets/2aca216e-e0d2-454e-b089-ee1eb04e947b" />
  <img width="758" height="1024" alt="pin" src="https://github.com/user-attachments/assets/c765b34f-ed4e-48d7-a59d-ff8ecd67aa7c" />
  <img width="758" height="1024" alt="kalenda" src="https://github.com/user-attachments/assets/a5f3b53e-1b33-414b-8173-3fac794cbd46" />
  <img width="758" height="1024" alt="cam" src="https://github.com/user-attachments/assets/9c087661-69b0-463b-937e-19b2567cab6b" />
  <img width="758" height="1024" alt="qr" src="https://github.com/user-attachments/assets/f3c19b37-0dad-4bd9-89ac-271c016d4211" />
  <img width="758" height="1024" alt="graf" src="https://github.com/user-attachments/assets/7819468a-c33b-409f-9845-2256def6a134" />
  <img width="758" height="1024" alt="tekst" src="https://github.com/user-attachments/assets/0d735375-caf9-4e8c-a4c8-6b5008a88f9b" />
  <img width="758" height="1024" alt="pogoda2" src="https://github.com/user-attachments/assets/6267ae6c-0263-4fb0-8189-c638cc5d685d" />
  <img width="758" height="1024" alt="statusy" src="https://github.com/user-attachments/assets/8e35f996-26a3-4e4f-9951-1938530a9028" />
  <img width="758" height="1024" alt="energia" src="https://github.com/user-attachments/assets/acb78d0e-ca38-451e-8fc2-f64f479d1c78" />
  <img width="758" height="1024" alt="podglad" src="https://github.com/user-attachments/assets/3bd6d185-33ae-4407-98c5-9b70821c27b9" />
  <img width="758" height="1024" alt="diag" src="https://github.com/user-attachments/assets/fe7eb843-a6f1-4ef7-a3a4-e006b93c528f" />
</details>
***
</p>

Integracja `visionect_joan` zmienia energooszczędny tablet e‑ink **Joan 6** w potężne centrum informacji […] (oryginalny opis).

***

## Spis treści
- [Najważniejsze funkcje](#najważniejsze-funkcje)
- [Dostępne encje](#dostępne-encje)
- [Usługi](#usługi)
- [Wskazówki konfiguracji usług](#wskazówki-konfiguracji-usług)
- [Warstwa interaktywna i webhooki](#warstwa-interaktywna-i-webhooki)
- [Instalacja](#instalacja)
- [Konfiguracja](#konfiguracja)
- [Instalacja i konfiguracja Visionect Software Suite](#instalacja-i-konfiguracja-visionect-software-suite)
- [Przykłady użycia](#przykłady-użycia)
- [Wydajność i bateria](#wydajność-i-bateria)
- [Bezpieczeństwo](#bezpieczeństwo)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Uwagi](#uwagi)
- [Licencja](#licencja)

---

## Najważniejsze funkcje
(oryginalna lista zachowana)
<details>
  <summary>Pokaż zrzut ekranu</summary>
  <img width="561" height="705" alt="pasek przycisków" src="https://github.com/user-attachments/assets/dd217c23-d402-43a8-acb3-1bf0ea841c74" />
</details>

***

## Dostępne encje
(oryginalne)
<details>
  <summary>Pokaż zrzut ekranu</summary>
  <img width="658" height="1002" alt="Zrzut ekranu" src="https://github.com/user-attachments/assets/67de6efe-ffd5-4757-8a82-71e46f039943" />
</details>

---

## Usługi
(Oryginalne sekcje + zrzuty pozostają – nie usuwam)

### Wyświetlanie treści
- `visionect_joan.send_button_panel` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1214" height="3814" alt="calastrona" src="https://github.com/user-attachments/assets/fdbb51ba-0f4b-4db4-98bd-e5d01b34ce77" />
</details>
***
- `visionect_joan.set_url` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1220" height="595" alt="image" src="https://github.com/user-attachments/assets/bfdf8101-1b45-45e0-ab1a-46c7ab79d96b" />
</details>
***
- `visionect_joan.send_text` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1225" height="2066" alt="image" src="https://github.com/user-attachments/assets/9912da53-becf-4932-ab7e-7f0a17a681d7" />
</details>
***
- `visionect_joan.send_image_url` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1234" height="1448" alt="image" src="https://github.com/user-attachments/assets/9da6769f-668a-4adb-9edf-b5fdc5851d55" />
</details>
***
- `visionect_joan.send_camera_snapshot` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1223" height="1472" alt="image" src="https://github.com/user-attachments/assets/6cec8748-a586-46c2-8f2b-2bcf-25237e08" />
</details>
***
- `visionect_joan.send_status_panel` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1230" height="1416" alt="image" src="https://github.com/user-attachments/assets/bb21ddb7-77bf-4db1-bc57-9ecf2c2d5021" />
</details>
***
- `visionect_joan.send_energy_panel` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1230" height="1423" alt="image" src="https://github.com/user-attachments/assets/66b3f26d-f5c3-4276-b837-de6b85cf9fcf" />
</details>
***
- `visionect_joan.send_weather` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1225" height="1237" alt="image" src="https://github.com/user-attachments/assets/588660d8-e0ff-48b3-b7a5-6d9432cd2329" />
</details>
***
- `visionect_joan.send_calendar` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1207" height="801" alt="kalendarz" src="https://github.com/user-attachments/assets/83f5d345-69ef-42af-84d3-f7f4f3c3b1a0" />
</details>
***
- `visionect_joan.send_todo_list` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1216" height="1201" alt="image" src="https://github.com/user-attachments/assets/6735340b-bec9-47a6-a72e-07d16da20943" />
</details>
***
- `visionect_joan.send_sensor_graph` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1219" height="1895" alt="image" src="https://github.com/user-attachments/assets/c5507b3b-28e6-47a1-a88a-11d936f2f35b" />
</details>
***
- `visionect_joan.send_rss_feed` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1225" height="1255" alt="image" src="https://github.com/user-attachments/assets/56316ce1-8350-49d5-a624-2f7a880b8a4e" />
</details>
***

### Interaktywność i nawigacja
- `visionect_joan.send_qr_code` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1223" height="1765" alt="image" src="https://github.com/user-attachments/assets/a55360c9-9f17-4b81-baf9-b990692bc2a0" />
</details>
***
- `visionect_joan.start_slideshow` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="606" height="729" alt="slideshow" src="https://github.com/user-attachments/assets/91d25761-2709-417b-9a2c-edf2104c5869" />
</details>
***
- `visionect_joan.send_keypad` […]
<details><summary>Pokaż zrzut ekranu</summary>
  <img width="1220" height="632" alt="image" src="https://github.com/user-attachments/assets/5df2b9d9-ae6e-4a60-9f9f-c787f7658135" />
</details>

### Parametry renderingu i zarządzanie
(oryginalne)
- `visionect_joan.set_session_options` […]
- `visionect_joan.clear_web_cache` […]
- `visionect_joan.force_refresh` […]
- `visionect_joan.set_display_rotation` […]
- `visionect_joan.clear_display` […]
- `visionect_joan.sleep_device` / `visionect_joan.wake_device` […]

---

## Wskazówki konfiguracji usług

| Usługa | Parametry kluczowe | Rekomendacja |
|--------|--------------------|--------------|
| set_url | url, add_back_button | Używaj nazw widoków (predefiniowanych) dla stabilności; adresy lokalne przy VSS w tym samym hoście |
| send_text | message, text_size, image_rotation | Rozmiar 32–48; unikaj zbyt częstych zmian dużych obrazów |
| send_button_panel | buttons[], webhook_id | 3–4 kolumny w pionie; każdy webhook z osobną automatyzacją |
| send_keypad | action_webhook_id, title | PIN max_length 3–6; po błędzie szybki komunikat i powrót do keypad |
| start_slideshow | views[], seconds_per_slide | ≥ 30 s aby ograniczyć zużycie baterii |
| send_sensor_graph | sensor_ids, hours | Godziny ≤ 24 w trybie częstego odświeżania |
| set_session_options | encoding, dithering | encoding=1 dla tekstu/statusów; encoding=4 + floyd‑steinberg dla zdjęć |
| send_rss_feed | feed_url, max_items | 5–10 pozycji czytelne; aktualizacja co 30–60 min |
| send_energy_panel | add_back_button, orientation | Portret czytelniejszy; wywołuj kontekstowo (geo-fence) |

Przykład automatyzacji “Powrót do menu głównego po 5 minutach nieaktywności”:
```
alias: "Joan: powrót do menu"
trigger:
  - platform: time_pattern
    minutes: "/5"
condition:
  - condition: template
    value_template: "{{ states('camera.joan_preview') != 'unavailable' }}"
action:
  - service: visionect_joan.set_url
    data:
      url: MainMenu
    target:
      device_id: YOUR_DEVICE_ID
```

---

## Warstwa interaktywna i webhooki
Priority “Wstecz”: 1) back_button_url 2) encja Back button target 3) globalny Main menu URL.
Wariant dotyk-cały-ekran: `click_anywhere_to_action: true`.

---

## Instalacja
(oryginalna sekcja bez zmian)

### Przez HACS (zalecane) […]
### Ręcznie […]

---

## Konfiguracja
(oryginalna) + upewnij się, że:
- API Key/Secret utworzone w VSS.
- Adres HA dostępny z hosta VSS (jeśli osobny).

---

## Instalacja i konfiguracja Visionect Software Suite

1. Zainstaluj Visionect Software Suite (dodatek / Docker).
2. Upewnij się, że port (np. 8081) jest dostępny z HA.
3. Utwórz API Key & Secret (Users → Add new API key).
4. W integracji wpisz IP/host bez protokołu (np. `192.168.1.10:8081`) jeśli wymaga.
5. Test: wywołaj `visionect_joan.force_refresh`; jeśli encja `camera` odświeży obraz – OK.
6. Oddzielny host? Skonfiguruj poprawny adres wewnętrzny HA (Ustawienia → System → Sieć).

---

## Przykłady użycia
(oryginalne + możesz dodać nowe)
- Światło przyciskiem webhook.
- PIN bezpieczeństwa.
- Rotacja widoków informacyjnych (slideshow).
- Panel energii przy wejściu do strefy.

---

## Wydajność i bateria

| Element | Wskazówka |
|---------|-----------|
| ReloadTimeout | ≥ 60 s dla statycznych widoków |
| Slideshow | Dłuższy czas slajdu = mniej odświeżeń |
| encoding | 1-bit dla tekstu; 4-bit gdy potrzebne odcienie |
| dithering | none dla prostych ikon; floyd‑steinberg dla fotograficznych elementów |
| Nadmierne odświeżenia | Grupuj aktualizacje (automatyzacja) |

---

## Bezpieczeństwo

- Webhooki bez uwierzytelniania – używaj głównie w sieci lokalnej.
- Nie wystawiaj publicznie portu webhooków bez proxy/autoryzacji.
- Trudne, nieoczywiste `webhook_id` (losowe stringi).
- PIN nie w logach – porównuj w szablonie.

---

## Rozwiązywanie problemów

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Brak reakcji przycisku | Zła nazwa webhook_id | Sprawdź w automatyzacji |
| “Stare” obrazy | Cache przeglądarki | `clear_web_cache`, `force_refresh` |
| Brak wykresu | Brak historii sensora | Włącz recorder |
| Wolno się odświeża | encoding=4 + duże obrazy | Zmień na encoding=1 |
| Nie zmienia orientacji | Sesja nie odświeżona | `set_display_rotation` + `force_refresh` |

Debug log:
```
logger:
  logs:
    custom_components.visionect_joan: debug
```

---

## Uwagi

- Projekt nie jest oficjalną integracją Visionect ani Home Assistant.
- Testowany na Joan 6.
- AI użyto do wspomagania rozwoju.
- [Opis instalacji VSS](https://github.com/Adam7411/Joan-6-Visionect_Home-Assistant_EN)
- [Zakup Joan 6](https://allegrolokalnie.pl/oferta/joan-6-nowy-home-assistant-energooszczedny-dotykowy-tablet-eink)

---

## Licencja
MIT
