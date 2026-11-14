using FmLauncher;
using System.Text.Json;
var root = args[0];
var csv = File.ReadAllLines(Path.Combine(root,"FmLauncher/src/FmLauncher/PositionAttributeWeights.csv"));
var header=csv[0].Split(';');
string[] roles=["GK","SW","DC","DL_DR","WBL_WBR","DM","MC","AMC","ML_MR_AML_AMR","FS","TS"];
var weights=csv.Skip(1).Where(l=>!string.IsNullOrWhiteSpace(l)).Select(l=>l.Split(';')).ToDictionary(v=>v[0]);
var classes=new byte[12*47];
for(var r=0;r<11;r++)for(var a=0;a<47;a++){
 var w=int.Parse(weights[GamePositionBackgroundPatch.NativeAttributes[a]][Array.IndexOf(header,roles[r])]);
 classes[(r+1)*47+a]=(byte)(w>=60?2:w>=20?1:0);
}
void Reject(byte[] invalid) { try { GamePositionBackgroundPatch.Build(0x12020000,0x12024000,invalid,true); throw new Exception("Invalid matrix accepted"); } catch(ArgumentException) {} }
Reject(new byte[1]); var badClass=(byte[])classes.Clone();badClass[100]=3;Reject(badClass);
var badOff=(byte[])classes.Clone();badOff[0]=1;Reject(badOff);
var p=GamePositionBackgroundPatch.Build(0x12020000,0x12024000,classes,true);
File.WriteAllBytes(Path.Combine(args[1],"position-code.bin"),p.Code);
File.WriteAllBytes(Path.Combine(args[1],"position-data.bin"),p.Data);
File.WriteAllText(Path.Combine(args[1],"position-payload.json"),JsonSerializer.Serialize(new{
 p.State,p.NativeNameCreatedEntry,p.LabelDrawEntry,p.BeginGenerationHookEntry,p.LabelDestructorEntry,
 p.BeginGenerationEntry,p.SetRoleEntry,p.RegisterEntry,p.RenderEntry,p.InvalidateLabelEntry,p.FontCopyEntry,p.PopupCommitEntry,
 CodeBytes=p.Code.Length,DataBytes=p.Data.Length,Classes=classes,RoleNames=roles,Attributes=GamePositionBackgroundPatch.NativeAttributes
},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"PASS Build: code={p.Code.Length}, data={p.Data.Length}, roles11/nativeattributes47");
