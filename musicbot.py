#musicbot.py
import youtube_dl
from youtubesearchpython import VideosSearch,PlaylistsSearch
import discord
from discord import FFmpegPCMAudio
import os
import random
import sys
from dotenv import load_dotenv

#bot token loaded from file ".env"
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#config for downloading videos and converting to mp3
ydl_opts = {
    'format': 'bestaudio/worstvideo',
    'quiet': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '96',
    }],
}

intents = discord.Intents().all()
client = discord.Client(prefix = '', intents=intents)

#login to discord
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

#global varaibles
vc = None
vp = None
confirm = False
queue = []
requestedBy = []

#clears folder containing downloaded mp3
def reset(queue, vp, rb):
    #downloaded music folder
    #place downloaded music folder in same dir as musicbot.py
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir = dir_path + "\downloaded"
    os.remove(os.path.join(dir, os.listdir(dir)[0]))
    if len(queue) > 0:
        del queue[0]
        del rb[0]
    if len(queue) > 0:
        play_next(queue, vp, rb)

#downloads and plays next song in queue
def play_next(queue, vp, rb):
    videoS = queue[0]

    videoInfo = VideosSearch(videoS, limit=1)
    videoTitle = videoInfo.result()['result'][0]['title']
    url = videoInfo.result()['result'][0]['link']

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        file = ydl.extract_info(url, download=True)
        path = file['title'] + "-" + file['id'] + ".mp3"

    #dir for music to be downloaded into
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir = dir_path + "\downloaded"
    
    #plays music using FFmpeg, after=... calls reset function once ffmpeg decides song is over
    #ffmpeg occasionaly decides to stop midway through a song
    #executable should lead to downloaded ffmpeg.exe withn ffmpeg folder
    #place ffmpeg in same dir as musicbot.py
    vp.play(FFmpegPCMAudio(os.path.join(str(dir), str(os.listdir(dir)[0])), executable=dir_path + "\\ffmpeg\\ffmpeg.exe"),after=lambda e: reset(queue, vp, rb))
    
#converts a string duration to an int seconds, used to calculate queue length
def duration_to_seconds(duration):
    duration = duration.split(':')
    return (int(duration[0]) * 60) + int(duration[1])

#converts int seconds to string duration, used to display calculated queue length
def seconds_to_duration(seconds):
    mins = int(seconds/60)
    secs = int(seconds%60)
    if secs < 10:
        secs = "0" + str(secs)
    return str(mins) + ":" + str(secs)

#calculates queue length
def queue_duration(queue, total_seconds = 0):
    for i in range(len(queue)):
        videoInfo = VideosSearch(queue[i], limit=1)
        videoDuration = videoInfo.result()['result'][0]['duration']
        total_seconds += duration_to_seconds(videoDuration)

    return seconds_to_duration(total_seconds)

