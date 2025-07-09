import os
import matplotlib.pyplot as plt
from datetime import datetime, date, time, timedelta, timezone
from scipy.io import wavfile
from utils import normalize_audio
import subprocess


def get_timecode(video_path):
    """Extract timecode from video stream using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream_tags=timecode',
        '-of', 'default=nw=1:nk=1',
        video_path
    ]
    print("Running command:", cmd)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timecode = result.stdout.strip()
    if not timecode:
        print("Warning: No timecode found in video stream. Using creation time instead.")
        # Fallback to creation time
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream_tags=creation_time',
            '-of', 'default=nw=1:nk=1',
            video_path
        ]
        print("Running command:", cmd)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        creation_time = result.stdout.strip()
        if not creation_time:
            raise ValueError("Neither timecode nor creation time found in video")
        return creation_time
    return timecode

def extract_audio(video_path, output_wav):
    """Extract audio from video as WAV using ffmpeg."""
    cmd = ['ffmpeg', '-y', '-i', video_path, '-vn', '-ac', '1', '-ar', '16000', output_wav]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def plot_camera_audio(wav_path, timecode_str, plt_obj=None, manual_date=None, start_time_str=None, end_time_str=None, frame_rate=59.94, target_rate=4000):
    """
    Plot audio waveform aligned with real time from video timecode.
    """
    # Load audio
    rate, data = wavfile.read(wav_path)
    duration = len(data) / rate

    # Normalize the audio data
    data = normalize_audio(data)

    # Parse timecode (format: HH:MM:SS:FF)
    hours, minutes, seconds, frames = map(int, timecode_str.split(':'))
    # Convert frames to microseconds using the exact frame rate
    microseconds = int((frames / frame_rate) * 1_000_000)
    start_time = datetime.combine(manual_date or date.today(), 
                                time(hours, minutes, seconds, microseconds),
                                tzinfo=timezone(timedelta(hours=2)))

    # Generate timestamps for x-axis
    timestamps = [start_time + timedelta(seconds=i / rate) for i in range(len(data))]

    # Filter data based on time range if specified
    if start_time_str and end_time_str:
        # Parse time with possible milliseconds
        try:
            start_range_time = datetime.strptime(start_time_str, '%H:%M:%S.%f').time()
        except ValueError:
            start_range_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
            
        try:
            end_range_time = datetime.strptime(end_time_str, '%H:%M:%S.%f').time()
        except ValueError:
            end_range_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
            
        start_range = datetime.combine(manual_date or date.today(), start_range_time, tzinfo=timezone(timedelta(hours=2)))
        end_range = datetime.combine(manual_date or date.today(), end_range_time, tzinfo=timezone(timedelta(hours=2)))
        
        # Filter data points within range
        mask = [(t >= start_range and t <= end_range) for t in timestamps]
        timestamps = [t for t, m in zip(timestamps, mask) if m]
        data = data[mask]

    # # Downsample the data
    # data = downsample_audio(data, rate, target_rate)
    # # Adjust timestamps for downsampled data
    # timestamps = [start_time + timedelta(seconds=i / target_rate) for i in range(len(data))]

    # Create new figure only if plt_obj is not provided
    if plt_obj is None:
        plt.figure(figsize=(12, 4))
        plt.title('Audio Signal Over Time')
        plt.xlabel('Time')
        plt.ylabel('Amplitude')
        plt.tight_layout()
        plt_obj = plt

    # Plot on the provided or new plot object
    plt_obj.plot(timestamps, data, label=f'Video Audio ({os.path.basename(wav_path)})', alpha=0.6, linewidth=0.8)
    plt_obj.legend(fontsize='small')

    return plt_obj, start_time, data, timestamps, target_rate
