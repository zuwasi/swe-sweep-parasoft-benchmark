# Demo video: Static Analysis vs the AI Agents

Built with the ESL demo video pipeline (storyboard, edge-tts narration, burned-in
subtitles). Scenes 04 and 05 are a genuine, unedited-in-content recording of
Parasoft C/C++test Standard scanning bug-era HDF5 code from the SWE-sweep dataset
(asciinema capture, idle time compressed, cut to the narration).

## Files
- `output/parasoft-vs-swe-sweep.mp4` - final video, 1920x1080, 2:42, H.264/AAC
- `output/youtube-thumbnail.jpg` - 1280x720 cover picture
- `output/transcript.md` - narration transcript with scene timings
- `scenes.md`, `video.json`, `edits.json` - storyboard, config, cuts
- `clips/scene04.mp4`, `clips/scene05.mp4` - the raw terminal recordings (untracked)

Numbers are the full-codebase rerun: Parasoft C/C++test scanned each complete
buildable codebase (no hints about bug locations): 53.1% of all 488 bugs flagged
inside the changed code, 55.6% of the 162 mechanism bugs, vs 4.5% for the best
SWE-sweep agent. The scene 04 recording is cut to the narration and ends before
the report summary line of that preliminary bug-file scan.

## Publish (YouTube)
Upload at https://www.youtube.com/upload and set the cover under Details, Thumbnail.
Suggested description end: `Learn more: https://www.eswlab.com` and `Contact: sales@eswlab.com`.
