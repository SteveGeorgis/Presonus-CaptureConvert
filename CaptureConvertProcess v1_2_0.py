# Last update: v1.2.0 2025-02-12 by SG

# This program is used to convert the Capture files that are recorded onto the SD card in the StudioLive Series III mixer to match the format of the Capture files that are recorded using the Capture app on a computer.
# This is done to facilite and simplify import into StudioOne and make it identical to importing recordings from a computer.
# There are numerous differences in the way that the tracks on the SD card named in the capture files.  These differences include:
# Track names, .wav audio file names, URLs to audio file names in .capture, stereo links and several other smaller metadata items.

# EXECUTION NOTE: this script was developed on MacOS and Python 3.11.2 .  It has also been tested on Windows 11 and Python 3.12.7

# v1.2.0 change:  cleaned up the program termination into one function.



import sys
import os
import json
import xml.etree.ElementTree as ET
import re
import shutil
import tkinter as tk
import pydub
from tkinter import filedialog
from datetime import datetime  # Import the `datetime` class

def terminate_program(term_message):    # function to terminate program with an error message
    print()
    print("Program cannot continue for this reason: ")
    print(term_message)
    print()
    input("Press any key to exit program ... ")
    sys.exit()
# end of program termination ##########################

# **************  function to convert two mono .wav files to a stereo .wav file *******************
def Mono_to_Stereo_WAV(left_WAV,right_WAV,stereo_WAV):
    # Suppress warnings from "pydub" module because there is an unimportant warning generated about not finding a funtion that we don't actually use
    import warnings
    import pydub
    warnings.filterwarnings("ignore", module="pydub")

    from pydub import AudioSegment

    # *** should add to check to confirm the left and right WAV files exist and handle error gracefully

    #open and read the left and right mono files:
    left_channel = AudioSegment.from_wav(left_WAV)
    right_channel = AudioSegment.from_wav(right_WAV)
    #convert to stereo file
    print ("Combining mono files into stereo: ",left_WAV," and ",right_WAV," --> ",stereo_WAV)
    stereo_file = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    stereo_file.export(stereo_WAV, format="wav")

# end of stereo file conversion function   ************************************************************************************************


def main(): #***************************************************************************************

# First step is to identify and open the directory that contains the Capture data we want to process.
    # All possible directories must exist within the current directory where this Python script is located.
    # Best way to do this is import the SD card capture folder into this directory.
    # After this program has successfully run, move the entire capture folder (including the Audio subfolder) to the StudioOne/Songs folder

    # Query to get the folder with the Capture data to be converted:
    
    # Initialize Tkinter root window (it won't show up)
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    # Bring the root window DIALOG BOX to the front (this helps with dialog visibility)
    root.lift()  # Raise the root window to the top
    
    print("Starting CaptureConvertProcess")
    print()
    print("In the dialog box,  Select the folder that contains Capture data to convert: ")
    Convert_folder=None    # initialize
    # Open file dialog box showing the directory tree
    while Convert_folder is None :
        Convert_folder = filedialog.askdirectory(title="Select the folder that contains the Capture data to convert:")
        # Check if a file was selected
        if Convert_folder:
            print(f"Folder selected:   {Convert_folder}")

        # set working directory path to selected folder    
    os.chdir(Convert_folder)
    input_dir = os.path.abspath(Convert_folder)

    # open the new Capture directory, list the contents and check that there is an "Audio" folder
    print("Opening working directory:", os.getcwd())

    # List all files and directories in the current directory
    Dir_entries = os.listdir()

    # Print each entryin the working directory (file or directory)
    for entry in Dir_entries:
        print("    ",entry)
    print()

    # Check that there is an "Audio" folder in the working directory.  Audio is where all the .wav files are located
    if "Audio" in os.listdir() and os.path.isdir("Audio"):
        # the 'Audio' directory exists
        # create a subdirectory to store the original linked mono .wav files after conversion to stereo
        global linked_mono_files_path  # make global because this will be used later
        linked_mono_files_path="./Audio/linked_mono_files" # name of sub-directory
        os.makedirs(linked_mono_files_path, exist_ok=True)
    else:
        # end program is Audio folder doesn't exist
        term_message="The 'Audio' sub-directory does not exist in this directory.  There must be an Audio subdirectory containing all the .wav audio source files."
        terminate_program(term_message)
        #####

