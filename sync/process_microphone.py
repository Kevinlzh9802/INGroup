from datetime import datetime, timedelta, timezone
from scipy.io import wavfile
from utils import normalize_audio

def plot_mic_audio(wav_path, plt_obj, start_time, sample_rate, start_time_str=None, end_time_str=None, track_idx=0, target_rate=4000):
    """
    Plot microphone audio with specified start time and sample rate.
    """
    # Load audio
    rate, data = wavfile.read(wav_path)
    if rate != sample_rate:
        print(f"Warning: File sample rate ({rate} Hz) differs from specified rate ({sample_rate} Hz)")
    
    # Handle multi-track audio
    if len(data.shape) > 1:
        if track_idx >= data.shape[1]:
            print(f"Warning: Track index {track_idx} out of range. Using first track.")
            track_idx = 0
        data = data[:, track_idx]
    
    # Normalize the audio data
    data = normalize_audio(data)
    
    # Generate timestamps
    timestamps = [start_time + timedelta(seconds=i / sample_rate) for i in range(len(data))]

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
            
        start_range = datetime.combine(start_time.date(), start_range_time, tzinfo=timezone(timedelta(hours=2)))
        end_range = datetime.combine(start_time.date(), end_range_time, tzinfo=timezone(timedelta(hours=2)))
        
        # Filter data points within range
        mask = [(t >= start_range and t <= end_range) for t in timestamps]
        timestamps = [t for t, m in zip(timestamps, mask) if m]
        data = data[mask]

    # # Downsample the data
    # data = downsample_audio(data, rate, target_rate)
    # # Adjust timestamps for downsampled data
    # timestamps = [start_time + timedelta(seconds=i / target_rate) for i in range(len(data))]

    # Overlay on existing plot
    plt_obj.plot(timestamps, data, label=f'Microphone Audio (Track {track_idx})', alpha=0.7, linewidth=0.5)
    plt_obj.legend(fontsize='small')
    
    return data, timestamps, target_rate
