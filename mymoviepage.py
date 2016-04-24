#!/usr/bin/env python

import imdb
import re
from os import listdir, access, W_OK
from os.path import isfile, isdir, dirname, abspath, join, getmtime
import logging as log
from optparse import OptionParser
from sys import exit

# globals
ia = imdb.IMDb()
file_ext = 'avi|divx|mkv|mpg|mp4|wmv|bin|ogm|vob|iso|img|bin|ts|rmvb|3gp|asf|flv|mov|movx|mpe|mpeg|mpg|mpv|ogg|ram|rm|wm|wmx|x264|xvid|dv|m4v'
purge_words = 'divx|dvdscr|aac|dvdrip|brrip|UNRATED|WEBSCR|KLAXXON|xvid|r5|com--scOrp|300mbunited|1channel|3channel|bray|blueray|5channel|1GB|1080p|720p|480p|CD1|CD2|CD3|CD4|x264|x264-sUN|Special Edition|Sample|sample'

def normalize_filename(movie_filename):
    file_ext_expr = "(?P<name>.*)\.({0})".format(file_ext)
    match = re.match(file_ext_expr, movie_filename, re.I)
    if not match:
        log.error('Cannot process filename {0}'.format(movie_filename))
        return None
    movie_filename = match.group('name')

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
    if not(filename_normalized):
        log.error('Could not normalize filename {0}'.format(filename))
        return None

    # search IMDB
    result = ia.search_movie(filename_normalized)

    # select the first retrieved movie
    try:
        movie = result[0]
    except:
        log.error('No movie found for file {0}'.format(filename))
        return None

    # retrieve information
    try:
        ia.update(movie)
    except:
        log.error('Error contacting IMDB API')
        return None

    title = movie['title']
    year = movie['year']
    directors = map(lambda x: {'id': x.personID, 'name': unicode(x['name'])}, movie['director'])
    cast = map(lambda x: {'id': x.personID, 'name': unicode(x['name'])}, movie['cast'])
    try:
        plot = movie['plot outline']
    except:
        try:
            plot = movie['plot']
        except:
            plot = 'No plot available.'
    rating = movie['rating']
    genre = ', '.join(movie['genre'])
    movieID = movie.movieID

    return {'title': title,
            'directors': directors,
            'cast': cast,
            'plot': plot,
            'year': year,
            'genre': genre,
            'rating': rating,
            'movieID':movieID}

def writehtmlheader(pagefile):
    with open(pagefile, 'w') as f:
        f.write(u"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <link rel="stylesheet" type="text/css" href="mymoviepage.css" />
        <link href='https://fonts.googleapis.com/css?family=Oxygen' rel='stylesheet' type='text/css' />
        <link href='https://fonts.googleapis.com/css?family=Arvo' rel='stylesheet' type='text/css' />
        <meta http-equiv="content-type" content="text/php; charset=utf-8" />
        <title>MyMoviePage</title>
    </head>
    <body>""".encode('utf-8'))

def writehtmlfooter(pagefile):
    with open(pagefile, 'a') as f:
        f.write(u'</body>\n</html>\n'.encode('utf-8'))

def personlink(person):
    return u'<a href="http://www.imdb.com/name/nm{0}">{1}</a>'.format(person['id'], person['name'])

def writehtmlentry(pagefile, movieinfo):
    with open(pagefile, 'a') as f:
        f.write(u'<div class="movie">\n')
        f.write(u'<h1><a href="http://www.imdb.com/title/tt{0}">{1}</a></h1>\n'.format(movieinfo['movieID'], movieinfo['title']).encode('utf-8'))
        f.write(u'<h2>by {0} ({1})</h2>\n'.format(u', '.join(map(personlink, movieinfo['directors'])), movieinfo['year']).encode('utf-8'))
        f.write(u'<span class="genre">{0}</span>\n'.format(movieinfo['genre']).encode('utf-8'))
        f.write(u'<span class="plot">{0}</span>\n'.format(movieinfo['plot']).encode('utf-8'))
        f.write(u'<span class="cast">With {0}.</span>\n'.format(u', '.join(map(personlink, movieinfo['cast'][:4]))).encode('utf-8'))
        f.write(u'<span class="rating">IMDB Rating: {0}</span>\n'.format(movieinfo['rating']))
        #f.write(u'<pre>{0}, {1}</pre>\n'.format(movieinfo['movieID'], movieinfo['directorID']))
        f.write(u'</div>\n')

def writehtmlpage(moviefiles, pagefile):
    writehtmlheader(pagefile)
    for moviefile in moviefiles:
        log.info('Getting info for movie {0}'.format(moviefile))
        movieinfo = get_movie_info(moviefile)
        if movieinfo:
            writehtmlentry(pagefile, movieinfo)
    writehtmlfooter(pagefile)

# main
# parse command line options
parser = OptionParser()
parser.add_option('-d',
                  '--moviedir',
                  dest='moviedir',
                  help='Movie file directory. Default: .',
                  default='.')
parser.add_option('-p',
                  '--pagefile',
                  dest='pagefile',
                  help='HTML output file. Default: mymoviepage.html',
                  default='mymoviepage.html')
parser.add_option('-l',
                  '--logfile',
                  dest='logfile',
                  help='log file. Default: mymoviepage.log',
                  default='mymoviepage.log')
parser.add_option('-f',
                  '--force',
                  dest='force',
                  action='store_true',
                  help='Generate HTML regardless of timestampsself.',
                  default=False)

(options, args) = parser.parse_args()

if not isdir(options.moviedir):
    log.error('{0} is not a valid directory, exiting.'.format(options.moviedir))
    exit(1)
if not access(dirname(abspath(options.pagefile)), W_OK):
    log.error('{0} is not writable, exiting.'.format(dirname(options.pagefile)))
    exit(1)
if not access(dirname(abspath(options.logfile)), W_OK):
    log.error('{0} is not writable, exiting.'.format(dirname(options.logfile)))
    exit(1)

log.basicConfig(filename=options.logfile, level=log.INFO)

# read movie file listdir
log.info('Reading file list from directory {0}'.format(options.moviedir))
moviefiles = [f for f in listdir(options.moviedir) if isfile(join(options.moviedir, f))]

# check if there are new movie files
try:
    last_update_movies = max(map(lambda x: getmtime(join(options.moviedir, x)), moviefiles))
except:
    last_update_movies = 0

try:
    last_update_pagefile = getmtime(options.pagefile)
except:
    # HTML file does not exist or it is not writeable
    last_update_pagefile = 0

if last_update_movies > last_update_pagefile or options.force:
    log.info('Found new movies in directory {0}'.format(options.moviedir))
    writehtmlpage(moviefiles, options.pagefile)
else:
    log.info('No movie found newer than the last update, nothing to do.')
