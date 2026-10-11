import unittest
from scripts.state_bridge import StateBridge

class PermissionProbeGateTests(unittest.TestCase):
    def check(self, wal, evidence):
        return StateBridge('.').is_verified_permission_probe(wal,evidence)
    def test_verified_single_registered_empty_root_is_probe(self):
        wal=[{'key':'screen:S01','status':'creating','node_id':'67:2','name':'S01 Trang chủ — Desktop'}]
        ev={'verified':True,'permission_probe':{'node_id':'67:2','name':wal[0]['name'],'type':'FRAME','page_id':'0:1','file_key':'file-key','child_count':0,'live_verified':True},'page_id':'0:1','figma_file_id':'file-key'}
        self.assertTrue(self.check(wal,ev))
        self.assertFalse(self.check(wal+wal,ev))
        ev['permission_probe']['child_count']=1
        self.assertFalse(self.check(wal,ev))
    def test_unverified_or_wrong_file_is_rejected(self):
        wal=[{'key':'screen:S01','status':'creating','node_id':'67:2','name':'S01 Trang chủ — Desktop'}]
        ev={'verified':True,'permission_probe':{'node_id':'67:2','name':wal[0]['name'],'type':'FRAME','page_id':'0:1','file_key':'wrong','child_count':0,'live_verified':True},'page_id':'0:1','figma_file_id':'file-key'}
        self.assertFalse(self.check(wal,ev))
        ev['permission_probe']['file_key']='file-key';ev['permission_probe']['live_verified']=False
        self.assertFalse(self.check(wal,ev))

if __name__=='__main__':unittest.main()
