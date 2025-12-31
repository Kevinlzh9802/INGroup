import os
import cv2
import argparse
import subprocess
import json
from pathlib import Path


def get_video_info(video_path):
    """Get video information using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)
    
    # Find video stream
    video_stream = None
    for stream in info['streams']:
        if stream['codec_type'] == 'video':
            video_stream = stream
            break
    
    if not video_stream:
        raise ValueError("No video stream found")
    
    fps_parts = video_stream['r_frame_rate'].split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1])
    duration = float(info['format']['duration'])
    
    return {
        'fps': fps,
        'duration': duration,
        'width': int(video_stream['width']),
        'height': int(video_stream['height'])
    }


def split_video_into_segments(video_path, segments_dir, segment_duration=60):
    """Split video into segments using ffmpeg."""
    segments_dir.mkdir(parents=True, exist_ok=True)
    
    print("Splitting video into segments using ffmpeg...")
    
    # Use ffmpeg to split video
    # segment_time sets the segment duration
    # reset_timestamps makes each segment start at 0
    # -c copy avoids re-encoding (much faster)
    cmd = [
        'ffmpeg', '-i', video_path,
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', str(segment_duration),
        '-reset_timestamps', '1',
        '-y',  # Overwrite output files
        str(segments_dir / 'segment_%04d.mp4')
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error splitting video: {result.stderr}")
        raise RuntimeError("Failed to split video")
    
    # Get list of created segments
    segments = sorted(segments_dir.glob('segment_*.mp4'))
    print(f"  Created {len(segments)} segments")
    return segments


def extract_frames_from_segment(segment_path, frames_dir, segment_idx):
    """Extract all frames from a video segment."""
    segment_frames_dir = frames_dir / f"segment_{segment_idx:04d}"
    segment_frames_dir.mkdir(exist_ok=True)
    
    # Set OpenCV read attempts to handle multi-stream videos
    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '10000'
    
    cap = cv2.VideoCapture(str(segment_path))
    if not cap.isOpened():
        print(f"  Warning: Could not open {segment_path.name}")
        return 0
    
    frame_idx = 0
    consecutive_failures = 0
    max_consecutive_failures = 100
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            consecutive_failures += 1
            if consecutive_failures > max_consecutive_failures:
                break
            continue
        
        consecutive_failures = 0
        
        # Save frame as image
        frame_filename = segment_frames_dir / f"frame_{frame_idx:06d}.jpg"
        cv2.imwrite(str(frame_filename), frame)
        
        frame_idx += 1
        
        # Progress indicator
        if frame_idx % 500 == 0:
            print(f"    Extracted {frame_idx} frames...")
    
    cap.release()
    print(f"  Segment {segment_idx}: extracted {frame_idx} frames")
    return frame_idx


def parse_video_into_segments(video_path, output_dir, segment_duration=60):
    """
    Parse a video into segments and extract frames from each segment.
    
    Args:
        video_path: Path to the input video file
        output_dir: Directory to store outputs
        segment_duration: Duration of each segment in seconds (default: 60)
    """
    # Create output directories
    output_path = Path(output_dir)
    segments_dir = output_path / "segments"
    frames_dir = output_path / "frames"
    
    # Get video info
    try:
        video_info = get_video_info(video_path)
        print(f"Video properties:")
        print(f"  FPS: {video_info['fps']:.2f}")
        print(f"  Duration: {video_info['duration']:.2f} seconds")
        print(f"  Resolution: {video_info['width']}x{video_info['height']}")
    except Exception as e:
        print(f"Error getting video info: {e}")
        return
    
    # Step 1: Split video into segments using ffmpeg
    try:
        segments = split_video_into_segments(video_path, segments_dir, segment_duration)
    except Exception as e:
        print(f"Error splitting video: {e}")
        return
    
    # Step 2: Extract frames from each segment
    print(f"\nExtracting frames from segments...")
    total_frames = 0
    
    for idx, segment_path in enumerate(segments):
        print(f"Processing segment {idx}...")
        frame_count = extract_frames_from_segment(segment_path, frames_dir, idx)
        total_frames += frame_count
    
    print(f"\nProcessing complete!")
    print(f"  Total segments: {len(segments)}")
    print(f"  Total frames: {total_frames}")
    print(f"  Segments saved to: {segments_dir}")
    print(f"  Frames saved to: {frames_dir}")


def extract_frames_around_timestamp(video_path, timestamp, output_dir="./data/camera/video_output/frames/ts_frames", 
                                     before_sec=0.5, after_sec=1.0, image_format='jpg', clear_past=True):
    """
    Extract frames within a time window around a specific timestamp.
    
    Args:
        video_path: Path to the input video file
        timestamp: Timestamp as [mm, ss] (e.g., [2, 5] for 2:05)
        output_dir: Directory to store extracted frames
        before_sec: Time window before timestamp in seconds (default: 0.5)
        after_sec: Time window after timestamp in seconds (default: 1.0)
        image_format: Output image format, 'jpg' or 'png' (default: 'jpg')
        clear_past: Clear past frames in the output directory (default: True)
    
    Returns:
        List of saved frame paths
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Clear past frames if clear_past is True
    if clear_past:
        for file in output_path.glob(f"*.{image_format}"):
            file.unlink()
    
    # Get video info
    try:
        video_info = get_video_info(video_path)
        fps = video_info['fps']
        duration = video_info['duration']
        print(f"Video FPS: {fps:.2f}, Duration: {duration:.2f}s")
    except Exception as e:
        print(f"Error getting video info: {e}")
        return []
    
    # Convert timestamp to seconds
    mm, ss = timestamp
    target_time = mm * 60 + ss
    
    # Calculate time window
    start_time = max(0, target_time - before_sec)
    end_time = min(duration, target_time + after_sec)
    
    print(f"Extracting frames from {start_time:.2f}s to {end_time:.2f}s")
    print(f"Target timestamp: {mm:02d}:{ss:02d} ({target_time:.2f}s)")
    
    # Calculate frame range
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    
    # Get video name without extension
    video_name = Path(video_path).stem
    
    # Set OpenCV read attempts
    os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '10000'
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return []
    
    # Set video position to start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    saved_frames = []
    current_frame = start_frame
    consecutive_failures = 0
    max_consecutive_failures = 100
    
    while current_frame <= end_frame:
        ret, frame = cap.read()
        
        if not ret:
            consecutive_failures += 1
            if consecutive_failures > max_consecutive_failures:
                print(f"Warning: Too many consecutive read failures, stopping early")
                break
            current_frame += 1
            continue
        
        consecutive_failures = 0
        
        # Calculate the actual time of this frame
        time_of_frame = current_frame / fps
        
        # Calculate mm and ss for this specific frame
        frame_mm = int(time_of_frame // 60)
        frame_ss = int(time_of_frame % 60)
        
        # Calculate frame number within the second
        # e.g., if time_of_frame is 64.5s with 60fps, frame_in_second = 30
        frame_in_second = int((time_of_frame % 1) * fps)
        
        # Create filename: videoname_mm_ss_ff.jpg (ff is frame number within the second)
        frame_filename = output_path / f"{video_name}_{frame_mm:02d}_{frame_ss:02d}_{frame_in_second:04d}.{image_format}"
        
        # Save frame
        cv2.imwrite(str(frame_filename), frame)
        saved_frames.append(frame_filename)
        
        current_frame += 1
    
    cap.release()
    
    print(f"Extracted {len(saved_frames)} frames")
    print(f"Frames saved to: {output_path}")
    
    return saved_frames


def main():
    # parser = argparse.ArgumentParser(
    #     description="Parse video into segments and extract frames"
    # )
    # parser.add_argument(
    #     "--video_path",
    #     help="Path to the input video file"
    # )
    # parser.add_argument(
    #     "-o", "--output",
    #     default="./video_output",
    #     help="Output directory (default: ./video_output)"
    # )
    # parser.add_argument(
    #     "-d", "--duration",
    #     type=int,
    #     default=60,
    #     help="Segment duration in seconds (default: 60)"
    # )
    
    # args = parser.parse_args()
    
    # if not os.path.exists(args.video_path):
    #     print(f"Error: Video file not found: {args.video_path}")
    #     return
    
    # parse_video_into_segments(args.video_path, args.output, args.duration)
    extract_frames_around_timestamp("E:\data_temp\outputs\camera_09.MP4", [1, 33])


if __name__ == "__main__":
    main()

