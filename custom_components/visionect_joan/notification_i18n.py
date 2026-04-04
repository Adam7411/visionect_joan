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
        "ollama_api_error": "[Visionect API]\nCould not load device list: {err}",
        "ollama_sep": "--- What the AI analyzed (VSS logs if available + full device list from API) ---",
        "ollama_no_data": "AI diagnostics: no data available for analysis (no logs and no API data).",
        "ollama_error": "AI diagnostics error: {err}",
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
        "safe_read_title": "Visionect Safe Config — Read",
        "safe_read_step1": "Step 1/3 completed: configuration read from tablet.\n\nDevice: `{device}`\n\n{values}\n\n{note}Next step: run `visionect_joan.apply_safe_device_config` to save selected values.",
        "safe_read_note_firmware": "Note: read results depend on firmware; the device may return empty values even when writes succeed.\n\n",
        "safe_read_note_noreadback": (
            "Note: this device/firmware does not return TCLV readback values. "
            "Treat step 1 as diagnostic (optional) and configure using step 2.\n\n"
        ),
        "safe_no_mapping": (
            "No TCLV mapping found for selected fields. Changes were not sent to device.\n\nDevice: `{device}`"
        ),
        "safe_no_mapping_title": "Visionect Safe Config — Mapping missing",
        "safe_applied": (
            "Device configuration saved.\n\nDevice: `{device}`\nChanged fields: {fields}\n\nApplied values:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Applied",
        "safe_apply_failed": (
            "Could not apply safe configuration changes.\n\nDevice: `{device}`\nNo rollback action was executed."
        ),
        "safe_apply_failed_title": "Visionect Safe Config — Apply failed",
        "safe_no_backup": (
            "Step 3/3 skipped: no backup available to restore.\n\nDevice: `{device}`\n"
            "Run `read_safe_device_config` and then `apply_safe_device_config` first."
        ),
        "safe_no_backup_title": "Visionect Safe Config — No backup",
        "safe_restored": (
            "Step 3/3 completed: rollback restored previous safe settings.\n\nDevice: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Restored",
        "safe_restore_failed": "Rollback failed while writing previous safe settings.\n\nDevice: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Restore failed",
        "safe_no_applied_fields": "No applied fields",
        "safe_set_minutes": "set to `{val}` minutes",
        "safe_set_value": "set to `{val}`",
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
        "safe_values_empty": "No device response",
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
        "ollama_api_error": "[Visionect API]\nNie udało się pobrać listy urządzeń: {err}",
        "ollama_sep": "--- Co analizowało AI (logi VSS, jeśli są + pełna lista urządzeń z API) ---",
        "ollama_no_data": "AI diagnostyka: brak danych do analizy (logi niedostępne i API nie zwróciło danych).",
        "ollama_error": "Błąd AI diagnostyki: {err}",
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
        "safe_read_title": "Visionect Safe Config — Odczyt",
        "safe_read_step1": "Krok 1/3 zakończony: konfiguracja została odczytana z tabletu.\n\nUrządzenie: `{device}`\n\n{values}\n\n{note}Następny krok: uruchom `visionect_joan.apply_safe_device_config`, aby zapisać wybrane wartości.",
        "safe_read_note_firmware": "Uwaga: odczyt jest zależny od firmware, czasem urządzenie zwraca puste wartości mimo poprawnego zapisu.\n\n",
        "safe_read_note_noreadback": (
            "Uwaga: to urządzenie/firmware nie zwraca wartości readback dla TCLV. "
            "Krok 1 traktuj jako diagnostyczny (opcjonalny), a konfigurację ustawiaj przez krok 2.\n\n"
        ),
        "safe_no_mapping": (
            "Nie znaleziono mapowania TCLV dla wybranych pól. Zmiany nie zostały wysłane do urządzenia.\n\nUrządzenie: `{device}`"
        ),
        "safe_no_mapping_title": "Visionect Safe Config — Brak mapowania",
        "safe_applied": (
            "Zapisano konfigurację urządzenia.\n\nUrządzenie: `{device}`\nZmienione pola: {fields}\n\nUstawione wartości:\n{applied}"
        ),
        "safe_applied_title": "Visionect Safe Config — Zapisano",
        "safe_apply_failed": (
            "Nie udało się zapisać zmian bezpiecznej konfiguracji.\n\nUrządzenie: `{device}`\nNie wykonano rollbacku."
        ),
        "safe_apply_failed_title": "Visionect Safe Config — Błąd zapisu",
        "safe_no_backup": (
            "Krok 3/3 pominięty: brak backupu do przywrócenia.\n\nUrządzenie: `{device}`\n"
            "Najpierw uruchom `read_safe_device_config`, a potem `apply_safe_device_config`."
        ),
        "safe_no_backup_title": "Visionect Safe Config — Brak backupu",
        "safe_restored": (
            "Krok 3/3 zakończony: rollback przywrócił poprzednie ustawienia.\n\nUrządzenie: `{device}`\n{values}"
        ),
        "safe_restored_title": "Visionect Safe Config — Przywrócono",
        "safe_restore_failed": "Rollback nie powiódł się podczas zapisu poprzednich ustawień.\n\nUrządzenie: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Błąd przywracania",
        "safe_no_applied_fields": "Brak ustawionych pól",
        "safe_set_minutes": "ustawiono na `{val}` minuty",
        "safe_set_value": "ustawiono na `{val}`",
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
        "safe_values_empty": "Brak odpowiedzi urządzenia",
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
        "ollama_api_error": "[Visionect API]\nGeräteliste konnte nicht geladen werden: {err}",
        "ollama_sep": "--- Was die KI analysiert hat (VSS-Logs falls vorhanden + vollständige Geräteliste von der API) ---",
        "ollama_no_data": "KI-Diagnose: keine Daten zur Analyse (keine Logs und keine API-Daten).",
        "ollama_error": "KI-Diagnosefehler: {err}",
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
        "safe_read_title": "Visionect Safe Config — Lesen",
        "safe_read_step1": "Schritt 1/3: Konfiguration vom Tablet gelesen.\n\nGerät: `{device}`\n\n{values}\n\n{note}Nächster Schritt: `visionect_joan.apply_safe_device_config` ausführen.",
        "safe_read_note_firmware": "Hinweis: Lesewerte hängen von der Firmware ab; leere Werte sind trotz erfolgreichem Schreiben möglich.\n\n",
        "safe_read_note_noreadback": (
            "Hinweis: Dieses Gerät/Firmware liefert keine TCLV-Readback-Werte. "
            "Schritt 1 ist optional diagnostisch; konfigurieren Sie über Schritt 2.\n\n"
        ),
        "safe_no_mapping": "Keine TCLV-Zuordnung für die gewählten Felder. Keine Änderungen gesendet.\n\nGerät: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Kein Mapping",
        "safe_applied": "Konfiguration gespeichert.\n\nGerät: `{device}`\nGeänderte Felder: {fields}\n\nGesetzte Werte:\n{applied}",
        "safe_applied_title": "Visionect Safe Config — Gespeichert",
        "safe_apply_failed": "Sichere Konfiguration konnte nicht geschrieben werden.\n\nGerät: `{device}`\nKein Rollback ausgeführt.",
        "safe_apply_failed_title": "Visionect Safe Config — Schreibfehler",
        "safe_no_backup": "Schritt 3/3 übersprungen: kein Backup.\n\nGerät: `{device}`\nZuerst `read_safe_device_config`, dann `apply_safe_device_config`.",
        "safe_no_backup_title": "Visionect Safe Config — Kein Backup",
        "safe_restored": "Schritt 3/3: Rollback hat vorherige Einstellungen wiederhergestellt.\n\nGerät: `{device}`\n{values}",
        "safe_restored_title": "Visionect Safe Config — Wiederhergestellt",
        "safe_restore_failed": "Rollback beim Schreiben fehlgeschlagen.\n\nGerät: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Wiederherstellung fehlgeschlagen",
        "safe_no_applied_fields": "Keine gesetzten Felder",
        "safe_set_minutes": "auf `{val}` Minuten gesetzt",
        "safe_set_value": "auf `{val}` gesetzt",
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
        "safe_values_empty": "Keine Geräteantwort",
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
        "ollama_api_error": "[Visionect API]\nImpossible de charger la liste des appareils : {err}",
        "ollama_sep": "--- Ce que l’IA a analysé (journaux VSS si disponibles + liste complète depuis l’API) ---",
        "ollama_no_data": "Diagnostic IA : aucune donnée à analyser (pas de journaux ni de données API).",
        "ollama_error": "Erreur du diagnostic IA : {err}",
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
        "safe_read_title": "Visionect Safe Config — Lecture",
        "safe_read_step1": "Étape 1/3 : configuration lue depuis la tablette.\n\nAppareil : `{device}`\n\n{values}\n\n{note}Étape suivante : exécuter `visionect_joan.apply_safe_device_config`.",
        "safe_read_note_firmware": "Note : la lecture dépend du firmware ; des valeurs vides sont possibles même après écriture.\n\n",
        "safe_read_note_noreadback": (
            "Note : ce matériel/firmware ne renvoie pas de lecture TCLV. "
            "L’étape 1 est optionnelle ; configurez via l’étape 2.\n\n"
        ),
        "safe_no_mapping": "Aucun mappage TCLV pour les champs choisis. Aucun envoi.\n\nAppareil : `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Pas de mappage",
        "safe_applied": "Configuration enregistrée.\n\nAppareil : `{device}`\nChamps modifiés : {fields}\n\nValeurs appliquées :\n{applied}",
        "safe_applied_title": "Visionect Safe Config — Enregistré",
        "safe_apply_failed": "Impossible d’appliquer la configuration sécurisée.\n\nAppareil : `{device}`\nAucun rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Échec d’écriture",
        "safe_no_backup": "Étape 3/3 ignorée : pas de sauvegarde.\n\nAppareil : `{device}`\nLancez d’abord `read_safe_device_config` puis `apply_safe_device_config`.",
        "safe_no_backup_title": "Visionect Safe Config — Pas de sauvegarde",
        "safe_restored": "Étape 3/3 : rollback, paramètres précédents restaurés.\n\nAppareil : `{device}`\n{values}",
        "safe_restored_title": "Visionect Safe Config — Restauré",
        "safe_restore_failed": "Échec du rollback.\n\nAppareil : `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Échec de restauration",
        "safe_no_applied_fields": "Aucun champ appliqué",
        "safe_set_minutes": "réglé sur `{val}` minutes",
        "safe_set_value": "réglé sur `{val}`",
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
        "safe_values_empty": "Pas de réponse de l’appareil",
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
        "ollama_api_error": "[Visionect API]\nNo se pudo cargar la lista de dispositivos: {err}",
        "ollama_sep": "--- Lo que analizó la IA (registros VSS si hay + lista completa desde la API) ---",
        "ollama_no_data": "Diagnóstico IA: no hay datos para analizar (sin registros ni datos de API).",
        "ollama_error": "Error del diagnóstico IA: {err}",
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
        "safe_read_title": "Visionect Safe Config — Lectura",
        "safe_read_step1": "Paso 1/3: configuración leída de la tablet.\n\nDispositivo: `{device}`\n\n{values}\n\n{note}Siguiente paso: ejecutar `visionect_joan.apply_safe_device_config`.",
        "safe_read_note_firmware": "Nota: la lectura depende del firmware; puede devolver valores vacíos aunque la escritura haya funcionado.\n\n",
        "safe_read_note_noreadback": (
            "Nota: este dispositivo/firmware no devuelve lectura TCLV. "
            "El paso 1 es opcional; configure en el paso 2.\n\n"
        ),
        "safe_no_mapping": "Sin mapeo TCLV para los campos elegidos. No se envió nada.\n\nDispositivo: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Sin mapeo",
        "safe_applied": "Configuración guardada.\n\nDispositivo: `{device}`\nCampos cambiados: {fields}\n\nValores aplicados:\n{applied}",
        "safe_applied_title": "Visionect Safe Config — Guardado",
        "safe_apply_failed": "No se pudo aplicar la configuración segura.\n\nDispositivo: `{device}`\nSin rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Error al guardar",
        "safe_no_backup": "Paso 3/3 omitido: no hay copia.\n\nDispositivo: `{device}`\nPrimero `read_safe_device_config` y luego `apply_safe_device_config`.",
        "safe_no_backup_title": "Visionect Safe Config — Sin copia",
        "safe_restored": "Paso 3/3: rollback restauró la configuración anterior.\n\nDispositivo: `{device}`\n{values}",
        "safe_restored_title": "Visionect Safe Config — Restaurado",
        "safe_restore_failed": "Fallo del rollback.\n\nDispositivo: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Error al restaurar",
        "safe_no_applied_fields": "Sin campos aplicados",
        "safe_set_minutes": "establecido en `{val}` minutos",
        "safe_set_value": "establecido en `{val}`",
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
        "safe_values_empty": "Sin respuesta del dispositivo",
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
        "ollama_api_error": "[Visionect API]\nApparatenlijst laden mislukt: {err}",
        "ollama_sep": "--- Wat de AI heeft geanalyseerd (VSS-logboeken indien aanwezig + volledige lijst via API) ---",
        "ollama_no_data": "AI-diagnose: geen gegevens om te analyseren (geen logboeken en geen API-gegevens).",
        "ollama_error": "AI-diagnosefout: {err}",
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
        "safe_read_title": "Visionect Safe Config — Uitlezen",
        "safe_read_step1": "Stap 1/3: configuratie van tablet gelezen.\n\nApparaat: `{device}`\n\n{values}\n\n{note}Volgende stap: `visionect_joan.apply_safe_device_config` uitvoeren.",
        "safe_read_note_firmware": "Let op: uitlezen hangt van firmware af; lege waarden zijn mogelijk na een geslaagde schrijfactie.\n\n",
        "safe_read_note_noreadback": (
            "Let op: dit apparaat/firmware geeft geen TCLV readback. "
            "Stap 1 is optioneel diagnostisch; configureer via stap 2.\n\n"
        ),
        "safe_no_mapping": "Geen TCLV-mapping voor gekozen velden. Niets verzonden.\n\nApparaat: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Geen mapping",
        "safe_applied": "Configuratie opgeslagen.\n\nApparaat: `{device}`\nGewijzigde velden: {fields}\n\nToegepaste waarden:\n{applied}",
        "safe_applied_title": "Visionect Safe Config — Opgeslagen",
        "safe_apply_failed": "Veilige configuratie kon niet worden geschreven.\n\nApparaat: `{device}`\nGeen rollback.",
        "safe_apply_failed_title": "Visionect Safe Config — Schrijffout",
        "safe_no_backup": "Stap 3/3 overgeslagen: geen back-up.\n\nApparaat: `{device}`\nEerst `read_safe_device_config`, daarna `apply_safe_device_config`.",
        "safe_no_backup_title": "Visionect Safe Config — Geen back-up",
        "safe_restored": "Stap 3/3: rollback heeft vorige instellingen hersteld.\n\nApparaat: `{device}`\n{values}",
        "safe_restored_title": "Visionect Safe Config — Hersteld",
        "safe_restore_failed": "Rollback mislukt.\n\nApparaat: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Herstel mislukt",
        "safe_no_applied_fields": "Geen toegepaste velden",
        "safe_set_minutes": "ingesteld op `{val}` minuten",
        "safe_set_value": "ingesteld op `{val}`",
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
        "safe_values_empty": "Geen apparaatantwoord",
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
        "ollama_api_error": "[Visionect API]\nNepodařilo se načíst seznam zařízení: {err}",
        "ollama_sep": "--- Co AI analyzovala (logy VSS pokud jsou + úplný seznam z API) ---",
        "ollama_no_data": "AI diagnostika: žádná data k analýze (chybí logy i data z API).",
        "ollama_error": "Chyba AI diagnostiky: {err}",
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
        "safe_read_title": "Visionect Safe Config — Čtení",
        "safe_read_step1": "Krok 1/3: konfigurace přečtena z tabletu.\n\nZařízení: `{device}`\n\n{values}\n\n{note}Další krok: spusťte `visionect_joan.apply_safe_device_config`.",
        "safe_read_note_firmware": "Poznámka: čtení závisí na firmwaru; prázdné hodnoty jsou možné i po úspěšném zápisu.\n\n",
        "safe_read_note_noreadback": (
            "Poznámka: toto zařízení/firmware nevrací TCLV readback. "
            "Krok 1 je volitelná diagnostika; konfigurujte krokem 2.\n\n"
        ),
        "safe_no_mapping": "Chybí mapování TCLV pro zvolená pole. Nic neodesláno.\n\nZařízení: `{device}`",
        "safe_no_mapping_title": "Visionect Safe Config — Chybí mapování",
        "safe_applied": "Konfigurace uložena.\n\nZařízení: `{device}`\nZměněná pole: {fields}\n\nNastavené hodnoty:\n{applied}",
        "safe_applied_title": "Visionect Safe Config — Uloženo",
        "safe_apply_failed": "Nepodařilo se zapsat bezpečnou konfiguraci.\n\nZařízení: `{device}`\nRollback neproběhl.",
        "safe_apply_failed_title": "Visionect Safe Config — Chyba zápisu",
        "safe_no_backup": "Krok 3/3 přeskočen: žádná záloha.\n\nZařízení: `{device}`\nNejdřív `read_safe_device_config`, pak `apply_safe_device_config`.",
        "safe_no_backup_title": "Visionect Safe Config — Žádná záloha",
        "safe_restored": "Krok 3/3: rollback obnovil předchozí nastavení.\n\nZařízení: `{device}`\n{values}",
        "safe_restored_title": "Visionect Safe Config — Obnoveno",
        "safe_restore_failed": "Rollback selhal.\n\nZařízení: `{device}`",
        "safe_restore_failed_title": "Visionect Safe Config — Chyba obnovení",
        "safe_no_applied_fields": "Žádná nastavená pole",
        "safe_set_minutes": "nastaveno na `{val}` minut",
        "safe_set_value": "nastaveno na `{val}`",
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
        "safe_values_empty": "Bez odpovědi zařízení",
    },
}


