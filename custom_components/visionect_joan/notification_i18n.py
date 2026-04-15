"""Persistent notification + Ollama diagnostic strings (pl, en, de, fr, es, nl, cs)."""

from __future__ import annotations

from .html_i18n import normalize_lang

_STR: dict[str, dict[str, str]] = {
    "en": {
        "context_truncated": "… (truncated)",
        "battery_low_title": "Low Battery (Visionect)",
        "battery_low_message": "Battery on **{device_name}** dropped to {pct:.0f}%. Please connect the charger.",
        "battery_tablet_heading": "LOW BATTERY",
        "battery_tablet_battery": "Battery: {pct:.0f}%",
        "battery_tablet_footer": "Please connect the charger.",
        "battery_full_title": "Tablet Fully Charged (Visionect)",
        "battery_full_message": "Tablet **{device_name}** is fully charged ({pct:.0f}%). You can unplug the charger.",
        "offline_title": "Connection lost (Visionect)",
        "offline_message": "Tablet **{device_name}** has not connected for over 4 hours. Check whether the battery ran out or Wi‑Fi was lost.",
        "ollama_title": "Visionect AI log analysis",
        "log_analysis_title": "Log analysis",
        "log_analysis_enable_ollama_hint": (
            "For an AI summary of these logs, enable **Ollama log analysis** under "
            "Visionect Joan → Configure (API URL + model). Reload the integration after saving."
        ),
        "log_analysis_no_data": (
            "No VSS log lines for this tablet's UUID and no API context to show."
        ),
        "ollama_api_error": "[Visionect API]\nCould not load device list: {err}",
        "ollama_sep": "--- What the AI analyzed (VSS logs if available + full device list from API) ---",
        "ollama_sep_single_device": "--- What the AI analyzed (VSS log lines mentioning this tablet's UUID + API snapshot for this device only) ---",
        "ollama_no_data": "AI diagnostics: no data available for analysis (no logs and no API data).",
        "ollama_error": "AI diagnostics error: {err}",
        "ollama_button_configure_title": "Ollama analysis not available",
        "ollama_button_configure_body": (
            "Ollama log analysis is turned off or not fully set up.\n\n"
            "To use **Analyze logs (Ollama)** on this tablet:\n"
            "1. Settings → Devices & services → Visionect Joan → **Configure**\n"
            "2. Open **Ollama log analysis**\n"
            "3. Enable **Enable Ollama log analysis**, enter **Ollama API URL** (e.g. http://127.0.0.1:11434) and **Model name**, then submit.\n\n"
            "If you just changed options, **reload** the Visionect Joan integration so the button can run analysis."
        ),
        "ollama_focus_prefix": (
            "[PRIORITY: this device only]\nUUID: {uuid}\n"
            "On-demand analysis for this tablet only. The JSON below is this device only.\n"
            "Check meaning: Session config check = Backend/URL/ReloadTimeout consistency in VSS session; "
            "URL reachability check = whether URL responds via HTTP in timeout; "
            "Device online check = current state from VSS /api/device.\n\nAPI snapshot (this device, JSON):\n"
        ),
        "diag_summary_title": "Diagnostics summary",
        "diag_summary_hint": "Quick read: session correctness, URL response, and current device presence in VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "diag_notification_title": "Visionect VSS diagnostics",
        "diag_notification_intro": "Diagnostics result (grouped by tablet):",
        "diag_group_core_checks": "Core checks",
        "diag_group_extended_checks": "Extended checks",
        "diag_group_findings": "Findings",
        "diag_orphan_check_label": "Orphan/session check",
        "diag_session_opts_label": "Session options",
        "diag_power_profile_label": "Power profile",
        "diag_extended_checks_desc": (
            "Orphan/session flag, SessionOptions (encoding/dithering), "
            "and SleepSchedule/PeriodicSleep/Push/PollingTime sanity hints."
        ),
        "diag_findings_issues": "Issues",
        "diag_findings_warnings": "Warnings",
        "diag_findings_autofix": "Auto-fix",
        "diag_ok_value": "OK",
        "diag_missing_value": "missing",
        "diag_none_value": "none",
        "diag_ollama_hint": (
            "With Ollama enabled, AI analyzes sections in this order: "
            "core checks -> extended checks -> findings, then builds a concise remediation summary."
        ),
        "select_config_title": "Views configuration (Visionect Joan)",
        "select_config_message": (
            "To manage views used by “Choose view” and “Back button target” lists:\n\n"
            "1) Go to: Settings → Devices & Services → Visionect Joan → Configure\n"
            "2) Select the “Views” menu.\n"
            "3) There you will find options:\n"
            "   • Add view: Enter a name and URL, then save.\n"
            "   • Remove view: Select a view from the list to delete it.\n"
            "   • Edit view: Select a view from the list to change its name or URL.\n\n"
            "Views are saved globally and will be available for all your Visionect devices."
        ),
        "safe_read_title": "Visionect Safe Config — Step 1/3 (read)",
        "safe_read_step1_head_ok": "Step 1/3 complete: safe configuration fields were retrieved.",
        "safe_read_step1_head_limited": "Step 1/3: TCLV metadata was retrieved from VSS, but the device did not return live readback for the mapped fields.",
        "safe_read_step1": (
            "{headline}\n\nDevice: `{device}`\n\n{values}\n\n{note}"
            "**Workflow:** **Step 1/3** (optional) — read/diagnose TCLV via VSS (live values, cache after a save, or empty if firmware has no readback). "
            "**Step 2/3** — `visionect_joan.apply_safe_device_config` writes your choices (backs up previous values first). "
            "**Step 3/3** (optional) — `visionect_joan.restore_safe_device_config` restores that backup for this device.\n"
        ),
        "safe_read_note_firmware": "Note: read results depend on firmware; the device may return empty values even when writes succeed.\n\n",
        "safe_read_note_noreadback": (
            "Note: this device/firmware does not return TCLV readback values. "
            "Treat step 1 as diagnostic (optional) and configure using step 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Note: this device/firmware does not return TCLV readback values. "
            "Displayed values come from the last successful apply (cache), not live readback.\n\n"
        ),
        "safe_no_mapping": (
            "No TCLV mapping found for selected fields. Changes were not sent to device.\n\nDevice: `{device}`"
        ),
        "safe_no_mapping_title": "Visionect Safe Config — Mapping missing",
        "safe_applied": (
            "Step 2/3: configuration saved.\n\nDevice: `{device}`\nChanged fields: {fields}\n\nApplied values:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Step 2/3 (saved)",
        "safe_apply_note_live_ok": "Verification: live TCLV readback is available for at least one changed field.",
        "safe_apply_note_no_readback": "Verification: saved, but firmware does not provide live TCLV readback for changed fields.",
        "safe_apply_footer_workflow": (
            "Optional step 3/3: `visionect_joan.restore_safe_device_config` restores the TCLV backup from before this apply (same device)."
        ),
        "safe_apply_failed": (
            "Could not apply safe configuration changes.\n\nDevice: `{device}`\nNo rollback action was executed."
        ),
        "safe_apply_failed_title": "Visionect Safe Config — Apply failed",
        "safe_no_backup": (
            "Step 3/3 skipped: no backup for this device.\n\nDevice: `{device}`\n"
            "Backups are created when you run `apply_safe_device_config` (step 2). Run step 2 first; step 1 (read) is optional."
        ),
        "safe_no_backup_title": "Visionect Safe Config — No backup",
        "safe_restored": (
            "Step 3/3 (optional): backup restored — previous safe TCLV values written back.\n\nDevice: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Step 3/3 (restored)",
        "safe_restore_failed": "Rollback failed while writing previous safe settings.\n\nDevice: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Restore failed",
        "safe_no_applied_fields": "No applied fields",
        "safe_set_minutes": "set to `{val}` minutes",
        "safe_set_value": "set to `{val}`",
        "safe_value_cache_tag": "(cache)",
        "safe_verify_none": "No fields to verify",
        "safe_verify_confirmed": "Confirmed: `{ok}`",
        "safe_verify_diff": "Different from requested: `{diff}`",
        "safe_verify_noresponse": "No device response: `{nores}`",
        "safe_field_heartbeat": "Heart beat interval",
        "safe_field_network_retry": "Network error retry interval",
        "safe_field_system_screens": "System screens",
        "safe_field_touch": "Touch mode",
        "safe_field_power_save": "Power saving mode",
        "safe_values_none": "- (no supported safe fields detected)",
        "safe_values_empty": "Unavailable (firmware without TCLV readback)",
        "recovery_html_title": "Choose a dashboard for this tablet.",
        "recovery_html_no_views": "No views defined. Add them in: Settings → Devices & services → Visionect Joan → Configure → Views.",
        "recovery_html_sticky_hint": "This page was opened without a tablet id in the URL. In VSS Default URL use the full address from the integration (it ends with device=…). Then choosing a view updates the WebKit session on VSS.",
        "recovery_apply_bad_request": "Invalid request.",
        "recovery_apply_forbidden": "Invalid or missing token.",
        "recovery_apply_bad_index": "Unknown view.",
        "recovery_apply_no_api": "Integration not ready. Restart Home Assistant and try again.",
        "recovery_apply_set_url_failed": "Could not set session URL on VSS. Check the device UUID and VSS.",
    },
    "pl": {
        "context_truncated": "… (skrócono)",
        "battery_low_title": "Niski stan baterii (Visionect)",
        "battery_low_message": "Bateria w urządzeniu **{device_name}** spadła do {pct:.0f}%. Proszę podłącz je do ładowania.",
        "battery_tablet_heading": "NISKI POZIOM BATERII",
        "battery_tablet_battery": "Bateria: {pct:.0f}%",
        "battery_tablet_footer": "Podłącz ładowarkę.",
        "battery_full_title": "Tablet naładowany (Visionect)",
        "battery_full_message": "Tablet **{device_name}** jest naładowany ({pct:.0f}%). Możesz odłączyć ładowarkę.",
        "offline_title": "Utrata połączenia (Visionect)",
        "offline_message": "Tablet **{device_name}** nie połączył się od ponad 4 godzin. Sprawdź, czy nie rozładowała się bateria lub czy nie stracił zasięgu Wi‑Fi.",
        "ollama_title": "Analiza AI logów Visionect",
        "log_analysis_title": "Analiza logów",
        "log_analysis_enable_ollama_hint": (
            "Żeby uzyskać tu podsumowanie od modelu AI, włącz **Analizę logów Ollama** w "
            "Visionect Joan → Konfiguruj (adres API + model). Po zapisie przeładuj integrację."
        ),
        "log_analysis_no_data": (
            "Brak linii logów VSS z UUID tego tabletu oraz brak kontekstu z API do wyświetlenia."
        ),
        "ollama_api_error": "[Visionect API]\nNie udało się pobrać listy urządzeń: {err}",
        "ollama_sep": "--- Co analizowało AI (logi VSS, jeśli są + pełna lista urządzeń z API) ---",
        "ollama_sep_single_device": "--- Co analizowało AI (linie logów VSS z tym UUID + snapshot API wyłącznie tego urządzenia) ---",
        "ollama_no_data": "AI diagnostyka: brak danych do analizy (logi niedostępne i API nie zwróciło danych).",
        "ollama_error": "Błąd AI diagnostyki: {err}",
        "ollama_button_configure_title": "Analiza Ollama niedostępna",
        "ollama_button_configure_body": (
            "Analiza logów przez Ollama jest wyłączona albo nie jest w pełni skonfigurowana.\n\n"
            "Żeby użyć przycisku **Analiza logów (Ollama)** przy tym tablecie:\n"
            "1. Ustawienia → Urządzenia i usługi → Visionect Joan → **Konfiguruj**\n"
            "2. Wejdź w **Analiza logów Ollama**\n"
            "3. Włącz **Włącz analizę logów przez Ollama**, podaj **Adres API Ollama** (np. http://127.0.0.1:11434) i **Nazwę modelu**, zapisz.\n\n"
            "Po zmianie opcji **przeładuj** integrację Visionect Joan, żeby przycisk mógł uruchomić analizę."
        ),
        "ollama_focus_prefix": (
            "[PRIORYTET: wyłącznie to urządzenie]\nUUID: {uuid}\n"
            "Analiza na żądanie tylko dla tego tabletu. Poniższy JSON dotyczy wyłącznie tego urządzenia.\n"
            "Znaczenie checków: Session config check = spójność Backend/URL/ReloadTimeout w sesji VSS; "
            "URL reachability check = czy URL odpowiada po HTTP w limicie czasu; "
            "Device online check = bieżący stan urządzenia z VSS /api/device.\n\nSnapshot API (tylko to urządzenie, JSON):\n"
        ),
        "diag_summary_title": "Podsumowanie diagnostyki",
        "diag_summary_hint": "Szybki skrót: poprawność sesji, odpowiedź URL i bieżąca obecność urządzenia w VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "diag_notification_title": "Diagnostyka VSS Visionect",
        "diag_notification_intro": "Wynik diagnostyki (pogrupowany per tablet):",
        "diag_group_core_checks": "Kontrole podstawowe",
        "diag_group_extended_checks": "Kontrole rozszerzone",
        "diag_group_findings": "Wnioski",
        "diag_orphan_check_label": "Kontrola orphan/sesji",
        "diag_session_opts_label": "Opcje sesji",
        "diag_power_profile_label": "Profil zasilania",
        "diag_extended_checks_desc": (
            "Flaga orphan/sesji, SessionOptions (encoding/dithering) oraz "
            "wskazówki dla SleepSchedule/PeriodicSleep/Push/PollingTime."
        ),
        "diag_findings_issues": "Problemy",
        "diag_findings_warnings": "Ostrzeżenia",
        "diag_findings_autofix": "Auto-fix",
        "diag_ok_value": "OK",
        "diag_missing_value": "brak",
        "diag_none_value": "brak",
        "diag_ollama_hint": (
            "Gdy Ollama jest włączona, AI czyta sekcje w kolejności: "
            "kontrole podstawowe -> kontrole rozszerzone -> wnioski, "
            "a potem buduje zwięzłe podsumowanie naprawcze."
        ),
        "select_config_title": "Konfiguracja widoków (Visionect Joan)",
        "select_config_message": (
            "Aby zarządzać widokami dostępnymi w listach „Wybierz widok” oraz „Cel przycisku Wstecz”:\n\n"
            "1) Przejdź do: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj\n"
            "2) Wybierz menu „Widoki” (Views).\n"
            "3) Tam znajdziesz opcje:\n"
            "   • Dodaj widok: Wpisz nazwę i adres URL, a następnie zapisz.\n"
            "   • Usuń widok: Wybierz widok z listy, aby go usunąć.\n"
            "   • Edytuj widok: Wybierz widok z listy, aby zmienić jego nazwę lub URL.\n\n"
            "Widoki są zapisywane globalnie i będą dostępne na wszystkich Twoich urządzeniach Visionect."
        ),
        "safe_read_title": "Visionect Safe Config — Krok 1/3 (odczyt)",
        "safe_read_step1_head_ok": "Krok 1/3 zakończony: pobrano wartości pól bezpiecznej konfiguracji.",
        "safe_read_step1_head_limited": "Krok 1/3: metadane TCLV z VSS są dostępne, ale urządzenie nie zwróciło bieżących wartości odczytu dla zmapowanych pól.",
        "safe_read_step1": (
            "{headline}\n\nUrządzenie: `{device}`\n\n{values}\n\n{note}"
            "**Workflow:** **Krok 1/3** (opcjonalny) — odczyt/diagnostyka TCLV z VSS (live, cache po zapisie w kroku 2 albo pusto przy braku readback). "
            "**Krok 2/3** — `visionect_joan.apply_safe_device_config` zapisuje wybrane wartości (najpierw robi kopię poprzednich na to urządzenie). "
            "**Krok 3/3** (opcjonalny) — `visionect_joan.restore_safe_device_config` przywraca tę kopię.\n"
        ),
        "safe_read_note_firmware": "Uwaga: odczyt jest zależny od firmware, czasem urządzenie zwraca puste wartości mimo poprawnego zapisu.\n\n",
        "safe_read_note_noreadback": (
            "Uwaga: to urządzenie/firmware nie zwraca wartości readback dla TCLV. "
            "Krok 1 traktuj jako diagnostyczny (opcjonalny), a konfigurację ustawiaj przez krok 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Uwaga: to urządzenie/firmware nie zwraca wartości readback dla TCLV. "
            "Pokazane wartości pochodzą z ostatniego udanego zapisu (cache), a nie z bieżącego odczytu.\n\n"
        ),
        "safe_no_mapping": (
            "Nie znaleziono mapowania TCLV dla wybranych pól. Zmiany nie zostały wysłane do urządzenia.\n\nUrządzenie: `{device}`"
        ),
        "safe_no_mapping_title": "Visionect Safe Config — Brak mapowania",
        "safe_applied": (
            "Krok 2/3: zapisano konfigurację.\n\nUrządzenie: `{device}`\nZmienione pola: {fields}\n\nUstawione wartości:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Krok 2/3 (zapis)",
        "safe_apply_note_live_ok": "Weryfikacja: live readback TCLV jest dostępny przynajmniej dla jednego zmienionego pola.",
        "safe_apply_note_no_readback": "Weryfikacja: zapisano, ale firmware nie zwraca live readback TCLV dla zmienionych pól.",
        "safe_apply_footer_workflow": (
            "Opcjonalny krok 3/3: `visionect_joan.restore_safe_device_config` przywraca kopię TCLV sprzed tego zapisu (to samo urządzenie)."
        ),
        "safe_apply_failed": (
            "Nie udało się zapisać zmian bezpiecznej konfiguracji.\n\nUrządzenie: `{device}`\nNie wykonano rollbacku."
        ),
        "safe_apply_failed_title": "Visionect Safe Config — Błąd zapisu",
        "safe_no_backup": (
            "Krok 3/3 pominięty: brak kopii zapasowej dla tego urządzenia.\n\nUrządzenie: `{device}`\n"
            "Kopia powstaje przy `apply_safe_device_config` (krok 2). Uruchom najpierw krok 2; krok 1 (odczyt) jest opcjonalny."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Brak backupu",
        "safe_restored": (
            "Krok 3/3 (opcjonalny): przywrócono kopię — poprzednie wartości TCLV zapisane z powrotem.\n\nUrządzenie: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Krok 3/3 (przywrócono)",
        "safe_restore_failed": "Rollback nie powiódł się podczas zapisu poprzednich ustawień.\n\nUrządzenie: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Błąd przywracania",
        "safe_no_applied_fields": "Brak ustawionych pól",
        "safe_set_minutes": "ustawiono na `{val}` minuty",
        "safe_set_value": "ustawiono na `{val}`",
        "safe_value_cache_tag": "(cache)",
        "safe_verify_none": "Brak pól do weryfikacji",
        "safe_verify_confirmed": "Potwierdzone: `{ok}`",
        "safe_verify_diff": "Różne od żądanych: `{diff}`",
        "safe_verify_noresponse": "Brak odpowiedzi urządzenia: `{nores}`",
        "safe_field_heartbeat": "Interwał heart beat",
        "safe_field_network_retry": "Ponów przy błędzie sieci",
        "safe_field_system_screens": "Ekrany systemowe",
        "safe_field_touch": "Tryb dotyku",
        "safe_field_power_save": "Oszczędzanie energii",
        "safe_values_none": "- (brak obsługiwanych pól safe)",
        "safe_values_empty": "Niedostępne (firmware bez TCLV readback)",
        "recovery_html_title": "Wybierz dashboard dla tego tabletu.",
        "recovery_html_no_views": "Brak zdefiniowanych widoków. Dodaj je w: Ustawienia → Urządzenia i usługi → Visionect Joan → Konfiguruj → Widoki.",
        "recovery_html_sticky_hint": "Strona otwarta bez identyfikatora tabletu w adresie. W VSS w Default URL wklej pełny adres z integracji (kończy się na device=…). Po wyborze widoku zapisze się on w sesji WebKit na VSS.",
        "recovery_apply_bad_request": "Nieprawidłowe żądanie.",
        "recovery_apply_forbidden": "Nieprawidłowy lub brakujący token.",
        "recovery_apply_bad_index": "Nieznany widok.",
        "recovery_apply_no_api": "Integracja nie jest gotowa. Zrestartuj Home Assistant i spróbuj ponownie.",
        "recovery_apply_set_url_failed": "Nie udało się ustawić adresu sesji na VSS. Sprawdź UUID urządzenia i dostępność VSS.",
    },
    "de": {
        "context_truncated": "… (gekürzt)",
        "battery_low_title": "Niedriger Akku (Visionect)",
        "battery_low_message": "Akku von **{device_name}** ist bei {pct:.0f}%. Bitte Ladegerät anschließen.",
        "battery_tablet_heading": "NIEDRIGER AKKUSTAND",
        "battery_tablet_battery": "Akku: {pct:.0f}%",
        "battery_tablet_footer": "Bitte Ladegerät anschließen.",
        "battery_full_title": "Tablet voll geladen (Visionect)",
        "battery_full_message": "Tablet **{device_name}** ist voll geladen ({pct:.0f}%). Sie können das Ladegerät abziehen.",
        "offline_title": "Verbindung verloren (Visionect)",
        "offline_message": "Tablet **{device_name}** war über 4 Stunden nicht verbunden. Prüfen Sie Akku und WLAN.",
        "ollama_title": "Visionect KI-Loganalyse",
        "log_analysis_title": "Log-Analyse",
        "log_analysis_enable_ollama_hint": (
            "Für eine KI-Zusammenfassung **Ollama Log-Analyse** unter Visionect Joan → "
            "Konfigurieren aktivieren (API-URL + Modell). Integration danach neu laden."
        ),
        "log_analysis_no_data": (
            "Keine VSS-Logzeilen zur UUID dieses Tablets und kein API-Kontext."
        ),
        "ollama_api_error": "[Visionect API]\nGeräteliste konnte nicht geladen werden: {err}",
        "ollama_sep": "--- Was die KI analysiert hat (VSS-Logs falls vorhanden + vollständige Geräteliste von der API) ---",
        "ollama_sep_single_device": "--- Was die KI analysiert hat (VSS-Logzeilen mit dieser Geräte-UUID + API-Snapshot nur dieses Geräts) ---",
        "ollama_no_data": "KI-Diagnose: keine Daten zur Analyse (keine Logs und keine API-Daten).",
        "ollama_error": "KI-Diagnosefehler: {err}",
        "ollama_button_configure_title": "Ollama-Analyse nicht verfügbar",
        "ollama_button_configure_body": (
            "Ollama-Loganalyse ist aus oder unvollständig konfiguriert.\n\n"
            "So nutzen Sie **Logs analysieren (Ollama)** für dieses Tablet:\n"
            "1. Einstellungen → Geräte & Dienste → Visionect Joan → **Konfigurieren**\n"
            "2. **Ollama Log-Analyse** öffnen\n"
            "3. **Ollama Log-Analyse aktivieren**, **Ollama API-URL** und **Modellname** eintragen, speichern.\n\n"
            "Nach Änderungen die Integration **neu laden**."
        ),
        "ollama_focus_prefix": (
            "[PRIORITÄT: nur dieses Gerät]\nUUID: {uuid}\n"
            "On-Demand-Analyse nur für dieses Tablet. Das JSON unten betrifft nur dieses Gerät.\n"
            "Prüfungsbedeutung: Session config check = Backend/URL/ReloadTimeout-Konsistenz in VSS; "
            "URL reachability check = ob die URL per HTTP innerhalb des Timeouts antwortet; "
            "Device online check = aktueller Status aus VSS /api/device.\n\nAPI-Snapshot (nur dieses Gerät, JSON):\n"
        ),
        "diag_summary_title": "Diagnosezusammenfassung",
        "diag_summary_hint": "Kurz: Sitzungs-Korrektheit, URL-Antwort und aktueller Gerätestatus in VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "select_config_title": "Ansichten konfigurieren (Visionect Joan)",
        "select_config_message": (
            "So verwalten Sie die Ansichten für „Ansicht wählen“ und „Ziel der Zurück-Taste“:\n\n"
            "1) Einstellungen → Geräte & Dienste → Visionect Joan → Konfigurieren\n"
            "2) Menü „Ansichten“ (Views) öffnen.\n"
            "3) Dort können Sie:\n"
            "   • Ansicht hinzufügen: Name und URL eingeben, speichern.\n"
            "   • Ansicht entfernen: Eintrag aus der Liste wählen und löschen.\n"
            "   • Ansicht bearbeiten: Eintrag wählen, Name oder URL ändern.\n\n"
            "Ansichten werden global gespeichert und gelten für alle Visionect-Geräte."
        ),
        "safe_read_title": "Visionect Safe Config — Schritt 1/3 (Lesen)",
        "safe_read_step1_head_ok": "Schritt 1/3: sichere Konfigurationsfelder wurden abgerufen.",
        "safe_read_step1_head_limited": "Schritt 1/3: TCLV-Metadaten von VSS OK, aber keine Live-Readback-Werte für die zugeordneten Felder.",
        "safe_read_step1": (
            "{headline}\n\nGerät: `{device}`\n\n{values}\n\n{note}"
            "**Ablauf:** **Schritt 1/3** (optional) — TCLV über VSS lesen/diagnostizieren (Live, Cache nach Schritt 2 oder leer ohne Readback). "
            "**Schritt 2/3** — `visionect_joan.apply_safe_device_config` schreibt Ihre Werte (vorher Backup pro Gerät). "
            "**Schritt 3/3** (optional) — `visionect_joan.restore_safe_device_config` stellt dieses Backup wieder her.\n"
        ),
        "safe_read_note_firmware": "Hinweis: Lesewerte hängen von der Firmware ab; leere Werte sind trotz erfolgreichem Schreiben möglich.\n\n",
        "safe_read_note_noreadback": (
            "Hinweis: Dieses Gerät/Firmware liefert keine TCLV-Readback-Werte. "
            "Schritt 1 ist optional diagnostisch; konfigurieren Sie über Schritt 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Hinweis: Dieses Gerät/Firmware liefert keine TCLV-Readback-Werte. "
            "Die angezeigten Werte stammen aus dem letzten erfolgreichen Schreiben (Cache), nicht aus Live-Readback.\n\n"
        ),
        "safe_no_mapping": "Keine TCLV-Zuordnung für die gewählten Felder. Keine Änderungen gesendet.\n\nGerät: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Kein Mapping",
        "safe_applied": (
            "Schritt 2/3: Konfiguration gespeichert.\n\nGerät: `{device}`\nGeänderte Felder: {fields}\n\nGesetzte Werte:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Schritt 2/3 (gespeichert)",
        "safe_apply_note_live_ok": "Prüfung: Live-TCLV-Readback ist für mindestens ein geändertes Feld verfügbar.",
        "safe_apply_note_no_readback": (
            "Prüfung: gespeichert, aber die Firmware liefert kein Live-TCLV-Readback für geänderte Felder."
        ),
        "safe_apply_footer_workflow": (
            "Optionaler Schritt 3/3: `visionect_joan.restore_safe_device_config` stellt das TCLV-Backup vor diesem Schreibvorgang wieder her (gleiches Gerät)."
        ),
        "safe_apply_failed": "Sichere Konfiguration konnte nicht geschrieben werden.\n\nGerät: `{device}`\nKein Rollback ausgeführt.",
        "safe_apply_failed_title": "Visionect Safe Config — Schreibfehler",
        "safe_no_backup": (
            "Schritt 3/3 übersprungen: kein Backup für dieses Gerät.\n\nGerät: `{device}`\n"
            "Backups entstehen bei `apply_safe_device_config` (Schritt 2). Zuerst Schritt 2 ausführen; Schritt 1 (Lesen) ist optional."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Kein Backup",
        "safe_restored": (
            "Schritt 3/3 (optional): Backup wiederhergestellt — vorherige TCLV-Werte zurückgeschrieben.\n\nGerät: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Schritt 3/3 (wiederhergestellt)",
        "safe_restore_failed": "Rollback beim Schreiben fehlgeschlagen.\n\nGerät: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Wiederherstellung fehlgeschlagen",
        "safe_no_applied_fields": "Keine gesetzten Felder",
        "safe_set_minutes": "auf `{val}` Minuten gesetzt",
        "safe_set_value": "auf `{val}` gesetzt",
        "safe_value_cache_tag": "(Cache)",
        "safe_verify_none": "Keine Felder zur Prüfung",
        "safe_verify_confirmed": "Bestätigt: `{ok}`",
        "safe_verify_diff": "Abweichend von Anforderung: `{diff}`",
        "safe_verify_noresponse": "Keine Geräteantwort: `{nores}`",
        "safe_field_heartbeat": "Heart-Beat-Intervall",
        "safe_field_network_retry": "Netzwerkfehler-Wiederholung",
        "safe_field_system_screens": "Systembildschirme",
        "safe_field_touch": "Touch-Modus",
        "safe_field_power_save": "Energiesparmodus",
        "safe_values_none": "- (keine unterstützten Safe-Felder)",
        "safe_values_empty": "Nicht verfügbar (Firmware ohne TCLV-Readback)",
        "recovery_html_title": "Wählen Sie ein Dashboard für dieses Tablet.",
        "recovery_html_no_views": "Keine Ansichten. Unter Einstellungen → Geräte & Dienste → Visionect Joan → Konfigurieren → Ansichten hinzufügen.",
        "recovery_html_sticky_hint": "Seite ohne Tablet-ID in der URL. In VSS Default URL die vollständige Adresse aus der Integration verwenden (endet mit device=…).",
        "recovery_apply_bad_request": "Ungültige Anfrage.",
        "recovery_apply_forbidden": "Ungültiges oder fehlendes Token.",
        "recovery_apply_bad_index": "Unbekannte Ansicht.",
        "recovery_apply_no_api": "Integration nicht bereit. Home Assistant neu starten.",
        "recovery_apply_set_url_failed": "Sitzungs-URL auf VSS konnte nicht gesetzt werden.",
    },
    "fr": {
        "context_truncated": "… (tronqué)",
        "battery_low_title": "Batterie faible (Visionect)",
        "battery_low_message": "La batterie de **{device_name}** est à {pct:.0f}%. Veuillez brancher le chargeur.",
        "battery_tablet_heading": "BATTERIE FAIBLE",
        "battery_tablet_battery": "Batterie : {pct:.0f} %",
        "battery_tablet_footer": "Veuillez brancher le chargeur.",
        "battery_full_title": "Tablette chargée (Visionect)",
        "battery_full_message": "La tablette **{device_name}** est chargée ({pct:.0f} %). Vous pouvez débrancher le chargeur.",
        "offline_title": "Connexion perdue (Visionect)",
        "offline_message": "La tablette **{device_name}** ne s’est pas connectée depuis plus de 4 h. Vérifiez la batterie ou le Wi‑Fi.",
        "ollama_title": "Analyse IA des journaux Visionect",
        "log_analysis_title": "Analyse des journaux",
        "log_analysis_enable_ollama_hint": (
            "Pour un résumé IA, activez **l'analyse des journaux Ollama** dans Visionect Joan → "
            "Configurer (URL API + modèle). Rechargez l'intégration après enregistrement."
        ),
        "log_analysis_no_data": (
            "Aucune ligne de journal VSS pour l'UUID de cette tablette ni contexte API."
        ),
        "ollama_api_error": "[Visionect API]\nImpossible de charger la liste des appareils : {err}",
        "ollama_sep": "--- Ce que l’IA a analysé (journaux VSS si disponibles + liste complète depuis l’API) ---",
        "ollama_sep_single_device": "--- Ce que l’IA a analysé (lignes de journaux VSS mentionnant l’UUID de cette tablette + instantané API pour ce seul appareil) ---",
        "ollama_no_data": "Diagnostic IA : aucune donnée à analyser (pas de journaux ni de données API).",
        "ollama_error": "Erreur du diagnostic IA : {err}",
        "ollama_button_configure_title": "Analyse Ollama indisponible",
        "ollama_button_configure_body": (
            "L’analyse des journaux Ollama est désactivée ou incomplète.\n\n"
            "Pour utiliser **Analyser les journaux (Ollama)** sur cette tablette :\n"
            "1. Paramètres → Appareils et services → Visionect Joan → **Configurer**\n"
            "2. Ouvrir **Analyse des journaux Ollama**\n"
            "3. Activer l’option, renseigner l’**URL API Ollama** et le **nom du modèle**, enregistrer.\n\n"
            "**Rechargez** l’intégration après modification."
        ),
        "ollama_focus_prefix": (
            "[PRIORITÉ : cette tablette uniquement]\nUUID : {uuid}\n"
            "Analyse à la demande pour cette tablette uniquement. Le JSON ci-dessous ne concerne que cet appareil.\n"
            "Signification des contrôles : Session config check = cohérence Backend/URL/ReloadTimeout dans la session VSS ; "
            "URL reachability check = la réponse HTTP de l’URL dans le délai ; "
            "Device online check = état courant depuis VSS /api/device.\n\nInstantané API (cet appareil seul, JSON) :\n"
        ),
        "diag_summary_title": "Résumé du diagnostic",
        "diag_summary_hint": "Résumé rapide : cohérence de session, réponse URL et présence actuelle dans VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "select_config_title": "Configuration des vues (Visionect Joan)",
        "select_config_message": (
            "Pour gérer les vues utilisées par « Choisir la vue » et « Cible du bouton Retour » :\n\n"
            "1) Réglages → Appareils et services → Visionect Joan → Configurer\n"
            "2) Ouvrez le menu « Vues » (Views).\n"
            "3) Vous pouvez :\n"
            "   • Ajouter une vue : nom et URL, puis enregistrer.\n"
            "   • Supprimer une vue : la choisir dans la liste.\n"
            "   • Modifier une vue : la choisir pour changer le nom ou l’URL.\n\n"
            "Les vues sont enregistrées globalement pour tous vos appareils Visionect."
        ),
        "safe_read_title": "Visionect Safe Config — Étape 1/3 (lecture)",
        "safe_read_step1_head_ok": "Étape 1/3 : champs de configuration sûre récupérés.",
        "safe_read_step1_head_limited": "Étape 1/3 : métadonnées TCLV OK sur VSS, mais pas de relecture en direct pour les champs mappés.",
        "safe_read_step1": (
            "{headline}\n\nAppareil : `{device}`\n\n{values}\n\n{note}"
            "**Déroulement :** **Étape 1/3** (optionnelle) — lire/diagnostiquer le TCLV via VSS (direct, cache après l’étape 2 ou vide sans readback). "
            "**Étape 2/3** — `visionect_joan.apply_safe_device_config` enregistre vos choix (sauvegarde préalable par appareil). "
            "**Étape 3/3** (optionnelle) — `visionect_joan.restore_safe_device_config` restaure cette sauvegarde.\n"
        ),
        "safe_read_note_firmware": "Note : la lecture dépend du firmware ; des valeurs vides sont possibles même après écriture.\n\n",
        "safe_read_note_noreadback": (
            "Note : ce matériel/firmware ne renvoie pas de lecture TCLV. "
            "L’étape 1 est optionnelle ; configurez via l’étape 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Note : ce matériel/firmware ne renvoie pas de lecture TCLV. "
            "Les valeurs affichées proviennent du dernier enregistrement réussi (cache), pas d’une lecture en direct.\n\n"
        ),
        "safe_no_mapping": "Aucun mappage TCLV pour les champs choisis. Aucun envoi.\n\nAppareil : `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Pas de mappage",
        "safe_applied": (
            "Étape 2/3 : configuration enregistrée.\n\nAppareil : `{device}`\nChamps modifiés : {fields}\n\nValeurs appliquées :\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Étape 2/3 (enregistré)",
        "safe_apply_note_live_ok": "Vérification : relecture TCLV en direct disponible pour au moins un champ modifié.",
        "safe_apply_note_no_readback": (
            "Vérification : enregistré, mais le firmware ne fournit pas de relecture TCLV en direct pour les champs modifiés."
        ),
        "safe_apply_footer_workflow": (
            "Étape 3/3 (optionnelle) : `visionect_joan.restore_safe_device_config` restaure la sauvegarde TCLV avant cet enregistrement (même appareil)."
        ),
        "safe_apply_failed": "Impossible d’appliquer la configuration sécurisée.\n\nAppareil : `{device}`\nAucun rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Échec d’écriture",
        "safe_no_backup": (
            "Étape 3/3 ignorée : aucune sauvegarde pour cet appareil.\n\nAppareil : `{device}`\n"
            "La sauvegarde est créée par `apply_safe_device_config` (étape 2). Exécutez d’abord l’étape 2 ; l’étape 1 (lecture) est optionnelle."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Pas de sauvegarde",
        "safe_restored": (
            "Étape 3/3 (optionnelle) : sauvegarde restaurée — anciennes valeurs TCLV réécrites.\n\nAppareil : `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Étape 3/3 (restauré)",
        "safe_restore_failed": "Échec du rollback.\n\nAppareil : `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Échec de restauration",
        "safe_no_applied_fields": "Aucun champ appliqué",
        "safe_set_minutes": "réglé sur `{val}` minutes",
        "safe_set_value": "réglé sur `{val}`",
        "safe_value_cache_tag": "(cache)",
        "safe_verify_none": "Aucun champ à vérifier",
        "safe_verify_confirmed": "Confirmé : `{ok}`",
        "safe_verify_diff": "Différent de la demande : `{diff}`",
        "safe_verify_noresponse": "Pas de réponse de l’appareil : `{nores}`",
        "safe_field_heartbeat": "Intervalle heart beat",
        "safe_field_network_retry": "Nouvelle tentative réseau",
        "safe_field_system_screens": "Écrans système",
        "safe_field_touch": "Mode tactile",
        "safe_field_power_save": "Économie d’énergie",
        "safe_values_none": "- (aucun champ safe pris en charge)",
        "safe_values_empty": "Indisponible (firmware sans readback TCLV)",
        "recovery_html_title": "Choisissez un tableau de bord pour cette tablette.",
        "recovery_html_no_views": "Aucune vue. Ajoutez-en dans Réglages → Appareils et services → Visionect Joan → Configurer → Vues.",
        "recovery_html_sticky_hint": "Page ouverte sans identifiant tablette dans l’URL. Dans Default URL du VSS, collez l’adresse complète de l’intégration (se termine par device=…).",
        "recovery_apply_bad_request": "Requête invalide.",
        "recovery_apply_forbidden": "Jeton invalide ou manquant.",
        "recovery_apply_bad_index": "Vue inconnue.",
        "recovery_apply_no_api": "Intégration pas prête. Redémarrez Home Assistant.",
        "recovery_apply_set_url_failed": "Impossible de définir l’URL de session sur le VSS.",
    },
    "es": {
        "context_truncated": "… (truncado)",
        "battery_low_title": "Batería baja (Visionect)",
        "battery_low_message": "La batería de **{device_name}** está al {pct:.0f}%. Conecte el cargador.",
        "battery_tablet_heading": "BATERÍA BAJA",
        "battery_tablet_battery": "Batería: {pct:.0f} %",
        "battery_tablet_footer": "Conecte el cargador.",
        "battery_full_title": "Tablet cargada (Visionect)",
        "battery_full_message": "La tablet **{device_name}** está cargada ({pct:.0f} %). Puede desenchufar el cargador.",
        "offline_title": "Conexión perdida (Visionect)",
        "offline_message": "La tablet **{device_name}** no se ha conectado en más de 4 horas. Compruebe batería o Wi‑Fi.",
        "ollama_title": "Análisis IA de registros Visionect",
        "log_analysis_title": "Análisis de registros",
        "log_analysis_enable_ollama_hint": (
            "Para un resumen con IA, activa **Análisis de registros Ollama** en Visionect Joan → "
            "Configurar (URL API + modelo). Recarga la integración tras guardar."
        ),
        "log_analysis_no_data": (
            "No hay líneas de registro VSS para el UUID de esta tableta ni contexto de API."
        ),
        "ollama_api_error": "[Visionect API]\nNo se pudo cargar la lista de dispositivos: {err}",
        "ollama_sep": "--- Lo que analizó la IA (registros VSS si hay + lista completa desde la API) ---",
        "ollama_sep_single_device": "--- Lo que analizó la IA (líneas de registro VSS con el UUID de esta tableta + instantánea API solo de este dispositivo) ---",
        "ollama_no_data": "Diagnóstico IA: no hay datos para analizar (sin registros ni datos de API).",
        "ollama_error": "Error del diagnóstico IA: {err}",
        "ollama_button_configure_title": "Análisis Ollama no disponible",
        "ollama_button_configure_body": (
            "El análisis de registros con Ollama está desactivado o incompleto.\n\n"
            "Para usar **Analizar registros (Ollama)** en esta tableta:\n"
            "1. Ajustes → Dispositivos y servicios → Visionect Joan → **Configurar**\n"
            "2. Abrir **Análisis de registros Ollama**\n"
            "3. Activar la opción, indicar la **URL API Ollama** y el **nombre del modelo**, guardar.\n\n"
            "**Recarga** la integración tras los cambios."
        ),
        "ollama_focus_prefix": (
            "[PRIORIDAD: solo esta tableta]\nUUID: {uuid}\n"
            "Análisis bajo demanda solo para esta tableta. El JSON siguiente es solo de este dispositivo.\n"
            "Significado de checks: Session config check = consistencia de Backend/URL/ReloadTimeout en sesión VSS; "
            "URL reachability check = si la URL responde por HTTP dentro del timeout; "
            "Device online check = estado actual desde VSS /api/device.\n\nInstantánea API (solo este dispositivo, JSON):\n"
        ),
        "diag_summary_title": "Resumen de diagnóstico",
        "diag_summary_hint": "Resumen rápido: coherencia de sesión, respuesta URL y presencia actual del dispositivo en VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "select_config_title": "Configuración de vistas (Visionect Joan)",
        "select_config_message": (
            "Para gestionar las vistas de «Elegir vista» y «Destino del botón Atrás»:\n\n"
            "1) Ajustes → Dispositivos y servicios → Visionect Joan → Configurar\n"
            "2) Abra el menú «Vistas» (Views).\n"
            "3) Allí puede:\n"
            "   • Añadir vista: nombre y URL, luego guardar.\n"
            "   • Eliminar vista: seleccionar en la lista.\n"
            "   • Editar vista: seleccionar para cambiar nombre o URL.\n\n"
            "Las vistas se guardan globalmente para todos los dispositivos Visionect."
        ),
        "safe_read_title": "Visionect Safe Config — Paso 1/3 (lectura)",
        "safe_read_step1_head_ok": "Paso 1/3: se obtuvieron los campos de configuración segura.",
        "safe_read_step1_head_limited": "Paso 1/3: metadatos TCLV OK en VSS, pero el dispositivo no devolvió valores en vivo para los campos asignados.",
        "safe_read_step1": (
            "{headline}\n\nDispositivo: `{device}`\n\n{values}\n\n{note}"
            "**Flujo:** **Paso 1/3** (opcional) — leer/diagnosticar TCLV vía VSS (en vivo, caché tras el paso 2 o vacío sin readback). "
            "**Paso 2/3** — `visionect_joan.apply_safe_device_config` guarda sus valores (antes hace copia por dispositivo). "
            "**Paso 3/3** (opcional) — `visionect_joan.restore_safe_device_config` restaura esa copia.\n"
        ),
        "safe_read_note_firmware": "Nota: la lectura depende del firmware; puede devolver valores vacíos aunque la escritura haya funcionado.\n\n",
        "safe_read_note_noreadback": (
            "Nota: este dispositivo/firmware no devuelve lectura TCLV. "
            "El paso 1 es opcional; configure en el paso 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Nota: este dispositivo/firmware no devuelve lectura TCLV. "
            "Los valores mostrados provienen del último guardado correcto (caché), no de una lectura en vivo.\n\n"
        ),
        "safe_no_mapping": "Sin mapeo TCLV para los campos elegidos. No se envió nada.\n\nDispositivo: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Sin mapeo",
        "safe_applied": (
            "Paso 2/3: configuración guardada.\n\nDispositivo: `{device}`\nCampos cambiados: {fields}\n\nValores aplicados:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Paso 2/3 (guardado)",
        "safe_apply_note_live_ok": "Verificación: hay readback TCLV en vivo para al menos un campo modificado.",
        "safe_apply_note_no_readback": (
            "Verificación: guardado, pero el firmware no ofrece readback TCLV en vivo para los campos modificados."
        ),
        "safe_apply_footer_workflow": (
            "Paso 3/3 (opcional): `visionect_joan.restore_safe_device_config` restaura la copia TCLV anterior a este guardado (mismo dispositivo)."
        ),
        "safe_apply_failed": "No se pudo aplicar la configuración segura.\n\nDispositivo: `{device}`\nSin rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Error al guardar",
        "safe_no_backup": (
            "Paso 3/3 omitido: no hay copia para este dispositivo.\n\nDispositivo: `{device}`\n"
            "La copia se crea con `apply_safe_device_config` (paso 2). Ejecute primero el paso 2; el paso 1 (lectura) es opcional."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Sin copia",
        "safe_restored": (
            "Paso 3/3 (opcional): copia restaurada — valores TCLV anteriores escritos de nuevo.\n\nDispositivo: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Paso 3/3 (restaurado)",
        "safe_restore_failed": "Fallo del rollback.\n\nDispositivo: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Error al restaurar",
        "safe_no_applied_fields": "Sin campos aplicados",
        "safe_set_minutes": "establecido en `{val}` minutos",
        "safe_set_value": "establecido en `{val}`",
        "safe_value_cache_tag": "(caché)",
        "safe_verify_none": "Sin campos que verificar",
        "safe_verify_confirmed": "Confirmados: `{ok}`",
        "safe_verify_diff": "Distintos de lo solicitado: `{diff}`",
        "safe_verify_noresponse": "Sin respuesta del dispositivo: `{nores}`",
        "safe_field_heartbeat": "Intervalo heart beat",
        "safe_field_network_retry": "Reintento de error de red",
        "safe_field_system_screens": "Pantallas del sistema",
        "safe_field_touch": "Modo táctil",
        "safe_field_power_save": "Ahorro de energía",
        "safe_values_none": "- (sin campos safe admitidos)",
        "safe_values_empty": "No disponible (firmware sin readback TCLV)",
        "recovery_html_title": "Elige un panel para esta tableta.",
        "recovery_html_no_views": "Sin vistas. Añádelas en Ajustes → Dispositivos y servicios → Visionect Joan → Configurar → Vistas.",
        "recovery_html_sticky_hint": "Página abierta sin id de tableta en la URL. En Default URL del VSS usa la dirección completa de la integración (termina en device=…).",
        "recovery_apply_bad_request": "Solicitud no válida.",
        "recovery_apply_forbidden": "Token no válido o ausente.",
        "recovery_apply_bad_index": "Vista desconocida.",
        "recovery_apply_no_api": "Integración no lista. Reinicia Home Assistant.",
        "recovery_apply_set_url_failed": "No se pudo fijar la URL de sesión en el VSS.",
    },
    "nl": {
        "context_truncated": "… (ingekort)",
        "battery_low_title": "Lage batterij (Visionect)",
        "battery_low_message": "Batterij van **{device_name}** is {pct:.0f}%. Sluit de oplader aan.",
        "battery_tablet_heading": "LAGE BATTERIJ",
        "battery_tablet_battery": "Batterij: {pct:.0f}%",
        "battery_tablet_footer": "Sluit de oplader aan.",
        "battery_full_title": "Tablet vol (Visionect)",
        "battery_full_message": "Tablet **{device_name}** is vol ({pct:.0f}%). U kunt de oplader loskoppelen.",
        "offline_title": "Verbinding verbroken (Visionect)",
        "offline_message": "Tablet **{device_name}** is meer dan 4 uur niet verbonden. Controleer batterij of Wi‑Fi.",
        "ollama_title": "Visionect AI-loganalyse",
        "log_analysis_title": "Loganalyse",
        "log_analysis_enable_ollama_hint": (
            "Voor een AI-samenvatting: schakel **Ollama loganalyse** in onder Visionect Joan → "
            "Configureren (API-URL + model). Laad de integratie daarna opnieuw."
        ),
        "log_analysis_no_data": (
            "Geen VSS-logregels voor de UUID van deze tablet en geen API-context."
        ),
        "ollama_api_error": "[Visionect API]\nApparatenlijst laden mislukt: {err}",
        "ollama_sep": "--- Wat de AI heeft geanalyseerd (VSS-logboeken indien aanwezig + volledige lijst via API) ---",
        "ollama_sep_single_device": "--- Wat de AI heeft geanalyseerd (VSS-logregels met UUID van deze tablet + API-momentopname alleen van dit apparaat) ---",
        "ollama_no_data": "AI-diagnose: geen gegevens om te analyseren (geen logboeken en geen API-gegevens).",
        "ollama_error": "AI-diagnosefout: {err}",
        "ollama_button_configure_title": "Ollama-analyse niet beschikbaar",
        "ollama_button_configure_body": (
            "Ollama-loganalyse staat uit of is niet volledig ingesteld.\n\n"
            "Om **Logboeken analyseren (Ollama)** voor deze tablet te gebruiken:\n"
            "1. Instellingen → Apparaten en diensten → Visionect Joan → **Configureren**\n"
            "2. **Ollama loganalyse** openen\n"
            "3. Inschakelen, **Ollama API-URL** en **modelnaam** invullen, opslaan.\n\n"
            "**Herlaad** de integratie na wijzigingen."
        ),
        "ollama_focus_prefix": (
            "[PRIORITEIT: alleen dit apparaat]\nUUID: {uuid}\n"
            "Analyse op aanvraag alleen voor deze tablet. De JSON hieronder is alleen dit apparaat.\n"
            "Betekenis van checks: Session config check = consistentie van Backend/URL/ReloadTimeout in VSS-sessie; "
            "URL reachability check = of URL via HTTP binnen timeout reageert; "
            "Device online check = actuele status uit VSS /api/device.\n\nAPI-momentopname (alleen dit apparaat, JSON):\n"
        ),
        "diag_summary_title": "Diagnosesamenvatting",
        "diag_summary_hint": "Snelle samenvatting: sessiecorrectheid, URL-respons en huidige apparaatstatus in VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "select_config_title": "Weergaven configureren (Visionect Joan)",
        "select_config_message": (
            "Beheer de weergaven voor «Weergave kiezen» en «Doel knop Terug»:\n\n"
            "1) Instellingen → Apparaten en diensten → Visionect Joan → Configureren\n"
            "2) Open het menu «Weergaven» (Views).\n"
            "3) Daar kunt u:\n"
            "   • Weergave toevoegen: naam en URL, daarna opslaan.\n"
            "   • Weergave verwijderen: uit de lijst kiezen.\n"
            "   • Weergave bewerken: uit de lijst kiezen om naam of URL te wijzigen.\n\n"
            "Weergaven worden globaal opgeslagen voor alle Visionect-apparaten."
        ),
        "safe_read_title": "Visionect Safe Config — Stap 1/3 (uitlezen)",
        "safe_read_step1_head_ok": "Stap 1/3: veilige configuratievelden opgehaald.",
        "safe_read_step1_head_limited": "Stap 1/3: TCLV-metadata van VSS OK, maar geen live readback voor de toegewezen velden.",
        "safe_read_step1": (
            "{headline}\n\nApparaat: `{device}`\n\n{values}\n\n{note}"
            "**Werkwijze:** **Stap 1/3** (optioneel) — TCLV via VSS lezen/diagnosticeren (live, cache na stap 2 of leeg zonder readback). "
            "**Stap 2/3** — `visionect_joan.apply_safe_device_config` schrijft uw waarden (eerst back-up per apparaat). "
            "**Stap 3/3** (optioneel) — `visionect_joan.restore_safe_device_config` herstelt die back-up.\n"
        ),
        "safe_read_note_firmware": "Let op: uitlezen hangt van firmware af; lege waarden zijn mogelijk na een geslaagde schrijfactie.\n\n",
        "safe_read_note_noreadback": (
            "Let op: dit apparaat/firmware geeft geen TCLV readback. "
            "Stap 1 is optioneel diagnostisch; configureer via stap 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Let op: dit apparaat/firmware geeft geen TCLV readback. "
            "De getoonde waarden komen uit de laatste succesvolle schrijfactie (cache), niet uit live readback.\n\n"
        ),
        "safe_no_mapping": "Geen TCLV-mapping voor gekozen velden. Niets verzonden.\n\nApparaat: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Geen mapping",
        "safe_applied": (
            "Stap 2/3: configuratie opgeslagen.\n\nApparaat: `{device}`\nGewijzigde velden: {fields}\n\nToegepaste waarden:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Stap 2/3 (opgeslagen)",
        "safe_apply_note_live_ok": "Verificatie: live TCLV-readback is beschikbaar voor minstens één gewijzigd veld.",
        "safe_apply_note_no_readback": (
            "Verificatie: opgeslagen, maar firmware biedt geen live TCLV-readback voor gewijzigde velden."
        ),
        "safe_apply_footer_workflow": (
            "Optionele stap 3/3: `visionect_joan.restore_safe_device_config` herstelt de TCLV-back-up vóór deze schrijfactie (zelfde apparaat)."
        ),
        "safe_apply_failed": "Veilige configuratie kon niet worden geschreven.\n\nApparaat: `{device}`\nGeen rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Schrijffout",
        "safe_no_backup": (
            "Stap 3/3 overgeslagen: geen back-up voor dit apparaat.\n\nApparaat: `{device}`\n"
            "Back-ups ontstaan bij `apply_safe_device_config` (stap 2). Voer eerst stap 2 uit; stap 1 (uitlezen) is optioneel."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Geen back-up",
        "safe_restored": (
            "Stap 3/3 (optioneel): back-up hersteld — eerdere TCLV-waarden teruggeschreven.\n\nApparaat: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Stap 3/3 (hersteld)",
        "safe_restore_failed": "Rollback mislukt.\n\nApparaat: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Herstel mislukt",
        "safe_no_applied_fields": "Geen toegepaste velden",
        "safe_set_minutes": "ingesteld op `{val}` minuten",
        "safe_set_value": "ingesteld op `{val}`",
        "safe_value_cache_tag": "(cache)",
        "safe_verify_none": "Geen velden om te verifiëren",
        "safe_verify_confirmed": "Bevestigd: `{ok}`",
        "safe_verify_diff": "Afwijkend van gevraagd: `{diff}`",
        "safe_verify_noresponse": "Geen apparaatantwoord: `{nores}`",
        "safe_field_heartbeat": "Heart beat-interval",
        "safe_field_network_retry": "Netwerkfout opnieuw proberen",
        "safe_field_system_screens": "Systeemschermen",
        "safe_field_touch": "Aanraakmodus",
        "safe_field_power_save": "Energiebesparing",
        "safe_values_none": "- (geen ondersteunde safe-velden)",
        "safe_values_empty": "Niet beschikbaar (firmware zonder TCLV-readback)",
        "recovery_html_title": "Kies een dashboard voor deze tablet.",
        "recovery_html_no_views": "Geen weergaven. Voeg toe via Instellingen → Apparaten en diensten → Visionect Joan → Configureren → Weergaven.",
        "recovery_html_sticky_hint": "Pagina geopend zonder tablet-id in de URL. Gebruik in VSS Default URL het volledige adres uit de integratie (eindigt op device=…).",
        "recovery_apply_bad_request": "Ongeldig verzoek.",
        "recovery_apply_forbidden": "Ongeldig of ontbrekend token.",
        "recovery_apply_bad_index": "Onbekende weergave.",
        "recovery_apply_no_api": "Integratie niet gereed. Herstart Home Assistant.",
        "recovery_apply_set_url_failed": "Sessie-URL op VSS instellen mislukt.",
    },
    "cs": {
        "context_truncated": "… (zkráceno)",
        "battery_low_title": "Slabá baterie (Visionect)",
        "battery_low_message": "Baterie zařízení **{device_name}** je na {pct:.0f} %. Připojte nabíječku.",
        "battery_tablet_heading": "SLABÁ BATERIE",
        "battery_tablet_battery": "Baterie: {pct:.0f} %",
        "battery_tablet_footer": "Připojte nabíječku.",
        "battery_full_title": "Tablet nabit (Visionect)",
        "battery_full_message": "Tablet **{device_name}** je nabit ({pct:.0f} %). Nabíječku můžete odpojit.",
        "offline_title": "Ztracené spojení (Visionect)",
        "offline_message": "Tablet **{device_name}** se nepřipojil déle než 4 hodiny. Zkontrolujte baterii nebo Wi‑Fi.",
        "ollama_title": "Visionect AI analýza logů",
        "log_analysis_title": "Analýza logů",
        "log_analysis_enable_ollama_hint": (
            "Pro shrnutí od AI zapněte **Analýzu logů Ollama** v Visionect Joan → "
            "Konfigurovat (URL API + model). Po uložení integraci znovu načtěte."
        ),
        "log_analysis_no_data": (
            "Žádné řádky logu VSS pro UUID tohoto tabletu ani kontext z API."
        ),
        "ollama_api_error": "[Visionect API]\nNepodařilo se načíst seznam zařízení: {err}",
        "ollama_sep": "--- Co AI analyzovala (logy VSS pokud jsou + úplný seznam z API) ---",
        "ollama_sep_single_device": "--- Co AI analyzovala (řádky logů VSS s UUID tohoto tabletu + snapshot API jen tohoto zařízení) ---",
        "ollama_no_data": "AI diagnostika: žádná data k analýze (chybí logy i data z API).",
        "ollama_error": "Chyba AI diagnostiky: {err}",
        "ollama_button_configure_title": "Analýza Ollama není k dispozici",
        "ollama_button_configure_body": (
            "Analýza logů Ollama je vypnutá nebo není kompletně nastavená.\n\n"
            "Pro použití **Analyzovat logy (Ollama)** u tohoto tabletu:\n"
            "1. Nastavení → Zařízení a služby → Visionect Joan → **Nakonfigurovat**\n"
            "2. Otevřít **Analýza logů Ollama**\n"
            "3. Zapnout, vyplnit **URL API Ollama** a **název modelu**, uložit.\n\n"
            "Po změně **znovu načtěte** integraci."
        ),
        "ollama_focus_prefix": (
            "[PRIORITA: pouze toto zařízení]\nUUID: {uuid}\n"
            "Analýza na vyžádání jen pro tento tablet. JSON níže je jen toto zařízení.\n"
            "Význam kontrol: Session config check = konzistence Backend/URL/ReloadTimeout v relaci VSS; "
            "URL reachability check = zda URL odpovídá přes HTTP v timeoutu; "
            "Device online check = aktuální stav z VSS /api/device.\n\nSnapshot z API (jen toto zařízení, JSON):\n"
        ),
        "diag_summary_title": "Souhrn diagnostiky",
        "diag_summary_hint": "Rychlé shrnutí: správnost relace, odezva URL a aktuální stav zařízení ve VSS.",
        "diag_session_check_label": "Session config check",
        "diag_url_check_label": "URL reachability check",
        "diag_online_check_label": "Device online check",
        "select_config_title": "Konfigurace zobrazení (Visionect Joan)",
        "select_config_message": (
            "Správa zobrazení pro „Vybrat zobrazení“ a „Cíl tlačítka Zpět“:\n\n"
            "1) Nastavení → Zařízení a služby → Visionect Joan → Konfigurovat\n"
            "2) Otevřete nabídku „Zobrazení“ (Views).\n"
            "3) Můžete:\n"
            "   • Přidat zobrazení: název a URL, uložit.\n"
            "   • Odstranit zobrazení: vybrat ze seznamu.\n"
            "   • Upravit zobrazení: vybrat a změnit název nebo URL.\n\n"
            "Zobrazení jsou uložena globálně pro všechna zařízení Visionect."
        ),
        "safe_read_title": "Visionect Safe Config — Krok 1/3 (čtení)",
        "safe_read_step1_head_ok": "Krok 1/3: pole bezpečné konfigurace načtena.",
        "safe_read_step1_head_limited": "Krok 1/3: metadata TCLV z VSS v pořádku, ale zařízení nevrátilo živé hodnoty pro mapovaná pole.",
        "safe_read_step1": (
            "{headline}\n\nZařízení: `{device}`\n\n{values}\n\n{note}"
            "**Postup:** **Krok 1/3** (volitelný) — čtení/diagnostika TCLV přes VSS (živě, cache po kroku 2 nebo prázdné bez readback). "
            "**Krok 2/3** — `visionect_joan.apply_safe_device_config` zapíše vaše hodnoty (nejdřív záloha pro zařízení). "
            "**Krok 3/3** (volitelný) — `visionect_joan.restore_safe_device_config` obnoví tuto zálohu.\n"
        ),
        "safe_read_note_firmware": "Poznámka: čtení závisí na firmwaru; prázdné hodnoty jsou možné i po úspěšném zápisu.\n\n",
        "safe_read_note_noreadback": (
            "Poznámka: toto zařízení/firmware nevrací TCLV readback. "
            "Krok 1 je volitelná diagnostika; konfigurujte krokem 2.\n\n"
        ),
        "safe_read_note_cached": (
            "Poznámka: toto zařízení/firmware nevrací TCLV readback. "
            "Zobrazené hodnoty pochází z posledního úspěšného zápisu (cache), ne z živého čtení.\n\n"
        ),
        "safe_no_mapping": "Chybí mapování TCLV pro zvolená pole. Nic neodesláno.\n\nZařízení: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Chybí mapování",
        "safe_applied": (
            "Krok 2/3: konfigurace uložena.\n\nZařízení: `{device}`\nZměněná pole: {fields}\n\nNastavené hodnoty:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Krok 2/3 (uloženo)",
        "safe_apply_note_live_ok": "Ověření: živý TCLV readback je k dispozici pro alespoň jedno změněné pole.",
        "safe_apply_note_no_readback": (
            "Ověření: uloženo, ale firmware neposkytuje živý TCLV readback pro změněná pole."
        ),
        "safe_apply_footer_workflow": (
            "Volitelný krok 3/3: `visionect_joan.restore_safe_device_config` obnoví zálohu TCLV před tímto zápisem (stejné zařízení)."
        ),
        "safe_apply_failed": "Nepodařilo se zapsat bezpečnou konfiguraci.\n\nZařízení: `{device}`\nRollback neproběhl.",
        "safe_apply_failed_title": "Visionect Safe Config — Chyba zápisu",
        "safe_no_backup": (
            "Krok 3/3 přeskočen: žádná záloha pro toto zařízení.\n\nZařízení: `{device}`\n"
            "Záloha vzniká při `apply_safe_device_config` (krok 2). Nejdřív spusťte krok 2; krok 1 (čtení) je volitelný."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Žádná záloha",
        "safe_restored": (
            "Krok 3/3 (volitelný): záloha obnovena — předchozí hodnoty TCLV zapsány zpět.\n\nZařízení: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Krok 3/3 (obnoveno)",
        "safe_restore_failed": "Rollback selhal.\n\nZařízení: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Chyba obnovení",
        "safe_no_applied_fields": "Žádná nastavená pole",
        "safe_set_minutes": "nastaveno na `{val}` minut",
        "safe_set_value": "nastaveno na `{val}`",
        "safe_value_cache_tag": "(cache)",
        "safe_verify_none": "Žádná pole k ověření",
        "safe_verify_confirmed": "Potvrzeno: `{ok}`",
        "safe_verify_diff": "Liší se od požadavku: `{diff}`",
        "safe_verify_noresponse": "Bez odpovědi zařízení: `{nores}`",
        "safe_field_heartbeat": "Interval heart beat",
        "safe_field_network_retry": "Opakování při chybě sítě",
        "safe_field_system_screens": "Systémové obrazovky",
        "safe_field_touch": "Dotykový režim",
        "safe_field_power_save": "Úspora energie",
        "safe_values_none": "- (žádná podporovaná safe pole)",
        "safe_values_empty": "Nedostupné (firmware bez TCLV readbacku)",
        "recovery_html_title": "Vyberte dashboard pro tento tablet.",
        "recovery_html_no_views": "Žádné pohledy. Přidejte je v Nastavení → Zařízení a služby → Visionect Joan → Konfigurovat → Pohledy.",
        "recovery_html_sticky_hint": "Stránka otevřená bez ID tabletu v adrese. V Default URL (VSS) vložte celou adresu z integrace (končí na device=…).",
        "recovery_apply_bad_request": "Neplatný požadavek.",
        "recovery_apply_forbidden": "Neplatný nebo chybějící token.",
        "recovery_apply_bad_index": "Neznámý pohled.",
        "recovery_apply_no_api": "Integrace není připravena. Restartujte Home Assistant.",
        "recovery_apply_set_url_failed": "Nepodařilo se nastavit URL relace na VSS.",
    },
}


# Compact Visionect Server Management API context for Ollama (see https://api.visionect.com/ , docs.visionect.com).
_OLLAMA_VSS_API_PL = (
    "Kontekst API Visionect (VSS):\n"
    "• VSS to serwer „cienkiego klienta”: renderuje aplikacje HTML (silnik WebKit/Okular) i wysyła grafikę na tablety; "
    "typowo port 8081, REST JSON, uwierzytelnianie nagłówkiem Authorization = HMAC-SHA256 (w stylu AWS S3 REST).\n"
    "• Obiekt urządzenia: State = online|offline (odczyt); Status (m.in. Battery, Charger, RSSI, Temperature, "
    "ExternalBattery, ConnectReason, ConnectivityUsed, ErrorCode, Push, ApplicationVersion; opcjonalnie PrematureWakeup). "
    "ErrorCode 0 lub 0x0 = brak błędu. ConnectReason np. heartbeat, wakeup — przy offline nie wyciągaj wniosku „zły ErrorCode” "
    "bez kontekstu (ostatni znany status może być nieaktualny, sen Wi‑Fi, zasięg).\n"
    "• Options urządzenia: m.in. SleepSchedule, PeriodicSleep, ScheduledWakeup, PollingTime, Firmware — wpływają na to, "
    "kiedy tablet się budzi i jak często łączy.\n"
    "• Sesja WebKit (per UUID): Backend Name=HTML, Fields.url = adres strony; w URL dozwolony placeholder {uuid}. "
    "Restart sesji przeładowuje WebKit; czyszczenie cache WebKit: batch UUID (integracja HA często to robi).\n"
    "• GET /api/orphans — urządzenia/sesje podejrzane o problem; przydatne przy „dziwnym” stanie.\n"
    "• Interpretacja stanu: `State=charging` traktuj jako stan zasilania (informacyjny), NIE jako awarię; "
    "awarię rozważaj dopiero przy ErrorCode != 0/0x0, nieosiągalnym URL, orphan error albo realnym OFFLINE.\n"
    "• GET/PUT /api/config — pełna konfiguracja serwera, m.in. Okular.Defaults.Backend.Fields.url = domyślny URI (jak „Default URL” "
    "w GUI); to NIE to samo co bieżący URL sesji konkretnego tabletu z /api/session/{Uuid}.\n"
    "• Uwierzytelnianie HMAC (AWS-like): pilnuj zgodności Date/Content-Type z podpisem, RequestPath (często z trailing slash), "
    "oraz kolejności pól: VERB + '\\n' + Content-Sha256 + '\\n' + Content-Type + '\\n' + Date + '\\n' + RequestPath.\n"
    "• Diagnostyka sesji WebKit: /api/session/{Uuid}, /api/session/{Uuid}/restart, /api/session/webkit-clear-cache (batch UUID). "
    "Jeśli URL działa, ale widok jest „stary”, sugeruj cache clear + restart sesji zamiast ogólnego restartu wszystkiego.\n"
    "• /api/live/device/{Uuid}/image(.png) pokazuje aktualny obraz na urządzeniu, a /cached pokazuje obraz po stronie serwera — "
    "różnica pomaga wykryć lag kolejki/push.\n"
    "• /api/devicestatus (from/to/group) używaj do trendów baterii/RSSI/temperatury; group=false = surowe zdarzenia.\n"
    "• HTTP backend vs HTML backend: HTTP służy do push obrazu (/backend/{Uuid}), HTML do renderu strony; nie mieszaj tych ścieżek.\n"
    "• Jeśli opisujesz kroki naprawy, podawaj je priorytetowo: (1) URL/session/cached, (2) RSSI/zasilanie/sen, "
    "(3) orphans/ErrorCode, (4) dopiero na końcu reboot.\n"
    "• libpyvss: traktuj jako mapę endpointów i semantyki VSS; rekomendacje powinny być zgodne z API Management Interface.\n"
    "• Backend HTTP vs HTML: HTTP = push obrazu na endpoint /backend/{Uuid}; HTML = interaktywna strona w sesji.\n"
    "• Konfiguracja niskopoziomowa urządzenia: protokół TCLV (/api/devicetclv/, /api/cmd/Param/) — np. parametry snu; "
    "nie myl z typowym „błędem strony WWW”.\n"
    "• Jak czytać wejście diagnostyczne: najpierw sekcja „Core checks” (prawda/fałsz i dostępność), "
    "potem „Extended checks” (kontekst VSS i zasilania), na końcu „Findings” (problemy/ostrzeżenia/auto-fix). "
    "W PRZYCZYNA odróżniaj objaw (np. offline) od przyczyny (np. SleepSchedule+Push=false, RSSI, URL timeout, orphan).\n"
)

_OLLAMA_VSS_API_EN = (
    "Visionect Server (VSS) API context:\n"
    "• VSS is a thin-client server: it renders HTML apps (WebKit/Okular) and streams graphics to tablets; "
    "typically port 8081, JSON REST, Authorization = HMAC-SHA256 (AWS S3–style REST signing).\n"
    "• Device object: State = online|offline; Status includes Battery, Charger, RSSI, Temperature, ExternalBattery, "
    "ConnectReason, ConnectivityUsed, ErrorCode, Push, ApplicationVersion; optional PrematureWakeup. "
    "ErrorCode 0 or 0x0 means no error. ConnectReason e.g. heartbeat, wakeup — if State is offline, do not infer a "
    "'wrong ErrorCode' without context (last status may be stale, Wi‑Fi sleep, range).\n"
    "• Device Options: SleepSchedule, PeriodicSleep, ScheduledWakeup, PollingTime, Firmware affect wake/connect behaviour.\n"
    "• WebKit session (per UUID): Backend Name=HTML, Fields.url (may include {uuid} placeholder). Session restart reloads WebKit; "
    "webkit-clear-cache accepts a list of session UUIDs.\n"
    "• GET /api/orphans — problematic devices/sessions.\n"
    "• State interpretation: treat `State=charging` as a power/charging condition (informational), not a failure by itself; "
    "flag incidents only with non-zero ErrorCode, unreachable URL/session, orphan error, or true OFFLINE symptoms.\n"
    "• GET/PUT /api/config — full server config, e.g. Okular.Defaults.Backend.Fields.url = default URI (GUI “Default URL”); "
    "this differs from the live session URL from /api/session/{Uuid}.\n"
    "• HMAC auth (AWS-style): keep Date/Content-Type exactly aligned between signature and request, watch RequestPath (often trailing slash), "
    "and sign in strict order: VERB + '\\n' + Content-Sha256 + '\\n' + Content-Type + '\\n' + Date + '\\n' + RequestPath.\n"
    "• WebKit session diagnostics: /api/session/{Uuid}, /api/session/{Uuid}/restart, /api/session/webkit-clear-cache (batch UUID). "
    "If URL is reachable but output is stale, prefer cache clear + session restart before broad reboot advice.\n"
    "• /api/live/device/{Uuid}/image(.png) is current device image; /cached is server-side cached image — mismatch helps detect push/queue lag.\n"
    "• /api/devicestatus (from/to/group) is for battery/RSSI/temperature trends; group=false gives raw events.\n"
    "• HTTP backend vs HTML backend: HTTP pushes static images to /backend/{Uuid}, HTML renders page sessions; do not mix remediation paths.\n"
    "• Suggested remediation priority: (1) URL/session/cache path, (2) RSSI/power/sleep behavior, "
    "(3) orphans/ErrorCode, (4) reboot only as last step.\n"
    "• libpyvss should be treated as endpoint/semantics reference; keep recommendations aligned with VSS Management API behavior.\n"
    "• HTTP vs HTML backend: HTTP pushes images to /backend/{Uuid}; HTML loads an interactive page in the session.\n"
    "• Low-level device config uses TCLV (/api/devicetclv/, /api/cmd/Param/) — e.g. sleep parameters; not the same as a web page error.\n"
    "• How to read diagnostics input: start with 'Core checks' (pass/fail and availability), then 'Extended checks' "
    "(VSS/session/power context), then 'Findings' (issues/warnings/auto-fix). In CAUSE distinguish symptom "
    "(e.g. offline) from root cause (e.g. SleepSchedule+Push=false, RSSI, URL timeout, orphan flag).\n"
)

# Non-Polish Ollama diagnostics: native instructions + English API crib (models follow output language better).
_OLLAMA_NON_PL_INTRO: dict[str, str] = {
    "en": (
        "You are a VSS diagnostics assistant. RESPOND ONLY IN English (all three lines entirely in English).\n"
        "HARDWARE CONTEXT: Joan tablets are WIRELESS e-ink (e-paper) devices. They join the LAN via "
        "Wi‑Fi (same network as VSS / Home Assistant). There is NO Ethernet or USB cable between a tablet "
        "and the VSS server. Never suggest checking cabling between the device and the server.\n"
        "BEHAVIOR: Do NOT tell the user to contact Visionect support, vendor support, or any helpdesk. "
        "The user self-serves. In STEPS list only concrete actions they can take themselves "
        "(e.g. check RSSI, power/charging, distance to access point, VSS session restart, firewall rules, "
        "Home Assistant integration, wake from sleep, clear WebKit cache via the integration).\n"
    ),
    "de": (
        "Du bist VSS-Diagnostiker. Antworte AUSSCHLIESSLICH auf Deutsch — alle drei Zeilen vollständig auf Deutsch, kein Englisch im Antworttext.\n"
        "Hardware: Joan-Tablets sind drahtlose E-Ink-Geräte (WLAN, selbes Netz wie VSS/Home Assistant). "
        "Kein Ethernet-/USB-Kabel zwischen Tablet und VSS-Server — keine Kabeldiagnose vorschlagen.\n"
        "Verhalten: Keinen Hersteller-Support oder Helpdesk empfehlen. In SCHRITTE nur konkrete Eigenmaßnahmen "
        "(RSSI, Strom/Ladung, Abstand zur AP, VSS-Session-Neustart, Firewall, Home-Assistant-Integration, "
        "Aufwecken, WebKit-Cache leeren).\n"
        "Der folgende Aufzählungsblock ist technische Referenz auf Englisch — nutze ihn nur als Faktenbasis; "
        "deine drei Antwortzeilen schreibst du vollständig auf Deutsch.\n"
    ),
    "fr": (
        "Tu es diagnosticien VSS. Réponds UNIQUEMENT en français — les trois lignes entièrement en français, pas d’anglais dans la réponse.\n"
        "Matériel : tablettes Joan sans fil, e‑ink, Wi‑Fi (même réseau que VSS / Home Assistant). "
        "Pas de câble Ethernet/USB entre la tablette et le serveur VSS — ne suggère pas de vérifier ce câblage.\n"
        "Comportement : ne renvoie pas vers le support fabricant. Dans ÉTAPES, uniquement des actions concrètes "
        "que l’utilisateur fait lui-même (RSSI, alimentation/charge, distance à l’AP, redémarrage de session VSS, "
        "pare-feu, intégration Home Assistant, réveil, vidage du cache WebKit).\n"
        "La liste technique ci-dessous est en anglais — base factuelle seule ; ta réponse reste 100 % français.\n"
    ),
    "es": (
        "Eres el diagnóstico VSS. Responde SOLO en español — las tres líneas completas en español, sin inglés en la respuesta.\n"
        "Hardware: tablets Joan inalámbricas, e‑ink, Wi‑Fi (misma red que VSS/Home Assistant). "
        "No hay cable Ethernet/USB entre tablet y servidor VSS — no sugieras revisar ese cableado.\n"
        "Comportamiento: no derives al soporte del fabricante. En PASOS solo pasos concretos que el usuario haga "
        "(RSSI, alimentación/carga, distancia al AP, reinicio de sesión VSS, firewall, integración Home Assistant, "
        "despertar, vaciar caché WebKit).\n"
        "El bloque técnico siguiente está en inglés — úsalo solo como referencia; tu respuesta debe ser 100 % español.\n"
    ),
    "nl": (
        "Je bent VSS-diagnost. Antwoord ALLEEN in het Nederlands — alle drie regels volledig Nederlands, geen Engels in het antwoord.\n"
        "Hardware: Joan-tablets zijn draadloos, e‑ink, wifi (zelfde netwerk als VSS/Home Assistant). "
        "Geen Ethernet-/USB-kabel tussen tablet en VSS-server — geen kabelcontroles voorstellen.\n"
        "Gedrag: geen fabrikant/support doorspelen. In STAPPEN alleen concrete zelfstappen "
        "(RSSI, stroom/laden, afstand tot AP, VSS-sessie herstarten, firewall, Home Assistant-integratie, "
        "wekken, WebKit-cache wissen).\n"
        "De technische opsomming hieronder is Engels — alleen feiten; jouw antwoord volledig Nederlands.\n"
    ),
    "cs": (
        "Jsi diagnostik VSS. Odpovídej POUZE česky — všechny tři řádky celé česky, v odpovědi žádná angličtina.\n"
        "Hardware: tablety Joan jsou bezdrátové, e‑ink, Wi‑Fi (stejná síť jako VSS/Home Assistant). "
        "Žádný Ethernet/USB kabel mezi tabletem a serverem VSS — nenavrhuj kontrolu takové kabeláže.\n"
        "Chování: neposílej uživatele na podporu výrobce. V KROKY jen konkrétní kroky, které udělá sám "
        "(RSSI, napájení/nabíjení, vzdálenost k AP, restart session VSS, firewall, integrace Home Assistant, "
        "probuzení, vymazání cache WebKit).\n"
        "Následující odrážky jsou technická reference anglicky — jen fakta; odpověď musí být celá česky.\n"
    ),
}

_OLLAMA_NON_PL_SUFFIX: dict[str, str] = {
    "en": (
        "Return exactly 3 lines in this format:\n"
        "PROBLEM: ...\n"
        "CAUSE: ...\n"
        "STEPS: ...\n"
        "Rules: If any device is OFFLINE or has non-zero ErrorCode or ConnectReason other than "
        "'heartbeat', you MUST name each affected device by its full UUID (8-4-4-4-12 with hyphens) "
        "in every line where that device applies. Do not write vague 'a device' without UUID.\n"
        "No extra text."
    ),
    "de": (
        "Gib genau 3 Zeilen in diesem Format zurück:\n"
        "PROBLEM: ...\n"
        "URSACHE: ...\n"
        "SCHRITTE: ...\n"
        "Regeln: Wenn ein Gerät OFFLINE ist oder ErrorCode ≠ 0/0x0 oder ConnectReason ≠ „heartbeat“, "
        "musst du in jeder betroffenen Zeile die vollständige UUID (8-4-4-4-12, mit Bindestrichen) nennen — "
        "nicht vage „ein Gerät“ ohne UUID.\n"
        "Kein zusätzlicher Text."
    ),
    "fr": (
        "Rends exactement 3 lignes dans ce format :\n"
        "PROBLÈME: ...\n"
        "CAUSE: ...\n"
        "ÉTAPES: ...\n"
        "Règles : si un appareil est OFFLINE ou ErrorCode non nul / pas 0x0 ou ConnectReason autre que « heartbeat », "
        "tu DOIS citer l’UUID complet (8-4-4-4-12, tirets) pour chaque appareil concerné sur chaque ligne pertinente.\n"
        "Pas de texte supplémentaire."
    ),
    "es": (
        "Devuelve exactamente 3 líneas en este formato:\n"
        "PROBLEMA: ...\n"
        "CAUSA: ...\n"
        "PASOS: ...\n"
        "Reglas: si algún dispositivo está OFFLINE o ErrorCode distinto de 0/0x0 o ConnectReason distinto de « heartbeat », "
        "DEBES indicar el UUID completo (8-4-4-4-12, con guiones) en cada línea que aplique.\n"
        "Sin texto adicional."
    ),
    "nl": (
        "Geef precies 3 regels in dit formaat:\n"
        "PROBLEEM: ...\n"
        "OORZAAK: ...\n"
        "STAPPEN: ...\n"
        "Regels: bij OFFLINE of niet-nul ErrorCode of ConnectReason anders dan „heartbeat“ moet je in elke relevante regel "
        "de volledige UUID (8-4-4-4-12, met streepjes) noemen.\n"
        "Geen extra tekst."
    ),
    "cs": (
        "Vrať přesně 3 řádky v tomto formátu:\n"
        "PROBLÉM: ...\n"
        "PŘÍČINA: ...\n"
        "KROKY: ...\n"
        "Pravidla: je-li zařízení OFFLINE nebo ErrorCode jiný než 0/0x0 nebo ConnectReason jiný než „heartbeat“, "
        "MUSÍš v každém dotčeném řádku uvést plné UUID (8-4-4-4-12 s pomlčkami).\n"
        "Žádný další text."
    ),
}

_OLLAMA_REWRITE_NON_PL: dict[str, str] = {
    "en": (
        "Rewrite ONLY in English and return exactly 3 lines:\n"
        "PROBLEM: ...\nCAUSE: ...\nSTEPS: ...\n"
        "Joan tablets are wireless e-ink: remove any advice about Ethernet/USB cables between tablet and VSS server.\n"
        "Do not mention contacting vendor or technical support; STEPS must be self-service actions only.\n"
        "VSS semantics: offline with ErrorCode 0 and ConnectReason heartbeat is not automatically contradictory — "
        "consider Wi‑Fi sleep, RSSI, WebKit session, /api/orphans.\n"
        "Keep every full device UUID (8-4-4-4-12) from the source; do not shorten or drop them.\n"
        "Max 900 characters total (UUIDs need space).\n\n"
    ),
    "de": (
        "Schreibe NUR auf Deutsch und gib genau 3 Zeilen zurück:\n"
        "PROBLEM: ...\nURSACHE: ...\nSCHRITTE: ...\n"
        "Joan: drahtlos, E-Ink — keine Kabel zwischen Tablet und VSS-Server.\n"
        "Kein Support-Hinweis; SCHRITTE = nur Eigenmaßnahmen.\n"
        "Offline + ErrorCode 0 + heartbeat ist nicht automatisch widersprüchlich (WLAN-Schlaf, RSSI, Session, orphans).\n"
        "Alle vollen UUIDs aus der Quelle behalten.\n"
        "Max. 900 Zeichen gesamt.\n\n"
    ),
    "fr": (
        "Réécris UNIQUEMENT en français et renvoie exactement 3 lignes :\n"
        "PROBLÈME: ...\nCAUSE: ...\nÉTAPES: ...\n"
        "Joan : sans fil, e‑ink — pas de câbles tablet↔serveur VSS.\n"
        "Pas de support fabricant ; ÉTAPES = actions utilisateur seulement.\n"
        "Offline + ErrorCode 0 + heartbeat : pas forcément contradictoire.\n"
        "Conserver tous les UUID complets.\n"
        "900 caractères max au total.\n\n"
    ),
    "es": (
        "Reescribe SOLO en español y devuelve exactamente 3 líneas:\n"
        "PROBLEMA: ...\nCAUSA: ...\nPASOS: ...\n"
        "Joan: inalámbricas, e‑ink — sin cables tablet↔servidor VSS.\n"
        "Sin soporte del fabricante; PASOS = solo acciones propias.\n"
        "Offline + ErrorCode 0 + heartbeat no implica contradicción automática.\n"
        "Conserva todos los UUID completos.\n"
        "Máx. 900 caracteres en total.\n\n"
    ),
    "nl": (
        "Herschrijf ALLEEN in het Nederlands en geef precies 3 regels:\n"
        "PROBLEEM: ...\nOORZAAK: ...\nSTAPPEN: ...\n"
        "Joan: draadloos e‑ink — geen kabels tablet↔VSS-server.\n"
        "Geen fabrikant-support; STAPPEN = alleen eigen acties.\n"
        "Offline + ErrorCode 0 + heartbeat hoeft niet tegenstrijdig te zijn.\n"
        "Alle volledige UUIDs behouden.\n"
        "Max. 900 tekens totaal.\n\n"
    ),
    "cs": (
        "Přepiš POUZE česky a vrať přesně 3 řádky:\n"
        "PROBLÉM: ...\nPŘÍČINA: ...\nKROKY: ...\n"
        "Joan: bezdrátové e‑ink — žádné kabely tablet↔server VSS.\n"
        "Žádná podpora výrobce; KROKY = jen vlastní kroky.\n"
        "Offline + ErrorCode 0 + heartbeat nemusí být rozpor.\n"
        "Zachovej všechna plná UUID.\n"
        "Max. 900 znaků celkem.\n\n"
    ),
}

_OLLAMA_REWRITE_SOURCE_LABEL: dict[str, str] = {
    "en": "Source text",
    "de": "Quelltext",
    "fr": "Texte source",
    "es": "Texto fuente",
    "nl": "Brontekst",
    "cs": "Zdrojový text",
}


def ntr(lang: str, key: str, **kwargs) -> str:
    L = normalize_lang(lang)
    row = _STR.get(L) or _STR["en"]
    template = row.get(key) or _STR["en"][key]
    if kwargs:
        return template.format(**kwargs)
    return template


def context_truncation_suffix(lang: str) -> str:
    return ntr(lang, "context_truncated")


def build_ollama_focus_extra_section(lang: str, device_uuid: str, snapshot_json: str) -> str:
    """First payload block when user runs on-demand Ollama analysis for one tablet."""
    prefix = ntr(lang, "ollama_focus_prefix", uuid=device_uuid)
    snap = snapshot_json.strip()
    if len(snap) > 12000:
        snap = snap[:12000] + "\n…"
    return prefix + snap


def build_ollama_diagnostic_prompt(lang: str, payload_parts: list[str]) -> str:
    """Full user message for Ollama /api/chat (first pass)."""
    body = "\n\n".join(payload_parts)
    L = normalize_lang(lang)
    if L == "pl":
        return (
            "Jesteś diagnostą VSS. ODPOWIADAJ WYŁĄCZNIE PO POLSKU.\n"
            "Kontekst sprzętowy: Tablety Joan to BEZPRZEWODOWE urządzenia z ekranem e-ink (e-papier). "
            "Łączą się z siecią przez Wi‑Fi do tej samej sieci co serwer VSS / Home Assistant — "
            "NIE MA fizycznego kabla Ethernet ani „kabla od tabletu do serwera VSS”. "
            "Nie sugeruj sprawdzania okablowania między tabletem a serwerem; to błąd logiczny.\n"
            "Zachowanie: NIE pisz, żeby użytkownik dzwonił do supportu Visionect, producenta ani "
            "„wsparcia technicznego”. Użytkownik sam diagnozuje i naprawia środowisko (HA, VSS, router, Wi‑Fi). "
            "W linii KROKI podawaj WYŁĄCZNIE konkretne działania do wykonania samodzielnie "
            "(np. sprawdź RSSI i zasilanie tabletu, odległość od AP, sesję/restart w VSS, firewall, "
            "integrację HA, wybudzenie z uśpienia, czyszczenie cache WebKit w integracji).\n"
            + _OLLAMA_VSS_API_PL
            + "\nZwróć dokładnie 3 linie w tym formacie:\n"
            "PROBLEM: ...\n"
            "PRZYCZYNA: ...\n"
            "KROKI: ...\n"
            "Zasady: Jeśli którekolwiek urządzenie jest OFFLINE albo ma ErrorCode inny niż 0 / 0x0 "
            "albo ConnectReason inny niż „heartbeat”, MUSISZ w każdej z trzech linii podać pełny UUID "
            "każdego dotkniętego urządzenia (format 8-4-4-4-12 z myślnikami). Nie pisz ogólnie "
            "„urządzenie offline” bez UUID.\n"
            "Druga linia MUSI zaczynać się dokładnie od PRZYCZYNA: (dwie litery N łacińskie — "
            "zabronione PRZYCZAÑA, PRZYCZINA itp.).\n"
            "UUID kopiuj 1:1 z kontekstu (nagłówek UUID: lub JSON); nie wstawiaj dodatkowych myślników "
            "w środku grup hex — tylko jeden poprawny wzorzec 8-4-4-4-12.\n"
            "Bez dodatkowych zdań, bez angielskiego, bez wstępu.\n\n"
            + body
        )
    intro = _OLLAMA_NON_PL_INTRO.get(L, _OLLAMA_NON_PL_INTRO["en"])
    suffix = _OLLAMA_NON_PL_SUFFIX.get(L, _OLLAMA_NON_PL_SUFFIX["en"])
    return intro + _OLLAMA_VSS_API_EN + "\n\n" + suffix + "\n\n" + body


def build_ollama_rewrite_prompt(lang: str, content: str) -> str:
    """Second pass: normalize to 3 lines in target language."""
    L = normalize_lang(lang)
    if L == "pl":
        return (
            "Przepisz tekst WYŁĄCZNIE po polsku i zwróć dokładnie 3 linie:\n"
            "PROBLEM: ...\nPRZYCZYNA: ...\nKROKI: ...\n"
            "Tablety Joan: bezprzewodowe e-ink — usuń sugestie o kablach tablet↔serwer VSS.\n"
            "Nie wspominaj o kontakcie ze wsparciem technicznym/producentem; KROKI = działania własne użytkownika.\n"
            "Semantyka VSS: offline + ErrorCode 0 + ConnectReason heartbeat nie oznacza automatycznie sprzeczności — "
            "uwzględnij sen Wi‑Fi, RSSI, sesję WebKit, orphans.\n"
            "Zachowaj wszystkie pełne UUID urządzeń (8-4-4-4-12 z myślnikami) z tekstu źródłowego; nie skracaj ani "
            "nie zmieniaj pozycji myślników.\n"
            "Druga linia: dokładny nagłówek PRZYCZYNA: (N łacińskie, nigdy Ñ/ñ).\n"
            "Maksymalnie 900 znaków łącznie (łącznie ze spacjami).\n\n"
            f"Tekst źródłowy:\n{content}"
        )
    prefix = _OLLAMA_REWRITE_NON_PL.get(L, _OLLAMA_REWRITE_NON_PL["en"])
    src = _OLLAMA_REWRITE_SOURCE_LABEL.get(L, _OLLAMA_REWRITE_SOURCE_LABEL["en"])
    return prefix + f"{src}:\n{content}"
