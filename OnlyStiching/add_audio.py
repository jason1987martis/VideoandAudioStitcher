import csv
import shutil
import subprocess
import sys
from pathlib import Path


# ==========================================================
# TIME PARSER
# ==========================================================

def parse_time(value):
    """
    Converts:
        12.5
        01:12.5
        00:01:12.5

    into seconds.
    """

    value = str(value).strip()

    if not value:
        return 0.0

    parts = value.split(":")

    if len(parts) == 1:
        return float(parts[0])

    elif len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])

        return minutes * 60 + seconds

    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"Invalid timestamp: {value}")


# ==========================================================
# CHECK FFMPEG
# ==========================================================

def check_ffmpeg():

    if shutil.which("ffmpeg") is None:
        print("\nERROR: FFmpeg not found.")
        print("Make sure ffmpeg is installed and available in PATH.")
        sys.exit(1)

    if shutil.which("ffprobe") is None:
        print("\nERROR: ffprobe not found.")
        sys.exit(1)


# ==========================================================
# CHECK WHETHER VIDEO HAS AUDIO
# ==========================================================

def video_has_audio(video_file):

    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        str(video_file)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return bool(result.stdout.strip())


# ==========================================================
# READ CSV
# ==========================================================

def read_csv(csv_file):

    csv_path = Path(csv_file).resolve()

    base_folder = csv_path.parent

    segments = []

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "audio_file",
            "start_time"
        }

        if not required_columns.issubset(
            reader.fieldnames or []
        ):
            raise ValueError(
                "\nCSV must contain at least:\n"
                "audio_file,start_time"
            )

        for row_number, row in enumerate(
            reader,
            start=2
        ):

            audio_name = row["audio_file"].strip()

            if not audio_name:
                continue

            audio_path = Path(audio_name)

            # If only filename is given,
            # search relative to CSV folder
            if not audio_path.is_absolute():
                audio_path = (
                    base_folder / audio_path
                )

            audio_path = audio_path.resolve()

            if not audio_path.exists():
                raise FileNotFoundError(
                    f"\nRow {row_number}: "
                    f"Audio file not found:\n"
                    f"{audio_path}"
                )

            start = parse_time(
                row["start_time"]
            )

            volume_text = (
                row.get("volume", "")
                .strip()
            )

            volume = (
                float(volume_text)
                if volume_text
                else 1.0
            )

            trim_text = (
                row.get("trim_start", "")
                .strip()
            )

            trim_start = (
                parse_time(trim_text)
                if trim_text
                else 0.0
            )

            duration_text = (
                row.get("duration", "")
                .strip()
            )

            duration = (
                parse_time(duration_text)
                if duration_text
                else None
            )

            segments.append({
                "audio_file": audio_path,
                "start": start,
                "volume": volume,
                "trim_start": trim_start,
                "duration": duration
            })

    return segments


# ==========================================================
# BUILD VIDEO WITH NEW NARRATION
# ==========================================================

