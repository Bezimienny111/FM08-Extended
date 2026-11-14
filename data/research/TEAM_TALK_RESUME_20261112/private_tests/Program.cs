using System.Text.Json.Nodes;
using FmLauncher;

var captures = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "captures"));
var own = Path.Combine(captures, "dotnet-test-fixtures");
Directory.CreateDirectory(own);
var h = Path.Combine(captures, "frontend_human_8020_20261112T103744526014Z.json");
var m = Path.Combine(captures, "second_half_8020_20261112T100418461655Z.json");
var ht = Path.Combine(captures, "halftime_8020_20261112T095958781693Z.json");
var process = new TeamTalkProcess(8020, 134389467680297377, "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d");
var provider = new OfflineTeamTalkProvider();
int count = 0;
void Check(bool condition, string label) { if (!condition) throw new Exception(label); count++; }
async Task Reject(TeamTalkReadRequest request)
{
    try { await provider.ReadAsync(request, CancellationToken.None); }
    catch (InvalidDataException) { count++; return; }
    throw new Exception("Invalid capture admitted.");
}
var result = await provider.ReadAsync(new(process,m,h), CancellationToken.None);
Check(result.Kind == "halftime" && result.Relevant && result.Players.Count == 11, "H2 context/entries");
Check(!result.PublicationReady && !result.SimultaneousHumanMatch, "No implicit publication/own scope");
var before = await provider.ReadAsync(new(process,ht,h), CancellationToken.None);
Check(!before.Relevant && before.StoredPhase == 0 && before.RawPhase == 1, "Old prematch survived halftime");
await Reject(new(process with { CreationFiletime=process.CreationFiletime+1 },m,h));
async Task Corrupt(string name, Action<JsonObject> mutation)
{
    var document=JsonNode.Parse(await File.ReadAllTextAsync(m))!.AsObject();
    mutation(document);
    var target=Path.Combine(own,name+".json");
    await File.WriteAllTextAsync(target,document.ToJsonString());
    await Reject(new(process,target,h));
}
await Corrupt("torn", d=>d["second"]!["controller"]!["controlled_side"]=0);
await Corrupt("ambiguous", d=> {
    d["first"]!["match_slots"]!["controller_2648"]=1234;
    d["second"]=d["first"]!.DeepClone();
});
await Corrupt("invalid_uid", d=> {
    d["first"]!["matches"]!["controller_3c"]!["teams"]![0]!["manager"]!["last_or_staged_talk"]!["entries"]![0]!["uid"]=uint.MaxValue;
    d["second"]=d["first"]!.DeepClone();
});
var nativeMemory=new TeamTalkFixtureMemory(process);
var nativeProvider=new BoundedTeamTalkProvider(_=>nativeMemory);
var live=await nativeProvider.ReadAsync(new(process,"",""),CancellationToken.None);
Check(live.SimultaneousHumanMatch && live.Relevant && live.Players.Single().RawEffect==0x2011 && !live.PublicationReady,"Coherent provider result");
Check(nativeMemory.Reads<=768 && nativeMemory.TotalBytes<=32768,"Native read budget");
async Task RejectMemory(Action<TeamTalkFixtureMemory> mutate)
{
    var memory=new TeamTalkFixtureMemory(process);mutate(memory);
    try { await new BoundedTeamTalkProvider(_=>memory).ReadAsync(new(process,"",""),CancellationToken.None); }
    catch(InvalidDataException) { count++; return; }
    throw new Exception("Unsafe simulated native state admitted.");
}
await RejectMemory(memory=>memory.U(0xa00074,0x123456));
await RejectMemory(memory=>memory.U(0x562648,0x123456));
await RejectMemory(memory=>memory.U(0x71059c,0x210000));
await RejectMemory(memory=>memory.B(0x0191136a,1));
await RejectMemory(memory=>memory.U(0xb10008,uint.MaxValue));
int phaseReads=0;
await RejectMemory(memory=>memory.Override=(address,bytes)=> address==0x95f30c && ++phaseReads==2 ? new byte[]{0} : null);
await RejectMemory(memory=>memory.IdentityOverride=n=>n==1?process:process with {CreationFiletime=process.CreationFiletime+1});
var finishedMemory=new TeamTalkFixtureMemory(process);finishedMemory.B(0x95f30c,5);finishedMemory.B(0xa20030,5);
var finished=await new BoundedTeamTalkProvider(_=>finishedMemory).ReadAsync(new(process,"",""),CancellationToken.None);
Check(!finished.Relevant && finished.Kind=="unsupported" && !finished.PublicationReady,"Postmatch cannot publish");
try { using var unsupported=new VerifiedTeamTalkProcessMemory(new(process with {Sha256="unsupported"},"","")); throw new Exception("Unpinned process opened"); }
catch(InvalidDataException) { count++; }
Check(live.CompletionCandidate && live.ExecutionFence==1 && live.EventTimestamp==19886,"Completion candidate requires fence/event");
async Task NotCandidate(Action<TeamTalkFixtureMemory> mutate,string label)
{
 var memory=new TeamTalkFixtureMemory(process);mutate(memory);
 var observation=await new BoundedTeamTalkProvider(_=>memory).ReadAsync(new(process,"",""),CancellationToken.None);
 Check(!observation.CompletionCandidate && !observation.PublicationReady,label);
}
await NotCandidate(memory=>memory.B(0x95f22c,0),"In-executor fence rejects");
await NotCandidate(memory=>memory.B(0xb4003c,255),"Old event payload rejects");
await NotCandidate(memory=>memory.U(0xb40004,19887),"Equal event/current tick rejects");
await NotCandidate(memory=>memory.U(0xb20010,65),"Different event fingerprint rejects");
await NotCandidate(memory=>{memory.U(0xa00b04,3);memory.U(0xa10008,0xa20000);},"Later talk cannot replace standard slot");
Console.WriteLine($"PASS: {count} private adapter checks; no process access.");
