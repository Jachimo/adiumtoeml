#!/usr/bin/env bash

# Modify this command before running it!
# Make sure options including don't-process-before date is set correctly in the adiumToEml.py script
# to prevent creation of a lot of duplicate items.

echo "Working in `pwd`"

find ~/Documents/Adium/Logs -name '*.xml' -print0 | xargs -0 -n1 -I {} ./adiumToEml.py {} ~/Documents/Adium/Converted/ > ~/Documents/Adium/adiumToEml-converter.log

# touch the output dir so that its mtime is last conversion date/time
#  in future, you can use that date/time to set the don't-process-before date, if desired
touch ~/Documents/Adium/Converted
