#!/usr/bin/env python3

import signal

def main():
  from blessed import Terminal
  from deps.chars import specialChars, commonTopBorder, commonBottomBorder, commonEmptyLine
  import time
  import subprocess
  import yaml
  import os

  global signal
  global currentServiceName
  global dockerCommandsSelectionInProgress
  global mainMenuList
  global currentMenuItemIndex
  global renderMode
  global paginationSize
  global paginationStartIndex
  global addonsFile
  term = Terminal()
  hotzoneLocation = [((term.height // 16) + 6), 0]
  paginationToggle = [10, term.height - 25]
  paginationStartIndex = 0
  paginationSize = paginationToggle[0]

  serviceService = './services/' + currentServiceName
  serviceTemplate = './.templates/' + currentServiceName
  addonsFile = serviceTemplate + "/addons.yml"
  
  def goBack():
    global dockerCommandsSelectionInProgress
    global needsRender
    dockerCommandsSelectionInProgress = False
    needsRender = 1
    print("Back to main menu")
    return True

  mainMenuList = []

  hotzoneLocation = [((term.height // 16) + 6), 0]

  dockerCommandsSelectionInProgress = True
  currentMenuItemIndex = 0
  menuNavigateDirection = 0

  # Render Modes:
  #  0 = No render needed
  #  1 = Full render
  #  2 = Hotzone only
  needsRender = 1

  def onResize(sig, action):
    global mainMenuList
    global currentMenuItemIndex
    mainRender(1, mainMenuList, currentMenuItemIndex)

  def generateLineText(text, textLength=None, paddingBefore=0, lineLength=64):
    result = ""
    for i in range(paddingBefore):
      result += " "

    textPrintableCharactersLength = textLength

    if (textPrintableCharactersLength) == None:
      textPrintableCharactersLength = len(text)

    result += text
    remainingSpace = lineLength - textPrintableCharactersLength

    for i in range(remainingSpace):
      result += " "
    
    return result

  def renderHotZone(term, renderType, menu, selection, hotzoneLocation, paddingBefore = 4):
    global paginationSize

    print(term.move(hotzoneLocation[0], hotzoneLocation[1]))

    if paginationStartIndex >= 1:
      print(term.center("{b}       {uaf}      {uaf}{uaf}{uaf}                                                   {ual}           {b}".format(
        b=specialChars[renderMode]["borderVertical"],
        uaf=specialChars[renderMode]["upArrowFull"],
        ual=specialChars[renderMode]["upArrowLine"]
      )))
    else:
      print(term.center(commonEmptyLine(renderMode)))

    for (index, menuItem) in enumerate(menu): # Menu loop
      if index >= paginationStartIndex and index < paginationStartIndex + paginationSize:
        lineText = generateLineText(menuItem[0], paddingBefore=paddingBefore)

        # Menu highlight logic
        if index == selection:
          formattedLineText = '{t.blue_on_green}{title}{t.normal}'.format(t=term, title=menuItem[0])
          paddedLineText = generateLineText(formattedLineText, textLength=len(menuItem[0]), paddingBefore=paddingBefore)
          toPrint = paddedLineText
        else:
          toPrint = '{title}{t.normal}'.format(t=term, title=lineText)
        # #####

        # Menu check render logic
        if menuItem[1]["checked"]:
          toPrint = "     (X) " + toPrint
        else:
          toPrint = "     ( ) " + toPrint

        toPrint = "{bv} {toPrint}  {bv}".format(bv=specialChars[renderMode]["borderVertical"], toPrint=toPrint) # Generate border
        toPrint = term.center(toPrint) # Center Text (All lines should have the same amount of printable characters)
        # #####
        print(toPrint)

    if paginationStartIndex + paginationSize < len(menu):
      print(term.center("{b}       {daf}      {daf}{daf}{daf}                                                   {dal}           {b}".format(
        b=specialChars[renderMode]["borderVertical"],
        daf=specialChars[renderMode]["downArrowFull"],
        dal=specialChars[renderMode]["downArrowLine"]
      )))
    else:
      print(term.center(commonEmptyLine(renderMode)))
    print(term.center(commonEmptyLine(renderMode)))
    print(term.center(commonEmptyLine(renderMode)))


  def mainRender(needsRender, menu, selection):
    global paginationStartIndex
    global paginationSize
    term = Terminal()
    
    if selection >= paginationStartIndex + paginationSize:
      paginationStartIndex = selection - (paginationSize - 1) + 1
      needsRender = 1
      
    if selection <= paginationStartIndex - 1:
      paginationStartIndex = selection
      needsRender = 1

    if needsRender == 1:
      print(term.clear())
      print(term.move_y(term.height // 16))
      print(term.black_on_cornsilk4(term.center('IOTstack NodeRed Addons')))
      print("")
      print(term.center(commonTopBorder(renderMode)))
      print(term.center(commonEmptyLine(renderMode)))
      print(term.center("{bv}      Select NodeRed Addons (npm) to install                                    {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center(commonEmptyLine(renderMode)))

    if needsRender >= 1:
      renderHotZone(term, needsRender, menu, selection, hotzoneLocation)

    if needsRender == 1:
      print(term.center(commonEmptyLine(renderMode)))
      print(term.center(commonEmptyLine(renderMode)))
      print(term.center("{bv}      Controls:                                                                 {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [Space] to select or deselect addon                                       {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [Up] and [Down] to move selection cursor                                  {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [Tab] Expand or collapse addon menu size                                  {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [S] Switch between sorted by checked and sorted alphabetically            {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [Enter] to save updated list                                              {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center("{bv}      [Escape] to cancel changes                                                {bv}".format(bv=specialChars[renderMode]["borderVertical"])))
      print(term.center(commonEmptyLine(renderMode)))
      print(term.center(commonEmptyLine(renderMode)))
      print(term.center(commonBottomBorder(renderMode)))

  def runSelection(selection):
    import types
    if len(mainMenuList[selection]) > 1 and isinstance(mainMenuList[selection][1], types.FunctionType):
      mainMenuList[selection][1]()
    else:
      print(term.green_reverse('IOTstack Error: No function assigned to menu item: "{}"'.format(mainMenuList[selection][0])))

  def isMenuItemSelectable(menu, index):
    if len(menu) > index:
      if len(menu[index]) > 1:
        if "skip" in menu[index][1] and menu[index][1]["skip"] == True:
          return False
    return True

  def loadAddonsMenu():
    global mainMenuList
    if os.path.exists(addonsFile):
      with open(r'%s' % addonsFile) as objAddonsFile:
        addonsLoaded = yaml.load(objAddonsFile, Loader=yaml.SafeLoader)
        defaultOnAddons = addonsLoaded["addons"]["default_on"]
        defaultOffAddons = addonsLoaded["addons"]["default_off"]
        if not os.path.exists(serviceService + '/addons_list.yml'):
          defaultOnAddons.sort()
          for (index, addonName) in enumerate(defaultOnAddons):
            mainMenuList.append([addonName, { "checked": True }])

          defaultOffAddons.sort()
          for (index, addonName) in enumerate(defaultOffAddons):
            mainMenuList.append([addonName, { "checked": False }])
        else:
          with open(r'%s' % serviceService + '/addons_list.yml') as objSavedAddonsFile:
            savedAddonsFile = yaml.load(objSavedAddonsFile, Loader=yaml.SafeLoader)
            savedAddons = savedAddonsFile["addons"]
            savedAddons.sort()
            for (index, addonName) in enumerate(savedAddons):
              mainMenuList.append([addonName, { "checked": True }])

            for (index, addonName) in enumerate(defaultOnAddons):
              if not addonName in savedAddons:
                mainMenuList.append([addonName, { "checked": False }])

            for (index, addonName) in enumerate(defaultOffAddons):
              if not addonName in savedAddons:
                mainMenuList.append([addonName, { "checked": False }])
            sortBy = 0
            mainMenuList.sort(key=lambda x: (x[1]["checked"], x[0]), reverse=True)

    else:
      print("Error: '{addonsFile}' file doesn't exist.".format(addonsFile=addonsFile))

  def checkMenuItem(selection):
    global mainMenuList
    if mainMenuList[selection][1]["checked"] == True:
      mainMenuList[selection][1]["checked"] = False
    else:
      mainMenuList[selection][1]["checked"] = True

  def saveAddonList():
    try:
      if not os.path.exists(serviceService):
        os.mkdir(serviceService)
      nodeRedYamlAddonsList = {
        "version": "1",
        "application": "IOTstack",
        "service": "nodered",
        "comment": "Selected addons",
        "addons": []
      }
      for (index, addon) in enumerate(mainMenuList):
        if addon[1]["checked"]:
          nodeRedYamlAddonsList["addons"].append(addon[0])

      with open(r'%s/addons_list.yml' % serviceService, 'w') as outputFile:
        yaml.dump(nodeRedYamlAddonsList, outputFile, default_flow_style=False, sort_keys=False)

    except Exception as err: 
      print("Error saving NodeRed Addons list", currentServiceName)
      print(err)
      return False
    return True


  if __name__ == 'builtins':
    global signal
    sortBy = 0
    term = Terminal()
    signal.signal(signal.SIGWINCH, onResize)
    loadAddonsMenu()
    with term.fullscreen():
      menuNavigateDirection = 0
      mainRender(needsRender, mainMenuList, currentMenuItemIndex)
      dockerCommandsSelectionInProgress = True
      with term.cbreak():
        while dockerCommandsSelectionInProgress:
          menuNavigateDirection = 0

          if not needsRender == 0: # Only rerender when changed to prevent flickering
            mainRender(needsRender, mainMenuList, currentMenuItemIndex)
            needsRender = 0

          key = term.inkey()
          if key.is_sequence:
            if key.name == 'KEY_TAB':
              if paginationSize == paginationToggle[0]:
                paginationSize = paginationToggle[1]
              else:
                paginationSize = paginationToggle[0]
              mainRender(1, mainMenuList, currentMenuItemIndex)
            if key.name == 'KEY_DOWN':
              menuNavigateDirection += 1
            if key.name == 'KEY_UP':
              menuNavigateDirection -= 1
            if key.name == 'KEY_ENTER':
              if saveAddonList():
                return True
              else:
                print("Something went wrong. Try saving the list again.")
            if key.name == 'KEY_ESCAPE':
              dockerCommandsSelectionInProgress = False
              return True
          elif key:
            if key == ' ': # Space pressed
              checkMenuItem(currentMenuItemIndex) # Update checked list
              needsRender = 2
            if key == 's':
              if sortBy == 0:
                sortBy = 1
                mainMenuList.sort(key=lambda x: x[0], reverse=False)
              else:
                sortBy = 0
                mainMenuList.sort(key=lambda x: (x[1]["checked"], x[0]), reverse=True)
              
              needsRender = 2

          if menuNavigateDirection != 0: # If a direction was pressed, find next selectable item
            currentMenuItemIndex += menuNavigateDirection
            currentMenuItemIndex = currentMenuItemIndex % len(mainMenuList)
            needsRender = 2

            while not isMenuItemSelectable(mainMenuList, currentMenuItemIndex):
              currentMenuItemIndex += menuNavigateDirection
              currentMenuItemIndex = currentMenuItemIndex % len(mainMenuList)
    return True

  return True

originalSignalHandler = signal.getsignal(signal.SIGINT)
main()
signal.signal(signal.SIGWINCH, originalSignalHandler)