def build_video_with_audio(
    video_file,
    csv_file,
    output_file,
    keep_original_audio
):

    video_file = Path(video_file).resolve()
    output_file = Path(output_file).resolve()

    if not video_file.exists():

        raise FileNotFoundError(
            f"Video not found:\n{video_file}"
        )

    segments = read_csv(csv_file)

    if not segments:

        raise ValueError(
            "No audio segments found in CSV."
        )

    has_audio = video_has_audio(
        video_file
    )

    print("\n------------------------------------------")
    print("INPUT INFORMATION")
    print("------------------------------------------")

    print(f"Video       : {video_file}")
    print(f"CSV         : {Path(csv_file).resolve()}")
    print(f"Output      : {output_file}")
    print(f"MP3 segments: {len(segments)}")

    print(
        f"Original audio: "
        f"{'YES' if has_audio else 'NO'}"
    )

    if keep_original_audio:
        print("Mode: KEEP original audio + narration")
    else:
        print("Mode: REMOVE original audio + narration")

    print("------------------------------------------\n")

    # ======================================================
    # INPUTS
    # ======================================================

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_file)
    ]

    # Add MP3 files
    for segment in segments:

        command.extend([
            "-i",
            str(segment["audio_file"])
        ])

    filters = []

    audio_labels = []

    # ======================================================
    # ORIGINAL AUDIO
    # ======================================================

    if keep_original_audio and has_audio:

        # Lower original video audio slightly
        # so narration is easier to hear.

        filters.append(
            "[0:a]"
            "aformat="
            "sample_rates=48000:"
            "channel_layouts=stereo,"
            "volume=0.30,"
            "apad"
            "[baseaudio]"
        )

        audio_labels.append(
            "[baseaudio]"
        )

    # ======================================================
    # PROCESS EACH MP3
    # ======================================================

    for index, segment in enumerate(
        segments,
        start=1
    ):

        delay_ms = int(
            segment["start"] * 1000
        )

        label = f"voice{index}"

        trim_filter = (
            f"atrim="
            f"start={segment['trim_start']}"
        )

        if segment["duration"] is not None:

            end_time = (
                segment["trim_start"]
                + segment["duration"]
            )

            trim_filter += (
                f":end={end_time}"
            )

        audio_filter = (
            f"[{index}:a]"
            f"{trim_filter},"
            f"asetpts=PTS-STARTPTS,"
            f"aresample=48000,"
            f"aformat="
            f"sample_rates=48000:"
            f"channel_layouts=stereo,"
            f"volume={segment['volume']},"
            f"adelay={delay_ms}:all=1"
            f"[{label}]"
        )

        filters.append(
            audio_filter
        )

        audio_labels.append(
            f"[{label}]"
        )

    # ======================================================
    # MIX AUDIO
    # ======================================================

    if len(audio_labels) == 1:

        # Only one narration track
        filters.append(
            f"{audio_labels[0]}"
            f"apad"
            f"[finalaudio]"
        )

    else:

        mix_inputs = "".join(
            audio_labels
        )

        filters.append(
            f"{mix_inputs}"
            f"amix="
            f"inputs={len(audio_labels)}:"
            f"duration=longest:"
            f"normalize=0,"
            f"alimiter=limit=0.95,"
            f"apad"
            f"[finalaudio]"
        )

    filter_complex = ";".join(
        filters
    )

    print("Creating video...")
    print()

    # ======================================================
    # FINAL COMMAND
    # ======================================================

    command.extend([

        "-filter_complex",
        filter_complex,

        # Use video stream only from original video
        "-map",
        "0:v:0",

        # Use newly created audio
        "-map",
        "[finalaudio]",

        # Copy video directly
        "-c:v",
        "copy",

        # Audio encoding
        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(output_file)
    ])

    process = subprocess.run(
        command
    )

    if process.returncode != 0:

        raise RuntimeError(
            "FFmpeg failed."
        )

    print()
    print("==========================================")
    print("VIDEO CREATED SUCCESSFULLY")
    print("==========================================")
    print(output_file)


# ==========================================================
# SUBTITLE PATH ESCAPING
# ==========================================================

def escape_subtitle_path(path):

    """
    Escape Windows path so FFmpeg subtitles
    filter can understand it.
    """

    path = str(
        Path(path).resolve()
    )

    path = path.replace(
        "\\",
        "/"
    )

    # Escape colon in:
    # D:/folder/file.srt
    # becomes
    # D\\:/folder/file.srt

    path = path.replace(
        ":",
        "\\:"
    )

    # Escape apostrophes

    path = path.replace(
        "'",
        "\\'"
    )

    return path


# ==========================================================
# ADD SUBTITLES
# ==========================================================

