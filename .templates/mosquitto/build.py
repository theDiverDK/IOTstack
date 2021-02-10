#!/usr/bin/env python3

issues = {} # Returned issues dict
buildHooks = {} # Options, and others hooks
haltOnErrors = True

# Main wrapper function. Required to make local vars work correctly
def main():
  import os
  import time
  import subprocess
  import shutil
  import sys
  
  from deps.consts import servicesDirectory, templatesDirectory, volumesDirectory
  from deps.common_functions import getExternalPorts, getInternalPorts, checkPortConflicts

  global dockerComposeServicesYaml # The loaded memory YAML of all checked services
  global toRun # Switch for which function to run when executed
  global buildHooks # Where to place the options menu result
  global currentServiceName # Name of the current service
  global issues # Returned issues dict
  global haltOnErrors # Turn on to allow erroring
  global hideHelpText # Showing and hiding the help controls text
  global serviceService

  serviceService = servicesDirectory + currentServiceName
  serviceTemplate = templatesDirectory + currentServiceName
  serviceVolume = volumesDirectory + currentServiceName

  try: # If not already set, then set it.
    hideHelpText = hideHelpText
  except:
    hideHelpText = False

  # documentationHint = 'https://sensorsiot.github.io/IOTstack/Containers/Mosquitto'

  # runtime vars
  portConflicts = []

  # This lets the menu know whether to put " >> Options " or not
  # This function is REQUIRED.
  def checkForOptionsHook():
    try:
      buildHooks["options"] = callable(runOptionsMenu)
    except:
      buildHooks["options"] = False
      return buildHooks
    return buildHooks

  # This function is REQUIRED.
  def checkForPreBuildHook():
    try:
      buildHooks["preBuildHook"] = callable(preBuild)
    except:
      buildHooks["preBuildHook"] = False
      return buildHooks
    return buildHooks

  # This function is REQUIRED.
  def checkForPostBuildHook():
    try:
      buildHooks["postBuildHook"] = callable(postBuild)
    except:
      buildHooks["postBuildHook"] = False
      return buildHooks
    return buildHooks

  # This function is REQUIRED.
  def checkForRunChecksHook():
    try:
      buildHooks["runChecksHook"] = callable(runChecks)
    except:
      buildHooks["runChecksHook"] = False
      return buildHooks
    return buildHooks

  # This service will not check anything unless this is set
  # This function is optional, and will run each time the menu is rendered
  def runChecks():
    checkForIssues()
    return []

  # This function is optional, and will run after the docker-compose.yml file is written to disk.
  def postBuild():
    return True

  # This function is optional, and will run just before the build docker-compose.yml code.
  def preBuild():
    # Setup service directory
    if not os.path.exists(serviceService):
      os.makedirs(serviceService, exist_ok=True)

    # Files copy
    shutil.copy(r'%s/mosquitto.conf' % serviceTemplate, r'%s/mosquitto.conf' % serviceService)
    shutil.copy(r'%s/filter.acl' % serviceTemplate, r'%s/filter.acl' % serviceService)

    # Setup volumes directory
    if not os.path.exists(serviceVolume):
      os.makedirs(serviceVolume, exist_ok=True)

    needPermissionsApplied = False

    if not os.path.exists(serviceVolume + '/data'):
      os.makedirs(serviceVolume + '/data', exist_ok=True)
      needPermissionsApplied = True
    if not os.path.exists(serviceVolume + '/log'):
      os.makedirs(serviceVolume + '/log', exist_ok=True)
      needPermissionsApplied = True
    if not os.path.exists(serviceVolume + '/pwfile'):
      os.makedirs(serviceVolume + '/pwfile', exist_ok=True)
      needPermissionsApplied = True

    # Directory ownership fix:
    if (needPermissionsApplied):
      print("Need to set owner on mosquitto directories with command: chown -R 1883:1883 " + serviceVolume)
      applyOwner = input("Set user 1883 on " + serviceVolume + " (Y/n): ").lower()
      print("")
      if (applyOwner) == '' or (applyOwner) == 'y':
        print("sudo chown -R 1883:1883 " + serviceVolume)
        subprocess.call("sudo chown -R 1883:1883 " + serviceVolume, shell=True)
      else:
        print("Permissions not set")
        time.sleep(1)


    return True

  # #####################################
  # Supporting functions below
  # #####################################

  def checkForIssues():
    envFileIssues = checkEnvFiles()
    if (len(envFileIssues) > 0):
      issues["envFileIssues"] = envFileIssues
    for (index, serviceName) in enumerate(dockerComposeServicesYaml):
      if not currentServiceName == serviceName: # Skip self
        currentServicePorts = getExternalPorts(currentServiceName, dockerComposeServicesYaml)
        portConflicts = checkPortConflicts(serviceName, currentServicePorts, dockerComposeServicesYaml)
        if (len(portConflicts) > 0):
          issues["portConflicts"] = portConflicts

  def checkEnvFiles():
    envFileIssues = []
    if not os.path.exists(serviceTemplate + '/filter.acl'):
      envFileIssues.append(serviceTemplate + '/filter.acl does not exist')
    if not os.path.exists(serviceTemplate + '/mosquitto.conf'):
      envFileIssues.append(serviceTemplate + '/mosquitto.conf does not exist')
    return envFileIssues

  # #####################################
  # End Supporting functions
  # #####################################

  if haltOnErrors:
    eval(toRun)()
  else:
    try:
      eval(toRun)()
    except:
      pass

# This check isn't required, but placed here for debugging purposes
global currentServiceName # Name of the current service
if currentServiceName == 'mosquitto':
  main()
else:
  print("Error. '{}' Tried to run 'mosquitto' config".format(currentServiceName))
