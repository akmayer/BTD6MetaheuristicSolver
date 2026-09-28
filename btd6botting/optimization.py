import os
import random
import time

import keyboard
import numpy as np
import pyautogui as pg
from IPython.display import clear_output
from scipy.ndimage import gaussian_filter

from .gameplay import (
    rolloutTape,
)
from .notifications import post_to_discord
from .tape import generateRandomActionTape, modifyTape


def score(round_num, dollars):
    return (round_num, dollars)


def verify_if_best(tp, tape, r1, d1, current_best):
    if current_best is not None:
        if score(r1, d1) <= score(current_best[2], current_best[3]):
            return r1, d1, False, None

    msg = "🏆 Potential new best - verifying..."
    print(msg)
    post_to_discord(msg)

    r2, d2, hp2, f2, _ = rolloutTape(tp, tape)
    time.sleep(1)
    pg.click(853, 811)
    time.sleep(1)
    pg.click(1132, 726)
    time.sleep(1)
    clear_output(wait=True)

    vr = min(r1, r2)
    vd = min(d1, d2)

    msg = f"Verification: Initial=({r1},{d1}) vs Second=({r2},{d2}) -> Used=({vr},{vd})"
    print(msg)
    post_to_discord(msg)

    return vr, vd, True, f2


def getHeatmapRun():
    mask = np.ones(shape=(1080, 1920))

    tapeParameters, tape = generateRandomActionTape(
        mask,
        T=0.5,
        maxTowers=1,
        avgUpgradesPerTowerPurchase=1,
        numActions=1000,
    )
    r, dollas, hp, _, rednessArr = rolloutTape(tapeParameters, tape, 0)
    mask = (rednessArr >= 0.1 * rednessArr.max()) & (rednessArr <= 0.75 * rednessArr.max())
    mask = mask.astype(float)
    blurredLarge = gaussian_filter(mask, sigma=150, mode="constant")
    blurredSmall = gaussian_filter(mask, sigma=20, mode="constant")
    mask = np.clip(blurredLarge - blurredSmall, 0, np.inf)
    time.sleep(1)
    pg.click(853, 811)
    time.sleep(1)
    pg.click(1132, 726)
    time.sleep(1)
    return mask


def run_optimization():
    mask = np.ones(shape=(1080, 1920))
    tapeParameters, tape = generateRandomActionTape(mask, 0.5, 3, 3, 10)
    for action in tape:
        print(action)

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

    mapSpecificHeatmap = getHeatmapRun()

    time.sleep(2)

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
            numActions=1000,
        )

        for a in tape[:10]:
            print(a)

        r1, d1, hp, failure_step, _ = rolloutTape(tapeParameters, tape)
        time.sleep(1)
        pg.click(853, 811)
        time.sleep(1)
        pg.click(1132, 726)
        time.sleep(1)
        clear_output(wait=True)

        r, dollars, did_verify, new_failure = verify_if_best(tapeParameters, tape, r1, d1, best_global)

        if did_verify:
            failure_step = new_failure

        candidate = (tapeParameters, tape, r, dollars, failure_step)
        beam.append(candidate)

        if best_global is None or score(r, dollars) > score(best_global[2], best_global[3]):
            best_global = candidate

        msg = f"Exploration {x+1}: Round={r}, Money={dollars}"
        print(msg)
        post_to_discord(msg)

    beam = sorted(beam, key=lambda x: score(x[2], x[3]), reverse=True)[:BEAM_WIDTH]

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
                    failureStep=failure_step,
                )

                r1, d1, hp, new_failure, _ = rolloutTape(new_tp, new_tape)
                time.sleep(1)
                pg.click(853, 811)
                time.sleep(1)
                pg.click(1132, 726)
                time.sleep(1)
                clear_output(wait=True)

                r, new_dollars, did_verify, verified_failure = verify_if_best(
                    new_tp, new_tape, r1, d1, best_global
                )

                if did_verify:
                    new_failure = verified_failure

                candidate = (new_tp, new_tape, r, new_dollars, new_failure)
                candidates.append(candidate)

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

        if no_improvement_counter >= STAGNATION_LIMIT:
            msg = "⚠️ Stagnation detected - rolling back suffix"
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
                targetingMutationChance=1.0,
            )

            r1, d1, hp, new_failure, _ = rolloutTape(new_tp, new_tape)
            time.sleep(1)
            pg.click(853, 811)
            time.sleep(1)
            pg.click(1132, 726)
            time.sleep(1)
            clear_output(wait=True)

            r, d, _, new_failure = verify_if_best(new_tp, new_tape, r1, d1, best_global)

            beam = [(new_tp, new_tape, r, d, new_failure)]
            best_global = beam[0]
            no_improvement_counter = 0

            msg = f"ROLLBACK RESULT: Round={r}, Money={d}"
            print(msg)
            post_to_discord(msg)
