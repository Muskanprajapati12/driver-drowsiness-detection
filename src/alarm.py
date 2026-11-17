# src/alarm.py - audio alarm using pygame

import os
import time
import wave

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # hide pygame's welcome message

import numpy as np
import pygame 

SAMPLE_RATE = 44100


def create_default_alarm_wav(path):
    """Creates a simple beep-beep alarm sound (880 Hz) and saves it as a WAV file."""
    frequency = 880
    beep_seconds = 0.30
    gap_seconds = 0.20

    t = np.linspace(0, beep_seconds, int(SAMPLE_RATE * beep_seconds), endpoint=False)
    beep = 0.6 * np.sin(2 * np.pi * frequency * t)

    # Short fade-in and fade-out so the beep does not click
    fade = int(SAMPLE_RATE * 0.01)
    envelope = np.ones_like(beep)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    beep = beep * envelope

    gap = np.zeros(int(SAMPLE_RATE * gap_seconds))
    one_cycle = np.concatenate([beep, gap])
    samples = np.concatenate([one_cycle, one_cycle])  # two beeps per loop

    pcm = (samples * 32767).astype("<i2")  # 16-bit samples

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)       # mono
        wav_file.setsampwidth(2)       # 2 bytes = 16 bit
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())


class AlarmPlayer:
    """
    Plays a looping alarm while the status is DROWSY.
    The sound is started only once per drowsy episode and stopped
    as soon as the status changes back.
    """

    def __init__(self, sound_path):
        self.available = False
        self._sound = None
        self._playing = False

        try:
            if not os.path.isfile(sound_path):
                create_default_alarm_wav(sound_path)
            pygame.mixer.init()
            self._sound = pygame.mixer.Sound(sound_path)
            self.available = True
        except (pygame.error, OSError) as error:
            print("WARNING: alarm sound is not available:", error)
            print("The program will still show the DROWSY warning on screen.")

    @property
    def is_playing(self):
        return self._playing

    def start(self):
        """Starts the looping alarm. Does nothing if it is already playing."""
        if not self.available or self._playing:
            return
        self._sound.play(loops=-1)  # -1 = repeat until stopped
        self._playing = True

    def stop(self):
        """Stops the alarm. Does nothing if it is not playing."""
        if not self._playing:
            return
        self._sound.stop()
        self._playing = False

    def update(self, status):
        """Call once per frame with the current status string."""
        if status == "DROWSY":
            self.start()
        else:
            self.stop()

    def close(self):
        """Stops the sound and shuts down the audio system."""
        self.stop()
        if pygame.mixer.get_init():
            pygame.mixer.quit()


if __name__ == "__main__":
    # Simple sound test: run this file directly and listen
    default_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "alarm.wav")
    )
    alarm = AlarmPlayer(default_path)

    if not alarm.available:
        print("Alarm sound is not available on this computer.")
    else:
        print("Playing the alarm for 3 seconds. You should hear beeps...")
        alarm.update("DROWSY")
        alarm.update("DROWSY")  # second call must NOT start a second sound
        time.sleep(3)
        alarm.update("ALERT")
        print("Alarm stopped. is_playing =", alarm.is_playing)
        alarm.close()