def add_subtitles(
    video_file,
    subtitle_file,
    output_file
):

    video_file = Path(
        video_file
    ).resolve()

    subtitle_file = Path(
        subtitle_file
    ).resolve()

    output_file = Path(
        output_file
    ).resolve()

    if not video_file.exists():

        raise FileNotFoundError(
            f"Video not found:\n"
            f"{video_file}"
        )

    if not subtitle_file.exists():

        raise FileNotFoundError(
            f"Subtitle file not found:\n"
            f"{subtitle_file}"
        )

    escaped_subtitle = (
        escape_subtitle_path(
            subtitle_file
        )
    )

    print()
    print("------------------------------------------")
    print("ADDING SUBTITLES")
    print("------------------------------------------")

    print(
        f"Video     : {video_file}"
    )

    print(
        f"Subtitles : {subtitle_file}"
    )

    print(
        f"Output    : {output_file}"
    )

    print("------------------------------------------")
    print()

    # ======================================================
    # BURN SUBTITLES INTO VIDEO
    # ======================================================

    subtitle_filter = (
        f"subtitles="
        f"'{escaped_subtitle}'"
    )

    command = [

        "ffmpeg",
        "-y",

        "-i",
        str(video_file),

        "-vf",
        subtitle_filter,

        # Video must be re-encoded when subtitles
        # are burned into the picture.

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "18",

        # Preserve existing audio
        "-c:a",
        "copy",

        "-movflags",
        "+faststart",

        str(output_file)
    ]

    print(
        "Burning subtitles into video..."
    )

    print()

    process = subprocess.run(
        command
    )

    if process.returncode != 0:

        raise RuntimeError(
            "FFmpeg subtitle processing failed."
        )

    print()
    print("==========================================")
    print("SUBTITLED VIDEO CREATED SUCCESSFULLY")
    print("==========================================")
    print(output_file)


# ==========================================================
# GET FILE PATH
# ==========================================================

def ask_file(prompt):

    path = input(prompt).strip()

    # Allow drag/drop paths surrounded by quotes

    path = path.strip('"')
    path = path.strip("'")

    return path


# ==========================================================
# MAIN MENU
# ==========================================================

def main():

    check_ffmpeg()

    print()
    print("==========================================")
    print("       VIDEO + AUDIO STITCHER")
    print("==========================================")

    print()
    print("Choose an option:")
    print()

    print(
        "1) REMOVE original video audio "
        "and ADD new narration"
    )

    print(
        "2) KEEP original video audio "
        "and ADD new narration"
    )

    print(
        "3) ADD subtitles to video"
    )

    print()

    choice = input(
        "Enter option [1/2/3]: "
    ).strip()

    # ======================================================
    # OPTION 1
    # ======================================================

    if choice == "1":

        print()
        print(
            "MODE 1:"
            " Remove original audio + add narration"
        )
        print()

        video_file = ask_file(
            "Enter input MP4 file: "
        )

        csv_file = ask_file(
            "Enter narration CSV file: "
        )

        output_file = ask_file(
            "Enter output MP4 "
            "[final_video.mp4]: "
        )

        if not output_file:
            output_file = (
                "final_video.mp4"
            )

        build_video_with_audio(
            video_file=video_file,
            csv_file=csv_file,
            output_file=output_file,
            keep_original_audio=False
        )

    # ======================================================
    # OPTION 2
    # ======================================================

    elif choice == "2":

        print()
        print(
            "MODE 2:"
            " Keep original audio + add narration"
        )
        print()

        video_file = ask_file(
            "Enter input MP4 file: "
        )

        csv_file = ask_file(
            "Enter narration CSV file: "
        )

        output_file = ask_file(
            "Enter output MP4 "
            "[final_video.mp4]: "
        )

        if not output_file:
            output_file = (
                "final_video.mp4"
            )

        build_video_with_audio(
            video_file=video_file,
            csv_file=csv_file,
            output_file=output_file,
            keep_original_audio=True
        )

    # ======================================================
    # OPTION 3
    # ======================================================

    elif choice == "3":

        print()
        print(
            "MODE 3: Add subtitles"
        )
        print()

        video_file = ask_file(
            "Enter input MP4 file: "
        )

        subtitle_file = ask_file(
            "Enter subtitle file (.srt): "
        )

        output_file = ask_file(
            "Enter output MP4 "
            "[subtitled_video.mp4]: "
        )

        if not output_file:

            output_file = (
                "subtitled_video.mp4"
            )

        add_subtitles(
            video_file=video_file,
            subtitle_file=subtitle_file,
            output_file=output_file
        )

    else:

        print()
        print(
            "Invalid option."
        )

        print(
            "Please select 1, 2 or 3."
        )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\nOperation cancelled."
        )

    except Exception as error:

        print()
        print("==========================================")
        print("ERROR")
        print("==========================================")

        print(error)

        print()

        sys.exit(1)