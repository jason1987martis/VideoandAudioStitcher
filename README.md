# Video and Audio Stitcher

A simple Python-based tool for combining narration audio, video, and subtitles using FFmpeg.

The tool is designed for situations where narration has been recorded as separate MP3 files and each narration segment must be placed at a specific position in an MP4 video.

It can also preserve or remove the original video audio and can burn subtitles into the final video.

---

## Features

The application provides three operating modes:

### 1. Replace Original Audio

Removes the existing audio track from the video and inserts the narration MP3 files according to timestamps defined in a CSV file.

Use this when the original video contains an unwanted voice or temporary narration.

```text
Original Video
      │
      ├── Video ──────────────────────┐
      │                               │
      └── Original Audio ── REMOVED   │
                                      ▼
Narration MP3 files ────────────── Final Video
```

---

### 2. Mix Narration with Original Audio

Keeps the original video audio and mixes the new narration over it.

The existing video audio is reduced in volume so that the narration remains clear.

```text
Original Audio ── 30% ──┐
                         ├── Audio Mix ── Final Video
Narration ─────── 100% ──┘
```

This mode is useful when the original video contains background sound, demonstrations, or system audio that should remain audible.

---

### 3. Add Subtitles

Burns subtitles from an `.srt` file directly into the video.

The subtitles become permanently visible in the resulting video and therefore work regardless of the media player being used.

Supported subtitle format:

```text
.srt
```

---

# Requirements

## Python

Python 3.10 or later is recommended.

Check your Python installation:

```powershell
python --version
```

---

## FFmpeg

FFmpeg and FFprobe must be installed and accessible from the system PATH.

Verify the installation using:

```powershell
ffmpeg -version
```

and:

```powershell
ffprobe -version
```

On Windows, FFmpeg can be installed using:

```powershell
winget install Gyan.FFmpeg
```

After installation, close and reopen PowerShell before running the program.

---

# Project Setup

Create a project folder:

```powershell
mkdir VideoandAudioSticher
cd VideoandAudioSticher
```

Create a Python virtual environment:

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

No additional Python packages are currently required because the program uses Python's built-in modules and FFmpeg.

---

# Recommended Folder Structure

A typical project can be organised as follows:

```text
VideoandAudioSticher/
│
├── add_audio.py
├── README.md
│
├── original.mp4
│
├── audio_segments.csv
│
├── 01.mp3
├── 02.mp3
├── 03.mp3
├── 04.mp3
├── 05.mp3
├── ...
├── svg24.mp3
│
├── subtitles.srt
│
└── venv/
```

The narration MP3 files do not necessarily have to be in the same directory as the Python script.

However, keeping the CSV file and MP3 files together makes management easier.

---

# Running the Program

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run:

```powershell
python add_audio.py
```

The following menu appears:

```text
==========================================
       VIDEO + AUDIO STITCHER
==========================================

Choose an option:

1) REMOVE original video audio and ADD new narration
2) KEEP original video audio and ADD new narration
3) ADD subtitles to video

Enter option [1/2/3]:
```

---

# Option 1 — Remove Original Audio and Add Narration

Choose:

```text
1
```

The program asks for:

```text
Enter input MP4 file:
Enter narration CSV file:
Enter output MP4:
```

Example:

```text
Enter input MP4 file: original.mp4
Enter narration CSV file: H200_audio_segments.csv
Enter output MP4 [final_video.mp4]: H200_Final.mp4
```

The original audio stream is discarded completely.

Only the narration defined in the CSV file will appear in the final output.

This is the recommended mode when replacing an existing voice-over.

---

# Option 2 — Keep Original Audio and Add Narration

Choose:

```text
2
```

Example:

```text
Enter input MP4 file: original.mp4
Enter narration CSV file: H200_audio_segments.csv
Enter output MP4 [final_video.mp4]: H200_Mixed.mp4
```

The existing audio from the original video is retained.

The default configuration reduces the original audio level and places the new narration above it.

This is useful for:

* screen-recording system sounds
* demonstrations
* background audio
* application sounds
* presentation audio

---

# Narration CSV Format

The narration timeline is controlled using a CSV file.

Example:

```csv
audio_file,start_time,volume,trim_start,duration
01.mp3,00:00:00,1.0,0,43
02.mp3,00:00:43,1.0,0,43
03.mp3,00:01:26,1.0,0,45
04.mp3,00:02:11,1.0,0,45
05.mp3,00:02:56,1.0,0,45
```

---

## CSV Columns

### audio_file

The MP3 file containing the narration.

Example:

```text
01.mp3
```

---

### start_time

The position in the video where the narration should begin.

Supported formats include:

```text
00:02:11
```

or:

```text
02:11
```

or seconds:

```text
131
```

Milliseconds can also be specified:

```text
00:02:11.500
```

---

### volume

Controls narration volume.

Normal volume:

```text
1.0
```

Lower volume:

```text
0.8
```

Higher volume:

```text
1.2
```

Recommended starting value:

```text
1.0
```

---

### trim_start

Specifies how many seconds should be skipped from the beginning of the MP3.

Normally:

```text
0
```

Example:

```text
2.5
```

means the first 2.5 seconds of the MP3 will be ignored.

---

### duration

Specifies how much of the MP3 should be used.

Example:

```text
43
```

means that a maximum of 43 seconds of the MP3 will be inserted.

The field can also be left blank if the complete MP3 should be used.

Example:

```csv
audio_file,start_time,volume,trim_start,duration
svg01.mp3,00:00:00,1.0,0,
```

---

# Example Timeline

Consider the following narration schedule:

```text
01 → 00:00
02 → 00:43
03 → 01:26
04 → 02:11
05 → 02:56
```

The program delays each MP3 internally and constructs a single narration track:

