"""RPM-only equivalents of pinned UI property/person lookup functions.

All object routes are bounded and fail closed; no native function is invoked.
"""
import struct

class ContextUnavailable(ValueError): pass

def active_human(read, file_u32, screen_address, class_name):
    def u32(a): return struct.unpack("<I", read(a, 4))[0]
    def i32(a): return struct.unpack("<i", read(a, 4))[0]
    def byte(a): return read(a, 1)[0]

    def property_value(pl, key):
        if u32(pl) != 0x0166A12C:
            raise ContextUnavailable("not PROPERTY_VALUE_LIST")
        if file_u32(0x0166A12C + 0x28) != 0x00F4C110:
            raise ContextUnavailable("property-list getter mismatch")
        before=read(pl+4,8)
        data,count=struct.unpack("<II",before)
        if count>128:
            raise ContextUnavailable("property-list count not admitted")
        pointers=struct.unpack("<"+"I"*count,read(data,count*4)) if count else ()
        matches=[]
        for address in pointers:
            raw=read(address,12)
            payload,kind,identifier=struct.unpack("<III",raw)
            if identifier==key:
                matches.append((address,payload,kind,raw[:8]))
        if read(pl+4,8)!=before:
            raise ContextUnavailable("property list changed")
        if len(matches)>1:
            raise ContextUnavailable("duplicate context property")
        return matches[0] if matches else None

    def local_reference(pl):
        missing=read(0x01B2424C,8)
        context=property_value(pl,0x64636E74)
        if context and context[3] != missing:
            raise ContextUnavailable("nonlocal/foreign reference context")
        ref=property_value(pl,0x64726566)
        if not ref or not ref[2] or u32(ref[2])!=0x0166DDE4:
            raise ContextUnavailable("missing typed dref")
        packed=ref[1]
        if packed>>24 != 1 or packed & 0x00FFFFFF >= 0x007FFFFF:
            raise ContextUnavailable("unsupported person reference")
        return packed,packed & 0x007FFFFF

    screen_pl=u32(screen_address+0x3C)
    human=property_value(screen_pl,0x4868756D)
    if not human or not human[2] or u32(human[2])!=0x0166E1A4:
        raise ContextUnavailable("active screen has no typed Hhum")
    # The PROPERTY_LIST converter F5D770 returns the payload dword unchanged.
    if file_u32(0x0166E1A4+0x54)!=0x00F5D770:
        raise ContextUnavailable("property-list conversion mismatch")
    packed,index=local_reference(human[1])

    table=u32(0x01B1ECD0+0x38)
    if u32(table)!=0x01595ED4:
        raise ContextUnavailable("not local DATABASE_TABLE<PERSON>")
    array=table+0x10 if index<u32(table+0x18) else u32(table+4)
    vtable=u32(array)
    if vtable not in {0x012942DC,0x01597E68} or file_u32(vtable+0x2C)!=0x00F9A0D0:
        raise ContextUnavailable("person array getter not admitted")
    data,count=struct.unpack("<II",read(array+4,8))
    if not index<count<=4000000:
        raise ContextUnavailable("person reference out of bounds")
    person=u32(data+index*4)
    # This is a secondary PERSON_TABLE base of HUMAN_NON_PLAYER (COL+4=29c).
    if u32(person)!=0x015AE024 or u32(person+0x18)!=index or i32(person+0x14)<=0:
        raise ContextUnavailable("not expected human PERSON_TABLE")
    complete=person-0x29C
    if u32(complete)!=0x015AE30C:
        raise ContextUnavailable("not HUMAN_NON_PLAYER complete object")

    # Native CBA790 -> C812C0 -> C7C7A0, translated as reads only.
    adjusted=person-i32(person-4)+0x10C
    team=u32(adjusted-0x9C)
    if class_name(team)!=".?AVTEAM@@" or byte(team+0x40)!=0:
        raise ContextUnavailable("human has no local club TEAM")
    club=u32(team+0x38)
    if u32(club)!=0x015996C4:
        raise ContextUnavailable("not expected CLUB")
    if local_reference(human[1])!=(packed,index) or u32(screen_address+0x3C)!=screen_pl:
        raise ContextUnavailable("active human changed")
    return {"status":"VERIFIED_LOCAL_HUMAN_OWN_CLUB",
            "packed_person_reference":packed,"person_index":index,
            "person_table":person,"human_complete_object":complete,
            "person_uid":u32(person+0x14),"team":team,"team_uid":u32(team+0x18),
            "club":club,"club_uid":u32(club+0x18)}

