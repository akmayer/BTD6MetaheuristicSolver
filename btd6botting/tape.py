import random
from collections import defaultdict

import numpy as np

from .config import (
    TOWER_PLACEMENT_KEYS,
    TOWER_X_MAX,
    TOWER_X_MIN,
    TOWER_Y_MAX,
    TOWER_Y_MIN,
)


def sampleCoordinate(towerPlacementDistribution, T=0.5, n=10):
    dist = towerPlacementDistribution.copy()

    mask = np.zeros_like(dist, dtype=bool)
    mask[TOWER_Y_MIN : TOWER_Y_MAX + 1, TOWER_X_MIN : TOWER_X_MAX + 1] = True

    dist[~mask] = 0.0
    dist /= dist.sum()

    dist_temp = dist ** (1 / T)
    dist_temp /= dist_temp.sum()

    flat_dist = dist_temp.ravel()
    flat_indices = np.arange(flat_dist.size)

    sampled_indices = np.random.choice(flat_indices, size=n, replace=False, p=flat_dist)

    coords = np.column_stack(np.unravel_index(sampled_indices, dist.shape))
    y_coords, x_coords = coords[:, 0], coords[:, 1]

    coordinates = [(int(x), int(y)) for x, y in zip(x_coords, y_coords)]
    if n == 1:
        return coordinates[0]
    return coordinates


def sampleRandomPurchase(towerPlacementDistribution, T=0.5):
    coordinates = sampleCoordinate(towerPlacementDistribution, T, 10)

    towerKey = random.choice(TOWER_PLACEMENT_KEYS)

    if random.random() < 0.5:
        targeting = "strong"
    else:
        targeting = "first"
    return towerKey, coordinates, targeting


def sampleRandomUpgrade(boughtTowers):
    towerKey = random.choice([x for x in list(boughtTowers.keys()) if boughtTowers[x] > 0])
    towerPlacementIdx = random.choice(range(boughtTowers[towerKey]))
    upgradeKey = random.choice([",", ".", "/"])
    return upgradeKey, towerKey, towerPlacementIdx


def generateRandomActionTape(
    towerPlacementDistribution,
    T=0.5,
    maxTowers=15,
    avgUpgradesPerTowerPurchase=2.5,
    numActions=40,
    freeDartMonkey=True,
):
    tapeParameters = (maxTowers, avgUpgradesPerTowerPurchase)
    actionTape = []
    boughtTowers = {}
    numTowersBought = 0

    for i in range(numActions):
        buyWeight = 1 / (1 + avgUpgradesPerTowerPurchase)
        upgradeWeight = avgUpgradesPerTowerPurchase / (1 + avgUpgradesPerTowerPurchase)

        actionIdentifier = random.choices(["buy", "upgrade"], weights=[buyWeight, upgradeWeight], k=1)[0]
        actionIdentifier = "buy" if (i <= 1) else actionIdentifier
        actionIdentifier = "upgrade" if (numTowersBought == (2 * maxTowers)) else actionIdentifier

        if actionIdentifier == "buy":
            towerKey, coordinates, targeting = sampleRandomPurchase(towerPlacementDistribution, T=0.5)

            if i == 0:
                towerKey = "u"

            elif freeDartMonkey and i == 1:
                towerKey = "q"
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

        else:
            upgradeKey, towerKey, towerPlacementIdx = sampleRandomUpgrade(boughtTowers)
            actionTape.append(("upgrade", (upgradeKey, towerKey, towerPlacementIdx)))

    return tapeParameters, actionTape


def probabilistic_adjacent_swap(lst, actionTranspositionChance):
    result = lst.copy()

    for i in range(0, len(result) - 1, 2):
        if random.random() < actionTranspositionChance:
            result[i], result[i + 1] = result[i + 1], result[i]

    return result


def mutateCoordinates(oldCoordinateList, buyCoordinateModificationChance, towerDistMap, T=0.5):
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
        towerKey = random.choice(TOWER_PLACEMENT_KEYS)
    else:
        towerKey = oldTowerKey
    return towerKey


def mutateTargeting(oldTargeting, targetingMutationChance):
    if random.random() < targetingMutationChance:
        if random.random() < 0.5:
            targeting = "strong"
        else:
            targeting = "first"
    else:
        targeting = oldTargeting
    return targeting


def mutateUpgradeKey(oldUpgradePath, upgradePathModificationChance):
    if random.random() < upgradePathModificationChance:
        upgradeKey = random.choice([",", ".", "/"])
    else:
        upgradeKey = oldUpgradePath
    return upgradeKey


