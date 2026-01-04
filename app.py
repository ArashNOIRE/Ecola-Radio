import os
import sys
import time
import json
import pygame
import random
import wave
import platform

# ================= PATHS =================
def resource_path(rel_path):
    """Works both in dev and PyInstaller onefile exe"""
    try:
        base = getattr(sys, "_MEIPASS")
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)

# Assets inside exe
STATIC_WAV = resource_path("assets/static.wav")
STATE_FILE = resource_path("state.json")

# Audios always external (beside exe)
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
AUDIOS_DIR = os.path.join(BASE_DIR, "Audios")

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
    if not os.path.exists(AUDIOS_DIR):
        raise FileNotFoundError(f"{AUDIOS_DIR} not found. Place your game audio folders here.")

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
    noise = pygame.mixer.Sound(STATIC_WAV)
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

    print(f"▶ {game} / {station}")  # offset now hidden

def save_state():
    state["last"]["game"] = current_game
    state["last"]["station"] = current_station
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# ================= TERMINAL CLEAR =================
def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

# ================= CLI =================
def main_menu():
    games = list(radios.keys())

    while True:
        clear_terminal()
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
        except (ValueError, IndexError):
            print("Invalid input")
            continue
        
        while True:
            clear_terminal()
            stations = list(radios[game].keys())
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
            except (ValueError, IndexError):
                continue

# ================= AUTO RESUME =================
last = state.get("last", {})
if last.get("game") and last.get("station"):
    try:
        play_station(last["game"], last["station"])
    except Exception:
        pass

main_menu()
