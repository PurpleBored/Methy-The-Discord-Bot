#Use pip install <name> to install those dependecies
#To use this bot create a .env file with no name and paste in that file '<DiscordToken=YOURTOKEN HERE>' More detailed instructions how to set everything up in the README.md
import asyncio
import os
import discord
import asyncio
import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from discord.ext import commands
from discord import client
#install this one like that "pip install load_dotenv"
from dotenv import load_dotenv

import utilities


load_dotenv()

token = os.getenv('discordToken')

# Set the bot intents accordingly to be able to read info about guild members.
intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=discord.Intents.default())

#Here you can change the prefix by deleting the '!' to something you like :)
bot = commands.Bot(command_prefix='!',intents=intents)

#YouTube is anoying and tries to kick the bot from its servers. Use this to reconnect instantly.
#(Because of that you will hear some lags and stuters while liseting to music.)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

#List with all the sessions currently active.
#TODO: Terminate season after X minutes have passed without interaction.
sessions = []

@bot.command(name='ping')
async def ping(ctx):
    color = int(0x5D3FD3)
    if round(ctx.bot.latency * 1000) <= 50:
        embed=discord.Embed(title="Ping", description=f"The ping is **{round(ctx.bot.latency *1000)}** milliseconds!", color=0x5D3FD3)
    elif round(ctx.bot.latency * 1000) <= 100:
        embed=discord.Embed(title="Ping", description=f"The ping is **{round(ctx.bot.latency *1000)}** milliseconds!", color=0x5D3FD3)
    elif round(ctx.bot.latency * 1000) <= 200:
        embed=discord.Embed(title="Ping", description=f"The ping is **{round(ctx.bot.latency *1000)}** milliseconds!", color=0x5D3FD3)
    else:
        embed=discord.Embed(title="Ping", description=f"The ping is **{round(ctx.bot.latency *1000)}** milliseconds!", color=0x5D3FD3)
    await ctx.send(embed=embed)

@bot.command(name='git', brief='Link to this projects github page ヾ(≧▽≦*)o')
async def git(ctx):
    await ctx.send("The source code of this project can be found at https://github.com/PurpleBored/Methy-The-Discord-Bot If you have any issues you can report that too on this github page :D")

@bot.command(name='plshelp')
async def help_command(ctx):
    embed = discord.Embed(title='List of Commands.', description='List of commands for alpha 0.03!:')
    embed.add_field(name='!play', value='Plays Music.', inline=False)
    embed.add_field(name='!stop', value='Stops Music playback.', inline=False)
    embed.add_field(name='!skip', value='Jumps to the next song in the queue.', inline=False)
    embed.add_field(name='!pause', value='Pauses Msuic playback.', inline=False)
    embed.add_field(name='!resume', value='Resumes Msuic playback.', inline=False)
    embed.add_field(name='!print', value='prints session id Music playing now and the queue.', inline=False)
    embed.add_field(name='!leave', value='Makes the bot leave the vc.', inline=False)
    embed.add_field(name='!git', value='Links to the github page of this bot :)', inline=False)
    embed.add_field(name='!ping', value='Checks if the bot is online and responding and says the latency.', inline=False)
    
    

    await ctx.send(embed=embed)

def check_session(ctx):
    """
    Checks if there is a session with the same characteristics (guild and channel) as ctx param.

    :param ctx: discord.ext.commands.Context

    :return: session()
    """
    if len(sessions) > 0:
        for i in sessions:
            if i.guild == ctx.guild and i.channel == ctx.author.voice.channel:
                return i
        session = utilities.Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = utilities.Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session


