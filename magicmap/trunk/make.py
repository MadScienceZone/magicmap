# Stupider script file to do essentially what the Makefile here does.
# for "make dist" on Windows
# vi:set ai sm nu ts=4 sw=4 expandtab:

import os, os.path, subprocess

dirlist=['docs', 'man', 'Test', 'lib/RagnarokMUD']

# dist: distclean builddocs
# 	(mkdir -p dist_bin && cd bin && for file in *; do sed 's/^#@@REL@@//' < $$file > ../dist_bin/$$file; done)
# 	./setup.py sdist --formats=gztar,zip

if os.path.exists('dist_bin'):
    for f in os.listdir('dist_bin'):
        print "Removing old dist_bin/{0}".format(f)
        os.unlink('dist_bin/'+f)
else:
    os.mkdir('dist_bin')

print "Copying/converting to dist_bin..."
exclude=False
for filename in os.listdir('bin'):
    if filename.endswith('~') or filename.startswith('.'): continue
    print "-", filename
    with open(os.path.join('bin', filename)) as input_file:
        with open(os.path.join('dist_bin', filename), 'w') as output_file:
            for line in input_file:
                if line.startswith('#@@REL@@'):
                    line = line[8:]
                    print "Enabling release-mode code:", line
                elif line.startswith('#@@BEGIN-DEV:'):
                    exclude=True
                    print "Excluding development-mode code:"
                    continue
                elif line.startswith('#:END-DEV@@'):
                    exclude=False
                    print "(end of excluded code)"
                    continue
                elif exclude:
                    print "   ", line
                    continue

                output_file.write(line)

    if exclude:
        print "*** *** *** *** End of source file encountered while"
        print "*** WARNING *** still in development-exclude mode!"
        print "*** *** *** *** (Forgot the #:END-DEV@@ line?)"
        exclude=False

print "Generating installer..."
subprocess.check_call(['python','setup.py','bdist_wininst'])
