import ctypes
ctypes.windll.user32.SetProcessDPIAware()

import time
import pyautogui as pg
import numpy as np
import matplotlib.pyplot as plt
from BTD6TopbarOCR.OCRGameInterface import GameInterface
from scipy.ndimage import gaussian_filter

interface = GameInterface()
towerPlacementKeys = "qwertyzxcvnasdfgjklpoh"
import keyboard
intervalBetweenActions = 0.05

def checkPlacementValidity(whitePixelSensitivity=2, redPixelSensitivity=2):
    im = np.array(pg.screenshot())
    mouseX, mouseY = pg.position()

    h, w, _ = im.shape

    # Define crop bounds with clamping
    x1 = max(mouseX - 100, 0)
    x2 = min(mouseX + 100, w)
    y1 = max(mouseY - 100, 0)
    y2 = min(mouseY + 50, h)

    # Ensure valid slice (in case cursor is extremely close to edge)
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


def selectAndPlaceTower(key, mouseX, mouseY, towerFree = False):
    keyboard.press(key)
    time.sleep(intervalBetweenActions)
    keyboard.release(key)
    pg.moveTo(mouseX, mouseY)
    time.sleep(intervalBetweenActions * 3)
    placementValidity = checkPlacementValidity()
    if placementValidity == "Valid":
        interface.analyzeTopbar()
        moneyBefore = interface.getMoney()
        pg.click()
        pg.moveTo(960, 0)
        time.sleep(intervalBetweenActions * 3)
        pg.click()
        interface.analyzeTopbar()
        moneyAfter = interface.getMoney()
        if towerFree:
            pass
        elif moneyAfter >= moneyBefore:
            
            pg.moveTo(1920, 100)
            placementValidity = "Invalid"
    return placementValidity

import time, keyboard
#time.sleep(3)
#selectAndPlaceTower("q", *(1391, 345))
def checkInRound(im):
    brightness = np.array(im)[-100:, -100:].mean()
    if brightness > 130 and brightness < 137:
        return True

def startRound():
    keyboard.press_and_release("space")
    time.sleep(intervalBetweenActions)
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
    processedIm = np.array(im)[550:650, 750: 1150]
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
        victoryMean[2] > 75
    ]
    for cond in conditions:
        if cond == False:
            return False
    plt.imshow(victoryTestIm)
    plt.show()
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
    time.sleep(intervalBetweenActions * 2)
    interface.analyzeTopbar()
    imBeforeTop = interface.topbar
    procBeforeTop = interface.topbarProc
    moneyBefore = interface.getMoney()
    imBefore = np.array(pg.screenshot())
    keyboard.press_and_release(upgradeKey)
    time.sleep(intervalBetweenActions * 2)

    
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
        plt.imshow(procBeforeTop, interpolation='none')
        plt.show()
        plt.imshow(procAfterTop, interpolation='none')
        plt.show()
        print(moneyAfter, moneyBefore)
        return True
    else:
        plt.imshow(imBeforeTop, interpolation= 'none')
        plt.show()
        plt.imshow(procBeforeTop, interpolation='none')
        plt.show()
        plt.imshow(imAfter, interpolation = 'none')
        plt.show()
        plt.imshow(procAfterTop, interpolation='none')
        plt.show()
        return False


#time.sleep(2)
#attemptUpgrade('/', 1366, 501)
import random

TOWER_X_MIN = 60
TOWER_X_MAX = 1550
TOWER_Y_MIN = 150
TOWER_Y_MAX = 950

