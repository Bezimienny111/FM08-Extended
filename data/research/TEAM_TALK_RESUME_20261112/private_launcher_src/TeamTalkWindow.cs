namespace FmLauncher;

// Context admission and standard-talk edit lock only; completion remains false.
internal static class TeamTalkWindow
{
    internal static bool IsCurrent(uint status,int phase,int stored,int counter)
    {
        if(phase is not (0 or 1) || (status&(0xcU|0x18000000U))!=0 ||
            (status&0x20000)==0 || (status&0x10)==0 || stored!=phase || counter!=phase+1)return false;
        int stage=(int)((~(status>>6))&1) | ((status&1)!=0?0:2);
        return stage==(phase==0?2:3);
    }
}