```text
VIDEO TIMELINE

00:00        00:43        01:26        02:11
  │            │            │            │
  ▼            ▼            ▼            ▼

[ 01 ]   [ 02 ]   [ 03 ]   [ 04 ]
```

You therefore do not need to manually edit or combine the MP3 files.

FFmpeg performs the alignment automatically.

---

# Option 3 — Add Subtitles

Choose:

```text
3
```

The program asks for:

```text
Enter input MP4 file:
Enter subtitle file (.srt):
Enter output MP4:
```

Example:

```text
Enter input MP4 file: H200_Final.mp4
Enter subtitle file (.srt): subtitles.srt
Enter output MP4 [subtitled_video.mp4]: Final_Subtitles.mp4
```

---

# SRT Subtitle Format

Example:

```text
1
00:00:00,000 --> 00:00:43,000
Welcome to the tutorial.

2
00:00:43,000 --> 00:01:26,000
This section explains the complete workflow .

3
00:01:26,000 --> 00:02:11,000
We will now discuss  login.

4
00:02:11,000 --> 00:02:56,000
Next, we will check the current session and create the required folders.
```

Each subtitle entry contains:

```text
Subtitle number
Start time --> End time
Subtitle text
```

---

# Recommended Workflow

For a video where the original voice must be replaced and subtitles must also be included, use the program in two stages.

First run:

```text
Option 1
```

to generate:

```text
Final.mp4
```

Then run the program again and select:

```text
Option 3
```

using:

```text
Final.mp4
```

as the input video.

The workflow becomes:

```text
Original Video
      │
      ▼
Remove Original Audio
      │
      ▼
Add Narration
      │
      ▼
H200_Final.mp4
      │
      ▼
Add SRT Subtitles
      │
      ▼
Final_Subtitles.mp4
```

---

# Output Quality

For narration modes, the original video stream is copied directly where possible.

This means the video does not need to be re-encoded.

Advantages include:

* faster processing
* no unnecessary video quality loss
* lower CPU usage
* original video resolution preserved

The audio output is encoded using AAC at:

```text
192 kbps
```

---

# Subtitle Encoding

When subtitles are burned into the picture, the video must be re-encoded.

The program uses:

```text
H.264 / libx264
```

with:

```text
CRF 18
```

This provides high visual quality while maintaining reasonable output file size.

---

# Drag-and-Drop Paths

On Windows, files can also be dragged from File Explorer directly into PowerShell.

For example:

```text
Enter input MP4 file:
```

Drag:

```text
D:\Projects\VideoandAudioSticher\original.mp4
```

into the PowerShell window.

The program automatically handles quotation marks around paths.

---

# Common Problems

## FFmpeg Not Found

Error:

```text
FFmpeg not found.
```

Check:

```powershell
ffmpeg -version
```

If FFmpeg is not installed:

```powershell
winget install Gyan.FFmpeg
```

Restart PowerShell after installation.

---

## MP3 File Not Found

Example:

```text
Audio file not found
```

Check that:

```text
01.mp3
02.mp3
03.mp3
```

exist in the expected folder.

If the CSV contains only filenames, the program searches for them relative to the CSV file location.

---

## CSV Column Error

The CSV must contain at least:

```csv
audio_file,start_time
```

Recommended full header:

```csv
audio_file,start_time,volume,trim_start,duration
```

---

## Narration Starts at the Wrong Position

Check the `start_time` column.

Example:

```csv
07.mp3,00:04:27,1.0,0,46
```

This starts `07.mp3` at:

```text
4 minutes 27 seconds
```

---

## Narration Is Too Loud

Reduce the volume:

```csv
07.mp3,00:04:27,0.8,0,46
```

---

## Narration Is Too Quiet

Increase the volume carefully:

```csv
07.mp3,00:04:27,1.2,0,46
```

Avoid very large values because they can cause clipping or distortion.

---

## Original Voice Is Still Audible

Use:

```text
Option 1
```

instead of Option 2.

Option 1 completely replaces the original video's audio track.

---

# Example PowerShell Session

```powershell
PS D:\Projects\VideoandAudioSticher> .\venv\Scripts\Activate.ps1

(venv) PS D:\Projects\VideoandAudioSticher> python add_audio.py

==========================================
       VIDEO + AUDIO STITCHER
==========================================

Choose an option:

1) REMOVE original video audio and ADD new narration
2) KEEP original video audio and ADD new narration
3) ADD subtitles to video

Enter option [1/2/3]: 1

MODE 1: Remove original audio + add narration

Enter input MP4 file: original.mp4
Enter narration CSV file: audio_segments.csv
Enter output MP4 [final_video.mp4]: Final.mp4
```

After processing:

```text
==========================================
VIDEO CREATED SUCCESSFULLY
==========================================

D:\Projects\VideoandAudioSticher\Final.mp4
```

---

# Typical H200 Training Video Workflow

For the H200 tutorial video, narration files can be organised as:

```text
01.mp3
02.mp3
03.mp3
...
24.mp3
```

with the CSV defining the corresponding locations:

```text
01 → 00:00
02 → 00:43
03 → 01:26
...
23 → 16:45
24 → 17:31
```

The Python program handles all timing and mixing automatically.

---

# Technologies Used

* Python
* FFmpeg
* FFprobe
* CSV
* MP4
* MP3
* SRT
* H.264
* AAC

---

# Notes

The program performs all processing locally.

No audio, video, or subtitle files are uploaded to any external service.

The speed of subtitle processing depends primarily on the CPU because burning subtitles requires video re-encoding.

Narration replacement is generally much faster because the original video stream can be copied without re-encoding.

---

# License

This project can be modified and adapted for internal, educational, research, and multimedia production workflows.
