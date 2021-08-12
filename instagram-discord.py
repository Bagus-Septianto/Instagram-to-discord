#!/usr/bin/python

# Copyright (c) 2020 Fernando
# Url: https://github.com/fernandod1/
# License: MIT

# DESCRIPTION:
# This script executes 2 actions:
# 1.) Monitors for new image posted in a instagram account.
# 2.) If found new image, a bot posts new instagram image in a discord channel.
# 3.) Repeat after set interval.

# REQUIREMENTS:
# - Python v3
# - Python module re, json, requests
import re
import json
import sys
import requests
import urllib.request
import os
import time
import random
from discord_webhook import DiscordWebhook, DiscordEmbed
# to test env on my own pc, im using dotenv
import dotenv
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file, override=True)

# USAGE:
# Set Environment Variables:
# Set IG_USERNAME to username account you want to monitor. Example - ladygaga
# Set WEBHOOK_URL to Discord account webhook url. To know how, just Google: "how to create webhook discord".
# Set TIME_INTERVAL to the time in seconds in between each check for a new post. Example - 1.5, 600 (default=600)
# Help: https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-set-environment-variables-in-linux/

INSTAGRAM_USERNAME = os.environ.get('IG_USERNAME')

USER_AGENT = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
]

# ----------------------- Do not modify under this line ----------------------- #


def get_user_fullname(html):
    if html.json()["graphql"]["user"]["full_name"]:
        return html.json()["graphql"]["user"]["full_name"]
    else:
        return INSTAGRAM_USERNAME

def get_profile_picture(html):
    return html.json()["graphql"]["user"]["profile_pic_url"]

def get_total_photos(html):
    return int(html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["count"])

def get_last_publication_url(html):
    return html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["shortcode"]

def get_last_photo_url(html):
    return html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["display_url"]

def get_last_thumb_url(html):
    return html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["thumbnail_src"]

def get_description_photo(html):
    if html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["edge_media_to_caption"]["edges"]:
        return html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
    else:
        return ""

def webhook(webhook_url, html):
    # for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
    # for all params, see https://discordapp.com/developers/docs/resources/channel#embed-object
    data = {
        # "content" : "https://instagram.com/p/+get_last_publication_url(html)",
        "username" : get_user_fullname(html),
        "avatar_url" : get_profile_picture(html)
    }
    data["embeds"] = []
    embed = {}
    embed["color"] = 13500529
    embed["title"] = "New Post from @"+INSTAGRAM_USERNAME+""
    embed["url"] = "https://www.instagram.com/p/" + \
        get_last_publication_url(html)+"/"
    embed["description"] = get_description_photo(html)
    embed["image"] = {"url":get_last_thumb_url(html)} # uncomment to post bigger image
    # embed["thumbnail"] = {"url": get_last_thumb_url(html)} # uncomment to add smaller image
    data["embeds"].append(embed)
    result = requests.post(webhook_url, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Image successfully posted in Discord, code {}.".format(
            result.status_code))