_OLLAMA_LANG_NAME: dict[str, str] = {
    "en": "English",
    "pl": "Polish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "nl": "Dutch",
    "cs": "Czech",
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


def build_ollama_diagnostic_prompt(lang: str, payload_parts: list[str]) -> str:
    """Full user message for Ollama /api/chat (first pass)."""
    body = "\n\n".join(payload_parts)
    L = normalize_lang(lang)
    if L == "pl":
        return (
            "Jesteś diagnostą VSS. ODPOWIADAJ WYŁĄCZNIE PO POLSKU.\n"
            "Zwróć dokładnie 3 linie w tym formacie:\n"
            "PROBLEM: ...\n"
            "PRZYCZYNA: ...\n"
            "KROKI: ...\n"
            "Zasady: Jeśli którekolwiek urządzenie jest OFFLINE albo ma ErrorCode inny niż 0 / 0x0 "
            "albo ConnectReason inny niż „heartbeat”, MUSISZ w każdej z trzech linii podać pełny UUID "
            "każdego dotkniętego urządzenia (format 8-4-4-4-12 z myślnikami). Nie pisz ogólnie "
            "„urządzenie offline” bez UUID.\n"
            "Bez dodatkowych zdań, bez angielskiego, bez wstępu; pisz poprawnie „PRZYCZYNA”.\n\n"
            + body
        )
    lang_name = _OLLAMA_LANG_NAME.get(L, "English")
    return (
        f"You are a VSS diagnostics assistant. RESPOND ONLY IN {lang_name}.\n"
        "Return exactly 3 lines in this format:\n"
        "PROBLEM: ...\n"
        "CAUSE: ...\n"
        "STEPS: ...\n"
        "Rules: If any device is OFFLINE or has non-zero ErrorCode or ConnectReason other than "
        "'heartbeat', you MUST name each affected device by its full UUID (8-4-4-4-12 with hyphens) "
        "in every line where that device applies. Do not write vague 'a device' without UUID.\n"
        "No extra text.\n\n"
        + body
    )


def build_ollama_rewrite_prompt(lang: str, content: str) -> str:
    """Second pass: normalize to 3 lines in target language."""
    L = normalize_lang(lang)
    if L == "pl":
        return (
            "Przepisz tekst WYŁĄCZNIE po polsku i zwróć dokładnie 3 linie:\n"
            "PROBLEM: ...\nPRZYCZYNA: ...\nKROKI: ...\n"
            "Zachowaj wszystkie pełne UUID urządzeń (8-4-4-4-12 z myślnikami) z tekstu źródłowego; nie skracaj.\n"
            "Maksymalnie 900 znaków łącznie (łącznie ze spacjami).\n\n"
            f"Tekst źródłowy:\n{content}"
        )
    lang_name = _OLLAMA_LANG_NAME.get(L, "English")
    return (
        f"Rewrite ONLY in {lang_name} and return exactly 3 lines:\n"
        "PROBLEM: ...\nCAUSE: ...\nSTEPS: ...\n"
        "Keep every full device UUID (8-4-4-4-12) from the source; do not shorten or drop them.\n"
        "Max 900 characters total (UUIDs need space).\n\n"
        f"Source text:\n{content}"
    )