def prepare_continue_queue(ctx):
    """
    Used to call next song in queue.

    Because lambda functions cannot call async functions, I found this workaround in discord's api documentation
    to let me continue playing the queue when the current song ends.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    fut = asyncio.run_coroutine_threadsafe(continue_queue(ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)


async def continue_queue(ctx):
    """
    Check if there is a next in queue then proceeds to play the next song in queue.

    As you can see, in this method we create a recursive loop using the prepare_continue_queue to make sure we pass
    through all songs in queue without any mistakes or interaction.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    if not session.q.theres_next():
        await ctx.send("The queue ended friend ＞︿＜ ")
        return

    session.q.next()

    voice = discord.utils.get(bot.voice_clients, guild=session.guild)
    source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

    if voice.is_playing():
        voice.stop()

    voice.play(source, after=lambda e: prepare_continue_queue(ctx))
    await ctx.send(session.q.current_music.thumb)
    await ctx.send(f"Now Playingq(≧▽≦q): {session.q.current_music.title}")


@bot.command(name='play')
async def play(ctx, *, arg):
    """
    Checks where the command's author is, searches for the music required, joins the same channel as the command's
    author and then plays the audio directly from YouTube.

    :param ctx: discord.ext.commands.Context
    :param arg: str
        arg can be url to video on YouTube or just as you would search it normally.
    :return: None
    """
    try:
        voice_channel = ctx.author.voice.channel

    # If command's author isn't connected, return.
    except AttributeError as e:
        print(e)
        await ctx.send("You are not in a vc")
        return

    # Finds author's session.
    session = check_session(ctx)

    # Searches for the video
    with youtube_dl.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
        try:
            requests.get(arg)
        except Exception as e:
            print(e)
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                'entries'][0]
        else:
            info = ydl.extract_info(arg, download=False)

    url = info['formats'][0]['url']
    thumb = info['thumbnails'][0]['url']
    title = info['title']

    session.q.enqueue(title, url, thumb)

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice:
        await voice_channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # If it is already playing something, adds to the queue
    if voice.is_playing():
        await ctx.send(thumb)
        await ctx.send(f"Added to queue: {title}")
        return
    else:
        await ctx.send(thumb)
        await ctx.send(f"Now Playingq(≧▽≦q): {title}")

        # Guarantees that the requested music is the current music.
        session.q.set_last_as_current()

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda ee: prepare_continue_queue(ctx))


@bot.command(name='next', aliases=['skip'])
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    # Finds author's session.
    session = check_session(ctx)
    # If there isn't any song to be played next, return.
    if not session.q.theres_next():
        await ctx.send("There is nothing left in queue")
        return

    # Finds an available voice client for the bot.
    voice = discord.utils.get(bot.voice_clients, guild=session.guild)

    # If it is playing something, stops it. This works because of the "after" argument when calling voice.play as it is
    # a recursive loop and the current song is already going to play the next song when it stops.
    if voice.is_playing():
        voice.stop()
        return
    else:
        # If nothing is playing, finds the next song and starts playing it.
        session.q.next()
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
        voice.play(source, after=lambda e: prepare_continue_queue(ctx))
        return


@bot.command(name='print')
async def print_info(ctx):
    """
    A debug command to find session id, what is current playing and what is on the queue.
    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    await ctx.send(f"Session ID: {session.id}")
    await ctx.send(f"Now Playing: {session.q.current_music.title}")
    queue = [q[0] for q in session.q.queue]
    await ctx.send(f"Things left in the queue: {queue}")


@bot.command(name='leave')
async def leave(ctx):
    """
    If bot is connected to a voice channel, it leaves it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected:
        check_session(ctx).q.clear_queue()
        await voice.disconnect()
    else:
        await ctx.send("Bot is not in any VC, so it can't leave.")


@bot.command(name='pause')
async def pause(ctx):
    """
    If playing audio, pause it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Nothing is currently playing.")


@bot.command(name='resume')
async def resume(ctx):
    """
    If audio is paused, resumes playing it.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused:
        voice.resume()
    else:
        await ctx.send("Music is paused already.")


@bot.command(name='stop')
async def stop(ctx):
    """
    Stops playing audio and clears the session's queue.

    :param ctx: discord.ext.commands.Context
    :return: None
    """
    session = check_session(ctx)
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing:
        voice.stop()
        session.q.clear_queue()
    else:
        await ctx.send("Nothing is currently playing.")


bot.run(token)
