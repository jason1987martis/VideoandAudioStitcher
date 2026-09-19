import win32com.client
from pathlib import Path


def list_voices():
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = speaker.GetVoices()

    print("\nAvailable Windows voices:\n")

    for i in range(voices.Count):
        print(f"{i}: {voices.Item(i).GetDescription()}")

    return voices


def text_to_wav(text, output_file, voice_index=0, rate=0, volume=100):

    output_file = str(Path(output_file).resolve())

    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = speaker.GetVoices()

    if voice_index >= voices.Count:
        raise ValueError("Invalid voice index.")

    speaker.Voice = voices.Item(voice_index)

    # Speech rate:
    # approximately -10 to +10
    speaker.Rate = rate

    # Volume:
    # 0 - 100
    speaker.Volume = volume

    # Create WAV stream
    stream = win32com.client.Dispatch("SAPI.SpFileStream")

    # 3 = SSFMCreateForWrite
    stream.Open(output_file, 3, False)

    speaker.AudioOutputStream = stream

    speaker.Speak(text)

    stream.Close()

    print(f"\nCreated: {output_file}")


if __name__ == "__main__":

    voices = list_voices()

    print()

    selected = int(
        input("Select voice number: ")
    )

    text = input(
        "\nEnter narration text:\n> "
    )

    text_to_wav(
        text=text,
        output_file="voice.wav",
        voice_index=selected,
        rate=0,
        volume=100
    )