def sampleCoordinate(towerPlacementDistribution, T = 0.5, n=10):
    # Normalize the tower placement distribution
    # Copy your tower placement distribution
    dist = towerPlacementDistribution.copy()
    
    # Create uniform mask for allowed area
    mask = np.zeros_like(dist, dtype=bool)
    mask[TOWER_Y_MIN:TOWER_Y_MAX+1, TOWER_X_MIN:TOWER_X_MAX+1] = True
    
    # Zero out everything outside the mask
    dist[~mask] = 0.0
    
    # Normalize the masked distribution
    dist /= dist.sum()
    
    # Apply temperature
    dist_temp = dist ** (1 / T)
    dist_temp /= dist_temp.sum()  # renormalize after temperature
    
    # Flatten for sampling
    flat_dist = dist_temp.ravel()
    flat_indices = np.arange(flat_dist.size)
    
    # Sample 10 unique indices according to the masked, temperature-adjusted distribution
    sampled_indices = np.random.choice(flat_indices, size=n, replace=False, p=flat_dist)
    
    # Convert sampled indices to 2D coordinates
    coords = np.column_stack(np.unravel_index(sampled_indices, dist.shape))
    y_coords, x_coords = coords[:, 0], coords[:, 1]  # NumPy: row=y, col=x
    
    # Convert to pyautogui screen coordinates (x, y)
    coordinates = [(int(x), int(y)) for x, y in zip(x_coords, y_coords)]
    if n == 1:
        return coordinates[0]
    else:
        return coordinates

def sampleRandomPurchase(towerPlacementDistribution, T = 0.5):
    
    # Convert back to 2D coordinates
    coordinates = sampleCoordinate(towerPlacementDistribution, T, 10)

    towerKey = random.choice(towerPlacementKeys)
    
    if random.random() < 0.5:
        targeting = 'strong'
    else:
        targeting = 'first'
    return towerKey, coordinates, targeting

def sampleRandomUpgrade(boughtTowers):
    towerKey = random.choice([x for x in list(boughtTowers.keys()) if boughtTowers[x] > 0])
    towerPlacementIdx = random.choice(range(boughtTowers[towerKey]))
    upgradeKey = random.choice([",", ".", "/"])
    return upgradeKey, towerKey, towerPlacementIdx

def generateRandomActionTape(towerPlacementDistribution,
                             T = 0.5,
                             maxTowers = 15,
                             avgUpgradesPerTowerPurchase = 2.5,
                             numActions=40,
                             freeDartMonkey = True
                            ):
    # right now just a tuple that holds the max number of towers
    tapeParameters = (maxTowers, avgUpgradesPerTowerPurchase)
    actionTape = []
    boughtTowers = {}  # track bought towers for upgrades
    numTowersBought = 0 

    for i in range(numActions):
        # always start with buy
        buyWeight = 1 / (1 + avgUpgradesPerTowerPurchase)
        upgradeWeight = avgUpgradesPerTowerPurchase / (1 + avgUpgradesPerTowerPurchase)

        actionIdentifier = random.choices(["buy", "upgrade"], weights = [buyWeight, upgradeWeight], k = 1)[0]
        actionIdentifier = "buy" if (i <= 1) else actionIdentifier
        actionIdentifier = 'upgrade' if ((numTowersBought == (2 * maxTowers))) else actionIdentifier


        if actionIdentifier == "buy":
            towerKey, coordinates, targeting = sampleRandomPurchase(towerPlacementDistribution, T = 0.5)
            
            if i == 0:
                towerKey = 'u'

            elif freeDartMonkey and i == 1:
                towerKey = 'q'
                if towerKey not in boughtTowers:
                    boughtTowers[towerKey] = 0
                boughtTowers[towerKey] += 1
                numTowersBought += 1
            
            elif i != 0:
                if towerKey not in boughtTowers:
                    boughtTowers[towerKey] = 0
                boughtTowers[towerKey] += 1
                numTowersBought += 1
            actionTape.append(("buy", (towerKey, coordinates, targeting)))

        else:  # upgrade

            upgradeKey, towerKey, towerPlacementIdx = sampleRandomUpgrade(boughtTowers)
            actionTape.append(("upgrade", (upgradeKey, towerKey, towerPlacementIdx)))

    return tapeParameters, actionTape

mask = np.ones(shape=(1080, 1920))

# example usage
tapeParameters, tape = generateRandomActionTape(mask, 0.5, 3, 3, 10)
for action in tape:
    print(action)
