# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 16:52:35 2020

@author: super
"""
import math
from typing import List

import cv2

from notes.note_objects import Stem, Note, Head, Flag, Beam, Accidental, AccidentalTypes
from staffs.staff_objects import Staff, Time
from template_matching.template_matching import template_matching_array, AvailableTemplates


def find_stems(staff: Staff) -> List[Stem]:
    img_bar = staff.image
    img_struct_ver = img_bar.copy()
    ver_size = int(img_bar.shape[0] / 15)
    ver_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_size))
    img_struct_ver2 = cv2.dilate(img_struct_ver, ver_struct, 1)
    img_struct_ver2 = cv2.erode(img_struct_ver2, ver_struct, 1)

    gray_ver = cv2.cvtColor(img_struct_ver2, cv2.COLOR_BGR2GRAY)
    (thresh_ver, im_bw_ver) = cv2.threshold(gray_ver, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    img_canny_ver = im_bw_ver.copy()
    gray2_ver = cv2.cvtColor(img_canny_ver, cv2.COLOR_GRAY2BGR)

    edges2_ver = cv2.Canny(gray2_ver, 100, 200)

    lines2_ver = cv2.HoughLinesP(edges2_ver, 1, math.pi, 1, None, 10,
                                 10)  # edges, rho, theta, threshold, --, minlinelen, maxlinegap

    #    imcopy = img_bar.copy()
    #    for linearr in lines2_ver:
    #        line = linearr[0]
    #        cv2.line(imcopy, (line[0],line[1]),(line[2],line[3]),(0,0,255),2)
    #
    #    cv2.imshow('stems', imcopy)

    stem_list: List[Stem] = []
    for line in lines2_ver:
        l = line[0]
        stem_list.append(Stem(l[0], l[1], l[2], l[3]))

    return stem_list


def detect_accidentals(staff: Staff, threshold: float, signature: Time) -> List[Accidental]:
    found_accidentals = template_matching_array(AvailableTemplates.AllKeys.value, staff, threshold)
    if len(found_accidentals.keys()) == 0:
        # No accidentals were found, so just cut to the chase already
        return []

    matched_accidentals: List[Accidental] = []
    for template in found_accidentals.keys():
        for match in found_accidentals[template]:
            matched_accidentals.append(Accidental(match[0], match[1], template))

    # Accidentals are sorted from left to right, in order to ease the application to notes later on
    matched_accidentals.sort(key=lambda acc: acc.x)

    for i in range(len(matched_accidentals)):
        current: Accidental = matched_accidentals[i]
        if current.acc_type in [AccidentalTypes.FLAT_DOUBLE, AccidentalTypes.SHARP_DOUBLE, AccidentalTypes.NATURAL]:
            # It is either a double flat, double sharp or a natural (and must therefore be local)
            current.set_is_local(True)
            continue

        previous: Accidental = matched_accidentals[i - 1]
        if previous:
            if previous.x - current.x < (staff.dist * 1.5) \
                    and (previous.y - current.y) > (staff.dist * 0.5) \
                    and previous.acc_type is current.acc_type:
                # A group of accidentals that are of the same type, sufficiently close and not on the same line
                previous.set_is_local(False)
                current.set_is_local(False)
            else:
                current.set_is_local(True)
                continue
        else:
            # clause that catches a single key accidental (so there is no previous)
            # Only works when at least one time signature was detected earlier!
            if signature:
                if current.x < signature.x:
                    current.set_is_local(False)
                else:
                    current.set_is_local(True)

    return matched_accidentals


def build_notes(heads: List[Head], stems: List[Stem], flags: List[Flag], beams: List[Beam],
                accidentals: List[Accidental], staff: Staff) -> List[Note]:
    dist = staff.dist
    nd = int(dist / 8)

    beam_names = {
        'single_beam': ('eighth', 2),
        'double_beam': ('sixteenth', 4),
        'triple_beam': ('demisemiquaver', 8)
    }

    notes: List[Note] = []

    for head in heads:
        hx1, hy1 = head.x, head.y
        hx2, hy2 = (hx1 + head.w, hy1 + head.h)

        for stem in stems:
            sx1, sy1 = stem.x, stem.y
            sx2, sy2 = (sx1 + stem.w, sy1 + stem.h)

            if sy1 in range(hy1, hy2 + 1) or sy2 in range(hy1, hy2 + 1):
                if sx1 in range(hx1 - nd, hx2 + nd + 1) or sx2 in range(hx1 - nd, hx2 + nd + 1):
                    x_min = min(sx1, sx2, hx1, hx2)
                    x_max = max(sx1, sx2, hx1, hx2)
                    y_min = min(sy1, sy2, hy1, hy2)
                    y_max = max(sy1, sy2, hy1, hy2)

                    head.connect()

                    if head.name == 'closed_notehead':
                        duration = 1
                        duration_text = 'quarter'
                    elif head.name == 'open_notehead':
                        duration = 2
                        duration_text = 'half'
                    else:
                        duration = 1
                        duration_text = 'unknown'
                    notes.append(Note(head, duration_text, duration * staff.divisions, (x_min, y_min, x_max, y_max)))

        if not head.connected:
            notes.append(Note(head, 'whole', 4 * staff.divisions, (hx1, hy1, hx2, hy2)))

    for note in notes:
        nx1, ny1 = note.x, note.y
        nx2, ny2 = (nx1 + note.w, ny1 + note.h)

        for flag in flags:
            fx1, fy1 = flag.x, flag.y
            fx2, fy2 = (fx1 + flag.w, fy1 + flag.h)

            if fy1 in range(ny1, ny2 + 1) or fy2 in range(ny1, ny2 + 1):
                if fx1 in range(nx1 - nd, nx2 + nd + 1) or fx2 in range(nx1 - nd, nx2 + nd + 1):
                    x_min = min(fx1, fx2, nx1, nx2)
                    x_max = max(fx1, fx2, nx1, nx2)
                    y_min = min(fy1, fy2, ny1, ny2)
                    y_max = max(fy1, fy2, ny1, ny2)

                    new_loc = (x_min, y_min, x_max, y_max)

                    if flag.name in ['flag_upside_down_1', 'flag_1']:
                        div = 2
                        duration_text = 'eighth'
                    elif flag.name in ['flag_upside_down_2', 'flag_2']:
                        div = 4
                        duration_text = 'sixteenth'
                    elif flag.name in ['flag_upside_down_3', 'flag_3']:
                        div = 8
                        duration_text = 'demisemiquaver'
                    else:
                        div = 2
                        duration_text = 'unknown'

                    note.update_location(new_loc)
                    note.update_duration(duration_text, int(note.duration / div))

        for beam in beams:
            bx1, by1 = beam.x, beam.y
            bx2, by2 = (bx1 + beam.w, by1 + beam.h)

            #            print(by1, by2, ny1, ny2)
            #            print(bx1, bx2, nx1, nx2, '\n')

            if by1 in range(ny1 - nd, ny2 + nd) or by2 in range(ny1 - nd, ny2 + nd):
                if bx1 in range(nx1 - nd, nx2 + nd + 1):
                    note.add_beam('begin', beam_names[beam.durname])
                elif bx2 in range(nx1 - nd, nx2 + nd + 1):
                    note.add_beam('end', beam_names[beam.durname])
                elif nx1 > bx1 + nd and nx2 < bx2 - nd:
                    note.add_beam('continue', beam_names[beam.durname])

    # TODO: somehow create full notes (check open heads not in note list?)

    # Apply accidentals to notes
    grouped_accidentals = group_accidentals(accidentals)
    for accidental_arr in grouped_accidentals:
        for accidental in accidental_arr:
            # Determine ranges for applying the accidentals (in case there is a key change somewhere in the staff)
            x_start = accidental_arr[0].x
            x_end = accidental_arr[-1].x + staff.dist * 1.5
            for _note in notes:
                if x_start <= _note.x < x_end and _note.note == accidental.note:
                    # Apply the accidental when it is in range, the same note,
                    # and non-local, or sufficiently close to the current note
                    if (not accidental.is_local) or (_note.x - accidental.x < staff.dist * 1.5):
                        _note.accidental = accidental

    return notes


# Group accidentals together in groups. Groups consist of local and nonlocal accidentals in alternating order
# Example: [n,n,n,l,l,l,l,n,l,l] -> [[n,n,n],[l,l,l,l],[n],[l,l]]
def group_accidentals(accidentals: List[Accidental]) -> List[List[Accidental]]:
    result: List[List[Accidental]] = [[]]
    group_index = 0
    for i in range(len(accidentals)):
        if accidentals[i].is_local:
            result[group_index].append(accidentals[i])
            group_index += 1
            continue
        else:
            while not accidentals[i].is_local:
                result[group_index].append(accidentals[i])
                i += 1
            group_index += 1
            continue

    return result
