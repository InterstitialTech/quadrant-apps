#!/bin/bash

pasuspender -- pd pd/main.pd &
sleep 2
python3 -u readSerial.py | pdsend 8000
