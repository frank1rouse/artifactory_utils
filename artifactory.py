'''
Created on Aug 20, 2014

@author: rousef
'''
import json, requests, re

'''
   Globals
'''
# Used in the "log" function to hold a file descriptor
# Must be instantiated prior to use.
LOG                      = ''

ARTIFACTORY_USERID       = ''
ARTIFACTORY_PASSWORD     = ''

REPOSITORY_URL           = 'http://repo.vmo.lab:8080/artifactory'
ARTIFACTORY_COPY_URL     = REPOSITORY_URL + '/api/copy/'
ARTIFACTORY_STORAGE_URL  = REPOSITORY_URL + '/api/storage/'
ARTIFACTORY_SEARCH_URL   = REPOSITORY_URL + '/api/search/artifact?name='

SUPPORTED_ARTIFACT_TYPES = ['jar', 'pom', 'tgz']
ARTIFACT_TYPES           = ['jar', 'pom', 'tgz', 'rpm', 'xml']

# Create an Artifact class essentially as a data structure with a few common methods
class Artifact:
    '''
    gav            - Group/Artifact/Version name with no slashes at either beginning or end
    artifact       - Full artifact name with version and type
    version        - Version can contain alpha-numerics
                     Not supported for all artifact types.
    type           - Only support the ARTIFACT_TYPES listed above
    repositories[] - List of all the repositories that the artifact resides
    short_name     - Name only without version or type information
    '''
    gav          = ''
    artifact     = ''
    version      = ''
    type         = ''
    repositories = []
    short_name   = ''

    def __init__(self, artifactName='', artifactGroup=''):
        self.gav = ''
        self.artifact = ''
        self.version = ''
        self.type = ''
        self.repositories = []
        self.short_name = ''

        if artifactName:
            # Grab everything after the final '.' character
            artifact_type = artifactName.rpartition('.')[2]

            # This means that we are given the full artifact name with version and type
            if artifact_type in ARTIFACT_TYPES:
                self.artifact   = artifactName
                self.type       = artifact_type
                # We have a shorter list of artifact types for which our version parsing works
                if artifact_type in SUPPORTED_ARTIFACT_TYPES:
                    # The parameter is the artifactName supplied without the '.<artifact_type>'
                    self.__separate_shortname_version(artifactName.rpartition('.')[0])
        # No error checking on this value so ensure it's correct.
        if artifactGroup:
            self.gav = artifactGroup

    # The assumption here is that version is the total string after the first '-<digit>' character sequence
    def __separate_shortname_version(self, artifactNameVersion):
        partitionedArtifactNameVersion = artifactNameVersion.partition('-')
        # Grab the first character string before the first dash '-'
        self.short_name = partitionedArtifactNameVersion[0]
        # The remaining string after the characters up to the first dash '-' are removed
        self.version = partitionedArtifactNameVersion[2]
        # Regular expression to find the first character as a digit
        firstCharIsDigit = re.compile('[0-9]+.*')
        # Version string must start with a digit
        while not firstCharIsDigit.match(self.version):
            # If the version string did not start with a digit we must divide the remaining version string at the dash '-'
            partitionedVersion = self.version.partition('-')

            # If the string can no longer be divided by a dash before we find a number it means that no version information is included with this jar
            if not partitionedVersion[0]:
                break

            # Add the next dash '-' sequence to the short_name variable
            self.short_name = self.short_name + '-' + partitionedVersion[0]
            # Once again the version is what is left of the string after the next dash '-' partition
            self.version = partitionedVersion[2]

    def discover_repositories(self):
        # Without full artifact name we may end up with false positives like ant vs ant-launcher and antlr
        if not self.artifact:
            log('Unable to determine repositories without full artifact name')
            return 0
        repository_data = json.loads(requests.get(url=ARTIFACTORY_SEARCH_URL + self.artifact).text)
        for item in repository_data['results']:
            full_repository_url = item['uri']
            repository = full_repository_url.partition(ARTIFACTORY_STORAGE_URL)[2].partition('/')[0]
            self.repositories.append(repository)
        return 1

    def discover_gav(self):
        # Without full artifact name we may end up with false positives like ant vs ant-launcher and antlr
        if not self.artifact:
            log('Unable to determine GAV without full artifact name')
            return 0
        repository_data = json.loads(requests.get(url=ARTIFACTORY_SEARCH_URL + self.artifact).text)
        for item in repository_data['results']:
            full_repository_url = item['uri']
            self.gav = full_repository_url.partition(ARTIFACTORY_STORAGE_URL)[2].partition('/')[2].partition('/' + self.artifact)[0]
            break
        return 1

###################################
# Log output to screen and log file
###################################
def log(msg):
    print msg
    LOG.write(msg+'\n')
    LOG.flush()

##############################################################################
# Copy the source path to the target repository. 
# Check the return message and fail if "successfully" is not found.
##############################################################################
def copy_artifact(source, target):
    post_return_code = json.loads(requests.post(ARTIFACTORY_COPY_URL + source,
                                                auth=(ARTIFACTORY_USERID, ARTIFACTORY_PASSWORD),
                                                params={'to': target}
                                                ).text)
    if not post_return_code.get('messages')[0].get('message').__contains__('successfully'):
        log('Failed to copy the following')
        log('Source             = "' + source + '"')
        log('Target Repository = "' + target + '"')
        return 0
    return 1

##############################################################################
# Test the ARTIFACTORY_STORAGE_URL with the given repository.
# If the return message contains the word "errors" return 0 otherwise return 1
##############################################################################
def repository_exists(repository):
    if json.loads(requests.get(url=ARTIFACTORY_STORAGE_URL + repository).text).__contains__('errors'):
        return 0
    return 1
