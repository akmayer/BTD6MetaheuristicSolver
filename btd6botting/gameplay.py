import random
import time
from collections import defaultdict

import keyboard
import matplotlib.pyplot as plt
import numpy as np
import pyautogui as pg
from IPython.display import display

from .config import (
    ENABLE_DEBUG_VISUALS,
    INTERVAL_BETWEEN_ACTIONS,
    TOWER_X_MAX,
    TOWER_X_MIN,
    TOWER_Y_MAX,
    TOWER_Y_MIN,
)
from .notifications import post_to_discord
from .state import IMAGES_OUT_OF_ROUND, interface


def _show_debug_image(im):
    if not ENABLE_DEBUG_VISUALS:
        return
    plt.figure()
    plt.imshow(im, interpolation="none")
    plt.show()
    plt.close()


def checkPlacementValidity(whitePixelSensitivity=2, redPixelSensitivity=2):
    im = np.array(pg.screenshot())
    mouseX, mouseY = pg.position()

    h, w, _ = im.shape

    x1 = max(mouseX - 100, 0)
    x2 = min(mouseX + 100, w)
    y1 = max(mouseY - 100, 0)
    y2 = min(mouseY + 50, h)

    if x1 >= x2 or y1 >= y2:
        return "Unselected"

    croppedIm = im[y1:y2, x1:x2]

    white_mask = (croppedIm == np.array([255, 255, 255])).all(axis=2)
    red_mask = (croppedIm == np.array([255, 0, 0])).all(axis=2)
    if np.median(white_mask.sum(axis=1)) >= whitePixelSensitivity:
        return "Valid"
    elif np.median(red_mask.sum(axis=1)) >= redPixelSensitivity:
        return "Invalid"
    else:
        return "Unselected"


def selectAndPlaceTower(key, mouseX, mouseY, towerFree=False):
    keyboard.press(key)
    time.sleep(INTERVAL_BETWEEN_ACTIONS)
    keyboard.release(key)
    pg.moveTo(mouseX, mouseY)
    time.sleep(INTERVAL_BETWEEN_ACTIONS * 3)
    placementValidity = checkPlacementValidity()
    if placementValidity == "Valid":
        interface.analyzeTopbar()
        moneyBefore = interface.getMoney()
        pg.click()
        pg.moveTo(960, 0)
        time.sleep(INTERVAL_BETWEEN_ACTIONS * 3)
        pg.click()
        interface.analyzeTopbar()
        moneyAfter = interface.getMoney()
        if towerFree:
            pass
        elif moneyAfter >= moneyBefore:
            pg.moveTo(1920, 100)
            placementValidity = "Invalid"
    return placementValidity


def checkInRound(im):
    brightness = np.array(im)[-100:, -100:].mean()
    if brightness > 130 and brightness < 137:
        return True


def startRound():
    keyboard.press_and_release("space")
    time.sleep(INTERVAL_BETWEEN_ACTIONS)
    im = pg.screenshot()
    brightness = np.array(im)[-100:, -100:].mean()
    if brightness < 130:
        keyboard.press_and_release("space")


def checkBetweenRounds(im):
    brightness = np.array(im)[-100:, -100:].mean()
    return brightness > 137


def checkDefeated(im):
    return (np.array(im)[300:400, 725:1200, 0] == 255).sum() > 25000


def checkInLevelupScreen(im):
    processedIm = np.array(im)[550:650, 750:1150]
    levelUpWhitePixCount = (processedIm == np.array([255, 255, 255])).all(axis=2).sum()
    return (levelUpWhitePixCount > 3200) and (levelUpWhitePixCount < 3800)


def checkInUnlockUpgrade(im):
    processedIm = np.array(im)[-100:, -350:]
    return (processedIm.mean() > 86) and (processedIm.mean() < 87)


def checkVictory(im):
    victoryTestIm = np.array(im)[900:930, 900:1050]
    whiteCount = np.count_nonzero(victoryTestIm == 255)
    victoryMean = victoryTestIm.mean(axis=(0, 1))
    conditions = [
        whiteCount > 3450,
        whiteCount < 3550,
        victoryMean[0] < 120,
        victoryMean[0] > 115,
        victoryMean[1] < 200,
        victoryMean[1] > 190,
        victoryMean[2] < 85,
        victoryMean[2] > 75,
    ]
    for cond in conditions:
        if cond is False:
            return False
    _show_debug_image(victoryTestIm)
    print(conditions)
    return True