#all bot commands containted here, don't kill me please
@client.event
async def on_message(message):
    #globals lmaooooo
    global vc
    global vp
    global queue
    global requestedBy
    global confirm

    #ignore msgs from bot itself
    if message.author == client.user:
        pass

    #pause
    elif message.content.lower().split()[0] == ("!pause"):
        if vp.is_playing():  
            await message.channel.send("**Paused** :pause_button:")
            vp.pause()
        elif vp.is_paused():
            await message.channel.send(":x: **The player is already paused**")

    #plays song/adds to queue, joins vc if not already connected
    elif message.content.lower().split()[0] == ("!p"):
        
        if vp == None:
            member = message.author
            vc = member.voice.channel
            vp = await vc.connect()
            await message.channel.send(":thumbsup: **Joined** `" + vc.name + "` **and bound to** " + message.channel.mention)
        if not vp.is_connected():
            member = message.author
            vc = member.voice.channel
            vp = await vc.connect()
        if vp.is_paused():
            vp.resume()
            await message.channel.send(":play_pause: **Resuming** :thumbsup:")
        elif len(message.content) > 3:
            videoS = ''
            if "!play" in message.content.lower():
                videoS = message.content.lower()[6:]
            else:
                videoS = message.content.lower()[3:]

            await message.channel.send("**Searching** :mag_right: `" + videoS + "`")

            #searching for videos
            videoInfo = VideosSearch(videoS, limit=1)
            playlistInfo = PlaylistsSearch(videoS, limit=1)

            videoDuration = videoInfo.result()['result'][0]['duration']
            vidDurationList = videoDuration.split(":")

            playlist = False
            
            if videoInfo.result()['result'] == [] and playlistInfo.result()['result'] == []:
                await message.channel.send(":x: **No matches**")
        
            elif videoInfo.result()['result'] == []:
                playlist = True

            elif len(vidDurationList) > 2:
                await message.channel.send(":x: **Please keep songs under 10 minutes in length** :x:")

            elif int(vidDurationList[0]) > 9:
                await message.channel.send(":x: **Please keep songs under 10 minutes in length** :x:")

            #if video passes checks, download/add to queue
            elif not playlist:
                videoTitle = videoInfo.result()['result'][0]['title']

                queue.append(videoTitle)
                requestedBy.append(message.author.name)     
                videoSeconds = duration_to_seconds(videoDuration)

                if len(queue) > 1:
                    await message.channel.send("**Playing** :notes: `" + videoTitle + "` - in " + queue_duration(queue, videoSeconds * -1) + "!")

                print()
                print("Song: " + videoTitle)
                print("Requested by: " + message.author.name)

                if not vp.is_playing():
                    async with message.channel.typing():
                        play_next(queue, vp, requestedBy)
                        if len(queue) == 1:
                            await message.channel.send("**Playing** :notes: `" + videoTitle + "` - Now!")
                
            elif playlist:
                await message.channel.send("Playlist support currently in progress")


    #joins vc
    elif message.content.lower().split()[0] == ("!summon") or message.content.lower().split()[0] == ("!join"):
        if vp == None:
            member = message.author
            vc = member.voice.channel
            vp = await vc.connect()
            await message.channel.send(":thumbsup: **Joined** `" + vc.name + "` **and bound to** " + message.channel.mention)
        if not vp.is_connected():
            member = message.author
            vc = member.voice.channel
            vp = await vc.connect()
            await message.channel.send(":thumbsup: **Joined** `" + vc.name + "` **and bound to** " + message.channel.mention)

    #disconnects from vc
    elif message.content.lower().split()[0] == ("!dc") or message.content.lower().split()[0] == ("!disconnect"):
        if vp != None:
            if vp.is_connected():
                queue = []
                vp.stop()
                await vp.disconnect()
                vp = None
                vc = None
                await message.channel.send(":mailbox_with_no_mail: **Successfully disconnected**")

    #shuffles queue, don't kill me for this code
    elif message.content.lower().split()[0] == ("!shuffle"):
        tempQ = queue[0]
        tempR = requestedBy[0]

        del queue[0]
        del requestedBy[0]

        newQ = [tempQ]
        newR = [tempR]

        for i in range(len(queue)):
            item = random.choice(queue)
            index = queue.index(item)
            newQ.append(queue[index])
            newR.append(requestedBy[index])
            del queue[index]
            del requestedBy[index]

        queue = newQ
        requestedBy = newR

        await message.channel.send("**Shuffled queue** :ok_hand:")

    #skips, "full skip" based on user role not yet implemented
    elif message.content.lower().split()[0] == ("!s"):
        vp.stop()
        await message.channel.send(":fast_forward: ***Skipped*** :thumbsup:")

    #clears queue
    elif message.content.lower().split()[0] == ("!clear"):
        tempQ = queue[0]
        tempR = requestedBy[0]
        queue.clear()
        requestedBy.clear()
        queue.append(tempQ)
        requestedBy.append(tempR)
        await message.channel.send(":boom: ***Cleared...*** :stop_button:")

    #displays queue, probably pretty innefficient here but idc
    elif message.content.lower().split()[0] == ("!q"):
        msg = "**Queue for " + message.guild.name + ":**\n\n"
        total_time = 0

        if len(queue) != 0:
            for i in range(len(queue)):
                videoInfo = VideosSearch(queue[i], limit=1)
                videoDuration = videoInfo.result()['result'][0]['duration']

                if i == 0:
                    msg = msg + ">>> __Now Playing:__\n" + queue[i] + " | `" + videoDuration + " Requested by: " + requestedBy[i] + "`\n"
                    total_time += duration_to_seconds(videoDuration)

                elif i == 1:
                    msg = msg + "\n__Up Next:__\n"
                    msg = msg + "\n`" + str(i) + ".` " + queue[i] + " | `" + videoDuration + " Requested by: " + requestedBy[i] +"`\n"
                    total_time += duration_to_seconds(videoDuration)

                else:
                    msg = msg + "\n`" + str(i) + ".` " + queue[i] + " | `" + videoDuration + " Requested by: " + requestedBy[i] +"`\n"
                    total_time += duration_to_seconds(videoDuration)

            if len(queue) == 1:
                msg = msg + "\n**" + str(len(queue)) + " song in queue | " + str(seconds_to_duration(total_time)) + " total length**"
            else:
                msg = msg + "\n**" + str(len(queue)) + " songs in queue | " + str(seconds_to_duration(total_time)) + " total length**"

            await message.channel.send(msg)
        else:
            await message.channel.send("**Queue is empty, let's get this party started! **:tada:")

    #displays song currently playing
    elif message.content.lower().split()[0] == ("!np"):
        videoInfo = VideosSearch(queue[0], limit=1)
        videoDuration = videoInfo.result()['result'][0]['duration']
        await message.channel.send("**Now playing:** `" + queue[0] + " | " + videoDuration + "`\n**Requested by: **`" + requestedBy[0] + "`")

    #replays song
    elif message.content.lower().split()[0] == ("!replay"):
        tempQ = queue[0]
        tempR = requestedBy[0]
        queue.append(tempQ)
        requestedBy.append(tempR)
        vp.stop()
        await message.channel.send(":musical_note: **Song progress reset** :track_previous:")

    #removes song of index i from queue
    elif message.content.lower().split()[0] == ("!remove"):
        ind = int(message.content[8:])
        await message.channel.send(":white_check_mark: **Removed** `" + queue[ind] + "`")
        del queue[ind]
        del requestedBy[ind]

    #sets bot discord status, replace "Spylee01" with your username
    elif message.content.lower().split()[0] == "!setstatus":
        if message.author.name == "Spylee01":
            # Setting `Playing ` status
            status = ""
            for i in message.content.lower().split():
                if i != "!setstatus":
                    status = status + i + " "
            await client.change_presence(activity=discord.Game(name=status))

    #Restarts whole program
    elif message.content.lower().split()[0] == "!refresh":
        confirm = True
        await message.channel.send("This command will refresh the bot, use !confirm to refresh. Please only use if bot freezes or crashes.")

    #Restarts whole program
    elif message.content.lower().split()[0] == "!confirm":
        if confirm:
            await message.channel.send("Restarting bot, please allow up to 15 seconds")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            await message.channel.send("Please start by using !refresh")

#Run client
client.run(TOKEN)
