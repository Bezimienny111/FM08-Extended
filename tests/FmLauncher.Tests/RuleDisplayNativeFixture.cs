using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using FmLauncher;
using Marshal=PanelRemoteMemory;

internal static partial class NativePanelFixture
{
    internal static void TestRuleDisplayNative(string gamePath)
    {
        Require(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(gamePath))).Equals(
            "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d",StringComparison.OrdinalIgnoreCase),"Primary R5 formatter hash only.");
        var report=new Dictionary<string,object?>{{"Status","PENDING"},{"ActualNativeFormatters",true},{"PrivateSuspendedProcess",true},{"MainResumed",false},{"UserProcessTouched",false}};
        var reports=Environment.GetEnvironmentVariable("FMEXT_RULES_FIXTURE_REPORT_ROOT") ?? Path.Combine(
            Path.GetDirectoryName(gamePath)!,"FmLauncher","data","research","LEAGUE_RULES_UI_LAUNCHER_VALUES_20261113","implementation");
        Require(Path.IsPathFullyQualified(reports),"Explicit absolute fixture report root required.");
        Directory.CreateDirectory(reports);var reportPath=Path.Combine(reports,"native-fixture-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfff")+".json");
        try
        {
            using var remote=new PanelRemoteProcess(gamePath);Marshal.Process=remote;
            var scratch=AllocatePanel(0x12000000,0x40000);var text=IntPtr.Add(scratch,0x2000);
            var original=remote.Read(new IntPtr((int)GameRuleDisplayPatch.EntryAddress),GameRuleDisplayPatch.NativeFormatterLength);
            Require(original.AsSpan(0,7).SequenceEqual(GameRuleDisplayPatch.OriginalEntry),"Formatter original entry guard.");
            report["OriginalFormatterSHA256"]=Convert.ToHexString(SHA256.HashData(original));
            var ctor=new NativeCode(0x1200D000);ctor.Emit(0x8B,0x4C,0x24,4);ctor.Call(0x00F4F380);ctor.Emit(0xC3);WritePanelCode(0x1200D000,ctor.Finish());
            var dtor=new NativeCode(0x1200D200);dtor.Emit(0x8B,0x4C,0x24,4,0x6A,0);dtor.Call(0x010312D0);dtor.Emit(0xC3);WritePanelCode(0x1200D200,dtor.Finish());
            // ABI canaries include ESP plus all nonvolatile registers. Calls the actual patched entry.
            var abi=new NativeCode(0x1200D100);abi.Emit(0x55,0x53,0x56,0x57);
            abi.Emit(0xBB);abi.Dword(0x11223344);abi.Emit(0xBE);abi.Dword(0x22334455);abi.Emit(0xBF);abi.Dword(0x33445566);abi.Emit(0xBD);abi.Dword(0x44556677);
            abi.Emit(0x89,0x25);abi.Dword(0x1200E000);
            abi.Emit(0xFF,0x74,0x24,0x1C,0xFF,0x74,0x24,0x1C,0xFF,0x74,0x24,0x1C);abi.Call(GameRuleDisplayPatch.EntryAddress);abi.Emit(0x83,0xC4,0x0C);
            abi.Emit(0x3B,0x25);abi.Dword(0x1200E000);abi.Branch(0x85,"bad");
            foreach(var (op,value)in new[]{((byte)0xFB,0x11223344u),((byte)0xFE,0x22334455u),((byte)0xFF,0x33445566u),((byte)0xFD,0x44556677u)})
            {abi.Emit(0x81,op);abi.Dword(value);abi.Branch(0x85,"bad");}
            abi.Jump("done");abi.Mark("bad");abi.Emit(0xB8);abi.Dword(0xDEADCAFE);abi.Mark("done");abi.Emit(0x5F,0x5E,0x5B,0x5D,0xC3);WritePanelCode(0x1200D100,abi.Finish());
            // CREATE_SUSPENDED stops before the executable's CRT startup. Initialize its REAL CRT heap/locks;
            // do not resume Main and do not replace allocators, GameString or formatter helpers with stubs.
            report["Phase"]="native CRT heap/locks";
            // Reproduce the bounded GetVersionExA -> CRT OS globals block from original entry1130153.
            // This selects the same WinNT heap/critical-section path as ordinary startup (not legacy Win9x).
            Marshal.WriteInt32(new IntPtr(0x1200E900),0x94);
            var os=new NativeCode(0x1200D400);os.Emit(0x68);os.Dword(0x1200E900);os.Emit(0xFF,0x15);os.Dword(0x0121A240);
            foreach(var (source,destination)in new[]{(0x1200E910u,0x01BDD968u),(0x1200E904u,0x01BDD974u),(0x1200E908u,0x01BDD978u)})
            {os.Emit(0xA1);os.Dword(source);os.Emit(0xA3);os.Dword(destination);}
            os.Emit(0xA1);os.Dword(0x1200E90C);os.Emit(0x25);os.Dword(0x7FFF);os.Emit(0xA3);os.Dword(0x01BDD96C);
            os.Emit(0xA1);os.Dword(0x1200E904);os.Emit(0xC1,0xE0,8,0x03,0x05);os.Dword(0x1200E908);os.Emit(0xA3);os.Dword(0x01BDD970);os.Emit(0xC3);
            WritePanelCode(0x1200D400,os.Finish());remote.Call(0x1200D400);
            Require(Marshal.ReadInt32(new IntPtr(0x01BDD968))==2&&Marshal.ReadInt32(new IntPtr(0x01BDD974))>4,"Native GetVersionExA identifies supported WinNT path.");
            report["NativeCRTPlatform"]=Marshal.ReadInt32(new IntPtr(0x01BDD968));report["NativeCRTOSMajor"]=Marshal.ReadInt32(new IntPtr(0x01BDD974));
            Require(remote.Call(0x011381F4,1)==1,"Native __heap_init.");
            Require(Marshal.ReadInt32(new IntPtr(0x01BDE0EC))==1,"Native heap selection matches actual WinNT startup.");
            Require(remote.Call(0x01135422)==1,"Native __mtinit.");
            Require(remote.Call(0x0112EB89)==0,"Native CRT ___onexitinit (first C initializer, no application constructors).");
            report["NativeCRTOnExitRegistry"]=true;
            report["NativeCRTHeapAndLocks"]=true;report["Phase"]="native GameString constructor";
            remote.Call(0x1200D000,text.ToInt32());Require(PanelText(text)=="","Actual GameString constructor and lazy string pool initialized.");
            report["Phase"]="actual formatter cases";
            // Fixture-only exception telemetry; ends only this owned remote thread after recording native EIP.
            var handler=new NativeCode(0x1200E300);handler.Emit(0x8B,0x44,0x24,4,0x8B,0x10,0x8B,0x48,4);
            void Capture(byte modrm,uint offset,uint destination)
            {handler.Emit(0x8B,modrm);handler.Dword(offset);handler.Emit(0xA3);handler.Dword(destination);}
            handler.Emit(0x8B,2,0xA3);handler.Dword(0x1200E800);
            Capture(0x82,0x0C,0x1200E804);Capture(0x81,0xB8,0x1200E808);Capture(0x81,0xC4,0x1200E80C);
            Capture(0x82,0x18,0x1200E810);Capture(0x81,0xAC,0x1200E814);Capture(0x81,0xB0,0x1200E818);
            Capture(0x81,0x9C,0x1200E81C);Capture(0x81,0xA0,0x1200E820);Capture(0x81,0xA4,0x1200E824);
            // The context stack is released by ExitThread, so copy a bounded512B before ending this owned thread.
            handler.Emit(0x8B,0xB1);handler.Dword(0xC4);handler.Emit(0xBF);handler.Dword(0x1200EA00);handler.Emit(0xB9);handler.Dword(128);handler.Emit(0xFC,0xF3,0xA5);
            handler.Emit(0xFF,0x35);handler.Dword(0x1200E800);handler.Emit(0xFF,0x15);handler.Dword(0x0121A254);WritePanelCode(0x1200E300,handler.Finish());
            Marshal.Copy(Encoding.ASCII.GetBytes("kernel32.dll\0"),0,new IntPtr(0x1200E600),13);
            var functionName=Encoding.ASCII.GetBytes("AddVectoredExceptionHandler\0");Marshal.Copy(functionName,0,new IntPtr(0x1200E640),functionName.Length);
            var register=new NativeCode(0x1200E400);register.Emit(0x68);register.Dword(0x1200E600);register.Emit(0xFF,0x15);register.Dword(0x0121A234);
            register.Emit(0x68);register.Dword(0x1200E640);register.Emit(0x50,0xFF,0x15);register.Dword(0x0121A154);
            register.Emit(0x68);register.Dword(0x1200E300);register.Emit(0x6A,1,0xFF,0xD0,0xC3);WritePanelCode(0x1200E400,register.Finish());
            Require(remote.Call(0x1200E400)!=0,"Private vectored exception capture registered.");
            // Exact static constructors from R5 CRT initializer functions12058E0/1206EB0/1205980.
            // NumberFormatAddress is a native argument MAP (F4D2A0), NOT a GameString.
            var globals=new NativeCode(0x1200D300);
            foreach(var (obj,ctorAddress)in new[]{(0x01B205CCu,0x00F4D2A0u),(0x01B208F0u,0x00F4FE70u),(0x01B2126Cu,0x00F4F380u)})
            {globals.Emit(0xB9);globals.Dword(obj);globals.Call(ctorAddress);}
            globals.Emit(0xC3);WritePanelCode(0x1200D300,globals.Finish());remote.Call(0x1200D300);
            report["ActualStaticFormatMapCacheAndEmptyConstructors"]=true;
            // Exact C++ initializer1205A00, statically proved199 F51CC0 calls for ASCII -99..99 plus _atexit.
            // F52950 reads these caller-independent native cached integer GameStrings during token expansion.
            report["Phase"]="native integer cache initializer";remote.Call(0x01205A00);
            Require(PanelText(new IntPtr(0x01B20DBC))=="0"&&PanelText(new IntPtr(0x01B20E10))=="7","Actual native cached integer initializer.");
            report["NativeIntegerCache199"]=true;
            // Exact bounded XCU dependency closure of grammar constants used by1004700 and its English helpers.
            // All23 initializers are27B: ASCII GameString F51CC0 + native _atexit; no application/UI constructors.
            for(var initializer=0x0120A190;initializer<=0x0120A450;initializer+=0x20)remote.Call(initializer);
            report["NativeGrammarConstants23"]=true;report["Phase"]="actual formatter cases";
            int rendered=0;
            (int,string) Render(int code,int side)
            {
                int value;
                try{value=remote.Call(0x1200D100,code,text.ToInt32(),side);}
                catch
                {
                    var capture=remote.Read(new IntPtr(0x1200E800),40);
                    report["NativeException"]=Enumerable.Range(0,10).Select(i=>BitConverter.ToUInt32(capture,i*4).ToString("X8")).ToArray();
                    report["NumberFormatObject"]=Convert.ToHexString(remote.Read(new IntPtr((int)GameRuleDisplayPatch.NumberFormatAddress),16));
                    var esp=BitConverter.ToInt32(capture,12);var words=remote.Read(new IntPtr(0x1200EA00),512);
                    report["ExceptionStackCodePointerCandidates"]=Enumerable.Range(0,words.Length/4).Select(i=>new{Stack=(esp+i*4).ToString("X8"),Value=BitConverter.ToUInt32(words,i*4)})
                        .Where(x=>x.Value>=0x400000&&x.Value<0x121A000).Select(x=>new{x.Stack,Value=x.Value.ToString("X8")}).ToArray();
                    throw;
                }
                Require(unchecked((uint)value)!=0xDEADCAFE,"cdecl stack/nonvolatile preservation.");rendered++;return(value&0xFF,PanelText(text));
            }
            (int Bench,int Subs) Numbers((int Status,string Text) v)
            {
                Require(v.Status==1,"Native formatter success status.");var n=Regex.Matches(v.Text,@"\d+").Select(m=>int.Parse(m.Value)).ToArray();
                Require(n.Length==2,"Native token expansion yielded two numbers: "+v.Text);return(n[0],n[1]);
            }
            var vanilla=new Dictionary<string,string>();
            for(var code=0;code<29;code++)for(var side=0;side<2;side++)
            {
                var before=PanelText(text);var result=Render(code,side);
                if(code==19)Require(result.Item2==before,"Vanilla19 preserves caller output.");
                else
                {
                    var n=Numbers(result);var bench=remote.Call(0x00AFE150,code,side)&0xFF;var subs=remote.Call(0x00AFE0D0,code,side)&0xFF;
                    Require(n==(bench,subs),"Vanilla display/getter equality.");vanilla[code+":"+side]=result.Item2;
                }
            }
            // Zero applied mask: all calls, including signed invalid codes and19, use original trampoline.
            void InstallDisplay(byte[] mask)
            {
                var bytes=GameRuleDisplayPatch.BuildPayload(0x12010000,mask);remote.Write(new IntPtr(0x12010000),bytes);
                var entry=GameRuleDisplayPatch.BuildEntryJump(0x12010000);remote.Write(new IntPtr((int)GameRuleDisplayPatch.EntryAddress),entry);
                Require(remote.Read(new IntPtr(0x12010000),bytes.Length).SequenceEqual(bytes)&&remote.Read(new IntPtr((int)GameRuleDisplayPatch.EntryAddress),entry.Length).SequenceEqual(entry),"Display full installation readback.");
            }
            InstallDisplay(new byte[29]);
            for(var code=0;code<29;code++)for(var side=0;side<2;side++)
            {
                var before=PanelText(text);var result=Render(code,side);
                Require(result.Item1==1&&(code==19?result.Item2==before:result.Item2==vanilla[code+":"+side]),"No override exact native text fallback.");
            }
            foreach(var bad in new[]{-1,-128,29,127,255})
            {var before=PanelText(text);var result=Render(bad,1);Require(result.Item1==0&&result.Item2==before,"Invalid signed native code fallback.");}
            var rules=Enumerable.Range(0,29).Select(code=>new RuleSettings{Code=code,Override=false,Substitutions=3,Bench=7}).ToArray();
            rules[0].Override=true;rules[0].Substitutions=5;rules[0].BenchOverride=true;rules[0].Bench=9;
            rules[19].Override=true;rules[19].Substitutions=4;rules[19].BenchOverride=true;rules[19].Bench=6;
            rules[22].BenchOverride=true;rules[22].Bench=10;
            rules[28].Override=true;rules[28].Substitutions=6;
            foreach(var limit in Enum.GetValues<RuleLimit>())
            {
                uint address=limit==RuleLimit.Substitutions?0x12011000u:0x12012000u;
                var bytes=MatchRulePatch.BuildPayload(address,rules,limit);remote.Write(new IntPtr((int)address),bytes);
                var entry=MatchRulePatch.BuildEntryJump(address+64,limit);remote.Write(new IntPtr((int)MatchRulePatch.GetterAddress(limit)),entry);
                SuspendedGameProcess.VerifyRuleInstallation(address,bytes,entry,limit,(a,n)=>remote.Read(new IntPtr((int)a),n));
            }
            var active=new byte[29];foreach(var code in new[]{0,19,22,28})active[code]=1;InstallDisplay(active);
            var examples=new Dictionary<string,string>();report["Examples"]=examples;
            void VerifyActive(string language)
            {
                foreach(var code in new[]{0,19,22,28})foreach(var side in new[]{0,1,255})
                {
                    var result=Render(code,side);var n=Numbers(result);var bench=remote.Call(0x00AFE150,code,side)&0xFF;var subs=remote.Call(0x00AFE0D0,code,side)&0xFF;
                    Require(n==(bench,subs),"Applied UI numbers equal installed engine getter results.");examples[language+":"+code+":"+side]=result.Item2;
                }
            }
            VerifyActive("en");Require(examples["en:0:0"]=="9 subs named, maximum 5 used","Actual English native template.");
            Require(Numbers(Render(3,0))==(5,3),"Unchanged code uses original formatter despite other code overrides.");
            // Controlled native translation dictionary record: real hash lookup+cached immutable UTF16 resource.
            var key=remote.Read(new IntPtr((int)GameRuleDisplayPatch.TemplateAddress),128).TakeWhile(b=>b!=0).ToArray();
            uint hash=unchecked((uint)remote.Call(0x01008F50,(int)GameRuleDisplayPatch.TemplateAddress,key.Length));
            int dictionary=Marshal.ReadInt32(new IntPtr(0x01B205F4));int buckets=Marshal.ReadInt32(new IntPtr(dictionary),0x10);
            Require(dictionary!=0&&buckets!=0,"Actual lazy native localization dictionary.");
            var bucket=new IntPtr(buckets+(int)(hash&0x1FFF)*4);var oldBucket=Marshal.ReadInt32(bucket);
            var localized=IntPtr.Add(scratch,0x28000);ImmutableString(localized,"Nazwanych: <%number#1 - subs named>; wykorzystanych: <%number#2 - subs used>");
            var entryNode=IntPtr.Add(scratch,0x29000);var choices=IntPtr.Add(scratch,0x2A000);var node=IntPtr.Add(scratch,0x2B000);var record=IntPtr.Add(scratch,0x2C000);
            Marshal.WriteInt32(entryNode,unchecked((int)hash));Marshal.WriteInt32(entryNode,4,oldBucket);Marshal.WriteInt32(entryNode,12,choices.ToInt32());
            // Native F4D440 hashes ASCII query, but node+10 stores UTF16; FF9500 converts only the query.
            var storedKey=Encoding.Unicode.GetBytes(Encoding.ASCII.GetString(key)+"\0");Marshal.Copy(storedKey,0,IntPtr.Add(entryNode,16),storedKey.Length);
            Marshal.WriteInt32(choices,1);Marshal.WriteInt32(choices,4,node.ToInt32());Marshal.WriteInt32(node,record.ToInt32());Marshal.WriteInt32(record,8,Marshal.ReadInt32(localized,8));
            Marshal.WriteInt32(bucket,entryNode.ToInt32());
            var lookup=new NativeCode(0x1200D500);lookup.Emit(0x8B,0x4C,0x24,0x0C,0xFF,0x74,0x24,8,0xFF,0x74,0x24,8);lookup.Call(0x00F4D440);lookup.Emit(0xC3);WritePanelCode(0x1200D500,lookup.Finish());
            var found=remote.Call(0x1200D500,(int)GameRuleDisplayPatch.TemplateAddress,key.Length,dictionary);report["NativeDictionaryLookup"]=found.ToString("X8");
            Require(found==entryNode.ToInt32(),"Actual native dictionary recognizes controlled translation record.");
            var setText=new NativeCode(0x1200D600);setText.Emit(0x8B,0x4C,0x24,4,0x6A,0,0xFF,0x74,0x24,0x0C);setText.Call(GameRuleDisplayPatch.SetTemplateAddress);setText.Emit(0xC3);WritePanelCode(0x1200D600,setText.Finish());
            remote.Call(0x1200D600,text.ToInt32(),(int)GameRuleDisplayPatch.TemplateAddress);report["RawLocalizedTemplate"]=PanelText(text);
            Require(PanelText(text).StartsWith("Nazwanych:",StringComparison.Ordinal),"Actual native localized template retrieval: "+PanelText(text));
            // Strong locale control: unmodified native formatter (zero active mask) must first render7/3 in PL,
            // while the independently patched engine getters remain9/5. Then the active adapter must display9/5.
            InstallDisplay(new byte[29]);var originalPL=Render(0,0);report["OriginalPolishControl"]=originalPL.Item2;
            Require(originalPL.Item2=="Nazwanych: 7; wykorzystanych: 3","Original native Polish template control.");
            InstallDisplay(active);VerifyActive("pl");
            Require(examples["pl:0:0"]=="Nazwanych: 9; wykorzystanych: 5","Actual native translation lookup and token substitution retained: "+examples["pl:0:0"]);
            Marshal.WriteInt32(bucket,oldBucket);
            // Real destructor then reconstruction prove adapter never takes ownership of caller's GameString.
            remote.Call(0x1200D200,text.ToInt32());remote.Call(0x1200D000,text.ToInt32());Require(PanelText(text)=="","Native destroy/recreate lifecycle.");
            Require(Numbers(Render(0,0))==(9,5),"Recreated output works after native destruction.");remote.Call(0x1200D200,text.ToInt32());
            report["Status"]="PASS_ACTUAL_NATIVE_FORMATTERS_AND_HOOK";report["Calls"]=rendered;report["Vanilla29BothSides"]=true;report["UnknownSignedFallback"]=true;
            report["ActualGetterPatchReadback"]=true;report["PartialIndependentLimits"]=true;report["Special19_22_28"]=true;report["StackAndNonvolatileCanaries"]=true;
            report["NativeGameStringCtorReuseDestructor"]=true;report["NativeTranslationDictionaryFixture"]=true;report["FormattersMocked"]=false;report["Examples"]=examples;
            Console.WriteLine("PASS: actual R5 GameString/AFDBF0/F521C0/F55BC0, native translation dictionary, verified engine getters, special codes, native fallback and cdecl canaries.");
        }
        catch(Exception e){report["Status"]="FAIL_NATIVE_FIXTURE";report["Error"]=e.ToString();throw;}
        finally{File.WriteAllText(reportPath,JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine(reportPath);}
    }
}
