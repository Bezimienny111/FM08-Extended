from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
source=base.parent/"GRAPHICS_COVERAGE_X14_20261112/audit_graphics.py"
spec=importlib.util.spec_from_file_location("graphics_audit_after_kits",source)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
audit.OUT=base/"after-install"
audit.main()
