import matplotlib.pyplot as plt
from datetime import date
import os
from process_video import plot_camera_audio, get_timecode, extract_audio
from process_midge import plot_midge_audio
from process_microphone import plot_audio_waveform_by_timecode
from utils import timecode_to_datetime

# Global configuration
# Edit this path to the data path
DATA_PATH = "C:/Users/zongh/OneDrive - Delft University of Technology/tudelft/projects/dataset_collection/cross_modal_sync/"
CAMERA_PATH_1 = os.path.join(DATA_PATH, "camera/trial2/GH010359.MP4")
CAMERA_PATH_2 = os.path.join(DATA_PATH, "camera/trial2/GH010543.MP4")  # Add your second camera path
MIDGE_PATH_1 = os.path.join(DATA_PATH, "midge/trial3/0MICHI1.wav")
MIDGE_PATH_2 = os.path.join(DATA_PATH, "midge/trial2/59/1748360592823_audio_2.wav")
MIC_PATH_1 = os.path.join(DATA_PATH, "microphone/UFX01_07.wav")
MIC_PATH_2 = os.path.join(DATA_PATH, "microphone/UFX01_08.wav")

# Time configuration
MIC_START_TIMECODE = "17:44:55:15"  # Mic start time in timecode format (HH:MM:SS:FF)
CUT_START_TIME = "17:23:00"         # Cut start time in HH:MM:SS.mmm format
CUT_END_TIME = "17:24:00"           # Cut end time in HH:MM:SS.mmm format

# Technical configuration
CAMERA_FRAME_RATE = 59.94  # Camera frame rate (59.94 fps)
MIC_FRAME_RATE = 29.97     # Microphone frame rate (29.97 fps)
MIC_SAMPLE_RATE = 48000    # Microphone sample rate
MIC_TRACK_IDX_1 = 1          # Index of the microphone track to plot (0-based)
MIC_TRACK_IDX_2 = 3          # Index of the microphone track to plot (0-based)


def main():
    # Create a single matplotlib plot object (figure and axes)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title('Audio Signal Over Time (with opacity for overlap visibility)', fontsize=14)
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    print(f"Processing camera 1: {CAMERA_PATH_1}")
    timecode1 = get_timecode(CAMERA_PATH_1)
    print(f"Timecode 1: {timecode1}")

    print(f"Processing camera 2: {CAMERA_PATH_2}")
    timecode2 = get_timecode(CAMERA_PATH_2)
    print(f"Timecode 2: {timecode2}")

    # Create audio directory if it doesn't exist
    audio_dir = os.path.join("data", "camera", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    # Generate output paths based on input video filenames
    video1_name = os.path.splitext(os.path.basename(CAMERA_PATH_1))[0]
    video2_name = os.path.splitext(os.path.basename(CAMERA_PATH_2))[0]
    wav1_path = os.path.join(audio_dir, f"{video1_name}.wav")
    wav2_path = os.path.join(audio_dir, f"{video2_name}.wav")
    
    # Extract audio from both cameras
    # extract_audio(CAMERA1_PATH, wav1_path)
    # extract_audio(CAMERA2_PATH, wav2_path)

    # Plot first camera audio and get the plot object
    # plt_obj, camera1_start_time, camera1_data, camera1_timestamps, camera1_rate = plot_camera_audio(
    #     wav1_path, timecode1, 
    #     plt_obj=plt_obj,
    #     manual_date=date(2025, 5, 27),
    #     start_time_str=CUT_START_TIME,
    #     end_time_str=CUT_END_TIME,
    #     frame_rate=CAMERA_FRAME_RATE
    # )

    # Plot second camera audio using the same plot object
    # _, camera2_start_time, camera2_data, camera2_timestamps, camera2_rate = plot_camera_audio(
    #     wav2_path, timecode2, 
    #     plt_obj=plt_obj,  # Pass the existing plot object
    #     manual_date=date(2025, 5, 27),
    #     start_time_str=CUT_START_TIME,
    #     end_time_str=CUT_END_TIME,
    #     frame_rate=CAMERA_FRAME_RATE
    # )

    # Add midge audio (with support for external timestamps)
    midge1_base, midge1_ext = os.path.splitext(MIDGE_PATH_1)
    midge1_ts_path = midge1_base + '-ts.txt'
    if os.path.exists(midge1_ts_path):
        print(f"Using external timestamps: {midge1_ts_path}")
        midge1_data, midge1_timestamps, midge1_rate = plot_midge_audio(
            MIDGE_PATH_1, midge1_ts_path, plt_obj=ax,
            start_time_str=CUT_START_TIME,
            end_time_str=CUT_END_TIME
        )
    else:
        print(f"No external timestamps found, using filename timestamp for {MIDGE_PATH_1}")
        raise ValueError("No external timestamps found")
    

    # midge2_data, midge2_timestamps, midge2_rate = plot_midge_audio(
    #     MIDGE2_PATH, plt_obj, camera1_start_time,
    #     start_time_str=CUT_START_TIME,
    #     end_time_str=CUT_END_TIME
    # )

    # plt.show()
    
    # Convert mic start timecode to datetime using mic frame rate
    mic_start_time = timecode_to_datetime(MIC_START_TIMECODE, MIC_FRAME_RATE, date(2025, 5, 27))
    
    # Add microphone audio
    # mic_data, mic_timestamps, mic_rate = plot_mic_audio(
    #     MIC_PATH_1, plt_obj, mic_start_time, MIC_SAMPLE_RATE,
    #     start_time_str=CUT_START_TIME,
    #     end_time_str=CUT_END_TIME,
    #     track_idx=MIC_TRACK_IDX_1
    # )

    # mic_data, mic_timestamps, mic_rate = plot_mic_audio(
    #     MIC_PATH_2, plt_obj, mic_start_time, MIC_SAMPLE_RATE,
    #     start_time_str=CUT_START_TIME,
    #     end_time_str=CUT_END_TIME,
    #     track_idx=MIC_TRACK_IDX_2
    # )

    # Print time ranges for debugging
    # print("\nTime ranges for each source:")
    # print(f"Camera 1: {camera1_timestamps[0]} to {camera1_timestamps[-1]}")
    # print(f"Midge 1: {midge1_timestamps[0]} to {midge1_timestamps[-1]}")
    # print(f"Mic 1: {mic_timestamps[0]} to {mic_timestamps[-1]}")
    # Get base date and timezone from midge timestamps
    base_datetime = midge1_timestamps[0]
    base_date = base_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    base_tz = base_datetime.tzinfo

    plot_audio_waveform_by_timecode(
        audio_dir=DATA_PATH + 'microphone/',
        start_tc=CUT_START_TIME,
        end_tc=CUT_END_TIME,
        track_index=40,
        fps=29.97,
        samplerate=48000,
        ax=ax,
        base_date=base_date,
        base_tz=base_tz
    )
    plt.savefig('camera_audio.png')
    plt.show()

if __name__ == "__main__":
    main()
    