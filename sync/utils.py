import numpy as np
from scipy import signal
from datetime import datetime, time, timedelta, timezone


def normalize_audio(data):
    """Normalize audio data to have maximum absolute value of 1.0"""
    return data / np.max(np.abs(data))

def downsample_audio(data, original_rate, target_rate=4000):
    """
    Downsample audio data to target sample rate.
    Args:
        data: Audio data array
        original_rate: Original sample rate
        target_rate: Target sample rate (default: 4000 Hz)
    Returns:
        Downsampled data and timestamps
    """
    # Calculate the number of samples in the downsampled data
    num_samples = int(len(data) * target_rate / original_rate)
    
    # Use scipy's resample function
    downsampled_data = signal.resample(data, num_samples)
    
    return downsampled_data

def timecode_to_datetime(timecode_str, frame_rate, base_date):
    """
    Convert timecode (HH:MM:SS:FF) to datetime object.
    Args:
        timecode_str: Timecode in HH:MM:SS:FF format
        frame_rate: Frames per second (e.g., 59.94 for 59.94fps)
        base_date: datetime.date object for the date part
    Returns:
        datetime object with microseconds precision
    """
    hours, minutes, seconds, frames = map(int, timecode_str.split(':'))
    # Convert frames to microseconds using the exact frame rate
    microseconds = int((frames / frame_rate) * 1_000_000)
    return datetime.combine(base_date, 
                          time(hours, minutes, seconds, microseconds),
                          tzinfo=timezone(timedelta(hours=2)))


def compute_cross_correlations(camera_data, midge1_data, midge2_data, camera_timestamps, midge1_timestamps, midge2_timestamps, rate):
    """Compute cross-correlations between audio segments and find time differences at maximum correlation."""
    def get_max_correlation(data1, data2, timestamps1, timestamps2, rate, label1, label2):
        # Compute cross-correlation
        correlation = signal.correlate(data1, data2, mode='full')
        lags = signal.correlation_lags(len(data1), len(data2), mode='full')
        
        # Find lag at maximum correlation
        max_corr_idx = np.argmax(correlation)
        max_lag = lags[max_corr_idx]
        
        # Convert lag to time difference
        time_diff = max_lag / rate
        
        # Get the actual timestamps at the points of maximum correlation
        if max_lag >= 0:
            start_time1 = timestamps1[0]
            start_time2 = timestamps2[max_lag]
        else:
            start_time1 = timestamps1[-max_lag]
            start_time2 = timestamps2[0]
            
        print(f"\nCross-correlation between {label1} and {label2}:")
        print(f"Maximum correlation at lag: {max_lag} samples")
        print(f"Time difference: {time_diff:.3f} seconds")
        print(f"Timestamp {label1}: {start_time1}")
        print(f"Timestamp {label2}: {start_time2}")
        print(f"Absolute time difference: {abs((start_time2 - start_time1).total_seconds()):.3f} seconds")
        
        return time_diff, correlation, lags

    # Compute correlations between all pairs
    print("\nComputing cross-correlations between audio segments...")
    
    # Camera vs Midge1
    time_diff1, corr1, lags1 = get_max_correlation(
        camera_data, midge1_data, camera_timestamps, midge1_timestamps, rate,
        "Camera", "Midge1"
    )
    
    # Camera vs Midge2
    time_diff2, corr2, lags2 = get_max_correlation(
        camera_data, midge2_data, camera_timestamps, midge2_timestamps, rate,
        "Camera", "Midge2"
    )
    
    # Midge1 vs Midge2
    time_diff3, corr3, lags3 = get_max_correlation(
        midge1_data, midge2_data, midge1_timestamps, midge2_timestamps, rate,
        "Midge1", "Midge2"
    )
    
    return {
        'camera_midge1': (time_diff1, corr1, lags1),
        'camera_midge2': (time_diff2, corr2, lags2),
        'midge1_midge2': (time_diff3, corr3, lags3)
    }

