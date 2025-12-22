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


def main():
    parser = argparse.ArgumentParser(
        description="Parse video into segments and extract frames"
    )
    parser.add_argument(
        "--video_path",
        help="Path to the input video file"
    )
    parser.add_argument(
        "-o", "--output",
        default="./video_output",
        help="Output directory (default: ./video_output)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=60,
        help="Segment duration in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return
    
    parse_video_into_segments(args.video_path, args.output, args.duration)


if __name__ == "__main__":
    main()

