import os
import json
import subprocess
import soundfile as sf
import matplotlib.pyplot as plt

def timecode_to_seconds(tc: str, fps=25):
    h, m, s, f = map(int, tc.split(':'))
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


def plot_audio_waveform_by_timecode(audio_dir, start_tc, end_tc, track_index=1, fps=25, samplerate=48000):
    start_sec = timecode_to_seconds(start_tc, fps)
    end_sec = timecode_to_seconds(end_tc, fps)

    timeline = build_file_timeline(audio_dir, fps)
    selected_files = find_files_for_range(timeline, start_sec, end_sec)

    if not selected_files:
        print("! No files found for the given timecode range.")
        return

    waveform = []

    for file_info in selected_files:
        file_start = file_info['start_time']
        file_end = file_info['end_time']
        filepath = file_info['filename']

        seg_start = max(start_sec, file_start)
        seg_end = min(end_sec, file_end)

        segment = extract_audio_segment(filepath, track_index, seg_start, seg_end, file_start, samplerate)
        waveform.extend(segment)

    # plot
    plt.figure(figsize=(10, 4))
    plt.plot(waveform)
    plt.title(f"Waveform from {start_tc} to {end_tc}")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# usage
plot_audio_waveform_by_timecode(
    audio_dir='../data/',
    start_tc='17:17:04:10',
    end_tc='17:18:06:00',
    track_index=40,
    fps=29.97,
    samplerate=48000
)
