# Magic Mapper 

# Work in progress (not yet release)
After being shelved for far too many years, we're creating this new
version of the mapper client. Full notes will appear here when we
release.

# Previous Versions
## 3.0.0a1 30-SEP-2010 (alpha)
This represents a wholesale reimplementation of major portions
of MSH as well as a substantial amount of new code.  The visual
magic mapper is the main new feature, which MSH never did (although
it was planned to do so at some point).  The project was ported from
Tcl to Python as part of the rewrite.

Renamed from MSH to MagicMapper but kept advancing the version numbers
from 2.12 to 3.0 in acknowledgement of its previous history as MSH.

### Bug fixes
legion
### Additions
also legion

### Known Issues
Not all functions are implemented.  It's fairly easy to confuse with
bad or unexpected input files.

# Older Work (as MudShell aka MSH)
## MSH 2.12
New icon button panel, graphical status indicators.  Notebook tabs
on configure screen (avoids the dialog from getting too long).
Added "transcript" logging (toggle on/off) as well as old feature
to save entire buffer.  Changed ESC-[J (clear screen) to actually
clear entire buffer (previously just printed several newlines).
Added more informative status messages when downloading images.
## MSH 2.10
Includes support for the new `RML` command.
## MSH 2.9
Allows you to configure the color of your game input as it appears
on the output window, and turn off the box drawn around it if you
prefer.

Also implements image cache ageing.

**IF YOU USED MSH 2.5-2.7, YOU WILL NEED TO DELETE YOUR CACHE FILES BEFORE USING 2.8 or 2.9.  IF YOU ARE GOING FROM 2.4 OR EARLIER STRAIGHT TO 2.8 or 2.9, THIS IS NOT NECESSARY.**

## MSH 2.8 (unreleased) 
image cache implemented
## MSH 2.7: (unreleased) 
bug fixes to 2.6
## MSH 2.6: (unreleased) 
bug fixes to 2.5
## MSH 2.5:
You can now expand the window

MSH now accepts graphic images which may be sent from the MUD
to display in-line in your MUD session window.

The default MSH directory is now `~/msh`, allowing you to upgrade MSH
to a new version without moving your files over to a new directory
each time.

MSH now lets you configure the size of the window and the colors
you use in the game.  These may be saved.

General improvements and hooks for future enhancements.
