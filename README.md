# Presonus-CaptureConvert
Python script to convert the Presonus StudioLive III mixer capture recordings on SD card to be fully compatible with StudioOne DAW

This program is used to convert the Capture files that are recorded onto the SD card in the Presonus StudioLive Series III mixer to match the format of the Capture files that are recorded using the Presonus Capture app on a Mac/Windows computer.
This is done to facilite and simplify import into StudioOne and make it identical to importing recordings from a computer.

There are numerous differences in the way that the tracks on the SD card are named and flagged in the SD card capture files.  These differences include:
track names, .wav audio file names, URLs to audio file names in .capture, stereo track links, track display color and several other smaller metadata items.

EXECUTION NOTE: this script was developed on MacOS and Python 3.11.2 .  It has not been tested on Windows as of 2024-11-20.
It has been tested on StudioOne 6.

TO USE THIS SCRIPT:
1. copy the script into any folder you like
2. after you have recorded onto an SD card from StudioLive mixer, copy the folder on the SD card that contains the recording session files (.capture,.scn, .cnfg files and the Audio folder contain all the .wav audio files) into any folder (most logical place is to create a new song folder in the StudioOne/Songs folder for the new recording)
3. Run the script.  A pop-up window allows you to select the folder that contains your SD card recording session.  The script will automatically extract all the metadata and update the .capture files (used by StudioOne DAW) to have all the proper track names, stereo track linkings and correct flags.  It will also convert any stereo-linked audio files (which the SD card records as separate mono audio files) into stereo audio files.  As the script progresses, it will print the names of all the file conversions.
4. upon completion, you will have a Capture data set that is ready for direct import into StudioOne.  You can copy the entire folder into your StudioOne/Songs folder or run it from where it sits.  This converted Capture data set should be identical to the data set created by the PreSonus Capture app on Mac or Windows.

A few more comments:
- the script will create new .capture and .scene files for StudioOne.  the original (unprocessed files will remain in place as .capture.orig and .scn)
- inside the Audio folder, a new folder called linked_mono_files may be created if you have one or more linked stereo tracks in your recording.  This sub-directory contains the original mono files (with relevent renames back the the associated track) and the new stereo .wav file will be in the Audio folder.  These linked mono files are not used and only exist as an archive of the orignal audio.
- program termination (with a relevant error message) will occur if the required files are not present in the selected directory.
