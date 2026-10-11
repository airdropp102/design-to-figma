import unittest
from scripts.prepare_rotation import rotation_states, rotation_links

class RotationPlanTests(unittest.TestCase):
    def test_two_colors_eight_unique_views(self):
        states=rotation_states()
        self.assertEqual(len(states),16)
        self.assertEqual(len({s['key'] for s in states}),16)
        self.assertEqual({s['angle'] for s in states},set(range(0,360,45)))
        self.assertEqual({s['color'] for s in states},{'ivory','sage'})
    def test_wrap_and_preserve_angle_when_changing_color(self):
        states=rotation_states();by={s['key']:s for s in states}
        for s in states:
            links=rotation_links(s,states)
            self.assertEqual(by[links['angle.next']]['angle'],(s['angle']+45)%360)
            self.assertEqual(by[links['angle.prev']]['angle'],(s['angle']-45)%360)
            for color in ('ivory','sage'):
                target=by[links['color.'+color]]
                self.assertEqual(target['angle'],s['angle'])
                self.assertEqual(target['color'],color)
            cursor=s['key']
            for _ in range(8):cursor=rotation_links(by[cursor],states)['angle.next']
            self.assertEqual(cursor,s['key'])

if __name__=='__main__':unittest.main()