def clickThroughLevelUpScreen():
    pg.click()
    time.sleep(2)
    pg.click()
    time.sleep(3)


def clickThroughVictoryScreen():
    pg.click(971, 906)
    time.sleep(2)
    pg.click(964, 842)
    time.sleep(2)
    winningScreenshot = pg.screenshot()
    post_to_discord("Victory!", winningScreenshot)
    pg.click(1767, 963)
    time.sleep(2)
    pg.click(1202, 832)
    time.sleep(2)
    pg.click()
    time.sleep(2)
    pg.click(1605, 36)
    time.sleep(2)
    pg.click(1069, 842)
    time.sleep(2)
    pg.click(1139, 729)
    time.sleep(2)


def attemptUpgrade(upgradeKey, mouseX, mouseY):
    pg.click(mouseX, mouseY)
    time.sleep(INTERVAL_BETWEEN_ACTIONS * 2)
    interface.analyzeTopbar()
    imBeforeTop = interface.topbar
    procBeforeTop = interface.topbarProc
    moneyBefore = interface.getMoney()
    keyboard.press_and_release(upgradeKey)
    time.sleep(INTERVAL_BETWEEN_ACTIONS * 2)

    try:
        interface.analyzeTopbar()
        moneyAfter = interface.getMoney()
    except IndexError:
        time.sleep(0.2)
        interface.analyzeTopbar()
        moneyAfter = interface.getMoney()

    imAfter = interface.topbar
    procAfterTop = interface.topbarProc

    pg.click(1350, 0)
    time.sleep(0.1)

    if moneyAfter < moneyBefore:
        print("Upgrade Log")
        _show_debug_image(procBeforeTop)
        _show_debug_image(procAfterTop)
        print(moneyAfter, moneyBefore)
        return True
    else:
        _show_debug_image(imBeforeTop)
        _show_debug_image(procBeforeTop)
        _show_debug_image(imAfter)
        _show_debug_image(procAfterTop)
        return False


def isUpgradeLogiciallyValid(towerKey, upgradeKey, upgradeInfo):
    blacklistedTiers = [
        ("o", ".", 3),
        ("s", "/", 3),
        ("h", ".", 3),
    ]

    for tier in blacklistedTiers:
        if tier[0] == towerKey and tier[1] == "upgradeKey" and tier[3] == (upgradeInfo[upgradeKey] - 1):
            return False

    if upgradeInfo[upgradeKey] == 5:
        return False

    crosspathedOther = True
    for key, upgradePoints in upgradeInfo.items():
        if key == upgradeKey:
            continue
        if upgradePoints == 0:
            crosspathedOther = False

    if crosspathedOther:
        return False

    if upgradeInfo[upgradeKey] == 2:
        for key, upgradePoints in upgradeInfo.items():
            if key == upgradeKey:
                continue
            if upgradePoints >= 3:
                return False

    return True


