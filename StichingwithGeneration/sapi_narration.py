import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pythoncom
    import win32com.client
except ImportError:
    print("\nERROR: pywin32 is not installed.")
    print("Install it with:")
    print("    pip install pywin32")
    sys.exit(1)


def parse_time(value):
    value = str(value).strip()
    if not value:
        return 0.0

    parts = value.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid time value: {value}")


def check_dependencies():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg was not found in PATH.")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe was not found in PATH.")


def get_audio_duration(filename):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(filename),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def get_sapi():
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = speaker.GetVoices()
    return speaker, voices


def list_voices():
    _, voices = get_sapi()
    print("\n==========================================")
    print("AVAILABLE WINDOWS SAPI VOICES")
    print("==========================================")
    for index in range(voices.Count):
        print(f"{index}) {voices.Item(index).GetDescription()}")
    print()
    return voices.Count


def synthesize_wav(text, output_file, voice_index, rate=0, volume=100):
    output_file = Path(output_file).resolve()
    speaker, voices = get_sapi()

    if voice_index < 0 or voice_index >= voices.Count:
        raise ValueError(
            f"Voice index {voice_index} is invalid. Available voices: 0 to {voices.Count - 1}"
        )

    speaker.Voice = voices.Item(voice_index)
    speaker.Rate = int(rate)
    speaker.Volume = int(volume)

    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(str(output_file), 3, False)  # SSFMCreateForWrite

    try:
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
    finally:
        stream.Close()

    return output_file


def build_atempo_chain(factor):
    factor = float(factor)
    if factor <= 0:
        raise ValueError("Tempo factor must be greater than zero.")

    filters = []
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    filters.append(f"atempo={factor:.8f}")
    return ",".join(filters)


def find_best_sapi_rate(text, target_speech_duration, voice_index, volume, temp_dir):
    tested = []

    def test_rate(rate):
        wav_path = temp_dir / f"candidate_rate_{rate:+d}.wav"
        if wav_path.exists():
            wav_path.unlink()

        synthesize_wav(
            text=text,
            output_file=wav_path,
            voice_index=voice_index,
            rate=rate,
            volume=volume,
        )

        duration = get_audio_duration(wav_path)
        tested.append(
            {
                "rate": rate,
                "duration": duration,
                "path": wav_path,
                "difference": abs(duration - target_speech_duration),
            }
        )

        print(f"      SAPI rate {rate:+d}: {duration:.2f}s")
        return duration

    initial_duration = test_rate(0)

    if abs(initial_duration - target_speech_duration) <= 0.35:
        return min(tested, key=lambda item: item["difference"])

    if initial_duration > target_speech_duration:
        previous_duration = initial_duration
        for rate in range(1, 11):
            duration = test_rate(rate)
            if duration <= target_speech_duration:
                break
            if duration >= previous_duration and rate >= 3:
                break
            previous_duration = duration
    else:
        previous_duration = initial_duration
        for rate in range(-1, -11, -1):
            duration = test_rate(rate)
            if duration >= target_speech_duration:
                break
            if duration <= previous_duration and rate <= -3:
                break
            previous_duration = duration

    return min(tested, key=lambda item: item["difference"])


def make_exact_length_mp3(input_wav, output_mp3, current_duration, target_speech_duration, slot_duration):
    output_mp3 = Path(output_mp3).resolve()
    output_mp3.parent.mkdir(parents=True, exist_ok=True)

    tempo_factor = current_duration / target_speech_duration
    tempo_filter = build_atempo_chain(tempo_factor)

    audio_filter = (
        f"{tempo_filter},"
        f"apad,"
        f"atrim=duration={slot_duration:.6f}"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", str(input_wav),
        "-vn",
        "-af", audio_filter,
        "-codec:a", "libmp3lame",
        "-b:a", "192k",
        str(output_mp3),
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return tempo_factor


def read_narration_csv(csv_file):
    csv_path = Path(csv_file).resolve()

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"audio_file", "start_time", "duration", "text"}
        headers = set(reader.fieldnames or [])
        missing = required - headers

        if missing:
            raise ValueError(
                "CSV is missing required column(s): "
                + ", ".join(sorted(missing))
                + "\nRequired columns: audio_file,start_time,duration,text"
            )

        rows = []
        for row_number, row in enumerate(reader, start=2):
            audio_file = row["audio_file"].strip()
            text = row["text"].strip()

            if not audio_file and not text:
                continue
            if not audio_file:
                raise ValueError(f"CSV row {row_number}: audio_file is blank.")
            if not text:
                raise ValueError(f"CSV row {row_number}: text is blank.")

            slot_duration = parse_time(row["duration"])
            if slot_duration <= 0:
                raise ValueError(f"CSV row {row_number}: duration must be greater than 0.")

            rows.append(
                {
                    "row_number": row_number,
                    "audio_file": audio_file,
                    "start_time": row["start_time"].strip(),
                    "slot_duration": slot_duration,
                    "text": text,
                }
            )

    return rows


