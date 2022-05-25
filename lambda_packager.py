"""
Creates zip files for each cw alarm package and places it in bin folder
which is then deployed to corresponding lambda function using Github actions.
"""

import zipfile
import os
import sys

def create_zip_file(zip_file_name:str, files: list[str], packages: list[str]):
    with zipfile.ZipFile(zip_file_name, 'w') as z:
        for f in files:
            z.write(f)
        for p in packages:
            for root,dir,pfiles in os.walk(p):
                for pf in pfiles:
                    pf_fullpath = os.path.join(root, pf)
                    if "__pycache__" in pf_fullpath:
                        continue
                    z.write(pf_fullpath)

def main():
    
    __root_drive = os.path.splitdrive(sys.executable)[0]
    __base_dir = f"{__root_drive}{os.path.sep}cloudwatch-alarms-manager"

    if (os.getcwd() != __base_dir):
        os.chdir(__base_dir)

    print ("AWS Lambda Packager")
    
    print ("creating ec2 alarms package")
    __zipfile = f"bin{os.path.sep}ec2alarms.zip"
    if os.path.exists(__zipfile):
        os.remove(__zipfile)
    create_zip_file(__zipfile,["cw_ec2alarm_runner.py"], ["ec2alarms"])

    print ("creating s3 alarms package")
    __zipfile = f"bin{os.path.sep}s3alarms.zip"
    if os.path.exists(__zipfile):
        os.remove(__zipfile)
    create_zip_file(__zipfile,["cw_s3alarm_runner.py"], ["s3alarms"])

if __name__ == "__main__":
    main()