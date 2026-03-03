import subprocess
import os
def adjust_video_resolution(video_path, output_path, resolution):
    """
    Adjust the resolution of a video.
    The output has the same number of frames, duration, and audio as the input;
    only the frame dimensions are changed. Audio is stream-copied (no re-encoding).
    Args:
        video_path: Path to the input video file
        output_path: Path to the output video file
        resolution: Tuple of (width, height)
    Returns:
        Path to the output video file
    """
    cmd = ['ffmpeg', '-y', '-i', video_path, '-vf', f'scale={resolution[0]}:{resolution[1]}', '-c:a', 'copy', output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def adjust_resolution_folder(input_folder, output_folder, resolution):
    """
    Adjust the resolution of all videos in a folder.
    Args:
        input_folder: Path to the input folder
        output_folder: Path to the output folder
        resolution: Tuple of (width, height)
    """
    for subfolder in os.listdir(input_folder):
        for file in os.listdir(os.path.join(input_folder, subfolder)):  
            if file.endswith('.mp4'):
                os.makedirs(os.path.join(output_folder, subfolder), exist_ok=True)
                adjust_video_resolution(os.path.join(input_folder, subfolder, file), os.path.join(output_folder, subfolder, file), resolution)

if __name__ == "__main__":
    adjust_resolution_folder("D:/Desktop/video_segs_incomplete/", "D:/Desktop/video_segs_10s_960p/", (960, 540))