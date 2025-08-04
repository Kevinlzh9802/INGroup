# INGroup

## Overview

This project provides tools for synchronizing and visualizing audio signals from multiple sources, such as cameras, midge recorders, and external microphones. It is designed for cross-modal synchronization tasks, especially in research or media production settings.

## Features
- **Extract and plot audio from video files** (e.g., GoPro cameras)
- **Plot midge audio** with support for external timestamp files
- **Plot microphone audio** by timecode, supporting multi-file and multi-track setups
- **Overlay multiple signals** on a single plot with opacity, making overlaps and synchronization easy to see
- **Customizable time ranges** for focused analysis
- **Automatic legend and labeling** for clarity
- **Saves the final plot as an image** (`camera_audio.png`)

## Requirements
- Python 3.7+
- Dependencies:
  - `matplotlib`
  - `numpy`
  - `scipy`
  - `soundfile`
  - `ffmpeg` and `ffprobe` (must be installed and available in your PATH)

Install Python dependencies with:
```bash
pip install matplotlib numpy scipy soundfile
```

## Usage

1. **Edit the paths** at the top of `sync/cross_sync.py` to point to your data files (camera videos, midge audio, microphone audio, etc.).
2. (Optional) Adjust the timecode and cut time settings as needed.
3. Run the main script:
   ```bash
   python sync/cross_sync.py
   ```
4. The script will:
   - Extract and plot audio from the specified sources
   - Overlay all signals on a single plot with transparency (opacity)
   - Show the plot in a window
   - Save the plot as `camera_audio.png` in the project root

**Note:**
- The saved image is generated just before the plot window appears. If you want to save a different view, adjust the code to save before `plt.show()`.
- If you add or remove sources, update the relevant sections in `cross_sync.py`.

## File Structure
- `sync/cross_sync.py` — Main script for synchronization and plotting
- `sync/process_video.py` — Functions for handling camera video and audio
- `sync/process_midge.py` — Functions for handling midge audio
- `sync/process_microphone.py` — Functions for handling microphone audio
- `sync/utils.py` — Utility functions
- `data/` — (Optional) Directory for extracted or intermediate data

## Customization
- You can adjust the opacity and line width in the plotting functions for different visualization needs.
- The script is modular; you can comment/uncomment sections in `main()` to include/exclude sources as needed.

## Troubleshooting
- If the saved image is empty, ensure `plt.savefig()` is called **before** `plt.show()`.
- Make sure all file paths are correct and all dependencies are installed.

---

For further customization or questions, check the code comments or contact the project maintainer.