# [restorationbot](https://www.reddit.com/user/restoration-bot)

<center><img src=https://i.imgur.com/Hl5LuMz.jpg width="70%"></center>

A reddit bot for automated photo restoration using Microsoft Research's 
[deep latent space translation Old Photo Restoration project](https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life).
Unlike many Reddit bots, this bot does not currently respond to bot summons/username mentions.

This bot searches through [/r/OldSchoolCool](oldschoolcool.reddit.com) for posts made by users sharing photos
of their family. It then pulls the photo and attempts to restore it, posting the results as a comment.

When posts which are determined to be of a user's family members are detected, the bot 
spins up a gcloud VM running PyTorch and a single K80 GPU to processes the photos.

To keep costs low the bot takes advantage of gcloud's preemptible VM instances and per-second billing in the following way:
 1. Detected familial posts have their images downloaded and dumped to a gcloud bucket.
 2. A preemptible Deep Learning VM is started
 3. A startup script is run which pulls the new images from the bucket into the VM, processes the images, transfers
 them back to the bucket, removes the files from the VM, and then shuts down.
 
This process typically takes ~ 2-3 minutes. The current (Oct 2020) rate for a pre-emptible N1 machines with 
7.5 GB of RAM and 1 K80 GPU is about 16￠ per hour. Additionally, Google offers per-second billing for their VMs, 
with an extremely low rate for terminated instances.

#### Issues:
- The MS model is a research project and is not built to have production grade efficiency so a GPU is currently a necessity.
- The training set images were 256x256 images so although the model does do a good job generalizing to
higher resolution images, inputs typically need to be resized to something ~1000-1500 px on the longest side.
- The current workflow always tries to enhance faces if it finds them in the image. Very blurry/out-of-focus facial
features will often be enhanced in strange/disturbing ways as the model must generate most of the face itself.