# **** we now have acquired and confirmed the Capture data directory. ****

    # Next, we need the .capture, .scn, and .cnfg files for the session.  These three files should have the same base filename just different extensions.
    global fname 
    fname = None    # initialize name of the base Convert file
    global scn 
    scn = None      # initialize name of the original scene file
    global cnfg 
    cnfg = None     # initialize name of the original config file
    global capture 
    capture = None  #name of the capture file to be converted
        

    # Get a list of all .captures that have corresponding .scn and .cnfg files, but that
    # haven't already been converted (e.g. there is not a .capture.orig or a .scene file as well)
    files = os.listdir()
    cap_list = []
    for i in files:
      if i[-len('.capture'):] == '.capture':
        fname = i[:-len('.capture')]
        if (fname+'.scn' in files) and (fname+'.cnfg' in files) and not (fname+'.capture.orig' in files) and not (fname+'.scene' in files):
          cap_list.append(fname)

    # if cap_list is empty, there were no matching or un-processed capture files in this directory
    if len(cap_list) == 0:  
        term_message="Cannot find a matching .capture, .scn, and .cnfg in this directory that hasn't already been converted because \n" + fname + ".capture.orig and " + fname + ".scene are both present."
        terminate_program(term_message)
        
    # If cap_list>1, there is more than one set of unprocessed capture files in directory.  Can't process because cannot determine which is associated with the Audio folder.  Exit the program
    if len(cap_list)>1:
        term_message="There is more than one unconverted set of capture files in this directory.  Cannot continue ..."
        terminate_program(term_message)
        
    # else we are good to proceed
    print("File to convert: ",cap_list)


# **** We have all our source files. Now we are ready to start processing the files. ******************

# First step is some metadata housekeeping:  Put the track color, volume, pan and flag data into the .capture file  [Note that the original capture file will be renamed .capture.orig]
# Also get the mixer track names from the .scn file and update the .capture track names


    for fname in cap_list:      
        print("Opening  " + fname + ".capture, " + fname + ".scn and " + fname + ".cnfg.")
        input("Press enter to continue ... ")

        # open get the JSON data from the .scn and .cnfg files
        with open(fname+".scn","r") as f_scn, open(fname+".cnfg","r") as f_cnfg:
            scn = json.load(f_scn)
            cnfg = json.load(f_cnfg)
        tree = ET.parse(fname+".capture")
        capture = tree.getroot()
        scene={}
        global line_info
        line_info={}
   
        track_num = 0
        for i in scn:
            scene[i] = scn[i]
    
            if i == 'line': 
                for l in scene[i]:
                    track_num +=1
                    line_info[l] = {'color': scene[i][l]['color'], 'username': scene[i][l]['username'], 'link' : scene[i][l]['link'], 'trk_num' : " " }
                    
                    #Now that we've saved the unsigned int version of the color, convert color to the 2's complement signed int version used in .capture file
                    if scene[i][l]['color'] > 2**31:
                        scene[i][l]['color'] -= 2**32
                    if scene[i][l]['aux_asn_flags']:
                        scene[i][l]['aux_asn_flags'] = -1
                    if scene[i][l]['fx_asn_flags']:
                        scene[i][l]['fx_asn_flags'] = 255

         
        Keep_Empty_Tracks = False  #Change this to True if you would like to keep all tracks in the capture, otherwise all empty mixer tracks will be deleted.


                                                   
        for i in cnfg:  #update .scene file with all data in .cnfg that is not in already .scene
            if i not in scene:
                scene[i] = cnfg[i]

        for i in capture.findall('AudioTrack'):
            #check for children (Empty Tracks) and if no children remove i
            if not Keep_Empty_Tracks and len(i.findall('AudioEvent')) == 0:
                capture.remove(i)
                continue

            #convert name of "Track #" to "ch#" so it can be looked up in .scn
            t_name = "ch" + i.attrib['name'].split()[-1]
            t_num=i.attrib['name'].split()[-1]     # get the track number string

            
           
            #convert track color format from .scn to the required .capture color format
            s_color = hex(line_info[t_name]['color']).upper()
            t_color = "#"+s_color[-2:]+s_color[-4:-2]+s_color[-6:-4]+s_color[-8:-6]
            i.set('color', t_color)

            # set track name in .capture
            i.set('name', line_info[t_name]['username'])

