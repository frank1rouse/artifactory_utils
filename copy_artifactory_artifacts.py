'''
Created on Aug 20, 2014

@author: rousef
'''
import sys, os, datetime, time, artifactory

def print_help():
    print 'Used to copy artifacts to a new repository'
    print ''
    print 'Usage: copy_artifactory_artifacts.py <artifact names file> <target repository> <userid> <password>'
    print ''
    print 'Artifact names file will be a single column of artifacts with version number.'
    print 'Example line entry "amqp-client-2.8.4.jar"'
    print ''
    print 'The target repository will be a pre-exisitng repository defined in the'
    print 'repository site below'
    print artifactory.REPOSITORY_URL
    print ''
    print 'The repository site will be searched for the artifact and if found it will be'
    print 'copied to the given repository. It will remain in the original repository.'
    sys.exit()

##########################################
# Ensure that enough arguments were passed
##########################################
if len(sys.argv) < 5:
    print 'Not enough arguments supplied'
    print ''
    print_help()

###########################
## Validate first parameter
###########################

# Ensure that the first parameter is a valid readable file
artifact_names_file = sys.argv[1]
# if not os.access(artifact_names_file, os.F_OK):
#     print 'Cannot find the file "' + artifact_names_file + '"'
#     print ''
#     print_help()

# os.access for testing the readability of files does not work beyond simple POSIX authentication
# Just attempt to read the file and catch the exception if unreadable.
try:
    artifact_names_file_descriptor=open(artifact_names_file, 'r')
except IOError, e:
    print 'Unable to read the file "' + artifact_names_file + '".'
    print ''
    print e.errno
    print ''
    print e
    print_help()

############################
## Validate second parameter
############################
target_repository = sys.argv[2]
# Ensure that the target repository given exists
if not artifactory.repository_exists(target_repository):
    print ''
    print 'Repository "' + target_repository + '" does not exist in repository "' + artifactory.REPOSITORY_URL + '".'
    print_help()

############################
## Assign username/password from parameters
############################
artifactory.ARTIFACTORY_USERID   = sys.argv[3]
artifactory.ARTIFACTORY_PASSWORD = sys.argv[4]

#########################################################
## Create log file with name of executable and time stamp
#########################################################
TIME_STAMP = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H_%M_%S')
log_file_name = sys.argv[0].rpartition('.')[0] + '_' + TIME_STAMP + '.log'
# Ensure that the log file can be created
try:
    artifactory.LOG=open(log_file_name, 'w')
except IOError, e:
    print ''
    print 'Unable to create the file "' + log_file_name + '".'
    print e.errno
    print ''
    print e
    sys.exit()

'''
Additional services to consider.
1. Info in report to detail where the artifact currently resides in the entire repository
2. Additional error message when the artifact exists in the target repository @ another release.
3. Create a command line policy that will allow the software to only have a single version of the software
   in a repository at a time.
4. Ensure when upgrading the version of an artifact you only upgrade a minor version.
5. Error message and log when a major update to an already installed artifact is detected
'''

############################################################################
# Loop through the artifacts in the file and copy into the target repository
############################################################################
with open(artifact_names_file, 'r') as artifact_names:
    for artifact_name in artifact_names:
        artifact_name = artifact_name.rstrip()
        artifactory.log('-------------------------------------------')
        artifactory.log('Processing artifact "' + artifact_name +'".')
        artifact = artifactory.Artifact(artifact_name)
        if not artifact.discover_repositories():
            artifactory.log('Skipping...')
        elif len(artifact.repositories) == 0:
            artifactory.log('Artifact "' + artifact_name + '" not found in any local repositories.')
            artifactory.log('Skipping...')
        else:
            artifact_already_in_target_repo = ''
            for search_repository in artifact.repositories:
                if search_repository == target_repository:
                    artifactory.log('Artifact "'+  artifact_name + '" is already in repository "' + target_repository + '"')
                    artifact_already_in_target_repo = 'true'
                    break
            if not artifact_already_in_target_repo:
                if not artifact.gav:
                    if not artifact.discover_gav():
                        artifactory.log('No GAV information')
                        artifactory.log('Skipping...')
                if artifact.gav:
                    source = artifact.repositories[0] +'/' + artifact.gav +'/' + artifact.artifact
                    target = '/' + target_repository + '/' + artifact.gav + '/' + artifact.artifact
                    artifactory.copy_artifact(source, target)
                    artifactory.log('Successfully copied "' + artifact.artifact + '" artifact from "' + artifact.repositories[0] + '" to "' + target_repository + '".')
                    # If the artifact type is jar go ahead and copy the corresponding pom file.
                    if artifact.type == 'jar':
                        pom = artifact.short_name + '-' + artifact.version + '.pom'
                        source = artifact.repositories[0] +'/' + artifact.gav +'/' + pom
                        target = '/' + target_repository + '/' + artifact.gav + '/' + pom
                        artifactory.copy_artifact(source, target)
                        artifactory.log('Successfully copied "' + pom + '" artifact from "' + artifact.repositories[0] + '" to "' + target_repository + '".')
sys.exit();