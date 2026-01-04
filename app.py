import os
import time
import json
import pygame
import random
import wave

# ================= PATHS =================
BASE_DIR = os.path.dirname(__file__)
AUDIOS_DIR = os.path.join(BASE_DIR, "Audios")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
STATE_FILE = os.path.join(BASE_DIR, "state.json")
NOISE_FILE = os.path.join(ASSETS_DIR, "static.wav")

# ================= INIT =================
pygame.mixer.init()

# ================= STATE =================
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {
        "global_start": time.time(),
        "last": {"game": None, "station": None}
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

GLOBAL_START = state["global_start"]

# ================= LOAD RADIOS =================
radios = {}  # radios[game][station] = (wav_path, duration_sec)

def get_wav_duration(path):
    with wave.open(path, "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate)

def load_radios():
    for game in os.listdir(AUDIOS_DIR):
        game_path = os.path.join(AUDIOS_DIR, game)
        if not os.path.isdir(game_path):
            continue

        radios[game] = {}

        for station in os.listdir(game_path):
            station_path = os.path.join(game_path, station)
            if not os.path.isdir(station_path):
                continue

            wavs = [f for f in os.listdir(station_path) if f.lower().endswith(".wav")]
            if len(wavs) != 1:
                raise RuntimeError(f"{station_path} must contain exactly one WAV")

            wav_path = os.path.join(station_path, wavs[0])
            duration = get_wav_duration(wav_path)

            radios[game][station] = (wav_path, duration)

load_radios()

# ================= PLAYBACK =================
current_game = None
current_station = None

def play_noise():
    noise = pygame.mixer.Sound(NOISE_FILE)
    noise.play()
    pygame.time.delay(random.randint(300, 600))

def play_station(game, station):
    global current_game, current_station

    pygame.mixer.music.stop()
    play_noise()

    wav_path, duration = radios[game][station]

    now = time.time()
    elapsed = now - GLOBAL_START
    offset = elapsed % duration

    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play(loops=-1, start=offset)

    current_game = game
    current_station = station

    print(f"▶ {game} / {station} @ {int(offset)}s")

def save_state():
    state["last"]["game"] = current_game
    state["last"]["station"] = current_station
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# ================= CLI =================
def main_menu():
    games = list(radios.keys())

    while True:
        print("\nGames:")
        for i, g in enumerate(games):
            print(f"{i} - {g}")
        print("q - quit")

        gsel = input("> ")
        if gsel == "q":
            save_state()
            break

        try:
            game = games[int(gsel)]

        except ValueError:
            print("enter a number or q")
            continue
        except IndexError:
            print("invalid index")
            continue
        
        stations = list(radios[game].keys())
        while True:
            print(f"\nStations ({game}):")
            for i, s in enumerate(stations):
                print(f"{i} - {s}")
            print("b - back")

            ssel = input("> ")
            if ssel == "b":
                break

            try:
                station = stations[int(ssel)]
                play_station(game, station)
            except:
                continue

# ================= AUTO RESUME =================
last = state.get("last", {})
if last.get("game") and last.get("station"):
    try:
        play_station(last["game"], last["station"])
    except:
        pass

main_menu()
