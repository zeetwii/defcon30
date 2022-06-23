from secrets import choice
import netCDF4 # needed to read and edit netCDF4 files
import shutil # needed to make a copy of the file
import glob # needed to search current directory
import sys # needed to exit

class Editor:

    def __init__(self, ncFile):
        """
        Init method

        Args:
            ncFile (str): the netCDF4 file to edit
        """

        self.dset = netCDF4.Dataset(ncFile, 'r+')

    def editInteractive(self):
        
        print("\nList of editable variables:")
        var = list(self.dset.variables.keys())
        for i in range(len(var)):
            print(f"{i} : {str(var[i])}")
        
        choice = input("Enter the field number to edit:")
        value = input('Enter the value to set to: ')

        self.dset[str(var[int(choice)])][:] = float(value)

        #self.dset['Total_cloud_cover_entire_atmosphere'][:] = 100
        #self.dset['Total_cloud_cover_entire_atmosphere'][:][self.dset['Total_cloud_cover_entire_atmosphere'][:]  <= 1000] = 150
        #self.dset.close()

if __name__ == "__main__":
    files = glob.glob('./*.nc')

    if len(files) < 1:
        print("No netCDF4 files found in current directory")
        print("Please make sure that all netCDF files are using '.nc' as a file extension")
        sys.exit(1)
    else:
        print("List of '.nc' files:")
        for i in range(len(files)):

            temp = str(files[i]).split('\\')
            files[i] = temp[len(temp) - 1]

            print(f'File {str(i)} : {str(files[i])}')

    fileChoice = input('Enter the number of the file to use, or anything to exit:')

    if str(fileChoice).isdigit():
        if int(fileChoice) < len(files):
            print(f'Using {str(files[int(fileChoice)])}')
            
            tempFile = str(files[int(fileChoice)]).split('.')[0]
            tempFile = tempFile + '-edit.nc'

            shutil.copyfile(str(files[int(fileChoice)]), tempFile)
            print(f"Creating {str(tempFile)} to contain edits")

            editor = Editor(tempFile)

            while True:
                try:
                    print("Edit fields, or press CTRL+C to exit:")
                    editor.editInteractive()
                except KeyboardInterrupt:
                    print("\nExiting")
                    sys.exit(0)

    else:
        print('Not an int, exiting')
        sys.exit()