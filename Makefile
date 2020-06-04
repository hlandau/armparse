all: test.py

enter:
	nix-shell -p python36.withPackages'(p: with p; [astor pyyaml])'

dump.pickle: asltool
	./asltool pickle-ast ~/3pr/isadef/ARM/ISA_AArch32_xml_v85A-2019-06 "$@"

test.py: dump.pickle armtrans.py
	./asltool translate -P "$<" "$@"
