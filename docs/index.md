# Project Overview

This project tries to detect intros of tv series by comparing pairs of episodes to find the largest common subset of frames.

### How the script compares videos
Each frame from the first quarter of each episode is extracted and a hash (https://pypi.org/project/ImageHash/) is made on the frame. Each frame hash is added to a long video hash.<br>
In pairs the longest identical string is searched from the two video hashes.<br>
Assumption: this is the intro

### Examples

To scan a directory containing at least 2 video files, debug logging enabled, logging debug output to file enabled, delete fingerprint data afterward

```
decode.py -i /path/to/tv/season -d -l -c
```