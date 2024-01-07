#!/usr/bin/python3 -u

import serial
import numpy as np
import json
import sys
import itertools


FILENAME_LEFT = '/dev/ttyACM0'
FILENAME_RIGHT = '/dev/ttyACM1'

DIFF_THRESH = 50

quadrant_left = serial.Serial(FILENAME_LEFT, 115200)
quadrant_right = serial.Serial(FILENAME_RIGHT, 115200)

scale_left = [0, 2, 4, 7]
scale_right = [9, 12, 14, 16]

report_left = None
report_right = None

"""
bs_last = np.ones(8, dtype=np.float32) * 512
hit_dist_left = [512,512,512,512]
hit_dist_right = [512,512,512,512]
engaged_left = [False, False, False, False]
engaged_right = [False, False, False, False]
was_engaged_left = [False, False, False, False]
was_engaged_right = [False, False, False, False]
elevation_was_engaged = False
"""

any_were_engaged = False
cof = 0

while True:

    while quadrant_left.in_waiting:
        report_raw = quadrant_left.readline();
        try:
            report_left = json.loads(report_raw)
        except json.decoder.JSONDecodeError:
            print('failed to parse')
            continue

    while quadrant_right.in_waiting:
        report_raw = quadrant_right.readline();
        try:
            report_right = json.loads(report_raw)
        except json.decoder.JSONDecodeError:
            print('failed to parse')
            continue

    if (report_left and report_right):

        print()

        # cycle COF on elevation first engaged
        """
        elevation_engaged =  (report_left['elevation']['en'] or report_right['elevation']['en'])
        if (elevation_engaged and (not elevation_was_engaged)):
            cof = (cof + 7) % 12
            print('cof %d;' % cof)
        """

        # if any_engaged has a rising edge, then do a key chnage
        any_engaged = False
        for r,k in itertools.product([report_left, report_right], ['l0', 'l1', 'l2', 'l3']):
            if r[k]['en']:
                any_engaged = True
                break
        if (any_engaged and not any_were_engaged):
            cof = (cof + 7) % 12
            print('cof %d;' % cof)
        any_were_engaged = any_engaged

        # board sample
        bs_left = tuple(np.clip(report_left[s]['dist'], 0,512) for s in ['l0', 'l1', 'l2', 'l3'])
        bs_right = tuple(np.clip(report_right[s]['dist'], 0,512) for s in ['l0', 'l1', 'l2', 'l3'])
        bs = np.array(bs_left + bs_right, dtype=np.float32)
        print('bs %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f;' % tuple(bs))

        # elevations
        aveL = (1 - report_left['elevation']['val']) * 1023
        aveR = (1 - report_right['elevation']['val']) * 1023
        print('aves %.2f %.2f;' % (aveL, aveR))

        # pitch
        pitchL = report_left['pitch']['val'] * 512
        pitchR = report_right['pitch']['val'] * 512
        print('pitches %.2f %.2f;' % (pitchL, pitchR))

        # roll
        rollL = report_left['roll']['val'] * 512
        rollR = report_right['roll']['val'] * 512
        print('rolls %.2f %.2f;' % (rollL, rollR))

        # events
        hits = ['hit0', 'hit1', 'hit2', 'hit3']
        events_left = report_left['events']
        for e in events_left:
            if e in hits:
                i = hits.index(e)
                print('hitL %d %.4f;' % (scale_left[i], 0.25))
            elif e == 'swl':
                print('lswipe 0;')
            elif e == 'swr':
                print('lswipe 1;')
        events_right = report_right['events']
        for e in events_right:
            if e in hits:
                i = hits.index(e)
                print('hitR %d %.4f;' % (scale_right[i], 0.25))
            elif e == 'swl':
                print('rswipe 0;')
            elif e == 'swr':
                print('rswipe 1;')

        # hits (velocity)
        """
        diff = bs_last - bs
        for i in range(8):
            #print('diff: (%d): %.2f' % (i,diff[i]))
            if (diff[i] > DIFF_THRESH):
                vel = diff[i] / 800
                if i < 4:
                    note = scale_left[i]
                    print('hitL %d %.4f;' % (note, vel))
                else:
                    note = scale_right[i-4]
                    print('hitR %d %.4f;' % (note, vel))
        """

        # swipes
        """
        if report_right['arc']['swr'] or report_right['arc']['swl']:
            print('modeselektor bang;')
        """

        # reset
        """
        bs_last = bs.copy()
        was_engaged_left = engaged_left.copy()
        was_engaged_right = engaged_right.copy()
        elevation_was_engaged = elevation_engaged
        report_left = None
        report_right = None
        """

