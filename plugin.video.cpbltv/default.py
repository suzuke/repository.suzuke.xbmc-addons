# -*- coding: utf-8 -*-

import urllib, urllib2
import re
import xbmc, xbmcgui, xbmcplugin
import sys
import urlparse
from F4mProxy import f4mProxyHelper
import json

plugin_url = sys.argv[0]
handle = int(sys.argv[1])
params = dict(urlparse.parse_qsl(sys.argv[2].lstrip('?')))
resolution_list = ['512 kbps-640x360', '1 Mbps-640x360', '2.4 Mbps-1280x720', '3.6 Mbps-1280x720']
live_resolution_list = ['596 bps-640x360', '1096 bps-640x360', '1596 bps-854x480', '2596 bps-960x540']

def index():
    # Live
    url = plugin_url + "?act=live"
    li = xbmcgui.ListItem("影音直播(LIVE)")
    xbmcplugin.addDirectoryItem(handle, url, li, True)

    # Replay
    url = plugin_url + "?act=replay&offset=1"
    li = xbmcgui.ListItem("完整賽事(REPLAY)")
    xbmcplugin.addDirectoryItem(handle, url, li, True)

    # Highlight
    url = plugin_url + "?act=highlight&offset=1"
    li = xbmcgui.ListItem("精彩短片(HIGHLIGHT)")
    xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)

def live():
    response = urllib2.urlopen("http://cpbltv.com").read()
    
    m = re.findall(r"<div id=\"cache_channel_\d\" style=\"[\w\:]+;\" >({.*?})", response)

    for i in m:
        json_dict = json.loads(i)
        time = json_dict['time']
        guest_name = json_dict['guest_name']
        host_name = json_dict['host_name']
        #double_game = json_dict['double_game']
        fieldsubname = json_dict['fieldsubname']
        channel_id = json_dict['channel_id']
        live_img = json_dict['live_img']

        if live_img == "c_rain.png":
            channel_id = 99 # rain
            time += " (因雨延賽)"

        url = plugin_url + "?act=livePlay&id=" + str(channel_id)
        li = xbmcgui.ListItem(fieldsubname + " " + host_name + " VS " + guest_name + " " + time)
        xbmcplugin.addDirectoryItem(handle, url, li, True)
    xbmcplugin.endOfDirectory(handle)

def replay():
    response = urllib2.urlopen("http://cpbltv.com/lists.php?&offset=" + params['offset'])
    if response:
        response = response.read()
    else:
        return

    channels = re.findall(r"top.location.href=\'([\w\.\/\:\=\?]+)\';\">[0-9]+&nbsp;([\x01-\xff]{6}\sVS\s[\x01-\xff]{6})\s([\d]{4}\/[\d]{2}\/[\d]{2}.*?)\<br\>", response)
    #channels = re.findall(r"<a href=\"([\w\.\/\:\=\?]+)\">\d+&nbsp;([\x01-\xff]{6}\sVS\s[\x01-\xff]{6})\s([\d]{4}\/[\d]{2}\/[\d]{2})", response.read())
    for channel in channels:
        gameInfo = " ".join(channel[1:])
        url = plugin_url + "?act=replayPlay&channel=" + channel[0] + "&gameInfo=" + gameInfo
        li = xbmcgui.ListItem(gameInfo)
        li.setProperty('mimetype', 'video/x-msvideo')
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    offset = str(int(params['offset'])+1)
    li = xbmcgui.ListItem("more...page(" + offset + ")")
    url = plugin_url + "?act=replay&offset=" + offset
    xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)

def highlight():
    response = urllib2.urlopen("http://www.cpbltv.com/highlight.php?&offset=" + params['offset'])
    if response:
        response = response.read()
    else:
        return

    channels = re.findall(r"href=\'(.*?)\';\">\d+\&nbsp;(.*?)<br>", response)
    for channel in channels:
        url = plugin_url + "?act=highlightPlay&channel=" + channel[0] + "&info=" + channel[1]
        li = xbmcgui.ListItem(channel[1])
        li.setProperty('mimetype', 'video/x-msvideo')
        xbmcplugin.addDirectoryItem(handle, url, li, True)

    offset = str(int(params['offset'])+1)
    li = xbmcgui.ListItem("more...page(" + offset + ")")
    url = plugin_url + "?act=highlight&offset=" + offset
    xbmcplugin.addDirectoryItem(handle, url, li, True)

    xbmcplugin.endOfDirectory(handle)


