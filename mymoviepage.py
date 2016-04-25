#!/usr/bin/env python

import imdb
import re
from os import listdir, access, W_OK
from os.path import isfile, isdir, dirname, abspath, join, getmtime
import logging as log
from optparse import OptionParser
from sys import exit
import shutil

# globals
ia = imdb.IMDb()
file_ext = 'avi|divx|mkv|mpg|mp4|wmv|bin|ogm|vob|iso|img|bin|ts|rmvb|3gp|asf|flv|mov|movx|mpe|mpeg|mpg|mpv|ogg|ram|rm|wm|wmx|x264|xvid|dv|m4v'
purge_words = 'divx|dvdscr|aac|dvdrip|brrip|UNRATED|WEBSCR|KLAXXON|xvid|r5|com--scOrp|300mbunited|1channel|3channel|bray|blueray|5channel|1GB|1080p|720p|480p|CD1|CD2|CD3|CD4|x264|x264-sUN|Special Edition|Sample|sample'
CSS_FILE = 'mymoviepage.css'
JS_FILE = 'list.js'
NOIMG = 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/IMDb_logo.svg/200px-IMDb_logo.svg.png'

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
    try:
        year = movie['year']
    except:
        year = '-'
    try:
        directors = map(lambda x: {'id': x.personID, 'name': unicode(x['name'])}, movie['director'])
    except:
        directors = []
    try:
        cast = map(lambda x: {'id': x.personID, 'name': unicode(x['name'])}, movie['cast'])
    except:
        cast = []
    try:
        plot = movie['plot outline']
    except:
        try:
            plot = movie['plot']
        except:
            plot = 'No plot available.'
    try:
        rating = movie['rating']
    except:
        rating = 'No rating found.'
    try:
        genre = ', '.join(movie['genre'])
    except:
        genre = ''
    movieID = movie.movieID
    try:
        cover = movie['cover url']
    except:
        cover = NOIMG

    return {'title': title,
            'directors': directors,
            'cast': cast,
            'plot': plot,
            'year': year,
            'genre': genre,
            'rating': rating,
            'movieID':movieID,
            'cover':cover,
            }

def writehtmlheader(pagefile):
    with open(pagefile, 'w') as f:
        f.write(u"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <link rel="stylesheet" type="text/css" href="{0}" />
        <link href='https://fonts.googleapis.com/css?family=Oxygen' rel='stylesheet' type='text/css' />
        <link href='https://fonts.googleapis.com/css?family=Arvo' rel='stylesheet' type='text/css' />
        <meta http-equiv="content-type" content="text/php; charset=utf-8" />
        <title>MyMoviePage</title>
    </head>
    <body>
        <div id="movies">
        <div id="controls">
          <input class="search" placeholder="Search" />
          <button class="sort" data-sort="title">Sort by title</button>
          <button class="sort" data-sort="genre">Sort by genre</button>
          <button class="sort" data-sort="year">Sort by year</button>
          <button class="sort" data-sort="rating">Sort by rating</button>
        </div>
          <ul class="list">""".format(CSS_FILE).encode('utf-8'))

def writehtmlfooter(pagefile):
    with open(pagefile, 'a') as f:
        f.write(u"""</ul>
    </div>
    <script src="{0}"></script>
    </body>
</html>""".format(JS_FILE).encode('utf-8'))

def personlink(person):
    try:
        link =  u'<a href="http://www.imdb.com/name/nm{0}">{1}</a>'.format(person['id'], person['name'])
    except:
        link = u'{0}'.format(person['name'])
    return link

def writehtmlentry(pagefile, movieinfo):
    with open(pagefile, 'a') as f:
        f.write(u'<li class="movie">\n')
        f.write(u'<a href="http://www.imdb.com/title/tt{0}"><img class="cover"src="{1}" /></a>\n'.format(movieinfo['movieID'], movieinfo['cover']).encode('utf-8'))
        f.write(u'<h1 class="title"><a href="http://www.imdb.com/title/tt{0}">{1}</a></h1>\n'.format(movieinfo['movieID'], movieinfo['title']).encode('utf-8'))
        if len(movieinfo['directors'])>0:
            f.write(u'<h2>by {0} (<span class="year">{1}</span>)</h2>\n'.format(u', '.join(map(personlink, movieinfo['directors'])), movieinfo['year']).encode('utf-8'))
        f.write(u'<span class="genre">{0}</span>\n'.format(movieinfo['genre']).encode('utf-8'))
        f.write(u'<span class="plot">{0}</span>\n'.format(movieinfo['plot']).encode('utf-8'))
        if len(movieinfo['cast'])>0:
            f.write(u'<span class="cast">With {0}.</span>\n'.format(u', '.join(map(personlink, movieinfo['cast'][:4]))).encode('utf-8'))
        f.write(u'<span class="rating">IMDB Rating: {0}</span>\n'.format(movieinfo['rating']))
        f.write(u'</li>\n')

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

target_dir = dirname(abspath(options.pagefile))
log_dir = dirname(abspath(options.logfile))
if not isdir(options.moviedir):
    log.error('{0} is not a valid directory, exiting.'.format(options.moviedir))
    exit(1)
if not access(target_dir, W_OK):
    log.error('{0} is not writable, exiting.'.format(target_dir))
    exit(1)
if not access(log_dir, W_OK):
    log.error('{0} is not writable, exiting.'.format(log_dir))
    exit(1)

log.basicConfig(filename=options.logfile,
                level=log.INFO,
                format='%(asctime)s %(message)s')

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

# generate HTML file
if last_update_movies > last_update_pagefile or options.force:
    log.info('Found new movies in directory {0}'.format(options.moviedir))
    writehtmlpage(moviefiles, options.pagefile)
else:
    log.info('No movie found newer than the last update, nothing to do.')

# copy static files
for static_file in [CSS_FILE, JS_FILE]:
    try:
        shutil.copy(static_file, target_dir)
    except:
        log.error('Cannot copy style file {0} in {1}'.format(static_file, target_dir))