from collections import defaultdict

def isUpgradeLogiciallyValid(towerKey, upgradeKey, upgradeInfo):

    blacklistedTiers = [
        # Desperado buff
        ('o', '.', 3),
        # Super monkey night shift
        ('s', '/', 3),
        # Any bank
        ('h', '.', 3)
    ]

    for tier in blacklistedTiers:
        if tier[0] == towerKey and tier[1] == 'upgradeKey' and tier[3] == (upgradeInfo[upgradeKey] - 1):
            return False


    # check if already T5 in selected upgrade
    if upgradeInfo[upgradeKey] == 5:
        return False

    # check if crosspathed between other two paths already 
    crosspathedOther = True
    for key, upgradePoints in upgradeInfo.items():
        if key == upgradeKey:
            continue
        if upgradePoints == 0:
            crosspathedOther = False

    if crosspathedOther:
        return False

    # check if this at two and one of the others 3 or more
    if upgradeInfo[upgradeKey] == 2:
        for key, upgradePoints in upgradeInfo.items():
            if key == upgradeKey:
                continue
            if upgradePoints >= 3:
                return False

    return True

def runTapeUntilWaiting(tapeParameters, tape, tapeStartIdx, towerInfoDictionary, freeDartMonkey = True):
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
            for coordinate in listOfCoordinates:
                try:
                    placementValidity = selectAndPlaceTower(towerKey, *coordinate, towerFree)
                except ValueError:
                    time.sleep(1)
                    placementValidity = selectAndPlaceTower(towerKey, *coordinate, towerFree)
                if placementValidity == "Valid":

                    # (coordinates, upgradeStats) tuple
                    if targeting == "strong":
                        keyboard.press_and_release("ctrl+tab")
                    towerInfoDictionary[towerKey].append((coordinate, {',' : 0, "." : 0, "/" : 0}))
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
            time.sleep(intervalBetweenActions)

        elif actionIdentifier == "buy" and totalTowers == maxTowers:
            tapeIdx += 1
            continue

        elif actionIdentifier == "upgrade":
            upgradeKey, towerKey, towerIdx = actionParameters
            towersMatchingKey = towerInfoDictionary.get(towerKey)
            if towersMatchingKey is None:
                #print(f"Warning: Was not able to find tower {towerKey} to upgrade.")
                tapeIdx += 1
                continue

            elif len(towersMatchingKey) <= towerIdx:
                #print(f"Warning: Idx larger than list of {towerKey} placements.")
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
        time.sleep(intervalBetweenActions)
    return towerInfoDictionary, tapeIdx
    
IMAGES_OUT_OF_ROUND = []
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
        for x in range(10):
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
            display(im)
    return rollingTape, tapeVictory, (redCountArray)
                    

def rolloutTape(tapeParameters, tape, maxTapeIdx = np.inf, freeDartMonkey = True):
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
            towerInfoDictionary, tapeIdx = runTapeUntilWaiting(tapeParameters, tape, tapeIdx, towerInfoDictionary)

        startRound()
        rollingTape, tapeVictory, rednessArr = takeActionsInRound(rollingTape)
        
    if tapeVictory:
        rolloutTape(tapeParameters, tape, maxTapeIdx)

    return *topbarStats, tapeIdx, rednessArr
import random

def probabilistic_adjacent_swap(lst, actionTranspositionChance):
    result = lst.copy()
    
    for i in range(0, len(result) - 1, 2):
        if random.random() < actionTranspositionChance:
            result[i], result[i + 1] = result[i + 1], result[i]
    
    return result

def mutateCoordinates(oldCoordinateList, buyCoordinateModificationChance, towerDistMap, T = 0.5):
    newCoordinateList = []
    sampledCoordinateList = sampleCoordinate(towerDistMap, T, len(oldCoordinateList))
    for idx, (xCoord, yCoord) in enumerate(oldCoordinateList):
        if random.random() < buyCoordinateModificationChance:
            newXCoord, newYCoord = sampledCoordinateList[idx]
        else:
            newXCoord = xCoord
            newYCoord = yCoord
        
        newCoordinateList.append((newXCoord, newYCoord))
    return newCoordinateList

