namespace FmLauncher;

internal sealed partial class SuspendedGameProcess
{
    internal uint ApplyTeamTalkUi(FileStream verified,bool polish)
    {
        uint code=Allocate(GameTeamTalkPatch.CodeSize),data=Allocate(GameTeamTalkPatch.DataSize);
        var payload=GameTeamTalkPatch.Build(code,data,polish);
        Write(data,payload.Data);Write(code,payload.Code);
        if(!Read(data,payload.Data.Length).SequenceEqual(payload.Data) || !Read(code,payload.Code.Length).SequenceEqual(payload.Code))
            throw new LauncherException("UnexpectedGameMemory");
        Protect(code,payload.Code.Length,0x20);Flush(code,payload.Code.Length);
        foreach(var (site,original,destination) in new (uint,byte[],uint)[]{
            (GameTeamTalkPatch.TitleAddress,GameTeamTalkPatch.TitleOriginal.ToArray(),payload.TitleEntry),
            (GameTeamTalkPatch.HintAddress,GameTeamTalkPatch.HintOriginal.ToArray(),payload.HintEntry),
            (GameTeamTalkPatch.CreateAddress,GameTeamTalkPatch.CreateOriginal.ToArray(),payload.CreateEntry),
            (GameTeamTalkPatch.CellAddress,GameTeamTalkPatch.CellOriginal.ToArray(),payload.CellEntry)})
        {
            byte[] expected=new byte[original.Length];verified.Position=site-0x400000;verified.ReadExactly(expected);
            if(!expected.SequenceEqual(original) || !Read(site,original.Length).SequenceEqual(original))
                throw new LauncherException("UnexpectedGameMemory");
            var protection=Protect(site,original.Length,0x40);var jump=BuildJump(site,destination,original.Length);
            Write(site,jump);Protect(site,original.Length,protection);Flush(site,original.Length);
            if(!Read(site,jump.Length).SequenceEqual(jump))throw new LauncherException("UnexpectedGameMemory");
        }
        return data;
    }
}
