"""Conservative context/edit-window predicate; never an executor completion proof."""
from dataclasses import dataclass
from team_talk_model import native_ui_stage

@dataclass(frozen=True)
class StandardTalkWindow:
    admitted: bool
    kind: str
    reason: str
    standard_edit_locked: bool = False
    completion_verified: bool = False

def standard_talk_window(status, phase, stored_phase, counter):
    if any(type(x) is not int for x in (status,phase,stored_phase,counter)) or not 0<=status<=0xffffffff:
        return StandardTalkWindow(False,"unknown","invalid raw state")
    if phase==5:
        return StandardTalkWindow(False,"unsupported","end-of-regular/extra-time transition; clear")
    if phase not in (0,1):
        return StandardTalkWindow(False,"unsupported","unsupported talk period; clear")
    if status & (0xc|0x18000000):
        return StandardTalkWindow(False,"unknown","native stop/transition flag; clear")
    if not status & 0x20000 or not status & 0x10:
        return StandardTalkWindow(False,"unknown","outside supported ordinary live period")
    stage=native_ui_stage(status)
    kind={0:"prematch",1:"halftime"}[phase]
    if stage != {0:2,1:3}[phase]:
        return StandardTalkWindow(False,kind,"talk is editable or period mismatch; clear")
    if stored_phase!=phase or counter!=phase+1:
        return StandardTalkWindow(False,kind,"not pinned standard slot0/1; clear")
    return StandardTalkWindow(True,kind,"ordinary running context and standard packet builder lock",True)
