# Windows SAPI Narration Generator

A local text-to-speech utility for generating narration audio from CSV files using the Windows Speech API (SAPI).

This tool is designed to work alongside the **Video and Audio Stitcher** project. It reads narration text and timing information from a CSV file, generates speech using an installed Windows voice, automatically fits the speech to the required slot duration, and exports MP3 files that can be inserted into a video.

No cloud API, subscription, or internet connection is required for speech generation.

---

## Features

- Uses Windows SAPI voices installed on the computer
- Runs completely locally
- Generates narration from text stored in a CSV file
- Automatically measures generated speech duration
- Automatically selects a suitable SAPI speech rate
- Fine-tunes narration duration using FFmpeg
- Adds optional silence at the end of each narration slot
- Exports MP3 files at 192 kbps
- Provides a simple interactive menu
- Includes a test mode for previewing individual voices and sentences
- Works directly with the CSV timing system used by `add_audio.py`

---

# Requirements

## Operating System

This tool is intended for:

```text
Windows 10
Windows 11
```

It uses the native Windows Speech API and therefore is not intended for Linux or macOS.

---

## Python

Python 3.10 or later is recommended.

Check your Python installation:

```powershell
python --version
```

---

## FFmpeg

FFmpeg and FFprobe must be installed and available from the system PATH.

Check FFmpeg:

```powershell
ffmpeg -version
```

Check FFprobe:

```powershell
ffprobe -version
```

On Windows, FFmpeg can be installed using:

```powershell
winget install Gyan.FFmpeg
```

After installation, close and reopen PowerShell.

---

## Python Package

The tool requires `pywin32`.

Install it inside your virtual environment:

```powershell
pip install pywin32
```

---

# Recommended Project Structure

A typical project can be organised as follows:

```text
VideoandAudioStitcher/
│
├── add_audio.py
├── sapi_narration.py
├── README.md
├── README_SAPI.md
├── audio_segments.csv
│
├── generated_audio/
│   ├── svg01.mp3
│   ├── svg02.mp3
│   ├── svg03.mp3
│   └── ...
│
└── venv/
```

---

# Creating a Virtual Environment

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install `pywin32`:

```powershell
pip install pywin32
```

---

# Running the Program

Run:

```powershell
python sapi_narration.py
```

The menu appears:

```text
==========================================
      WINDOWS SAPI NARRATION TOOL
==========================================

1) List installed Windows voices
2) Generate all narration MP3 files from CSV
3) Test one narration sentence
4) Exit

Enter option [1/2/3/4]:
```

---

# Option 1 — List Installed Windows Voices

Choose:

```text
1
```

The program displays the SAPI-compatible voices installed on your computer.

Example:

```text
==========================================
AVAILABLE WINDOWS SAPI VOICES
==========================================

0) Microsoft David Desktop - English (United States)
1) Microsoft Zira Desktop - English (United States)
2) Microsoft Mark Desktop - English (United States)
```

The exact list depends on the voices installed in Windows.

Remember the number of the voice you want to use.

---

# Option 2 — Generate Narration from CSV

Choose:

```text
2
```

The program asks for:

```text
Select voice number:
Enter narration CSV file:
Output folder [generated_audio]:
Silence to leave at end of each slot [2.0 seconds]:
Voice volume [100]:
```

Example:

```text
Select voice number: 1

Enter narration CSV file: audio_segments.csv
Output folder [generated_audio]: generated_audio
Silence to leave at end of each slot [2.0 seconds]: 2
Voice volume [100]: 100
```

The program then processes every narration row in the CSV.

---

# CSV Format

The CSV must contain the following columns:

```csv
audio_file,start_time,duration,text
```

It may also contain additional columns used by the video stitching program.

A recommended full format is:

```csv
audio_file,start_time,volume,trim_start,duration,text
svg01.mp3,00:00:00,1.0,0,43,"Welcome to this tutorial."
svg02.mp3,00:00:43,1.0,0,43,"This section explains the complete workflow."
svg03.mp3,00:01:26,1.0,0,45,"Before beginning, remember that this is a shared system."
```

---

# CSV Columns

## `audio_file`

The name of the MP3 file that will be generated.

Example:

```text
svg01.mp3
```

---

## `start_time`

The position in the final video where the narration begins.

Example:

```text
00:04:27
```

This field is mainly used later by `add_audio.py`.

The SAPI narration tool keeps it in the CSV so both tools can use the same file.

---

## `duration`

The complete duration of the narration slot.

Example:

```text
43
```

means:

```text
43 seconds
```