###     New code to test for stereo links ##################
###     we only want to set the link flag in the .capture file if this track number is odd (first track in a linked stereo pair always has to be and odd trk # on StudioLive mixer) AND if the link flag for trk # +1 (the adjacent even track) is also 1 (indicating an actual stereo pair)
#            if t_num%2 != 0:  # test for odd track num
#                if line_info[t_name]['link'] == 1 and line_info[test trk_num +1 to see if the link flag is also set:
#                   then set the link flags for this track.
#               else:
#                   clear the link flag for this track.
#           else:       # this is an even track
#               if link flag for this trk is set:
#                   if link flag on previous trk # is set # indicating that this is the second track of the stereo pair
#                       set the link flag for this track
#               else:
#                   clear the link flag for this track


            # add link flag to .capture (this flag is not used by StudioOne, but will be used below to identify stereo linked tracks)
            i.set('link', str(line_info[t_name]['link']))
            i.set('trk_num', t_num) # add a track number object to be used later - this is ignored by Studio One

            # add speaker flag baszed on the link flag.  this is used by StudioOne to make the track stereo or mono.  1=mono, 3=stereo
            if line_info[t_name]['link'] == 1:  # Default to 0 if 'link' attribute is missing=="1":
                i.set('speaker', "3")   # set speaker flag to stereo
            else:
                i.set('speaker', "1")   # set speaker flag to mono

        # now we need to write back the new .capture and the .scene.  First create an archive of the original .capture file by renaming with suffix .orig
        os.rename(fname+".capture",fname+".capture.orig")    # rename the original capture file before writing the new one
        tree.write(fname+".capture", encoding="UTF-8", xml_declaration=True)
        with open(fname+".scene",'w') as f_scene:
            json.dump(scene,f_scene, indent="\t")
        
    print()
    print("Done with "+fname+".capture metadata update.")
    print()
    print("Next update audio files names and make stereo files.  This may take a bit of time depending on the length and number of audio tracks ...")
    print()
#    input("Press enter to continue ... ") debug command
    
# ****************************************************************************************************************

