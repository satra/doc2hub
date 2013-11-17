# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Config options needed are:

gmail_username
gmail_password
github_username
github_password

store in json file

google_doc url

author mapping between google and github
"""

import os
import re
import json
import zipfile
import subprocess

import sh

import gdata.docs.data
import gdata.docs.client


class Converter(object):

    def __init__(self, authconfig_file):
        with open(authconfig_file, 'rt') as fp:
            config = json.load(fp)
        if config is None:
            raise ValueError('Config is empty')
        self._config = config
        self._client = gdata.docs.client.DocsClient(source='Doc2Hub')
        self._client.ssl = True  # Force all API requests through HTTPS
        self._client.http_client.debug = False  # True for HTTP debugging
        self._client.ClientLogin(config['gmail_username'],
                                 config['gmail_password'],
                                 self._client.source)
        self.pandoc = sh.pandoc.bake()
        self.git = sh.git.bake()
        self._format_ext = dict(rst='rst',
                                markdown='md',
                                markdown_github='md')
        self.ext = None

    def get_user_input(self, prompt):
        print prompt

    def print_feed(self, regexp=None):
        feed = self._client.GetDocList()
        print '\n'
        if not feed.entry:
            print 'No entries in feed.\n'
        for entry in feed.entry:
            name = entry.title.text.encode('UTF-8')
            if re.match(regexp, name):
                print entry.title.text.encode('UTF-8'),\
                    entry.GetDocumentType(), \
                    entry.resource_id.text
                # List folders the document is in.
                for folder in entry.InFolders():
                    print folder.title

    def get_entry(self, docname):
        # Create a query matching exactly a title, and include collections
        query = gdata.docs.client.DocsQuery(title=docname,
                                            title_exact='true',
                                            show_collections='true')

        feed = self._client.GetResources(q=query)
        if not feed.entry:
            raise ValueError('No entries in feed.')
        return feed.entry

    def get_revisions(self, entry):
        return self._client.GetRevisions(entry)

    def convert(self, docname, dirname, author_map, file_format='rst'):
        try:
            self.ext = self._format_ext[file_format]
        except KeyError:
            print "Error: Please specify 'rst' or 'markdown' for file_format"

        entry = self.get_entry(docname)

        if len(entry) == 1:
            entry = entry[0]
        else:
            raise ValueError('multiple entries for %s' % docname)
        pwd = os.getcwd()
        starting_revision = -1
        if os.path.exists(dirname):
            os.chdir(dirname)
            proc = subprocess.Popen('git log HEAD^..HEAD',
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            o, e = proc.communicate()
            if 'revision:' in o:
                rev_split = o.split('revision:')
                starting_revision = int(rev_split[-1].replace('\"', ''))
        else:
            os.mkdir(dirname)
            os.chdir(dirname)
            self.git.init()
        revision_feed = self._client.get_revisions(entry)
        for rev in revision_feed.entry:
            revision_number = int(rev.id.text.split('/')[-1])
            if revision_number <= starting_revision:
                continue
            email = rev.author[0].email.text
            if email in author_map:
                name = author_map[email]
            else:
                name = email
            date = rev.updated.text
            self._client.download_archive(rev,
                                          '/tmp/%s.zip' % docname,
                                          {'exportFormat': 'zip'})
            os.system('rm -rf images')
            zipfile.ZipFile('/tmp/%s.zip' % docname).extractall(path='/tmp')
            docname_fmt = docname.replace('-', '')
            os.rename('/tmp/%s.html' % docname_fmt, '/tmp/%s.html' % docname)

            self.pandoc("/tmp/%s.html" % docname,
                        f='html',
                        t=file_format,
                        o='%s%s.%s' % (dirname, docname, self.ext))

            if os.path.exists('images'):
                self.git.add("%s.%s images/*.png" % (docname, self.ext))
            else:
                self.git.add("%s.%s" % (docname, self.ext))
            #commit_str = '--date=%s --author="%s <%s>" -m "revision: %d"'
            self.git.commit("%s.%s" % (docname, self.ext),
                            date=date,
                            author="\"%s <%s>\"" % (name, email),
                            m="\"revision: %d\"" % revision_number)
            #os.system('git commit --date=%s --author="%s <%s>" -m
            # "revision: %d"'%(date, name, email, revision_number))
            print revision_number > starting_revision
            if revision_number > starting_revision:
                os.system('git push origin master')
                #self.git.push('origin',
                #              'master',
                #              _in=[self._config['github_username'],
                #                   self._config['github_password']],
                #              _out=self.get_user_input)
            print "finished converting revision: %d" % revision_number
        os.chdir(pwd)