Time notation can also be used:

```text
00:00:43
```

---

## `text`

The narration that should be spoken.

Example:

```text
"Welcome to this tutorial on using the H200 GPU system."
```

If the narration contains commas, keep the text inside quotation marks.

---

# Automatic Duration Fitting

The main purpose of this tool is to make the generated narration fit within the available video slot.

Suppose the CSV contains:

```csv
svg01.mp3,00:00:00,1.0,0,43,"Welcome to this tutorial..."
```

The video slot is:

```text
43 seconds
```

If the end padding is:

```text
2 seconds
```

the program targets approximately:

```text
Speech         : 41 seconds
Ending silence :  2 seconds
--------------------------------
Total MP3      : 43 seconds
```

---

# How the Duration Fitting Works

The workflow is:

```text
Narration Text
      │
      ▼
Windows SAPI
      │
      ▼
Generate Speech
      │
      ▼
Measure Duration
      │
      ▼
Try Faster / Slower SAPI Rate
      │
      ▼
Choose Closest Rate
      │
      ▼
Fine-Tune with FFmpeg
      │
      ▼
Add Ending Silence
      │
      ▼
Final MP3 Matching Slot Duration
```

---

# SAPI Speech Rate

Windows SAPI supports speech-rate adjustment.

Typical values are:

```text
-10 = extremely slow
 -5 = slow
  0 = normal
 +5 = fast
+10 = extremely fast
```

The program automatically tries suitable rates and selects the one closest to the target duration.

You do not normally need to choose the rate manually when generating narration from CSV.

---

# FFmpeg Fine Adjustment

SAPI speech-rate values are relatively coarse.

For example:

```text
Target duration : 41.00 seconds
SAPI rate +2    : 42.10 seconds
SAPI rate +3    : 39.80 seconds
```

The program may choose:

```text
SAPI rate +2
```

and then use FFmpeg to make a small timing correction.

Example:

```text
42.10 seconds
       ↓
FFmpeg tempo adjustment
       ↓
41.00 seconds
```

This helps preserve natural-sounding speech while keeping the narration synchronized with the video.

---

# Example Processing Output

A typical segment may look like:

```text
[1/24] svg01.mp3
    Slot         : 43.00s
    Speech target: 41.00s

      SAPI rate +0: 47.21s
      SAPI rate +1: 44.53s
      SAPI rate +2: 41.92s

    Selected rate: +2
    SAPI duration : 41.92s
    FFmpeg tempo  : 1.0224x
    Final MP3     : 43.02s
    Created       : generated_audio\svg01.mp3
```

The MP3 is then ready to be used by the video stitching program.

---

# Option 3 — Test a Voice

Choose:

```text
3
```

The tool asks for:

```text
Select voice number:
SAPI speech rate:
Voice volume:
Narration text:
Output WAV filename:
```

Example:

```text
Select voice number: 1
SAPI speech rate [-10 to +10, default 0]: 0
Voice volume [100]: 100

Enter narration text:
> Welcome to the H200 training tutorial.

Output WAV [sapi_test.wav]:
```

The program creates:

```text
sapi_test.wav
```

and displays its duration.

This is useful when deciding which Windows voice sounds best before generating all narration files.

---

# Speech Volume

The SAPI volume can be set between:

```text
0 to 100
```

Recommended:

```text
100
```

If the narration needs to be quieter later, the volume can also be controlled in the main video CSV using the `volume` column.

---

# End Padding

End padding leaves silence after the spoken narration.

Example:

```text
Slot duration : 45 seconds
End padding   :  2 seconds
Speech target : 43 seconds
```

Recommended values:

```text
1.0 seconds
2.0 seconds
3.0 seconds
```

A value around:

```text
2.0 seconds
```

works well for most tutorial videos because it prevents narration segments from sounding rushed or colliding with the next section.

---

# Generated Audio

The generated files are saved as MP3 using:

```text
MP3
192 kbps
```

Example output:

```text
generated_audio/
├── svg01.mp3
├── svg02.mp3
├── svg03.mp3
├── svg04.mp3
├── ...
└── svg24.mp3
```

---

# Using the Generated Narration with the Video Stitcher

After generating the narration files, run:

```powershell
python add_audio.py
```

Choose:

```text
1) REMOVE original video audio and ADD new narration
```

Then provide the same CSV file.

Example:

```text
Input video:
original.mp4

Narration CSV:
audio_segments.csv

Output:
final_video.mp4
```

The complete workflow becomes:

```text
Narration CSV
     │
     ├── Text
     ├── Timing
     └── Duration
           │
           ▼
   sapi_narration.py
           │
           ▼
      svg01.mp3
      svg02.mp3
      svg03.mp3
         ...
           │
           ▼
       add_audio.py
           │
           ▼
     final_video.mp4
```

---

# Recommended Workflow

A practical workflow is:

```text
1. Prepare narration text in the CSV
2. Run sapi_narration.py
3. Test/list Windows voices
4. Generate all MP3 narration files
5. Listen to selected narration clips
6. Correct any text that sounds unnatural
7. Run add_audio.py
8. Replace the original video's audio
9. Add subtitles if required
10. Review the final video
```

---

# Long Narration Warning

Automatic speed correction works best when the narration text is reasonably close to the available slot duration.

For example, attempting to place a very long paragraph inside a 15-second slot may result in speech that sounds unnaturally fast.

If a segment requires a very large speed correction, edit the narration text and shorten it.

A better approach is:

```text
Shorten the text
       ↓
Generate again
       ↓
Use moderate SAPI rate
       ↓
Small FFmpeg correction
```

rather than forcing extremely fast speech.

---

# Pronunciation

Windows voices may pronounce technical terms, abbreviations, names, and acronyms differently from what you expect.

For example:

```text
Slurm
MIG
CUDA
SSH
Apptainer
H200
```

If pronunciation is incorrect, changing the written narration to a phonetic-friendly form can help.

For example, a narration-only spelling can be used while keeping the correct technical term in subtitles or on-screen text.

Always preview important technical narration before generating the final video.

---

# Troubleshooting

## `pywin32` Not Found

Error:

```text
ERROR: pywin32 is not installed.
```

Install:

```powershell
pip install pywin32
```

---

## FFmpeg Not Found

Check:

```powershell
ffmpeg -version
```

If it is missing:

```powershell
winget install Gyan.FFmpeg
```

Restart PowerShell afterward.

---

## No Voices Are Listed

Check Windows speech settings and verify that at least one Windows voice is installed.

Then run:

```powershell
python sapi_narration.py
```

and choose:

```text
1) List installed Windows voices
```

---

## CSV Missing `text`

The narration generator requires:

```text
text
```

in addition to the timing information.

Required fields are:

```csv
audio_file,start_time,duration,text
```

---

## CSV Text Contains Commas

Place narration inside quotation marks.

Correct:

```csv
svg01.mp3,00:00:00,43,"Welcome everyone, and thank you for watching."
```

Incorrect:

```csv
svg01.mp3,00:00:00,43,Welcome everyone, and thank you for watching.
```

---

## Narration Sounds Too Fast

Possible causes:

- too much text for the available slot
- slot duration is incorrect
- end padding is too large

Try:

- shortening the narration
- reducing end padding
- increasing the slot duration if the video permits

---

## Narration Sounds Too Slow

The text may be too short for the slot.

You can:

- add additional useful narration
- increase the end padding
- allow natural silence at the end

Do not unnecessarily stretch very short narration across a long video segment.

---

# Example CSV

```csv
audio_file,start_time,volume,trim_start,duration,text
svg01.mp3,00:00:00,1.0,0,43,"Welcome to this tutorial on using the H200 GPU system."
svg02.mp3,00:00:43,1.0,0,43,"This section explains the complete workflow and the Slurm rule."
svg03.mp3,00:01:26,1.0,0,45,"We will now discuss shared-system rules and SSH login."
svg04.mp3,00:02:11,1.0,0,45,"Next, check your current session and create the required project folders."
```

---

# Main Tools Used

The narration generator uses:

- Python
- Windows Speech API (SAPI)
- `pywin32`
- FFmpeg
- FFprobe
- CSV
- WAV
- MP3

---

# Privacy

Speech generation is performed locally using Windows SAPI.

Narration text and generated audio are not sent to an external text-to-speech service by this program.

This makes the tool suitable for:

- internal training material
- educational videos
- research demonstrations
- offline narration workflows
- environments where cloud TTS is not desirable

---

# Integration with `add_audio.py`

The narration generator is deliberately kept in a separate file:

```text
sapi_narration.py
```

while video processing remains in:

```text
add_audio.py
```

This keeps the project modular.

The same CSV can be shared between both programs:

```text
audio_segments.csv
```

The narration generator uses:

```text
audio_file
start_time
duration
text
```

The video stitcher additionally uses fields such as:

```text
volume
trim_start
```

Therefore a single CSV can describe the entire narration workflow.

---

# License

This utility can be modified and adapted for educational, research, multimedia, and internal production workflows.