#   Now we have to perform more processing:
#
#   1. identify linked stereo tracks and get the urls of the corresponding .wav files
#   2. rename to two linked mono urls to track_name+L and track_name+R.  Then convert these two mono files to a stereo .wav file
#   3. update the first of the linked track with the url of the new stereo track
#   4. remove the second of the linked tracks in .capture (leaving only the first one with the new url for the stereo .wav file)
#   5. modify .capture file to update audio file URLs in each track to match the stereo track name
#   6. rename the .wav filename in Audio folder to match the corresponding track names in .capture file
#   7. then we will repeat steps 5 and 6 for all the remaining mono tracks

    # Parse capture XML data
    tree = ET.parse(fname+".capture")
    capture = tree.getroot()
    global Audio_path
    Audio_path ='./Audio/'  # set the path for all the .wav files in Audio directory
    global track_name
    global skip_next_trk
    skip_next_trk = False
    global link_trk_count
    link_trk_count=0

    # identify track with link flag=1.  Then remove the AudioTrack for the following track, leaving just the first track in .capture .
    # Then combine the two mono files into a stereo .wav file with track_name as the filename.

    # Loop through all AudioTrack elements
    for trk_index, i in enumerate(capture.findall('AudioTrack')):
        # Convert link_flag to integer for comparison
        link_flag = int(i.attrib.get('link', 0))  # Default to 0 if 'link' attribute is missing
        track_name=i.attrib['name']  # get the name of the track

        t_num=int(i.attrib['trk_num'])  # get the track number and identify odd or even track number for stereo linking process
        if t_num%2 == 0:    # if even track number, we don't do the stereo linking
            even_trk=True
        else:
            even_trk=False
        
        # first check to see if the next track should be skipped because it is part of a linked pair.  Also skip if an even track number
        if skip_next_trk == False and even_trk == False:
        
            # If link_flag is set to 1, then process the stereo linked tracks:
            # - get urls for the two linked mono .wav files (these will always be adjacent tracks from the StudioLive mixer)
            # - convert the two mono .wav files to a stereo .wav file
            # - update the mono urls to the new filename with _L and _R suffixes., respecitvely
            # - remove the next AudioTrack element (if it exists)
            
            if link_flag == 1:
                # Get the list of AudioTrack elements again
                tracks = capture.findall('AudioTrack')
                
                # determine if this linked track (odd numbered) has a matching sequential even numbered track to go with it.  i.e. do both tracks of the linked pair exist
                if trk_index - link_trk_count + 1  < len(tracks):
                    next_index=trk_index-link_trk_count+1
                    next_trk_name=tracks[next_index].get('name')
                    if track_name != next_trk_name:
                        continue  # exit the for loop
                else:
                    continue  # exit the for loop

                # both linked tracks exist
                # now get the urls of the two linked mono .wav files and convert to a stereo file.

                # Loop through all AudioEvent elements to get .wav urls
                for audio_event in i.findall(".//AudioEvent"):    
                        
                        # get the two mono urls
                        url_left = audio_event.attrib['url']
                        url_right = url_left  # initialize the right side url
                        
                        # extract the clip # from each audio_event in .capture
                        clip_num=re.search(r'\((\d+)\)', url_left).group(1)
                        
                        # Extract track number from URL - this is the sequential clip number in the original filename
                        # Use regular expression to extract the digit following the last '/' character
                        match = re.search(r'/(\d+)\.', url_left)
                        left_url_num = int(match.group(1))  # Extract the matched number as an integer
                        right_url_num = left_url_num + 1    # Increment the track number
                                                
                        # Convert the integers to strings and update the right url
                        url_right = url_right.replace(f"/{left_url_num}", f"/{right_url_num}")

                        # Convert the two mono files to stereo
                        stereo_url=Audio_path+track_name+"("+clip_num+").wav"
                        Mono_to_Stereo_WAV(url_left,url_right,stereo_url)

                        audio_event.set('url', stereo_url)  # update .capture with new stereo file url

                        # next, rename to left/right urls to track_name suffixed with _L and _R to make them obvious
                        url_L=Audio_path+track_name+"("+clip_num+")_L.wav"
                        os.rename(url_left,url_L)        
                        url_R=Audio_path+track_name+"("+clip_num+")_R.wav"
                        os.rename(url_right,url_R)

                        # next, move the _L and _R.wav files to a subdirectory to archive
                        shutil.move(url_L, linked_mono_files_path)
                        shutil.move(url_R, linked_mono_files_path)

                        # update .capture with new stereo file url
                        audio_event.set('url', stereo_url)
                        audio_event.set('name',track_name+"("+clip_num+")") # sets the clip name in the AudioEvent

                # finally, remove the second of the linked tracks in .capture, leaving just the first one (now a stereo .wav file)
                
                remove_trk_num=trk_index-link_trk_count+1 # compute the index to the linked track that will be removed. note: trk_index starts from zero to reference track 1
                if  remove_trk_num <= len(tracks):
                    link_trk_count += 1  # increment this counter each time a linked track is removed.  this will be used to offset trk_index
                    capture.remove(tracks[remove_trk_num])

                skip_next_trk = True  # set flag to skip second track of the linked pair

        else:       # stereo linked track process skipped ... proceed to next AudioTrack
            skip_next_trk = False
                
    #Write the modified XML back to the capture file
    tree.write(fname+".capture", encoding="UTF-8", xml_declaration=True)


    # Finally, rename all the .wav files that were not converted to stereo (the mono files) to the track name and then update the urls in .capture

    clip_num=0

    #loop thru all tracks in outer loop to get track name, then update the original .wav filename url with new filename based on track_name and trk_num
    for i in capture.findall('AudioTrack'):

        track_name = i.attrib['name']
        
        # only perform the conversion for mono tracks (link=0)
        
        # ***** Note: there is a minor problem that will remain unresolved becasue it doesn't cause any problems. If, in the section above, when processing linked stereo tracks ...
        # ... if there is an even-numbered track with link flag set (without a matching odd-numbered track to form the stereo pair), that track will be mono but still have the link flag = 1 and "speaker" flag =3.
        # This problem will remain unfixed because the problem only occurs if only the right track of a stereo linked pair is armed for recording to the SD card.  This is essentially a user error at the time of recording.
        # The effect of this is that those audio .wav files will not be renamed and will retain the original audio clip filenames.
        # A second effect is that when imported into StudioOne, the track will be shown in the Track Editor as stereo instead of mono.  This is easily changed in StudioOne.
                
        link_flag = int(i.attrib['link'])  # read link flag for track
        if link_flag == 0 :   # test for mono tracks

            # Loop through all mono AudioEvent elements and update url attributes
            for audio_event in i.findall(".//AudioEvent"):
           
                # Update only the filename part of the url 
                old_url = audio_event.attrib['url']
                # Extract track number from URL - this is the sequential clip number that is in the original filename
                clip_num = re.search(r'\((\d+)\)', old_url).group(1)
                new_url = old_url.rsplit("/", 1)[0] + "/"+track_name+"("+clip_num+").wav"  # Retain the path, change the filename
                audio_event.set('url', new_url)
                print("Renaming ",old_url," --> ",new_url)
                os.rename(old_url,new_url)

             # Set the file's modification date to today's date
                now = datetime.now()
                timestamp = now.timestamp()  # Convert to POSIX timestamp
                os.utime(new_url, (timestamp, timestamp))
                
                audio_event.set('name',track_name+"("+clip_num+")") # sets the clip name in the AudioEvent

#   Write the modified XML back to the capture file
    tree.write(fname+".capture", encoding="UTF-8", xml_declaration=True)

    # all operations finished
    print()
    print("Done and ready for import into StudioOne!")
    print("  - you can copy the entire capture directory (including Audio folder) into your StudioOne/Songs directory and open it from there.")
    input("Press any key ...")

# ********* end of main()  ********************************************************************


############################################
# Execute the program

if __name__ == '__main__':
    main()

# end of program 
# ******************************************






















































      