def replayPlay():
    choice = xbmcgui.Dialog().select('選擇解析度', resolution_list)
    response = urllib2.urlopen("http://cpbltv.com" + params['channel'])
    if response:
        response = response.read()
    else:
        return
    main_url = "http://www.cpbltv.com"
    m = re.findall(r"iframe src=\"([\/\w\.\?\&\=]+autoPlay=true)", response)
    url = main_url + m[0]
    response = urllib2.urlopen(url)
    url = re.findall(r"url\:\s\"([\/\w\d\-\.\:]+index.m3u8\?token1=[\w\-\d]+&token2=[\w\_\-\d]+&expire1=[\d]+&expire2=[\d]+)", response.read())
    url = str(url[0])
    response = urllib2.urlopen(url)
    resolution_urls = re.findall("([\w\-\=\_]+).m3u8\?token1=[\w\-\d]+&token2=[\w\_\-\d]+&expire1=[\d]+&expire2=[\d]+", response.read())
    url = re.sub("index", resolution_urls[choice], url)
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    li = xbmcgui.ListItem(params['gameInfo'])
    playlist.clear()
    playlist.add(url=url, listitem=li)
    xbmc.Player().play(playlist)

def livePlay():
    if params['id'] == "99":
        xbmcgui.Dialog().ok("提醒","因雨延賽")
        return

    response = urllib2.urlopen("http://www.cpbltv.com/channel/" + params['id'] + ".html").read()
    m = re.findall(r"live_offline", response)
    if m:
        xbmcgui.Dialog().ok("提醒","現在非直播時段")
        return
    
    choice = xbmcgui.Dialog().select('選擇解析度', live_resolution_list)
    data = { 'type':'live',
             'id': params['id']}
    req = urllib2.Request("http://www.cpbltv.com/vod/player.html?&type=live&width=620&height=348&id="+params['id']+"&0.9397849941728333", urllib.urlencode(data))
    response = urllib2.urlopen(req)
    #print response.read()
    m = re.findall(r"var play_url = \'(.*?)\'", response.read())
    #m = re.findall(r"var play_url = '([\?\w\d\_\&\-\=]+)", response.read())
    url = str(m[0])
    player = f4mProxyHelper()
    player.playF4mLink(url, name="直播", resolution=choice)


def highlightPlay():
    choice = xbmcgui.Dialog().select('選擇解析度', resolution_list)
    response = urllib2.urlopen(params['channel'])
    if response:
        response = response.read()
    else:
        return
    main_url = "http://www.cpbltv.com"
    m = re.findall(r"iframe src=\"([\/\w\.\?\&\=]+autoPlay=true)", response)
    url = main_url + m[0]
    response = urllib2.urlopen(url)
    url = re.findall(r"url\:\s\"([\/\w\d\-\.\:]+index.m3u8\?token1=[\w\-\d]+&token2=[\w\_\-\d]+&expire1=[\d]+&expire2=[\d]+)", response.read())
    url = str(url[0])
    response = urllib2.urlopen(url)
    resolution_urls = re.findall("([\w\-\=\_]+).m3u8\?token1=[\w\-\d]+&token2=[\w\_\-\d]+&expire1=[\d]+&expire2=[\d]+", response.read())
    url = re.sub("index", resolution_urls[choice], url)
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    li = xbmcgui.ListItem(params['info'])
    playlist.clear()
    playlist.add(url=url, listitem=li)
    xbmc.Player().play(playlist)

{
    'index': index,
    'replay': replay,
    'live': live,
    'highlight': highlight,
    'replayPlay': replayPlay,
    'livePlay': livePlay,
    'highlightPlay': highlightPlay,
}[params.get('act', 'index')]()
