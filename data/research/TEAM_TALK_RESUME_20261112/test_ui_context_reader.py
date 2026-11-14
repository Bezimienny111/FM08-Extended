import struct
import unittest
from ui_context_reader import active_human, frontend_active_human, ContextUnavailable

class Memory:
    def __init__(self): self.data={}
    def put(self,a,b):
        for i,v in enumerate(b):self.data[a+i]=v
    def u32(self,a,v):self.put(a,struct.pack("<I",v))
    def read(self,a,n):
        try:return bytes(self.data[a+i] for i in range(n))
        except KeyError as exc:raise AssertionError("fixture missing read "+hex(a)) from exc
    def zero(self,a,n):self.put(a,b"\0"*n)

def fixture():
    m=Memory()
    for a,n in [(0x10000,0x40),(0x20000,16),(0x21000,12),(0x22000,16),
                (0x23000,4),(0x24000,4),(0x25000,12),(0x26000,4),
                (0x28000,0x20),(0x2A000,16),(0x30000,0x2C0),
                (0x40000,0x44),(0x50000,0x20),(0x01B2424C,8),(0x01B1ECD0+0x38,4)]:
        m.zero(a,n)
    m.u32(0x10000+0x3C,0x20000)
    m.u32(0x20000,0x0166A12C);m.u32(0x20004,0x27000);m.u32(0x20008,1);m.u32(0x27000,0x21000)
    m.put(0x21000,struct.pack("<III",0x22000,0x23000,0x4868756D))
    m.u32(0x23000,0x0166E1A4)
    m.u32(0x22000,0x0166A12C);m.u32(0x22004,0x24000);m.u32(0x22008,1);m.u32(0x24000,0x25000)
    m.put(0x25000,struct.pack("<III",0x01000003,0x26000,0x64726566));m.u32(0x26000,0x0166DDE4)
    m.u32(0x01B1ECD0+0x38,0x28000);m.u32(0x28000,0x01595ED4)
    m.u32(0x28010,0x012942DC);m.u32(0x28014,0x2A000);m.u32(0x28018,4)
    m.u32(0x2A00C,0x3029C);m.u32(0x3029C,0x015AE024);m.u32(0x3029C+0x14,12345);m.u32(0x3029C+0x18,3)
    m.u32(0x30000,0x015AE30C);m.u32(0x30298,0x29C);m.u32(0x30070,0x40000)
    m.u32(0x40038,0x50000);m.u32(0x40018,902);m.u32(0x50000,0x015996C4);m.u32(0x50018,870)
    fmap={0x0166A12C+0x28:0x00F4C110,0x0166E1A4+0x54:0x00F5D770,0x012942DC+0x2C:0x00F9A0D0}
    return m,fmap

class HumanContextTests(unittest.TestCase):
    def resolve(self,m,f):
        return active_human(m.read,lambda a:f[a],0x10000,
                            lambda p:".?AVTEAM@@" if p==0x40000 else "foreign")

    def test_native_route_without_invoking_a_function(self):
        m,f=fixture();r=self.resolve(m,f)
        self.assertEqual(r["person_index"],3);self.assertEqual(r["person_uid"],12345)
        self.assertEqual(r["team_uid"],902);self.assertEqual(r["club_uid"],870)

    def test_wrong_ui_type_is_rejected(self):
        m,f=fixture();m.u32(0x23000,1)
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_non_person_or_sentinel_ref_rejected(self):
        for bad in (0x18000003,0x017FFFFF,0x01800003):
            m,f=fixture();m.u32(0x25000,bad)
            with self.subTest(bad=bad),self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_foreign_context_rejected(self):
        m,f=fixture();m.u32(0x22008,2);m.u32(0x24004,0x26010)
        m.put(0x26010,struct.pack("<III",5,6,0x64636E74))
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_fake_human_primary_is_rejected(self):
        m,f=fixture();m.u32(0x30000,1)
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_same_vtable_with_wrong_person_index_is_rejected(self):
        m,f=fixture();m.u32(0x3029C+0x18,2)
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_nonclub_team_is_rejected(self):
        m,f=fixture();m.put(0x40040,b"\1")
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

    def test_missing_human_is_unavailable(self):
        m,f=fixture();m.u32(0x20008,0)
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

class FrontendHumanTests(unittest.TestCase):
    def fixture(self):
        m,f=fixture()
        for a,n in [(0x01915230,12),(0x60000,4),(0x61000,16),(0x62000,8)]:
            m.zero(a,n)
        m.u32(0x01915230,0x61000);m.u32(0x01915234,0x60000)
        m.u32(0x61000,0x01294CD4);m.u32(0x61004,0x62000)
        m.put(0x61008,struct.pack("<h",1));m.u32(0x62000,0x60000);m.u32(0x60000,3)
        f[0x01294CD4+0x2C]=0x00913D30
        return m,f
    def resolve(self,m,f):
        return frontend_active_human(m.read,lambda a:f[a],
            lambda p:".?AVTEAM@@" if p==0x40000 else "foreign")
    def test_unique_typed_frontend_member(self):
        m,f=self.fixture();r=self.resolve(m,f)
        self.assertEqual(r["person_uid"],12345)
        self.assertEqual(r["team_uid"],902)
        self.assertEqual(r["frontend_member"],0x60000)
    def test_missing_or_duplicate_membership_rejected(self):
        for count,pointer in [(1,0x60004),(2,0x60000)]:
            m,f=self.fixture();m.put(0x61008,struct.pack("<h",count));m.u32(0x62000,pointer);m.u32(0x62004,pointer)
            with self.subTest(count=count),self.assertRaises(ContextUnavailable):self.resolve(m,f)
    def test_nonlocal_ui_mode_rejected(self):
        m,f=self.fixture();m.u32(0x01915238,1)
        with self.assertRaises(ContextUnavailable):self.resolve(m,f)

if __name__=="__main__":unittest.main(verbosity=2)
