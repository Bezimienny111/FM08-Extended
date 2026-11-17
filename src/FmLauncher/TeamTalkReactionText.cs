namespace FmLauncher;

internal static class TeamTalkReactionText
{
    private static readonly (ulong Bit,string Pl,string En)[] Flags=
    [
        (1,"Motywacja","Motivated"),(2,"Pobudzenie","Fired up"),
        (4,"Lepsze morale","Morale boost"),(8,"Spadek morale","Morale drop"),
        (0x10,"Demotywacja","Demotivated"),(0x20,"Mniejsza presja","Pressure relieved"),
        (0x40,"Większa presja","More pressure"),(0x80,"Słabsze skupienie","Lower focus"),
        (0x100,"Lepsze skupienie","Improved focus"),(0x200,"Zadowolenie","Happy"),
        (0x400,"Niezadowolenie","Unhappy"),(0x800,"Złość","Angry"),
        (0x1000,"Poczucie niesprawiedliwości","Felt victimised"),
        (0x2000,"Poczucie docenienia","Felt admired"),
        (0x4000,"Zazdrość o kolegę","Jealous of teammate"),
        (0x8000,"Dezorientacja","Confused"),(0x10000,"Zignorował rozmowę","Ignored the talk")
    ];
    internal static string Format(ulong mask,bool polish)
    {
        if(mask==0)return polish?"Brak szczególnej reakcji":"No particular reaction";
        // Native B1AA70 applies fire-up, ELSE motivate, ELSE the negative drive
        // branch. Keep the raw mask in evidence/frames, but do not present the
        // skipped demotivation branch as a second effective drive result.
        if((mask&2)!=0)mask&=~(1UL|0x10UL);
        else if((mask&1)!=0)mask&=~0x10UL;
        var words=Flags.Where(f=>(mask&f.Bit)!=0).Select(f=>polish?f.Pl:f.En).ToList();
        if((mask&~0x1ffffUL)!=0)words.Add(polish?"Inna reakcja":"Other reaction");
        return string.Join("; ",words);
    }
}