def generate_from_csv(csv_file, output_folder, voice_index, end_padding=2.0, volume=100):
    rows = read_narration_csv(csv_file)
    output_folder = Path(output_folder).resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError("No narration rows were found in the CSV.")

    print("\n==========================================")
    print("SAPI NARRATION GENERATOR")
    print("==========================================")
    print(f"CSV            : {Path(csv_file).resolve()}")
    print(f"Output folder  : {output_folder}")
    print(f"Voice index    : {voice_index}")
    print(f"End padding    : {end_padding:.2f}s")
    print(f"Segments       : {len(rows)}")
    print("==========================================\n")

    success_count = 0

    for item_number, row in enumerate(rows, start=1):
        slot_duration = row["slot_duration"]
        target_speech_duration = slot_duration - end_padding

        if target_speech_duration < 0.75:
            target_speech_duration = max(0.25, slot_duration * 0.90)

        output_name = Path(row["audio_file"]).name
        if Path(output_name).suffix.lower() != ".mp3":
            output_name = Path(output_name).with_suffix(".mp3").name

        output_path = output_folder / output_name

        print(f"[{item_number}/{len(rows)}] {output_name}")
        print(f"    Slot         : {slot_duration:.2f}s")
        print(f"    Speech target: {target_speech_duration:.2f}s")

        with tempfile.TemporaryDirectory(prefix="sapi_fit_") as temp:
            temp_dir = Path(temp)

            best = find_best_sapi_rate(
                text=row["text"],
                target_speech_duration=target_speech_duration,
                voice_index=voice_index,
                volume=volume,
                temp_dir=temp_dir,
            )

            tempo_factor = make_exact_length_mp3(
                input_wav=best["path"],
                output_mp3=output_path,
                current_duration=best["duration"],
                target_speech_duration=target_speech_duration,
                slot_duration=slot_duration,
            )

        final_duration = get_audio_duration(output_path)

        print(f"    Selected rate: {best['rate']:+d}")
        print(f"    SAPI duration : {best['duration']:.2f}s")
        print(f"    FFmpeg tempo  : {tempo_factor:.4f}x")
        if tempo_factor < 0.85 or tempo_factor > 1.20:
            print("    WARNING       : Large tempo correction; consider editing the narration text.")
        print(f"    Final MP3     : {final_duration:.2f}s")
        print(f"    Created       : {output_path}\n")

        success_count += 1

    print("==========================================")
    print("GENERATION COMPLETE")
    print("==========================================")
    print(f"Created {success_count} narration file(s) in:\n{output_folder}\n")


def generate_test_clip(text, output_file, voice_index, rate=0, volume=100):
    output_file = Path(output_file).resolve()
    if output_file.suffix.lower() != ".wav":
        output_file = output_file.with_suffix(".wav")

    synthesize_wav(
        text=text,
        output_file=output_file,
        voice_index=voice_index,
        rate=rate,
        volume=volume,
    )

    duration = get_audio_duration(output_file)
    print(f"\nCreated : {output_file}")
    print(f"Duration: {duration:.2f} seconds\n")


def ask_path(prompt, default=None):
    value = input(prompt).strip().strip('"').strip("'")
    if not value and default is not None:
        return default
    return value


def ask_int(prompt, default=None):
    value = input(prompt).strip()
    if not value and default is not None:
        return int(default)
    return int(value)


def ask_float(prompt, default=None):
    value = input(prompt).strip()
    if not value and default is not None:
        return float(default)
    return float(value)


def main():
    check_dependencies()
    pythoncom.CoInitialize()

    try:
        while True:
            print("\n==========================================")
            print("      WINDOWS SAPI NARRATION TOOL")
            print("==========================================\n")
            print("1) List installed Windows voices")
            print("2) Generate all narration MP3 files from CSV")
            print("3) Test one narration sentence")
            print("4) Exit\n")

            choice = input("Enter option [1/2/3/4]: ").strip()

            if choice == "1":
                list_voices()

            elif choice == "2":
                voice_count = list_voices()
                if voice_count == 0:
                    raise RuntimeError("No Windows SAPI voices were found.")

                voice_index = ask_int("Select voice number: ")
                csv_file = ask_path("\nEnter narration CSV file: ")
                default_output_folder = str(Path(csv_file).resolve().parent)
                output_folder = ask_path(
                    f"Output folder [{default_output_folder}]: ",
                    default=default_output_folder,
                )
                end_padding = ask_float(
                    "Silence to leave at end of each slot [2.0 seconds]: ",
                    default=2.0,
                )
                volume = ask_int("Voice volume [100]: ", default=100)

                if not 0 <= volume <= 100:
                    raise ValueError("Volume must be between 0 and 100.")
                if end_padding < 0:
                    raise ValueError("End padding cannot be negative.")

                generate_from_csv(
                    csv_file=csv_file,
                    output_folder=output_folder,
                    voice_index=voice_index,
                    end_padding=end_padding,
                    volume=volume,
                )

            elif choice == "3":
                voice_count = list_voices()
                if voice_count == 0:
                    raise RuntimeError("No Windows SAPI voices were found.")

                voice_index = ask_int("Select voice number: ")
                rate = ask_int(
                    "SAPI speech rate [-10 to +10, default 0]: ",
                    default=0,
                )
                if rate < -10 or rate > 10:
                    raise ValueError("SAPI rate must be between -10 and +10.")

                volume = ask_int("Voice volume [100]: ", default=100)
                text = input("\nEnter narration text:\n> ").strip()
                output_file = ask_path(
                    "\nOutput WAV [sapi_test.wav]: ",
                    default="sapi_test.wav",
                )

                generate_test_clip(
                    text=text,
                    output_file=output_file,
                    voice_index=voice_index,
                    rate=rate,
                    volume=volume,
                )

            elif choice == "4":
                print("\nExiting.")
                break

            else:
                print("\nInvalid option. Choose 1, 2, 3, or 4.")

    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
    except subprocess.CalledProcessError as error:
        print("\n==========================================")
        print("FFMPEG / FFPROBE ERROR")
        print("==========================================")
        print(error)
        sys.exit(1)
    except Exception as error:
        print("\n==========================================")
        print("ERROR")
        print("==========================================")
        print(error)
        sys.exit(1)