def webhookRewrite(webhook_url, html):
    webhook = DiscordWebhook(url=webhook_url, username=get_user_fullname(html), avatar_url=get_profile_picture(html))
    number_of_embed = 0
    Role_ID = os.environ.get("ROLE_ID", "no role_id in the .env")
    nodes = html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
    for node in nodes: # check from bottom
        if node["node"]["shortcode"] == os.environ["LAST_IMAGE_ID"]: # if looped until last image, check embed then post
            break
        embed = DiscordEmbed(title="New Post from @" + INSTAGRAM_USERNAME, 
                            url="https://www.instagram.com/p/" + node["node"]["shortcode"] + "/", 
                            color="CE0071")
        embed.set_image(url=node["node"]["thumbnail_src"]) # uncomment to post bigger image
        # embed.set_thumbnail(url=node["node"]["thumbnail_src"]) # uncomment to add smaller image
        if node["node"]["edge_media_to_caption"]["edges"]:
            desc = node["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
            if 'bit.ly/' in desc:
                desc = desc.replace('bit.ly/', ' https://bit.ly/')
            if 's.id/' in desc:
                desc = desc.replace('s.id/', ' https://s.id/')
            if 'forms.gle/' in desc:
                desc = desc.replace('forms.gle/', ' https://forms.gle/')
            if 'https://' in desc:
                webhook.set_content("<@&"+Role_ID+">")
            embed.set_description(desc)

        webhook.add_embed(embed) # add embed to webhook
        number_of_embed += 1
        if number_of_embed == 5: # if embed maxed (5), then post the webhook
            webhook.execute()
            webhook = DiscordWebhook(url=webhook_url, username=get_user_fullname(html), avatar_url=get_profile_picture(html))
            number_of_embed = 0
            time.sleep(1) # to prevent Discord webhook rate limiting

    if number_of_embed != 0: # if theres some data that isnt posted yet, then post
        webhook.execute()

# i decided to use DiscordWebhook library
# def webhookRewrite2(webhook_url, html): 
#     data = {
#         # "content" : "https://instagram.com/p/+get_last_publication_url(html)",
#         "username" : get_user_fullname(html),
#         "avatar_url" : get_profile_picture(html)
#     }
#     data["embeds"] = []
#     embed = {}
#     index = 0
#     nodes = html.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
#     for node in nodes: # check from bottom
#         embed["color"] = 13500529
#         embed["title"] = "New Post from @" + INSTAGRAM_USERNAME
#         embed["url"]   = "https://www.instagram.com/p/" + node["node"]["shortcode"] + "/"
#         if node["node"]["edge_media_to_caption"]["edges"]:
#             embed["description"] = node["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
#         else:
#             embed["description"] = ""
#         embed["image"] = {"url":node["node"]["thumbnail_src"]}
#         data["embeds"].append(embed)
#         if (index + 1) % 5 == 0:
#             result = requests.post(webhook_url, json=data)
#             data["embeds"] = []
#             embed = {}
#             try:
#                 result.raise_for_status()
#             except requests.exceptions.HTTPError as err:
#                 print(err)
#             else:
#                 print("Image successfully posted in Discord, code {}.".format(
#                     result.status_code))
#         if node["node"]["shortcode"] == os.environ["LAST_IMAGE_ID"] and index != 0: # if looped until last image, check embed then post
#             if (index + 1) % 5 != 0:
#                 result = requests.post(webhook_url, json=data)
#                 try:
#                     result.raise_for_status()
#                 except requests.exceptions.HTTPError as err:
#                     print(err)
#                 else:
#                     print("Image successfully posted in Discord, code {}.".format(
#                         result.status_code))
#             break
#         index += 1

def get_instagram_html(INSTAGRAM_USERNAME):
    headers = {
        "Host": "www.instagram.com",
        "User-Agent": random.choice(USER_AGENT)
    }
    html = requests.get("https://www.instagram.com/" +
                        INSTAGRAM_USERNAME + "/feed/?__a=1", headers=headers)
    return html


def main():
    try:
        html = get_instagram_html(INSTAGRAM_USERNAME)
        if(os.environ.get("LAST_IMAGE_ID") == get_last_publication_url(html)):
            print("No new image to post in discord.")
        else:
            print("New image to post in discord.")
            webhookRewrite(os.environ.get("WEBHOOK_URL"),
                    html) # just 1x request
            os.environ["LAST_IMAGE_ID"] = get_last_publication_url(html)
            dotenv.set_key(dotenv_file, "LAST_IMAGE_ID", os.environ["LAST_IMAGE_ID"]) # save to .env
    except Exception as e:
        print(e)


if __name__ == "__main__":
    if os.environ.get('IG_USERNAME') != None and os.environ.get('WEBHOOK_URL') != None:
        while True:
            main()
            time.sleep(float(os.environ.get('TIME_INTERVAL') or 600)) # 600 = 10 minutes
    else:
        print('Please configure environment variables properly!')