def mutateTowerKey(oldTowerKey, buyTowerReselectionChance):
    if random.random() < buyTowerReselectionChance:
        towerKey = random.choice(towerPlacementKeys)
    else:
        towerKey = oldTowerKey
    return towerKey

def mutateTargeting(oldTargeting, targetingMutationChance):
    if random.random() < targetingMutationChance:
        if random.random() < 0.5:
            targeting = 'strong'
        else:
            targeting = 'first'
    else:
        targeting = oldTargeting
    return targeting

def mutateUpgradeKey(oldUpgradePath, upgradePathModificationChance):
    if random.random() < upgradePathModificationChance:
        upgradeKey = random.choice([",", ".", "/"])
    else:
        upgradeKey = oldUpgradePath
    return upgradeKey

def mutateUpgradeTowerSelectionKey(oldTowerKey, oldPlacementIdx, boughtTowers, upgradeTowerModificationChance):
    if random.random() < upgradeTowerModificationChance or boughtTowers[oldTowerKey] == 0:
        towerKey = random.choice([x for x in list(boughtTowers.keys()) if boughtTowers[x] > 0])
        towerPlacementIdx = random.choice(range(boughtTowers[towerKey]))
    else:
        towerKey = oldTowerKey
        towerPlacementIdx = oldPlacementIdx
    return towerKey, towerPlacementIdx

def modifyTape(tapeParameters, tape, frozenPrefixSize,
               towerPlacementDistribution,
               T = 0.5,
               actionTypeFlipChance = 0.1,
               buyTowerReselectionChance = 0.1,
               buyCoordinateModificationChance = 0.15,
               upgradePathModificationChance = 0.1,
               upgradeTowerModificationChance = 0.1,
               targetingMutationChance = 0.2,
               failureStep = 10000000000
              ):

    maxTowers, avgUpPerTower = tapeParameters

    # Slight global parameter mutation (optional — you can disable if unstable)
    maxTowers += random.randint(-1, 1)
    avgUpPerTower += (random.random() - 0.5)

    boughtTowers = defaultdict(int)
    numBoughtTowers = 0

    newTape = []

    # ----------------------------
    # Phase 1: Replay frozen prefix EXACTLY
    # ----------------------------
    for idx in range(min(frozenPrefixSize, len(tape))):
        actionIdentifier, actionParameters = tape[idx]

        newTape.append((actionIdentifier, actionParameters))

        # Update state WITHOUT mutation
        if idx == 0:
            numBoughtTowers += 1

        elif idx == 1:
            towerKey, _, _ = actionParameters
            boughtTowers[towerKey] += 1
            numBoughtTowers += 1

        elif actionIdentifier == "buy":
            towerKey, _, _ = actionParameters
            boughtTowers[towerKey] += 1
            numBoughtTowers += 1

        elif actionIdentifier == "upgrade":
            pass  # no effect on counts


    # ----------------------------
    # Phase 2: Mutate suffix
    # ----------------------------
    for idx in range(frozenPrefixSize, len(tape)):
        

        actionIdentifier, actionParameters = tape[idx]

        if idx == failureStep:
            buyTowerReselectionChance = 1.0
            buyCoordinateModificationChance = 01.0
            upgradePathModificationChance = 1.0
            upgradeTowerModificationChance = 1.0
            targetingMutationChance = 1.0

        # ----------------------------
        # Special handling for first two indices IF they are not frozen
        # ----------------------------
        if idx == 0:
            heroKey, coordinateList, targeting = actionParameters

            newCoordinateList = mutateCoordinates(coordinateList, buyCoordinateModificationChance, towerPlacementDistribution)
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append((actionIdentifier, (heroKey, newCoordinateList, newTargeting)))
            numBoughtTowers += 1
            continue

        elif idx == 1:
            towerKey, coordinateList, targeting = actionParameters

            newTowerKey = mutateTowerKey(towerKey, buyTowerReselectionChance)
            newCoordinateList = mutateCoordinates(coordinateList, buyCoordinateModificationChance, towerPlacementDistribution)
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append((actionIdentifier, (newTowerKey, newCoordinateList, newTargeting)))

            boughtTowers[newTowerKey] += 1
            numBoughtTowers += 1
            continue

        # ----------------------------
        # BUY action
        # ----------------------------
        if actionIdentifier == "buy":

            if random.random() < (actionTypeFlipChance * (avgUpPerTower / (1 + avgUpPerTower))):
                newUpgradeActionParameters = sampleRandomUpgrade(boughtTowers)
                newTape.append(('upgrade', newUpgradeActionParameters))
                continue

            towerKey, coordinateList, targeting = actionParameters

            newTowerKey = mutateTowerKey(towerKey, buyTowerReselectionChance)
            newCoordinateList = mutateCoordinates(coordinateList, buyCoordinateModificationChance, towerPlacementDistribution)
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append(('buy', (newTowerKey, newCoordinateList, newTargeting)))

            boughtTowers[newTowerKey] += 1
            numBoughtTowers += 1
            continue

        # ----------------------------
        # UPGRADE action
        # ----------------------------
        elif actionIdentifier == "upgrade":

            if random.random() < (actionTypeFlipChance * (1 / (1 + avgUpPerTower))) and (numBoughtTowers < 2 * maxTowers):
                towerKey, coordinates, targeting = sampleRandomPurchase(towerPlacementDistribution)

                newTape.append(('buy', (towerKey, coordinates, targeting)))

                boughtTowers[towerKey] += 1  # ✅ FIXED BUG (was newTowerKey before)
                numBoughtTowers += 1
                continue

            upgradeKey, towerKey, placementIdx = actionParameters

            newUpgradeKey = mutateUpgradeKey(upgradeKey, upgradePathModificationChance)
            newTowerKey, newPlacementIdx = mutateUpgradeTowerSelectionKey(
                towerKey,
                placementIdx,
                boughtTowers,
                upgradeTowerModificationChance
            )

            newTape.append(('upgrade', (newUpgradeKey, newTowerKey, newPlacementIdx)))
            continue

    return (maxTowers, avgUpPerTower), newTape    
