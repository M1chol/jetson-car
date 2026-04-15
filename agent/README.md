# Uruchamianie agenta
upewnij się że środowisko wirtualne jest aktywne, oraz wszystkie wymagane biblioteki zainstalowane.
  
Z poziomu głównego folderu `jetson-car`
```
python -m agent.start
```

# Minimalna instrukcja konfiguracji słuchawek Bluetooth z mikrofonem

Zainstaluj `bluetuith` jeśli nie jest dostępne

## 1. Przygotowanie słuchawek
Włącz parowanie na słuchawkach (zazwyczaj przytrzymaj przycisk zasilania)

## 2. Połączenie przez bluetuith

```bash
bluetuith
```

- `s` — włącz skanowanie
- `↑/↓` — wybierz słuchawki
- `Enter` — połącz
- `p` — sparuj (jeśli nowe)
- `Alt+m, Q` — wyjście

## 3. Sprawdź dostępne profile

```bash
pactl list cards | grep -B 5 -A 15 "Name: bluez"
```

Szukaj linii `Profiles:` — zanotuj nazwę profilu z mikrofonem (np. `handsfree_head_unit`, `headset_head_unit`, `hfp`) oraz nazwę w formacie `bluez_card.XX_XX_XX_XX_XX_XX`.

## 4. Zmień profil na obsługujący mikrofon

```bash
pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX nazwa_profilu_z_mikrofonem
```

(Wklej właściwy adres MAC z kroku 3)

## 5. Test

```bash
arecord -d 5 test.wav && aplay test.wav
```

## 6. Sprawdź sample rate mikrofonu

```bash
pactl list sources | grep -A 5 "bluez_source" | grep "Sample Specification"
```
