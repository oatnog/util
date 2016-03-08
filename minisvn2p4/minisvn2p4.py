#!/usr/bin/env python
#
# (c) 2010 Allan Anderson
#
# quick and dirty subversion to perforce importer
#
# requires pysvn (http://pysvn.tigris.org/) and P4Python
# 

import pysvn
from P4 import P4,P4Exception
from shutil import copyfile, copytree, ignore_patterns, move, rmtree
from datetime import datetime
import os
import logging
import logging.config
from itertools import izip, tee

# Set the following variables to match your environment
#
# SVN working directory 
svn_path = '/home/a/Source/svnproject/trunk'
# P4 workspace root
p4client_path = '/home/a/Source/p4root'

# first revision we care about importing
START_REVISION = 1
REVISON_FILE = './completed_revision'

# Connect to Perforce
# must create the clientspec ahead of time
p4 = P4()
p4.port = "localhost:1666"
p4.user = "allan_anderson"
p4.client = "importworkspace"

# No need to edit below this line

try:
    p4.connect()
except P4Exception:
    for e in p4.errors:
        print e
    sys.exit(1)

logging.config.fileConfig("svn2pylogging.conf")
logger = logging.getLogger("svn2p4")

# snagged from the itertools recipes page
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


svn = pysvn.Client()

first_revision = pysvn.Revision(pysvn.opt_revision_kind.number,START_REVISION)
if not os.path.exists(REVISON_FILE):

    working_revision = svn.update(svn_path,revision=first_revision)

    # initial copy and add
    if os.path.exists(p4client_path):
        #p4.run('revert',p4client_path)
        rmtree(p4client_path)

    copytree(svn_path,p4client_path, ignore=ignore_patterns('.svn*'))
    
    
    for root, dirs, files in os.walk(p4client_path):
        if files:
            try:
                p4.run('add', [os.path.join(root,name) for name in files])
            except P4Exception:
                for e in p4.errors:
                    logger.error(e)
            
    svn_log = \
                 svn.log( svn_path,
                           revision_start=first_revision,
                           revision_end=first_revision,)
    
    
    change_description = 'Revision: ' + str(working_revision[0].number) + \
                       '\t\tDate: ' + datetime.fromtimestamp(svn_log[0].data['date']).isoformat() + \
                       '\nAuthor: ' + svn_log[0].data['author'] + \
                       '\nMessage: ' + svn_log[0].data['message']
    
    p4.run_submit('-d',change_description)
    logger.info("Submitted first Perforce change, Svn Rev " + str(working_revision[0].number) + \
                " by "+ svn_log[0].data['author'])

else:
    with open(REVISON_FILE) as revision_file:
        for last_completed_revision in revision_file:
            first_revision = pysvn.Revision(pysvn.opt_revision_kind.number,last_completed_revision)
    
# Move on to the rest of the changes

head_revision = pysvn.Revision(pysvn.opt_revision_kind.head)

svn_log = \
             svn.log( svn_path,
                       revision_start=first_revision,
                       revision_end=head_revision,)

# list of pysvn Revision objects in the svn directory to be imported
dm_revisions = [ log.data['revision'] for log in svn_log ]



# loop over the revisions and compare them like this: 1vs2, 2vs3, 3vs4...
for previous_rev, current_rev in pairwise(dm_revisions):
    # find which files have changed between the last revision
    # and the one we are importing
    summary = \
            svn.diff_summarize( svn_path,
                              revision1=previous_rev,
                              revision2=current_rev)
    
    # extract lists of the added, modified, and deleted files (not dirs)
    svn_added = [ diff.data['path'] for diff in summary 
                  if diff.data['summarize_kind']==pysvn.diff_summarize_kind.added
                  and diff.data['node_kind']==pysvn.node_kind.file]
    svn_modified = [ diff.data['path'] for diff in summary 
                     if diff.data['summarize_kind']==pysvn.diff_summarize_kind.modified
                     and diff.data['node_kind']==pysvn.node_kind.file]
    svn_delete = [ diff.data['path'] for diff in summary 
                   if diff.data['summarize_kind']==pysvn.diff_summarize_kind.delete
                   and diff.data['node_kind']==pysvn.node_kind.file]

    # Update the local SVN working directory to the next revision
    # so we can start copying over the files to the p4 workspace
    working_revision = svn.update(svn_path,revision=current_rev)
    
    # Apply the Svn file changes to the P4 workspace
    for deleted_file in svn_delete:
        p4_deleted_file = os.path.join(p4client_path, deleted_file)
        try:
            p4.run('delete', p4_deleted_file)
        except P4Exception:
            for e in p4.errors:
                logger.error(e)
    
    for added_file in svn_added:
        p4_added_file = os.path.join(p4client_path, added_file)
        if not os.path.exists(os.path.dirname(p4_added_file)):
            os.makedirs(os.path.dirname(p4_added_file))
        copyfile(os.path.join(svn_path, added_file), p4_added_file)
        try:
            p4.run('add', p4_added_file)
        except P4Exception:
            for e in p4.errors:
                logger.error(e)

    for edited_file in svn_modified:
        p4_edited_file = os.path.join(p4client_path, edited_file)
        if not os.path.exists(os.path.dirname(p4_edited_file)):
            os.makedirs(os.path.dirname(p4_edited_file))
        try:
            p4.run('edit', p4_edited_file)
        except P4Exception:
            for e in p4.errors:
                logger.error(e)
            p4.run('add', p4_edited_file) # should never have to do this
        copyfile(os.path.join(svn_path, edited_file), p4_edited_file)
    
    # Now that we've deleted, added, and edited all files changed in this revision,
    # get the log info and submit    
    svn_log = \
            svn.log( svn_path,
                     revision_start=current_rev,
                     revision_end=current_rev,)



    change_description = 'Revision: ' + str(current_rev.number) + \
                       '\t\tDate: ' + datetime.fromtimestamp(svn_log[0].data['date']).isoformat() + \
                       '\nAuthor: ' + svn_log[0].data['author'] + \
                       '\nMessage: ' + svn_log[0].data['message']

    
    try:
        p4.run_submit('-d',change_description)
    except P4Exception:
        for e in p4.errors:
            logger.error(e)
                      
    logger.info("Submitted Perforce change for Svn Rev " + str(current_rev.number) + \
                " by " + svn_log[0].data['author'])
    # keep track of last imported revision so we can restart the import
    rev_file = open(REVISON_FILE,'w')
    rev_file.write(str(current_rev.number))
    rev_file.close()

logger.info("Import complete!")    