import requests, os, io
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1484529687618129920/Kpu1aWlP7UwcJR8hnQR20OHkcvqI2pOnliWAlzljWvefX6vz15Ra6S-XNSnH0oM5wCty"


def post_to_discord(message, image=None):
    try:
        data = {"content": message}

        if image:
            # Convert PIL image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            files = {
                "file": ("screenshot.png", img_bytes, "image/png")
            }

            requests.post(
                DISCORD_WEBHOOK,
                data=data,
                files=files,
                timeout=5
            )
        else:
            requests.post(
                DISCORD_WEBHOOK,
                json=data,
                timeout=5
            )

    except Exception:
        pass  # fail silently
def getHeatmapRun():
    mask = np.ones(shape=(1080, 1920))

    tapeParameters, tape = generateRandomActionTape(mask, T = 0.5,
                                                    maxTowers = 1, 
                                                    avgUpgradesPerTowerPurchase = 1, 
                                                    numActions = 1000)
    r, dollas, hp, _, rednessArr = rolloutTape(tapeParameters, tape, 0)
    mask = (rednessArr >= 0.1 * rednessArr.max()) & (rednessArr <= 0.75 * rednessArr.max())
    mask = mask.astype(float)
    blurredLarge = gaussian_filter(mask, sigma=150, mode='constant')
    blurredSmall = gaussian_filter(mask, sigma=20, mode='constant')
    mask = np.clip(blurredLarge - blurredSmall, 0, np.inf)
    # reset UI
    time.sleep(1)
    pg.click(853, 811)
    time.sleep(1)
    pg.click(1132, 726)
    time.sleep(1)
    return mask
import random
import time
import os
from IPython.display import clear_output

