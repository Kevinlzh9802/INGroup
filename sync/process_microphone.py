import os
import json
import subprocess
import soundfile as sf
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import numpy as np

def timecode_to_seconds(tc: str, fps=25):
    parts = list(map(int, tc.split(':')))
    if len(parts) == 3:
        h, m, s = parts
        f = 0
    elif len(parts) == 4:
        h, m, s, f = parts
    else:
        raise ValueError(f"Invalid timecode format: {tc}")
    return h * 3600 + m * 60 + s + f / fps


def get_file_info(filepath):
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        filepath
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    metadata = json.loads(result.stdout)

    timecode = metadata['format']['tags'].get('timecode')
    duration = float(metadata['format']['duration'])
    return timecode, duration


def build_file_timeline(audio_dir, fps):
    timeline = []
    for fname in sorted(os.listdir(audio_dir)):
        if fname.lower().endswith('.wav'):
            full_path = os.path.join(audio_dir, fname)
            timecode, duration = get_file_info(full_path)
            if timecode:
                start_sec = timecode_to_seconds(timecode, fps)
                end_sec = start_sec + duration
                timeline.append({
                    'filename': full_path,
                    'start_time': start_sec,
                    'end_time': end_sec
                })
    return timeline


def find_files_for_range(timeline, start_sec, end_sec):
    result = []
    for entry in timeline:
        if end_sec <= entry['start_time']:
            break
        if start_sec < entry['end_time'] and end_sec > entry['start_time']:
            result.append(entry)
    return result


def extract_audio_segment(filepath, track_index, start_time, end_time, file_start, samplerate):
    data, sr = sf.read(filepath)
    assert sr == samplerate, "Sample rate mismatch"
    channel_data = data[:, track_index]
    start_sample = int((start_time - file_start) * sr)
    end_sample = int((end_time - file_start) * sr)
    return channel_data[start_sample:end_sample]


def plot_audio_waveform_by_timecode(audio_dir, start_tc, end_tc, track_index=1, fps=25, samplerate=48000, ax=None, base_date=None, base_tz=None):
    """
    Plot the audio waveform for a given timecode range on the provided matplotlib Axes.
    If ax is None, a new figure and axes will be created.
    """
    start_sec = timecode_to_seconds(start_tc, fps)
    end_sec = timecode_to_seconds(end_tc, fps)

    timeline = build_file_timeline(audio_dir, fps)
    selected_files = find_files_for_range(timeline, start_sec, end_sec)

    if not selected_files:
        print("❌ No files found for the given timecode range.")
        return

    waveform = []
    times = []
    # Use a reference date (e.g., today)
    if base_date is None:
        ref_date = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        ref_date = base_date
    if base_tz is not None:
        ref_date = ref_date.replace(tzinfo=base_tz)

    for file_info in selected_files:
        file_start = file_info['start_time']
        file_end = file_info['end_time']
        filepath = file_info['filename']

        seg_start = max(start_sec, file_start)
        seg_end = min(end_sec, file_end)

        segment = extract_audio_segment(filepath, track_index, seg_start, seg_end, file_start, samplerate)
        waveform.extend(segment)
        n_samples = len(segment)
        # Each sample's absolute time as datetime
        segment_times = [ref_date + datetime.timedelta(seconds=seg_start + i / samplerate) for i in range(n_samples)]
        times.extend(segment_times)

    # Normalize waveform before plotting
    if len(waveform) > 0:
        waveform = np.array(waveform)
        waveform = waveform / np.max(np.abs(waveform))

    # 绘图
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, waveform)
    ax.set_title(f"Waveform from {start_tc} to {end_tc}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Amplitude")
    ax.grid(True)
    # Format x-axis as HH:MM:SS
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.tight_layout()
    # Do not call plt.show() here

# usage

