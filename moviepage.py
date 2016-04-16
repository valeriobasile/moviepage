#!/usr/bin/env python

import imdb
import re
from os import listdir
from os.path import isfile, join
import logging as log

ia = imdb.IMDb()

file_ext = 'avi|divx|mkv|mpg|mp4|wmv|bin|ogm|vob|iso|img|bin|ts|rmvb|3gp|asf|flv|mov|movx|mpe|mpeg|mpg|mpv|ogg|ram|rm|wm|wmx|x264|xvid|dv'
purge_words = 'divx|dvdscr|aac|dvdrip|brrip|UNRATED|WEBSCR|KLAXXON|xvid|r5|com--scOrp|300mbunited|1channel|3channel|bray|blueray|5channel|1GB|1080p|720p|480p|CD1|CD2|CD3|CD4|x264|x264-sUN|Special Edition|Sample|sample'

def normalize_filename(movie_filename):
    file_ext_expr = "(?P<name>.*)\.({0})".format(file_ext)
    movie_filename = re.match(file_ext_expr, movie_filename, re.I).group("name")

    purge_words_list = "(?i)({0})(.*)$".format(purge_words)
    purge_digit = "(\d{4})(.*)$"
    purge_spl_chars = "(\[|\()(.*)$"
    purge_dot_underscore = "(\.|_)"
    purge_hypen_aps = "(\-|')"

    re_str = re.sub(purge_spl_chars, "", movie_filename, )
    re_str = re.sub(purge_words_list, "", re_str, re.I)
    re_str = re.sub(purge_digit, "", re_str, )
    re_str = re.sub(purge_dot_underscore, " ", re_str, )
    re_str = re.sub(purge_hypen_aps, "", re_str, )

    return re_str.rstrip().lstrip()

def get_movie_info(filename):
    filename_normalized = normalize_filename(filename)

    # search IMDB
    result = ia.search_movie(filename_normalized)

    # select the first retrieved movie
    try:
        movie = result[0]
    except:
        log.error('No movie found for file {0}'.format(filename))
        return None

    # retrieve information
    ia.update(movie)

    title = movie['title']
    year = movie['year']
    director = movie['director'][0]['name']
    try:
        plot = movie['plot outline']
    except:
        try:
            plot = movie['plot']
        except:
            plot = 'No plot available.'
    rating = movie['rating']
    return "{0} (by {2}, {1})\nRating: {4}\n{3}".format(title, year, director, plot,rating)

moviedir = 'movies'
moviefiles = [f for f in listdir(moviedir) if isfile(join(moviedir, f))]
for moviefile in moviefiles:
    movieinfo = get_movie_info(moviefile)
    if movieinfo:
        print movieinfo
        print
