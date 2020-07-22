from typing import TYPE_CHECKING, Optional, List, Union

from models.staff_objects import ClefTypes

if TYPE_CHECKING:
    from models.note_objects import Rest, Note
    from models.staff import Staff
    from models.staff_objects import Key, Clef, Time


class Measure:
    Gnotes = ['G', 'F', 'E', 'D', 'C', 'B', 'A']
    Goctave = 6

    def __init__(self, input_staff: 'Staff', nr: int, start: int, end: int):
        self.lines = input_staff.lines
        self.dist = input_staff.dist

        self.measure = nr
        self.start = start
        self.end = end

        self.show_clef: bool = False
        self.show_key: bool = False
        self.show_time: bool = False

        self.clef: Optional['Clef'] = None
        self.key: Optional['Key'] = None
        self.time: Optional['Time'] = None

        self.clef_line = 2

        self.notes = self.Gnotes
        self.octave = self.Goctave
        self.divisions = input_staff.divisions
        self.staff = input_staff

        self.note_objects: List['Note'] = []
        self.rest_objects: List['Rest'] = []
        self.chord_locs = []
        self.backup_locs = []
        self.backup_times = {}

    def set_clef(self, clef: 'Clef'):
        self.clef = clef
        self.update_clef()

    def set_clef_line(self, clef_line: int):
        self.clef_line = clef_line

    def set_key(self, key: 'Key'):
        self.key = key

    def set_time(self, time: 'Time'):
        self.time = time

    def update_clef(self):
        if self.clef.type == ClefTypes.G_CLEF.name:
            self.clef_line = 2
            self.notes = self.Gnotes
            self.octave = self.Goctave
        elif self.clef.type == ClefTypes.C_CLEF.name:
            self.clef_line = 3
            self.notes = self.Gnotes[6:] + self.Gnotes[:6]
            self.octave = self.Goctave - 1
        elif self.clef.type == ClefTypes.F_CLEF.name:
            self.clef_line = 4
            self.notes = self.Gnotes[5:] + self.Gnotes[:5]
            self.octave = self.Goctave - 2
        else:
            raise ValueError(f'{self.clef.type} is an unsupported Clef type')

    def set_divisions(self, div):
        self.divisions = div

    def assign_objects(self, notes: List['Note'], rests: List['Rest']):
        self.note_objects = [note for note in notes if self.start < note.x < self.end]
        self.rest_objects = [rest for rest in rests if self.start < rest.x < self.end]

    def get_objects(self) -> List[Union['Note', 'Rest']]:
        result: List[Union['Note', 'Rest']] = self.note_objects
        result += self.rest_objects
        return sorted(result, key=lambda x: x.x)

    def find_backups(self):
        objects = self.get_objects()
        for i in range(1, len(objects)):
            obj_1 = objects[i - 1]
            obj_2 = objects[i]
            if obj_1.x + obj_1.w > obj_2.x:
                if obj_1.duration == obj_2.duration:
                    if obj_1.type == obj_2.type == 'note':
                        self.chord_locs.append(i)
                    else:
                        self.backup_locs.append(i)
                        self.backup_times[i] = obj_1.duration
                elif obj_1.duration > obj_2.duration:
                    self.backup_locs.append(i)
                    self.backup_times[i] = obj_1.duration
                else:
                    objects[i - 1] = obj_2
                    objects[i] = obj_1
                    # switch objects
                    self.backup_locs.append(i)
                    self.backup_times[i] = obj_2.duration
