# Workflow for a project including Python, PyCharm, Kivy, KivyMD, Buildozer, Ubuntu WSL, Android Studio
## The project
The app collects data with a user interface written in KivyMD, stores them in an Sqlite DB, collects the data once a 
month into a spreadsheet using openpyxl, and sends the spreadsheet via email. The UI can be nicely developed and tested with 
PyCharm under Wndows, and with buildozer on Linux you can create an app with the UI working. But it turns out that the storage of files and the sending of emails requires special Android features, that I could not find out how to achieve this with buildozer. So I switched to Android Studio to complete the application. This turns into a development cycle:
* Change the code in PyCharm (Windows) and test it as much as possible
* Run buildozer android debug  (not deploy, run) (Linux)
* Change manifests, build.gradle, icons, etc. in Android Studio (Windows)
* Run the app from Android Studio (Windows)
* back to PyCharm

You can view the project on https://github.com/michaelu123/FPFLEGE2.

These steps are described now in more detail.

## Setup
On Windows we install PyCharm, Android Studio, and the Ubuntu WSL (https://wiki.ubuntu.com/WSL).
We start an Ubuntu Shell via the normal Windows Start Menu, where you find an Ubuntu Button. This opens a window with a bash shell.
On Ubuntu, we install Python3, and buildozer (pip install buildozer). No use to install buildozer on Windows, it does not work on
Windows as of March 2020. On Windows, you set up a normal PyCharm project. In my case, the project is on C:\users\michael\PycharmProjects/Fpflege2. From Ubuntu, this is seen as /mnt/c/users/michael/PycharmProjects/Fpflege2. My home directory on Ubuntu is /home/michaelu. In it, I edit .profile, and add these lines (edit where necessary):
```
PATH="$HOME/.buildozer/android/platform/android-sdk/platform-tools:$PATH"
F2=/mnt/c/users/michael/PycharmProjects/FPFLEGE2
BU=$F2/.buildozer/android/platform/build-armeabi-v7a
RE=$BU/dists/arbeitsblatt__armeabi-v7a/release
export F2 BU RE
```
F2 is the root of the project, BU contains the build produced later by buildozer, and RE contains eventually the release APK. Replace arbeitsblatt eventually with your package name, see below.

Now we develop and test our project with Pycharm on Windows as far as possible. With Kivy/KivyMD we can also test the UI. I could also test the sqlite and the openpyxl code on Windows. Then comes the time to run the program as an app on Android.

## Setup buildozer
When we installed buildozer on Ubuntu, lots and lots of files were installed, under $HOME/.buildozer, $HOME/buildozer and $HOME/.local/bin/buildozer. Make sure that buildozer is on your PATH, by typing in the Ubuntu shell:
```
type buildozer
```
which should return
```
buildozer is /home/{username}/.local/bin/buildozer
```
Next, in $F2, you setup buildozer. You should also look at https://buildozer.readthedocs.io/en/latest.
Enter
```
cd $F2; buildozer init
```
which creates a file buildozer.spec in $F2, the project's root directory. You can see and edit this file with PyCharm.
The most important lines in this file are
* title
* package.name
* package.domain
* source.dir
* requirements

In my case, title = Arbeitsblatt, package.name=arbeitsblatt, package.domain=org.fpflege, source.dir=/mnt/c/users/Michael/PycharmProjects/FPFLEGE2/venv/src,
requirements = kivy,kivymd,python3,openpyxl,sqlite3,jdcal,et_xmlfile,plyer.

The title will be later the name of your app. The package.domain has the effect, that your external data (an Android term) will be stored in /storage/emulated/0/Android/Data/{package.domain}. The source dir is where your main.py lives, and requirements is a list of package dependencies. 
You will probably not get this right the first time. Either during the build process or when the app runs will there be missing dependencies. Just add them to requirements, as you proceed. E.g. for me, jdcal and et_xmlfile came as a surprise.

## Special notes on KivyMD
For KivyMD, I added the lines
kivymd.dir = /mnt/c/users/Michael/PycharmProjects/FPFLEGE2/venv/Lib/site-packages/kivymd
requirements.source.kivymd = %(kivymd.dir)s
presplash.filename = %(kivymd.dir)s/images/kivymd_logo.png
icon.filename = %(kivymd.dir)s/images/kivymd_logo.png

## Connecting a device
Now it depends if you connect a real phone to your computer, or if you use an emulator. In the latter case, use Android Studio to start an emulated phone. In either way, you should call
```
adb devices
```
to see "something" under "List of devices attached". There is a pitfall here, Once the adb daemon is running, you can call adb either via Ubuntu or Windows. Above, you added the platform-tools directory to the PATH, so that adb is found (under /home/michaelu/.buildozer/android/platform/android-sdk/platform-tools/adb in my case), but if the daemon is started by Ubuntu, no devices are found. In this case, call 
```
adb kill-server
```
from either Windows or Ubuntu, and then again "adb devices", but now from Windows. In my case, the platform-tools are installed under d:\Android\AndroidSDK\platform-tools, so first thing I do after login is to cd there, and call adb devices:
```
D:\Android\AndroidSDK\platform-tools>adb devices
* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
00d21cd1da4a33f0        device
```

## Run buildozer
Now that we have an attached device, we call on Ubuntu:
```
cd $F2
buildozer android debug deploy run
```
This triggers lots and lots of activities the first time. Among them, all packages from the requirements are loaded, plus the Android SDK, NDK, and other tools. When this succeeds, your app was at least started on the device, even though it may have crashed immediately. Also, the directory $BU exists now, where the apk file can be found in $BU/dists/{package.name}_armeabi-v7a/build/outputs/apk/debug. Edit $HOME/.profile and for RE replace "arbeitsblatt" with your package.name.

You will want to find out how your app performed and why it (probably) crashed. All you have, though, is the output of "adb logcat". It contains also output from the Python print statement. You can write the logcat into a file, with adb logcat -u >file.txt. Again, you can call this from Windows or Ubuntu. I did not use the Android Studio Debugger yet. I do not believe that it is of any use to debug Python code, but perhaps I am wrong. So it is back to debugging with print statements.

But probably your first messages indicate missing requirements. Edit buildozer.spec, e.g. with PyCharm, then call buildozer again from the Ubuntu bash.

## Android Studio
Eventually you realize that you have to change AndroidManifest.xml, or add resources, or add special Java/Kotlin code. I got some insights from the book "Building Android Apps in Python Using Kivy with Android Studio: With Pyjnius, Plyer, and Buildozer" from Ahmed Fawzy Mohamed Gad ( https://www.amazon.de/gp/product/B07Z4LZHX9/ref=ppx_yo_dt_b_d_asin_title_o02?ie=UTF8&psc=1). But I think it is a bit overprized, and leaves out many things. It taught me especially, that the directory $BU/dists looks like an Android Studio Project. So go ahead and start Android Studio, and click File/Open (not File/New or File/Import), then navigate to the dists directory. You see that the {package.name}_armeabi-v7a directory is flagged with a green icon. Select it and click OK. Wait a bit so that the Studio settles, it will run some tasks in the background. Perhaps you want to push it, by clicking File/Sync Project with Gradle Files. Toggle in the upper left corner between Project and Android. Under Android, you should eventually see subdirectories manifests, java, java (generated), assets, jniLibs, res. In Gradle Scripts, you see just one build.gradle, marked as Module, i.e. the Project build.gradle does not exist. Everything is in this gradle file.

### Run/Debug Configuration 
In the top middle you have a dropdown list, to the right of the hammer icon, which reads {package.name}_armeabi_v7a. Click on it and choose "Edit Configurations". In the "General" tab, under "Installation Options", select Deploy: APK from app bundle. The "Default APK" leaves out the SDL2 code (as I found out by trial and error, not by understanding what this all means). Under Miscellaneous, you may want to tick "Show logcat automatically" and "Clear log before launch".

When you now click Run (the green triangle in the top middle, a bit to the right), probably some warnings/errors pop up. Among them,
Studio complains that the SDK path in local.properties is invalid (buildozer put 
```
sdk.dir=/home/michaelu/.buildozer/android/platform/android-sdk
```
into it. Studio outputs a notification:
```
The path '\home\michaelu\.buildozer\android\platform\android-sdk'
does not belong to a directory.
Android Studio will use this Android SDK instead:
'D:\Android\AndroidSDK'
and will modify the project's local.properties file.
```
and puts this into local.properties: 
```
## This file must *NOT* be checked into Version Control Systems,
# as it contains information specific to your local configuration.
#
# Location of the SDK. This is only used by Gradle.
# For customization when using a Version Control System, please read the
# header note.
#Sun Mar 08 17:53:01 CET 2020
sdk.dir=D\:\\Android\\AndroidSDK
```

The change we did to the Run configuration causes the "Edit Configuration" window to pop up and to complain about the gradle plugin version. I updated to version 3.6.1 and changed in build.gradle the buildscript/dependencies/classpath to 'com.android.tools.build:gradle:3.6.1'. This takes effect after some time and syncing.
Then Studio complains about the lines in src/main/AndroidManifest.xml
```
   <!-- Android 2.3.3 -->
    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="29" />
```
with the message: 
```
build.gradle: The targetSdk version should not be declared in the android manifest file. You can move the version from the manifest to the defaultConfig in the build.gradle file.
<a href="remove.sdk.from.manifest">Remove targetSdkVersion and sync project</a>
Affected Modules: <a href="openFile:C:/Users/Michael/PycharmProjects/FPFLEGE2/.buildozer/android/platform/build
```
Fix this by deleting the above lines.
Next it complains about a file build/outputs/apk/debug/output.json. Delete it. Then, in my case, Run compiled and deployed the APK.

Probably you have other problems to fix, but hopefully you eventually get here. Remember, we did not yet add functionality, we are merely trying to build and deploy an apk via Android Studio in the same way that we did with "buildozer android debug deploy run".

##More changes
In my case, the app started but crashed early, because sqlite could not open the database file. This requires in AndroidManifest.xml 
the lines
```
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
```
and in main.py I had to add code to aquire these permissions. Furthermore, sending the email with an attachment required two changes: Plyer/android_email.py does not handle attachments, and the attachment URL must be provided by a FileProvider. The FileProvider comes from AndroidX, so I have to add a dependency to AndroidX in the manifest. I will not describe these changes here, you can look them up in the github project, in main.py/aquire_permissions, android_email.py, AndroidManifest.xml, utils.py/getDataDir,  res/xml/provider_paths.xml.

## Saving Android Studio state
What I am aiming at: sometimes you have to change the Python code, sometimes you have to change some Studio files. Changes in the Python code require you to call buildozer again. But then, many of the files you changed under the /dists directory will be overwritten by buildozer!
After I reconstructed the overwritten files 2 or 3 times, I choose the approach which I am following til today: 
When Android Studio produced an apk, I copied the whole /dists subtree to /dists.stu. In dists.stu I keep all files that are used by Android Studio and not identical to those in /dists. Before I call Sync or Run in Android Studio, I copy these files from /dists.stu to /dists. After I changed files for Studio successfully, I copy them from /dists to /dists.stu. Files in Studio do not change so often.

In my github project, in directory MUH, you find a shell script that I call after buildozer, before continuing with Studio, plus the files copied from dists.stu to dists. Also, cpstu.sh removes some output.json files, about which Studio otherwise complains.

When coming back to PyCharm, I currently do not call an inverse script. Rather, I edit local.properties by hand, reverting to the one-liner "sdk.dir=/home/michaelu/.buildozer/android/platform/android-sdk". If I forget this, I get a very nasty error. The error message contains the complete contents of local.properties. This is probably a buildozer bug.

I begin by starting PyCharm, Android Studio, Ubuntu, and a MSDOS command prompt. In cmd I call adb devices, then adb logcat. All these programs stay active. 

Then my loop:
- develop and test in PyCharm
- make sure dists/../local.properties is the one-liner, edit in PyCharm (or call a script)
- call buildozer debug in Ubuntu
- call cpstu.sh in Ubuntu
- in Android Studio sync to Gradle Files, then Run.

When I need a release apk, instead of Run I call Build/Generate Signed Bundle or APK/APK. The result is then to be found in $RE. I install it with adb install $RE/*apk from Ubuntu.

## Alternate approach
Why not open the /dists.stu directory in Android Studio, and copy the files generated by buildozer from /dists to /dists.stu? The sad fact is that I do not know what these files are. Even sadder, even after days of searching the net I did not find a description of the inner workings of buildozer/python-for-android/sdl2. After inspecting an apk file with Studio (just double click the apk), I noticed a file private.mp3, roughly 10MB, two thirds of the apk. It would not play as an audio file! Renaming it to private.tar and opening it with e.g. 7zip, you get an idea that the compiled python code is in there. So I tried to copy private.mp3 from dists to dists.stu, and ran Android Studio on /dists.stu. This worked partly. After changes to Python code, calling buildozer, copying private.mp3 to /dists.stu, the app had not changed. Maybe I overlooked something, maybe private.mp3 does not contain everything, I gave up and returned to the previous scheme. But with some more effort this approach may also work. I am however miffed that nobody cares to explain how python is made to run on Android.