#towerPlacementKeys = "asdfgp"
towerPlacementKeys = "qwertyzxcvnasdfgjklpoh"


seed = int.from_bytes(os.urandom(4), "big")
print("Seed:", seed)
random.seed(seed)
np.random.seed(seed)

time.sleep(3)

keyboard.press("u")
time.sleep(0.5)
keyboard.release("u")
pg.moveTo(1920, 100)
time.sleep(0.5)

# ----------------------------
# Scoring
# ----------------------------
def score(round_num, dollars):
    return (round_num, dollars)


# ----------------------------
# Verify ONLY when needed
# ----------------------------
def verify_if_best(tp, tape, r1, d1, current_best):
    # If not beating current best, skip verification
    if current_best is not None:
        if score(r1, d1) <= score(current_best[2], current_best[3]):
            return r1, d1, False, None

    msg = "🏆 Potential new best — verifying..."
    print(msg)
    post_to_discord(msg)

    r2, d2, hp2, f2, _ = rolloutTape(tp, tape)
    # reset UI
    time.sleep(1)
    pg.click(853, 811)
    time.sleep(1)
    pg.click(1132, 726)
    time.sleep(1)
    clear_output(wait=True)  # <-- ADD THIS

    vr = min(r1, r2)
    vd = min(d1, d2)

    msg = f"Verification: Initial=({r1},{d1}) vs Second=({r2},{d2}) → Used=({vr},{vd})"
    print(msg)
    post_to_discord(msg)

    return vr, vd, True, f2


mapSpecificHeatmap = getHeatmapRun()

time.sleep(2)


# ----------------------------
# Config
# ----------------------------
BEAM_WIDTH = 1
MUTATIONS_PER_BEAM = 1

INITIAL_EXPLORATION_RUNS = 20

FREEZE_BACKTRACK_MIN = 5
FREEZE_BACKTRACK_MAX = 15

LIGHT_MUTATION_CHANCE = 0.3

SHOCK_PROB = 0.15
SHOCK_BACKTRACK_MIN = 20
SHOCK_BACKTRACK_MAX = 80

STAGNATION_LIMIT = 25
ROLLBACK_RATIO = 0.7


# ----------------------------
# Initial Exploration
# ----------------------------
beam = []
best_global = None

for x in range(INITIAL_EXPLORATION_RUNS):
    maxTowerExploration = random.randint(6, 12)
    avgUpPerTower = random.uniform(1, 4)

    tapeParameters, tape = generateRandomActionTape(
        mapSpecificHeatmap,
        T=0.5,
        maxTowers=maxTowerExploration,
        avgUpgradesPerTowerPurchase=avgUpPerTower,
        numActions=1000
    )

    for a in tape[:10]:
        print(a)

    r1, d1, hp, failure_step, _ = rolloutTape(tapeParameters, tape)
    # reset UI
    time.sleep(1)
    pg.click(853, 811)
    time.sleep(1)
    pg.click(1132, 726)
    time.sleep(1)
    clear_output(wait=True)  # <-- ADD THIS

    # verify ONLY if it could be best
    r, dollars, did_verify, new_failure = verify_if_best(
        tapeParameters, tape, r1, d1, best_global
    )

    if did_verify:
        failure_step = new_failure

    candidate = (tapeParameters, tape, r, dollars, failure_step)
    beam.append(candidate)

    # update best_global immediately (IMPORTANT)
    if best_global is None or score(r, dollars) > score(best_global[2], best_global[3]):
        best_global = candidate

    msg = f"Exploration {x+1}: Round={r}, Money={dollars}"
    print(msg)
    post_to_discord(msg)

    

beam = sorted(beam, key=lambda x: score(x[2], x[3]), reverse=True)[:BEAM_WIDTH]


# ----------------------------
# Optimization Loop
# ----------------------------
iteration = 1
no_improvement_counter = 0

