using System;
using System.IO;
using System.Reflection;
class ApplyX15RosterBatch {
 static int Main(string[] a) {try {
  if(a.Length!=4&&(a.Length!=5||a[4]!="--validate"))throw new ArgumentException("editor source output preparedDir [--validate]");
  string editor=Path.GetFullPath(a[0]);
  var domain=AppDomain.CreateDomain("X15RosterBatch",null,new AppDomainSetup{ApplicationBase=Path.GetDirectoryName(editor)});
  try{var w=(VerifiedNativeSquadsWorker)domain.CreateInstanceFromAndUnwrap(Assembly.GetExecutingAssembly().Location,typeof(VerifiedNativeSquadsWorker).FullName);w.ScopedRosterBatch(a[1],a[2],a[3],a.Length==5,"x15215");}
  finally{AppDomain.Unload(domain);}return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