def runTapeUntilWaiting(tapeParameters, tape, tapeStartIdx, towerInfoDictionary, freeDartMonkey=True):
    maxTowers = tapeParameters[0]
    waitingForMoney = False
    tapeIdx = tapeStartIdx
    while not waitingForMoney:
        if tapeIdx >= len(tape):
            break
        currentAction = tape[tapeIdx]
        actionIdentifier, actionParameters = currentAction
        totalTowers = sum(len(tower_list) for tower_list in towerInfoDictionary.values())
        if actionIdentifier == "buy" and totalTowers < maxTowers:
            towerKey, listOfCoordinates, targeting = actionParameters
            towerFree = False
            if freeDartMonkey and tapeIdx == 1:
                towerFree = True
            placementValidity = "Invalid"
            for coordinate in listOfCoordinates:
                try:
                    placementValidity = selectAndPlaceTower(towerKey, *coordinate, towerFree)
                except ValueError:
                    time.sleep(1)
                    placementValidity = selectAndPlaceTower(towerKey, *coordinate, towerFree)
                if placementValidity == "Valid":
                    if targeting == "strong":
                        keyboard.press_and_release("ctrl+tab")
                    towerInfoDictionary[towerKey].append((coordinate, {",": 0, ".": 0, "/": 0}))
                    tapeIdx += 1
                    break

                elif placementValidity == "Invalid":
                    continue

                elif placementValidity == "Unselected":
                    waitingForMoney = True
                    break

                else:
                    raise Exception("SelectAndPlace Returned Something Unexpected")

            if placementValidity == "Invalid":
                tapeIdx += 1

            pg.moveTo(1920, 300)
            time.sleep(INTERVAL_BETWEEN_ACTIONS)

        elif actionIdentifier == "buy" and totalTowers == maxTowers:
            tapeIdx += 1
            continue

        elif actionIdentifier == "upgrade":
            upgradeKey, towerKey, towerIdx = actionParameters
            towersMatchingKey = towerInfoDictionary.get(towerKey)
            if towersMatchingKey is None:
                tapeIdx += 1
                continue

            elif len(towersMatchingKey) <= towerIdx:
                tapeIdx += 1
                continue

            coordinate, upgradeInfo = towersMatchingKey[towerIdx]

            print(f"Upgrading {towerKey} with {upgradeKey}")
            print(f"{towerKey} has info:", upgradeInfo)

            if not isUpgradeLogiciallyValid(towerKey, upgradeKey, upgradeInfo):
                tapeIdx += 1
                continue

            upgradeSuccess = attemptUpgrade(upgradeKey, *coordinate)
            print(f"Upgrade Success: {upgradeSuccess}")
            print()
            if upgradeSuccess:
                upgradeInfo[upgradeKey] += 1
                tapeIdx += 1
            else:
                waitingForMoney = True
                break
        time.sleep(INTERVAL_BETWEEN_ACTIONS)
    return towerInfoDictionary, tapeIdx


def takeActionsInRound(rollingTape):
    tapeVictory = False
    timesOutOfRound = 0
    im = pg.screenshot()

    imArray = np.array(im).astype(float)[:, :, 0]
    redCountArray = np.zeros_like(imArray)
    while timesOutOfRound < 2:
        for key in "1234567":
            keyboard.press_and_release(key)
            time.sleep(0.01)
        for _ in range(10):
            pg.moveTo(random.randint(TOWER_X_MIN, TOWER_X_MAX), random.randint(TOWER_Y_MIN, TOWER_Y_MAX))
        im = pg.screenshot()

        imArray = np.array(im).astype(float)

        if checkInLevelupScreen(im):
            clickThroughLevelUpScreen()
        elif checkDefeated(im):
            IMAGES_OUT_OF_ROUND.append((im, "Defeated"))
            rollingTape = False
            break
        elif checkVictory(im):
            IMAGES_OUT_OF_ROUND.append((im, "Victory"))
            clickThroughVictoryScreen()
            tapeVictory = True
            rollingTape = False
            break
        elif checkInRound(im):
            rednessArray = imArray[:, :, 0] > 2 * (imArray[:, :, 1] + imArray[:, :, 2])
            redCountArray[rednessArray] += 1
            timesOutOfRound = 0
            continue
        elif checkBetweenRounds(im):
            IMAGES_OUT_OF_ROUND.append((im, "Between Rounds"))
            timesOutOfRound += 1
        else:
            time.sleep(0.2)
            pg.click(1350, 0)
            time.sleep(0.2)
            print("Warning, in unknown menu")
            if ENABLE_DEBUG_VISUALS:
                display(im)
    return rollingTape, tapeVictory, redCountArray


def rolloutTape(tapeParameters, tape, maxTapeIdx=np.inf, freeDartMonkey=True):
    towerInfoDictionary = defaultdict(list)
    tapeIdx = 0
    rollingTape = True
    while rollingTape:
        interface.analyzeTopbar()
        topbarStats = [interface.getRound(), interface.getMoney(), interface.getHealth()]
        if interface.getRound() == 0:
            time.sleep(2)
            im = pg.screenshot()

            if checkInLevelupScreen(im):
                clickThroughLevelUpScreen()
                time.sleep(2)
                interface.analyzeTopbar()
                topbarStats = [interface.getRound(), interface.getMoney(), interface.getHealth()]
            else:
                raise Exception()

        if tapeIdx < maxTapeIdx:
            towerInfoDictionary, tapeIdx = runTapeUntilWaiting(
                tapeParameters, tape, tapeIdx, towerInfoDictionary, freeDartMonkey
            )

        startRound()
        rollingTape, tapeVictory, rednessArr = takeActionsInRound(rollingTape)

    if tapeVictory:
        rolloutTape(tapeParameters, tape, maxTapeIdx)

    return *topbarStats, tapeIdx, rednessArr
