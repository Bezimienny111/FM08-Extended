from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("graphics_audit_after_install",base/"audit_graphics.py")
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
audit.OUT=base/"after-install"
audit.main()
