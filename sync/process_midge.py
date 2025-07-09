import os
from datetime import datetime, timedelta, timezone
from scipy.io import wavfile
import re
import numpy as np
from utils import normalize_audio

TIMEZONE = timezone(timedelta(hours=2))

def plot_midge_audio_old(wav_path, plt_obj, camera_start_time, start_time_str=None, end_time_str=None, target_rate=4000):
    """
    Read additional audio file with Unix timestamp in filename and overlay it on the existing plot.
    """
    # Extract timestamp from filename (in seconds with optional milliseconds)
    match = re.search(r'(\d+)_audio_\d+\.wav', os.path.basename(wav_path))
    if not match:
        raise ValueError("Filename does not contain a valid timestamp")

    unix_timestamp = int(match.group(1))
    start_time = datetime.fromtimestamp(np.floor(unix_timestamp / 1000), timezone(timedelta(hours=2)))

    # Load audio
    rate, data = wavfile.read(wav_path)
    
    # Normalize the audio data
    data = normalize_audio(data)
    
    # Generate timestamps
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
            
        start_range = datetime.combine(camera_start_time.date(), start_range_time, tzinfo=timezone(timedelta(hours=2)))
        end_range = datetime.combine(camera_start_time.date(), end_range_time, tzinfo=timezone(timedelta(hours=2)))
        
        # Filter data points within range
        mask = [(t >= start_range and t <= end_range) for t in timestamps]
        timestamps = [t for t, m in zip(timestamps, mask) if m]
        data = data[mask]

    # # Downsample the data
    # data = downsample_audio(data, rate, target_rate)
    # # Adjust timestamps for downsampled data
    # timestamps = [start_time + timedelta(seconds=i / target_rate) for i in range(len(data))]

    # Overlay on existing plot with different colors and transparency
    plt_obj.plot(timestamps, data, label=os.path.basename(wav_path), alpha=0.6, linewidth=0.8)
    plt_obj.legend(fontsize='small')
    
    return data, timestamps, target_rate

def plot_midge_audio(wav_path, timestamps_path, plt_obj, start_time_str=None, end_time_str=None, target_rate=4000):
    """
    Plot midge audio using external timestamps. Interpolate timestamps linearly so every sample (or every 1024th sample) has a timestamp.
    """

    # Load timestamps from txt file
    with open(timestamps_path, 'r') as f:
        timestamps = [datetime.fromtimestamp(int(line.strip()) / 1000, tz=TIMEZONE) for line in f if line.strip()]
    timestamps = np.array(timestamps)

    # Load audio
    rate, data = wavfile.read(wav_path)
    if data.ndim > 1:
        data = data[:, 0]  # Use first channel if stereo

    # Normalize
    data = data / np.max(np.abs(data))

    # Handle block structure
    block_size = len(data) // len(timestamps)
    if len(data) % len(timestamps) != 0:
        raise ValueError(f"Audio length {len(data)} is not a multiple of timestamps length {len(timestamps)}")
    data = data[:len(timestamps) * block_size]

    # Mask timestamps and corresponding blocks before interpolation
    if start_time_str and end_time_str:
        base_date = timestamps[0].date()
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M:%S.%f').time()
        except ValueError:
            start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
        start_range = datetime.combine(base_date, start_time, tzinfo=TIMEZONE)

        try:
            end_time = datetime.strptime(end_time_str, '%H:%M:%S.%f').time()
        except ValueError:
            end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
        end_range = datetime.combine(base_date, end_time, tzinfo=TIMEZONE)

        # Mask on original timestamps
        mask = (timestamps >= start_range) & (timestamps <= end_range)
        timestamps = timestamps[mask]
        # Mask the audio blocks
        data = data.reshape(-1, block_size)[mask].reshape(-1)

    # Now interpolate only the filtered timestamps and data
    timestamps_float = np.array([t.timestamp() for t in timestamps])
    interp_times_float = np.concatenate([
        np.linspace(timestamps_float[i], timestamps_float[i+1], block_size, endpoint=False)
        for i in range(len(timestamps) - 1)
    ])
    interp_times_float = np.concatenate([interp_times_float, np.full(block_size, timestamps_float[-1])])
    interp_times = np.array([datetime.fromtimestamp(ts, tz=TIMEZONE) for ts in interp_times_float])

    # Plot
    plt_obj.plot(interp_times, data, label=os.path.basename(wav_path) + ' (interpolated)', alpha=0.6, linewidth=0.8)
    plt_obj.legend(fontsize='small')
    return data, interp_times, rate