while True:
    candidates = []

    for (tp, tape, r, dollars, failure_step) in beam:
        for _ in range(MUTATIONS_PER_BEAM):

            backtrack = random.randint(FREEZE_BACKTRACK_MIN, FREEZE_BACKTRACK_MAX)
            frozen_prefix = max(0, failure_step - backtrack)

            if random.random() < SHOCK_PROB:
                shock_back = random.randint(SHOCK_BACKTRACK_MIN, SHOCK_BACKTRACK_MAX)
                frozen_prefix = max(0, failure_step - shock_back)
                mutation_strength = 1.0
            else:
                mutation_strength = LIGHT_MUTATION_CHANCE

            new_tp, new_tape = modifyTape(
                tp,
                tape,
                frozen_prefix,
                mapSpecificHeatmap,
                actionTypeFlipChance=mutation_strength,
                buyTowerReselectionChance=mutation_strength,
                buyCoordinateModificationChance=mutation_strength,
                upgradePathModificationChance=mutation_strength,
                upgradeTowerModificationChance=mutation_strength,
                targetingMutationChance=mutation_strength,
                failureStep=failure_step
            )

            r1, d1, hp, new_failure, _ = rolloutTape(new_tp, new_tape)
            # reset UI
            time.sleep(1)
            pg.click(853, 811)
            time.sleep(1)
            pg.click(1132, 726)
            time.sleep(1)
            clear_output(wait=True)  # <-- ADD THIS

            # verify ONLY if contender for best
            r, new_dollars, did_verify, verified_failure = verify_if_best(
                new_tp, new_tape, r1, d1, best_global
            )

            if did_verify:
                new_failure = verified_failure

            candidate = (new_tp, new_tape, r, new_dollars, new_failure)
            candidates.append(candidate)

            # update best_global immediately
            if score(r, new_dollars) > score(best_global[2], best_global[3]):
                best_global = candidate
                no_improvement_counter = 0

                msg = f"✅ New BEST: Round={r}, Money={new_dollars}"
                print(msg)
                post_to_discord(msg)
            else:
                no_improvement_counter += 1

            msg = f"Iter {iteration}: Round={r}, Money={new_dollars}"
            print(msg)
            post_to_discord(msg)

            # reset UI
            time.sleep(1)
            pg.click(853, 811)
            time.sleep(1)
            pg.click(1132, 726)
            time.sleep(1)

            iteration += 1

    combined = beam + candidates
    combined = sorted(combined, key=lambda x: score(x[2], x[3]), reverse=True)

    beam = combined[:BEAM_WIDTH]

    msg = f"BEST: Round={best_global[2]}, Money={best_global[3]}"
    print(msg)
    post_to_discord(msg)

    # ----------------------------
    # Stagnation → rollback
    # ----------------------------
    if no_improvement_counter >= STAGNATION_LIMIT:
        msg = "⚠️ Stagnation detected — rolling back suffix"
        print(msg)
        post_to_discord(msg)

        tp, tape, r, dollars, failure_step = best_global

        rollback_point = int(failure_step * ROLLBACK_RATIO)

        new_tp, new_tape = modifyTape(
            tp,
            tape,
            rollback_point,
            mapSpecificHeatmap,
            actionTypeFlipChance=1.0,
            buyTowerReselectionChance=1.0,
            buyCoordinateModificationChance=1.0,
            upgradePathModificationChance=1.0,
            upgradeTowerModificationChance=1.0,
            targetingMutationChance=1.0
        )

        r1, d1, hp, new_failure, _ = rolloutTape(new_tp, new_tape)
        # reset UI
        time.sleep(1)
        pg.click(853, 811)
        time.sleep(1)
        pg.click(1132, 726)
        time.sleep(1)
        clear_output(wait=True)  # <-- ADD THIS

        r, d, _, new_failure = verify_if_best(
            new_tp, new_tape, r1, d1, best_global
        )

        beam = [(new_tp, new_tape, r, d, new_failure)]
        best_global = beam[0]
        no_improvement_counter = 0

        msg = f"ROLLBACK RESULT: Round={r}, Money={d}"
        print(msg)
        post_to_discord(msg)