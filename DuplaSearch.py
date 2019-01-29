# search for dupla files in 1-n directories
# posibly delete the duplas (first one keep)
# THERE WAS CHANGED DELETING TO "SAFE DELETING" - move the duplas into new subdir "DUPLA" (can be changed in global varianble CFG_DUPLA_MOVE_DIR_NAME)
# it's not recursive in subdirectories!!! (TODO)

import os
import sys
import hashlib
import shutil

global_bDeleting = False
global_paths = []
CFG_DUPLA_MOVE_DIR_NAME = "DUPLA"
CFG_DUPLA_OVERVIEW_FILE_NAME = "dupla.html"
CFG_MoreVERBOUS = False # list the all files
CFG_SKIPZERO = True # exclude the zero len files

def help():
    print("Usage: <skript> [-d] path1 [path2] ... [pathN]")
    print("     -d ... for delete duplicates (move them to new subdir!)")
    print("     path1 can be * ... all dirs in current dir")

# test the parametres

if (len(sys.argv) < 2):
    help()
    sys.exit()

if (len(sys.argv) == 2) and (sys.argv[1] == "-d"):
    print("Error: Missing source path!")
    help()
    sys.exit()

# probably success start, lets go

def appendDirs(path2list):
    if path2list == ".": # redundant... only for nice formatting
        dirs = [d for d in os.listdir(path2list) if os.path.isdir(d) and d!="." and d!=".."]
    else:
       dirs = [os.path.join(path2list, d) for d in os.listdir(path2list) if os.path.isdir(os.path.join(path2list, d)) and d!="." and d!=".."]
    for d in dirs:
            global_paths.append(d)

def appendCurDir():
    appendDirs(".")

argv_i = 1
while (argv_i < len(sys.argv)):
    if (sys.argv[argv_i] == "-d"):
        global_bDeleting = True
    else:
        # if path = * then add all subdirs of current dir
        # else add only path from argument
        if (sys.argv[argv_i] == "*"):
            appendCurDir()
        else:
            global_paths.append(sys.argv[argv_i])
    argv_i += 1

# the parametres loaded

print("Loading "+str(len(global_paths))+" paths...")

for path in global_paths:
    # check if the paths are real - warn if not
    if (not(os.path.isdir(path))):
        print("Error: Some path/s are not real directories (missing or not directory)!")
        print("E.q.: " + path)
        sys.exit()

# 1. run = scan for all files and their size ... save them as "filepath":"size" into global_files
# in global_files identify candidates (same size) ... save the list of possibly duplicates
# 2. run = rescan the candidates and instead of "size" save the "file hash" in dictionary global_files
# in global_files recheck the duplicates ... save the list of true duplicates
global_files = {}

for path in global_paths:
    # scan all files in paths
    print("Scanning files in " + path, end='')
    # there can be possibly add directory recursion (TODO)
    dir_files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    print(" | found " + str(len(dir_files)) + " files")
    if CFG_MoreVERBOUS:
        print(dir_files)
    # search for their size and save it
    for f in dir_files:
        fs = 0
        try:
            fs = os.path.getsize(f)
        except:
            pass
        global_files[f] = fs

print("-----------")

# part when we match files on their file size - it's pre-filtering for proper dupla-check later (only performance)

global_possiblyDupla = []

n = 0
for fx,fx_size in global_files.items():
    i = 0
    for fy,fy_size in global_files.items():
        if i <= n:
            i += 1
            continue
        i += 1
        if (fx_size == fy_size) and (fx!=fy) and ((not CFG_SKIPZERO) or fx_size!=0):
            global_possiblyDupla.append((fx,fy))
    n += 1

print("Possibly duplas: " + str(len(global_possiblyDupla)) + " (files with the same nozero size)")
if CFG_MoreVERBOUS:
    print(global_possiblyDupla)


print("-----------")
print("Check if realy dupla...")

# check if realy dupla (match byte by byte)

def hashFile(filepath):
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def isDupla(filepath, filepath2):
    try:
        if hashFile(filepath) == hashFile(filepath2):
            return True
    except:
        pass
    return False

global_trueDuplas = []

for (f1,f2) in global_possiblyDupla:
    if isDupla(f1, f2):
        print("True: " + f1 + " / " + f2)
        global_trueDuplas.append((f1, f2))
    else:
        print("NOT: " + f1 + " / " + f2)

print("-----------")

# the final report - if deleting, the final check if so, ...
# THERE WAS CHANGED DELETING TO "SAFE DELETING" - move the duplas into new subdir "DUPLA" (can be changed in global varianble)

if len(global_trueDuplas) > 0:
    print("Found " + str(len(global_trueDuplas)) + " duplas")
    if global_bDeleting:
        print("Warning: All duplas except of original will be moved to DUPLA dir!")
        print("Do you still want to continue? Y/N:")
        answer = ""
        while (not answer):
            answer = input()
        possible_answers = ['Y', 'y', 'Z', 'z', 'A', 'a']
        if not(any(answer == a for a in possible_answers)):
            print("So just print it into file duplas.txt")
            global_bDeleting = False
        else:
            try:
                os.makedirs(CFG_DUPLA_MOVE_DIR_NAME)
            except:
                pass

    file = open(CFG_DUPLA_OVERVIEW_FILE_NAME, "w") 

    i_trashed = 0
    for (f1, f2) in global_trueDuplas:
        if global_bDeleting:
            print("Trashing: " + f2)
            try:
                shutil.move(f2, CFG_DUPLA_MOVE_DIR_NAME)
                f2 = os.path.join(CFG_DUPLA_MOVE_DIR_NAME, os.path.basename(f2))
                i_trashed += 1
            except:
                print("Error moving: " + f2 + " (probably moved before)")
        file.write('<img src="'+f1+'">')
        file.write('<img src="'+f2+'">')
        file.write('<hr>'+ os.linesep)

    file.close() 

    if global_bDeleting:
        print("-----------")
        print("Moved " + str(i_trashed) + " files!")
    print("Final overview of duplas can be found in " + CFG_DUPLA_OVERVIEW_FILE_NAME)
