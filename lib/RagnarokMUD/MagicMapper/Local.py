########################################################################################
#  _______  _______  _______ _________ _______  _______  _______  _______              #
# (       )(  ___  )(  ____ \\__   __/(  ____ \(       )(  ___  )(  ____ ) Ragnarok    #
# | () () || (   ) || (    \/   ) (   | (    \/| () () || (   ) || (    )| MUD         #
# | || || || (___) || |         | |   | |      | || || || (___) || (____)| Magic       #
# | |(_)| ||  ___  || | ____    | |   | |      | |(_)| ||  ___  ||  _____) Mapper      #
# | |   | || (   ) || | \_  )   | |   | |      | |   | || (   ) || (       Client      #
# | )   ( || )   ( || (___) |___) (___| (____/\| )   ( || )   ( || )       (rag.com)   #
# |/     \||/     \|(_______)\_______/(_______/|/     \||/     \||/                    #
#   ______    __       _______         _______  _        _______           _______     #
#  / ____ \  /  \     (  __   )       (  ___  )( \      (  ____ )|\     /|(  ___  )    #
# ( (    \/  \/) )    | (  )  |       | (   ) || (      | (    )|| )   ( || (   ) |    #
# | (____      | |    | | /   | _____ | (___) || |      | (____)|| (___) || (___) |    #
# |  ___ \     | |    | (/ /) |(_____)|  ___  || |      |  _____)|  ___  ||  ___  |    #
# | (   ) )    | |    |   / | |       | (   ) || |      | (      | (   ) || (   ) |    #
# ( (___) )_ __) (_ _ |  (__) |       | )   ( || (____/\| )      | )   ( || )   ( | _  #
#  \_____/(_)\____/(_)(_______)       |/     \|(_______/|/       |/     \||/     \|(_) #
#                                                                                      #
########################################################################################
#
# THIS MODULE IS FOR LOCAL MUD SITES TO MAKE CUSTOMIZED SETTINGS. 
#                                                                 
# SEE INSTRUCTIONS BELOW.                                         
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Local Settings
#

#
# Local room id obscuring filter
#
# You don't want players to be able to determine your room
# file names by guessing (or they'd download areas they have
# not yet visited).  Define this function to take a room ID
# string as defined in your MUDlib and return some kind of
# opaque public ID which will consistently and uniquely be
# generated from this room ID but can't easily be reversed.
#
# RESTRICTIONS:
#
# The resulting public ID MUST not include directory 
# separator characters (usually \ or /).
#
# It also MUST not contain colon (:) characters.
#
# The public ID SHOULD be at least 3 characters long.
# 

def gen_public_room_id(private_id):
    "Turn private room ID to an obscured but consistent public one."

    #
    # Trivial example:
    # Convert to hex
    #
    return ''.join(["%02x" % ord(char) for char in private_id])
