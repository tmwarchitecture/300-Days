"""
This should be run in ironpython
"""
import subprocess
import rhinoscriptsyntax as rs
import tempfile
import datetime
import os
import shutil

###CLASSES###
class Animation():
    """
    Initialize the Animation.
    Then call AddFrame() to add each screenshot from the active viewport.
    Finish with Create(videoFile) to save the MP4 to the videoFile location.

    Default height and width = 800

    Parameters:
      videoName (str): name of video (eg. "105b")
      sourceFolder (directory path): optional path to save the images. Otherwise saved and deleted in temp.
    Returns:
    Example:
        animation = SaveMP4.Animation("test1")
        for i in range(10):
            animation.AddFrame()
        animation.Create(r'C:\Users\Tim\Desktop')
    """
    def __init__(self, videoName, sourceFolder = None):
        """Initializes the function
        """
        if sourceFolder is not None:
            if os.path.isdir(sourceFolder) == False:
                raise Exception("{} does not exist".format(str(sourceFolder)))
        if os.path.isfile(r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\MP4\MP4_support.py"):
            self.pythonPath = r"C:\Users\Tim\AppData\Local\Programs\Python\Python37-32\python.exe"
            self.supportFole = r"D:\Files\Work\LIBRARY\06_RHINO\10_Python\MP4\MP4_support.py"
        else:
            self.pythonPath = r"C:\Python27\python.exe"
            self.supportFole = r"C:\Tim\200 Days\MP4_support.py"
        self.sourceFolder = sourceFolder
        self.videoName = videoName
        self.fps = 30
        self.width = 800
        self.height = 800
        self.temporary = False
        if sourceFolder is None:
            self.sourceFolder = tempfile.mkdtemp()
            self.temporary = True
        self.frameNumber = 0
        self.frameFilePaths = []


    def AddFrame(self, numberOfPasses = 500):
        """
        Parameters:
        Returns:
            path of the saved frame
        Example:
          fileName = xxxxx
          Format = 190723_xxxxx_003
        """
        year = int(datetime.datetime.today().strftime('%Y'))-2000
        md = datetime.datetime.today().strftime('%m%d')
        date = str(year) + str(md)

        frameNumberStr = self.frameNumber
        frameNumberStr = str(frameNumberStr).zfill(4)
        self.frameNumber += 1

        fileName = date + "_" + self.videoName + "_" + frameNumberStr + ".jpg"
        file_path = os.path.join(self.sourceFolder, fileName)
        self.frameFilePaths.append(file_path)

        rs.Command('-_viewCaptureToFile w=' + str(self.width) + ' N='+str(numberOfPasses)+ ' h='+str(self.height)+' s=1 TransparentBackground=No "' + str(file_path) + '" Enter', False)
        return file_path


    def Create(self, animFolder = None, openAfter = True, frames2Keep = []):
        """
        Parameters:
          animFolder (str): Optional mp4 folder location. ie "C:\Users\Tim\Desktop"
          openAfter (bool): Optional boolean to launch video after completed
          frames2Keep ([int]): Optional frames 2 save into images images folder.
        Returns:
            path of the saved animation
        """
        if self.frameNumber < 1:
            raise Exception("frameNumber = {}. Use AddFrame() method first".format(self.frameNumber))
        
        if animFolder is None:
            animFolder = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        
        animFile = os.path.join(animFolder, self.videoName + '.mp4')
        
        commands = [
        self.pythonPath,
        self.supportFole,
        self.sourceFolder,
        animFile,
        str(self.fps)]
        
        for frameNum in frames2Keep:
            two_up =  os.path.abspath(os.path.join(animFolder ,".."))
            target = os.path.join(two_up, 'images')
            if os.path.isdir(target) == False:
                print "Target {} does not exist".format(target)
            shutil.copy(self.frameFilePaths[int(frameNum)], target)
        
        try:
            subprocess.check_output(commands)
            if openAfter:
                subprocess.Popen(r'explorer ' + animFile)
            if self.temporary:
                try:
                    shutil.rmtree(self.sourceFolder)
                except:
                    print "Failed to remove temp files"
            return animFile
        except subprocess.CalledProcessError as e:
            print "Animation Creation Error"
            print e.output
            return None


    def Cleanup(self):
        if self.temporary:
            try:
                shutil.rmtree(self.sourceFolder)
            except:
                print "Failed to remove temp files"


if __name__ == "__main__":
    filter = "MP4 Video File(*.mp4)|*.mp4|All Files (*.*)|*.*||"
    videoPath = rs.SaveFileName(filter = filter, filename = 'Anim.mp4', extension = 'mp4')
    jpg2mp4(r'C:\Users\Tim\Desktop\temp', videoPath)