def mutateUpgradeTowerSelectionKey(
    oldTowerKey, oldPlacementIdx, boughtTowers, upgradeTowerModificationChance
):
    if random.random() < upgradeTowerModificationChance or boughtTowers[oldTowerKey] == 0:
        towerKey = random.choice([x for x in list(boughtTowers.keys()) if boughtTowers[x] > 0])
        towerPlacementIdx = random.choice(range(boughtTowers[towerKey]))
    else:
        towerKey = oldTowerKey
        towerPlacementIdx = oldPlacementIdx
    return towerKey, towerPlacementIdx


def modifyTape(
    tapeParameters,
    tape,
    frozenPrefixSize,
    towerPlacementDistribution,
    T=0.5,
    actionTypeFlipChance=0.1,
    buyTowerReselectionChance=0.1,
    buyCoordinateModificationChance=0.15,
    upgradePathModificationChance=0.1,
    upgradeTowerModificationChance=0.1,
    targetingMutationChance=0.2,
    failureStep=10000000000,
):
    maxTowers, avgUpPerTower = tapeParameters

    maxTowers += random.randint(-1, 1)
    avgUpPerTower += random.random() - 0.5

    boughtTowers = defaultdict(int)
    numBoughtTowers = 0

    newTape = []

    for idx in range(min(frozenPrefixSize, len(tape))):
        actionIdentifier, actionParameters = tape[idx]

        newTape.append((actionIdentifier, actionParameters))

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
            pass

    for idx in range(frozenPrefixSize, len(tape)):
        actionIdentifier, actionParameters = tape[idx]

        if idx == failureStep:
            buyTowerReselectionChance = 1.0
            buyCoordinateModificationChance = 1.0
            upgradePathModificationChance = 1.0
            upgradeTowerModificationChance = 1.0
            targetingMutationChance = 1.0

        if idx == 0:
            heroKey, coordinateList, targeting = actionParameters

            newCoordinateList = mutateCoordinates(
                coordinateList, buyCoordinateModificationChance, towerPlacementDistribution
            )
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append((actionIdentifier, (heroKey, newCoordinateList, newTargeting)))
            numBoughtTowers += 1
            continue

        elif idx == 1:
            towerKey, coordinateList, targeting = actionParameters

            newTowerKey = mutateTowerKey(towerKey, buyTowerReselectionChance)
            newCoordinateList = mutateCoordinates(
                coordinateList, buyCoordinateModificationChance, towerPlacementDistribution
            )
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append((actionIdentifier, (newTowerKey, newCoordinateList, newTargeting)))

            boughtTowers[newTowerKey] += 1
            numBoughtTowers += 1
            continue

        if actionIdentifier == "buy":
            if random.random() < (actionTypeFlipChance * (avgUpPerTower / (1 + avgUpPerTower))):
                newUpgradeActionParameters = sampleRandomUpgrade(boughtTowers)
                newTape.append(("upgrade", newUpgradeActionParameters))
                continue

            towerKey, coordinateList, targeting = actionParameters

            newTowerKey = mutateTowerKey(towerKey, buyTowerReselectionChance)
            newCoordinateList = mutateCoordinates(
                coordinateList, buyCoordinateModificationChance, towerPlacementDistribution
            )
            newTargeting = mutateTargeting(targeting, targetingMutationChance)

            newTape.append(("buy", (newTowerKey, newCoordinateList, newTargeting)))

            boughtTowers[newTowerKey] += 1
            numBoughtTowers += 1
            continue

        elif actionIdentifier == "upgrade":
            if random.random() < (actionTypeFlipChance * (1 / (1 + avgUpPerTower))) and (
                numBoughtTowers < 2 * maxTowers
            ):
                towerKey, coordinates, targeting = sampleRandomPurchase(towerPlacementDistribution)

                newTape.append(("buy", (towerKey, coordinates, targeting)))

                boughtTowers[towerKey] += 1
                numBoughtTowers += 1
                continue

            upgradeKey, towerKey, placementIdx = actionParameters

            newUpgradeKey = mutateUpgradeKey(upgradeKey, upgradePathModificationChance)
            newTowerKey, newPlacementIdx = mutateUpgradeTowerSelectionKey(
                towerKey,
                placementIdx,
                boughtTowers,
                upgradeTowerModificationChance,
            )

            newTape.append(("upgrade", (newUpgradeKey, newTowerKey, newPlacementIdx)))
            continue

    return (maxTowers, avgUpPerTower), newTape
