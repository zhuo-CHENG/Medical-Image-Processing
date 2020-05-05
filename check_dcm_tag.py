from __future__ import print_function

import SimpleITK as sitk
import sys, os

if len ( sys.argv ) < 2:
    print( "Usage: DicomImagePrintTags <input_file>" )
    sys.exit ( 1 )

reader = sitk.ImageFileReader()

reader.SetFileName( sys.argv[1] )
reader.LoadPrivateTagsOn();

reader.ReadImageInformation();

for k in reader.GetMetaDataKeys():
    v = reader.GetMetaData(k)
    print("({0}) = = \"{1}\"".format(k,v))

print("Image Size: {0}".format(reader.GetSize()));
print("Image PixelType: {0}".format(sitk.GetPixelIDValueAsString(reader.GetPixelID())));