def frontend_active_human(read, file_u32, class_name):
    """Native frontend-selected CLIENT_HUMAN member -> local HUMAN_NON_PLAYER.

    Entry membership is checked against CLIENT_HUMAN_ARRAY, not guessed from
    manager flags or home/away ordering. No functions are called in FM.
    """
    def u32(a):return struct.unpack("<I",read(a,4))[0]
    def i32(a):return struct.unpack("<i",read(a,4))[0]
    def byte(a):return read(a,1)[0]
    selected=u32(0x01915234)
    mode=u32(0x01915238)
    listing=u32(0x01915230)
    if not selected or mode&1 or not listing:
        raise ContextUnavailable("no admitted frontend active-human context")
    if u32(listing)!=0x01294CD4 or file_u32(0x01294CD4+0x2C)!=0x00913D30:
        raise ContextUnavailable("not CLIENT_HUMAN_ARRAY")
    header=read(listing+4,6)
    data,count=struct.unpack("<Ih",header)
    if not 1<=count<=16:
        raise ContextUnavailable("frontend human count not admitted")
    members=struct.unpack("<"+"I"*count,read(data,count*4))
    if members.count(selected)!=1:
        raise ContextUnavailable("active human is not one unique list member")
    index=u32(selected)
    if index>=0x007FFFFF:
        raise ContextUnavailable("invalid active human PERSON index")
    table=u32(0x01B1ECD0+0x38)
    if u32(table)!=0x01595ED4:
        raise ContextUnavailable("not local DATABASE_TABLE<PERSON>")
    array=table+0x10 if index<u32(table+0x18) else u32(table+4)
    vt=u32(array)
    if vt not in {0x012942DC,0x01597E68} or file_u32(vt+0x2C)!=0x00F9A0D0:
        raise ContextUnavailable("person array getter not admitted")
    data,count=struct.unpack("<II",read(array+4,8))
    if not index<count<=4000000:
        raise ContextUnavailable("person reference out of bounds")
    person=u32(data+index*4)
    if u32(person)!=0x015AE024 or u32(person+0x18)!=index or i32(person+0x14)<=0:
        raise ContextUnavailable("not HUMAN_NON_PLAYER secondary PERSON_TABLE")
    complete=person-0x29C
    if u32(complete)!=0x015AE30C:
        raise ContextUnavailable("not HUMAN_NON_PLAYER complete object")
    adjusted=person-i32(person-4)+0x10C
    team=u32(adjusted-0x9C)
    if class_name(team)!=".?AVTEAM@@" or byte(team+0x40)!=0:
        raise ContextUnavailable("active human has no local club TEAM")
    club=u32(team+0x38)
    if u32(club)!=0x015996C4:
        raise ContextUnavailable("not expected CLUB")
    if (u32(0x01915234)!=selected or u32(0x01915230)!=listing
        or u32(0x01915238)!=mode or read(listing+4,6)!=header
        or u32(selected)!=index):
        raise ContextUnavailable("frontend context changed during read")
    return {"status":"VERIFIED_FRONTEND_HUMAN_MEMBER","source":"504B60/508FF0/4F9300/8D9AE0/C21650",
            "frontend_member":selected,"frontend_array":listing,"person_index":index,
            "person_uid":u32(person+0x14),"person_table":person,
            "human_complete_object":complete,"team":team,"team_uid":u32(team+0x18),
            "club":club,"club_uid":u32(club+0x18)}
